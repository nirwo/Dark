"""
Dark Web Intelligence Scanner - Automatic Scheduler

This module provides functionality to schedule and run periodic dark web scans
without overloading the Tor network. It uses a queuing system to manage
scan requests and execute them at appropriate intervals.
"""

import os
import time
import json
import logging
import datetime
import threading
import schedule
import argparse
from queue import Queue
from collections import deque

# Import the dark web search functionality
from darkweb_search import dark_web_search, save_results_to_json, analyze_results

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='scheduler.log'
)
logger = logging.getLogger('dark-scheduler')

# Global scan queue and thread lock
scan_queue = Queue()
scan_history = deque(maxlen=100)  # Keep track of last 100 scans
active_scans = {}
lock = threading.Lock()

# Configurable settings
TOR_COOLDOWN_SECONDS = 30  # Time to wait between Tor requests
MAX_CONCURRENT_SCANS = 1   # Maximum number of concurrent scans
SCHEDULE_FILE = "scan_schedule.json"

def load_schedule():
    """Load the scan schedule from the JSON file."""
    if not os.path.exists(SCHEDULE_FILE):
        return []
    
    try:
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading schedule: {e}")
        return []

def save_schedule(schedule_data):
    """Save the scan schedule to the JSON file."""
    try:
        with open(SCHEDULE_FILE, 'w') as f:
            json.dump(schedule_data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving schedule: {e}")
        return False

def add_scheduled_scan(query, search_type, frequency, day_of_week=None, time_of_day=None, description=None):
    """
    Add a new scheduled scan to the system.
    
    Args:
        query: The email, domain, username, or phone to search for
        search_type: Type of search (email, domain, username, phone)
        frequency: daily, weekly, monthly
        day_of_week: Required for weekly scans (0-6, Monday is 0)
        time_of_day: Time to run in 24-hour format (HH:MM)
        description: Optional description of this scheduled scan
    
    Returns:
        dict: The newly created schedule entry
    """
    schedule_data = load_schedule()
    
    # Generate unique ID
    scan_id = str(int(time.time()))
    
    # Set default time if not provided
    if not time_of_day:
        time_of_day = "03:00"  # Default to 3 AM
        
    new_entry = {
        "id": scan_id,
        "query": query,
        "search_type": search_type,
        "frequency": frequency,
        "day_of_week": day_of_week,
        "time_of_day": time_of_day,
        "description": description,
        "created_at": datetime.datetime.now().isoformat(),
        "last_run": None,
        "next_run": None,
        "enabled": True
    }
    
    # Calculate next run time
    update_next_run_time(new_entry)
    
    schedule_data.append(new_entry)
    save_schedule(schedule_data)
    
    # Add to the current schedule
    setup_scan_job(new_entry)
    
    return new_entry

def update_next_run_time(entry):
    """Update the next run time for a schedule entry."""
    now = datetime.datetime.now()
    hours, minutes = map(int, entry["time_of_day"].split(":"))
    
    if entry["frequency"] == "daily":
        # Set to today at specified time
        next_run = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        # If that time has already passed today, set to tomorrow
        if next_run <= now:
            next_run = next_run + datetime.timedelta(days=1)
    
    elif entry["frequency"] == "weekly":
        # Get current day of week (0-6, Monday is 0)
        current_dow = now.weekday()
        days_ahead = entry["day_of_week"] - current_dow
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        next_run = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        next_run = next_run + datetime.timedelta(days=days_ahead)
    
    elif entry["frequency"] == "monthly":
        # Run on the 1st of next month
        if now.day == 1 and now.replace(hour=hours, minute=minutes) > now:
            next_run = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        else:
            # Get the 1st of next month
            if now.month == 12:
                next_run = now.replace(year=now.year+1, month=1, day=1, 
                                      hour=hours, minute=minutes, second=0, microsecond=0)
            else:
                next_run = now.replace(month=now.month+1, day=1,
                                      hour=hours, minute=minutes, second=0, microsecond=0)
    
    entry["next_run"] = next_run.isoformat()
    return entry

def cancel_scheduled_scan(scan_id):
    """Cancel a scheduled scan by its ID."""
    schedule_data = load_schedule()
    updated_schedule = [entry for entry in schedule_data if entry["id"] != scan_id]
    
    if len(updated_schedule) < len(schedule_data):
        save_schedule(updated_schedule)
        # Clear all jobs and recreate them without the cancelled one
        schedule.clear()
        for entry in updated_schedule:
            if entry["enabled"]:
                setup_scan_job(entry)
        return True
    
    return False

def setup_scan_job(entry):
    """Set up the scheduled job based on entry configuration."""
    hours, minutes = map(int, entry["time_of_day"].split(":"))
    time_str = f"{hours:02d}:{minutes:02d}"
    
    if entry["frequency"] == "daily":
        schedule.every().day.at(time_str).do(queue_scan, entry["query"], entry["search_type"], entry["id"])
    
    elif entry["frequency"] == "weekly":
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        day_name = days[entry["day_of_week"]]
        getattr(schedule.every(), day_name).at(time_str).do(queue_scan, entry["query"], entry["search_type"], entry["id"])
    
    elif entry["frequency"] == "monthly":
        # For monthly, we'll handle this specially in the run_pending function
        pass

def queue_scan(query, search_type, schedule_id=None):
    """Add a scan to the queue and return immediately."""
    scan_queue.put((query, search_type, schedule_id))
    logger.info(f"Queued scan for {query} (type: {search_type})")
    
    # If this is a scheduled scan, update the last_run timestamp
    if schedule_id:
        schedule_data = load_schedule()
        for entry in schedule_data:
            if entry["id"] == schedule_id:
                entry["last_run"] = datetime.datetime.now().isoformat()
                update_next_run_time(entry)
                break
        save_schedule(schedule_data)
    
    return True

def process_scan_queue():
    """Process the scan queue, respecting rate limits."""
    if scan_queue.empty():
        return
    
    # Check if we can run another scan
    with lock:
        if len(active_scans) >= MAX_CONCURRENT_SCANS:
            return
    
    # Get the next scan
    query, search_type, schedule_id = scan_queue.get()
    
    # Mark as active
    scan_id = f"{query}_{int(time.time())}"
    with lock:
        active_scans[scan_id] = {
            "query": query,
            "search_type": search_type,
            "start_time": datetime.datetime.now(),
            "schedule_id": schedule_id
        }
    
    # Start the scan in a new thread
    threading.Thread(target=run_scan, args=(query, search_type, scan_id)).start()

def run_scan(query, search_type, scan_id):
    """Run a dark web scan and save results."""
    try:
        logger.info(f"Starting scan: {query} (type: {search_type})")
        
        # Run the actual scan
        results = dark_web_search(query, search_type)
        
        # Save results to JSON
        save_results_to_json(query)
        
        # Analyze results
        analysis = analyze_results(query)
        
        # Record scan in history
        scan_history.append({
            "id": scan_id,
            "query": query,
            "search_type": search_type,
            "timestamp": datetime.datetime.now().isoformat(),
            "results_count": analysis.get("total_mentions", 0),
            "highest_risk": max(analysis.get("risk_levels", {}).items(), key=lambda x: ["low", "medium", "high", "critical"].index(x[0]) if x[1] > 0 else -1)[0]
        })
        
        logger.info(f"Completed scan: {query} with {analysis.get('total_mentions', 0)} mentions")
        
    except Exception as e:
        logger.error(f"Error scanning {query}: {str(e)}")
    finally:
        # Clean up
        with lock:
            if scan_id in active_scans:
                del active_scans[scan_id]
        
        # Wait before processing next scan to avoid overloading Tor
        time.sleep(TOR_COOLDOWN_SECONDS)

def scheduler_daemon():
    """Main scheduler daemon that runs continuously."""
    logger.info("Starting Dark Web Scanner scheduler daemon")
    
    # Load and set up all scheduled scans
    schedule_data = load_schedule()
    for entry in schedule_data:
        if entry["enabled"]:
            setup_scan_job(entry)
    
    try:
        while True:
            # Run any scheduled jobs
            schedule.run_pending()
            
            # Check for monthly scans that should run today
            now = datetime.datetime.now()
            if now.day == 1:  # First day of month
                for entry in schedule_data:
                    if entry["frequency"] == "monthly" and entry["enabled"]:
                        # Check if job should run at this hour
                        hours, minutes = map(int, entry["time_of_day"].split(":"))
                        if now.hour == hours and now.minute >= minutes and now.minute < minutes + 5:
                            queue_scan(entry["query"], entry["search_type"], entry["id"])
            
            # Process the scan queue
            process_scan_queue()
            
            # Sleep to avoid high CPU usage
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Scheduler daemon stopped by user")

def get_scan_status():
    """Get the status of all active and queued scans."""
    status = {
        "active_scans": list(active_scans.values()),
        "queued_scans": scan_queue.qsize(),
        "recent_scans": list(scan_history)
    }
    return status

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dark Web Scanner Scheduler")
    parser.add_argument("--add", action="store_true", help="Add a new scheduled scan")
    parser.add_argument("--query", type=str, help="Query to search for")
    parser.add_argument("--type", type=str, choices=["email", "domain", "username", "phone"], help="Type of search")
    parser.add_argument("--frequency", type=str, choices=["daily", "weekly", "monthly"], help="Scan frequency")
    parser.add_argument("--day", type=int, choices=range(7), help="Day of week (0-6, Monday is 0)")
    parser.add_argument("--time", type=str, help="Time to run (HH:MM)")
    parser.add_argument("--description", type=str, help="Description of this scan")
    parser.add_argument("--list", action="store_true", help="List all scheduled scans")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument("--cancel", type=str, help="Cancel a scheduled scan by ID")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon to process scheduled scans")
    
    args = parser.parse_args()
    
    if args.add:
        if not args.query or not args.type or not args.frequency:
            print("Error: --query, --type, and --frequency are required for adding a scan")
            parser.print_help()
            exit(1)
            
        if args.frequency == "weekly" and args.day is None:
            print("Error: --day is required for weekly scans")
            exit(1)
            
        entry = add_scheduled_scan(
            args.query, args.type, args.frequency, 
            args.day, args.time, args.description
        )
        print(f"Added new scheduled scan with ID: {entry['id']}")
        print(f"Next run scheduled for: {entry['next_run']}")
        
    elif args.list:
        schedule_data = load_schedule()
        print(f"Found {len(schedule_data)} scheduled scans:")
        for entry in schedule_data:
            status = "ENABLED" if entry["enabled"] else "DISABLED"
            print(f"{entry['id']} | {status} | {entry['query']} | {entry['frequency']} | Next: {entry['next_run']}")
            
    elif args.status:
        status = get_scan_status()
        print(f"Active scans: {len(status['active_scans'])}")
        for scan in status['active_scans']:
            print(f"  {scan['query']} ({scan['search_type']}) - Started at {scan['start_time']}")
        print(f"Queued scans: {status['queued_scans']}")
        print(f"Recent scans: {len(status['recent_scans'])}")
        for scan in list(status['recent_scans'])[-5:]:  # Show last 5
            print(f"  {scan['timestamp']} - {scan['query']} - {scan['results_count']} mentions (Risk: {scan['highest_risk']})")
            
    elif args.cancel:
        if cancel_scheduled_scan(args.cancel):
            print(f"Successfully cancelled scan with ID: {args.cancel}")
        else:
            print(f"No scan found with ID: {args.cancel}")
            
    elif args.daemon:
        scheduler_daemon()
        
    else:
        parser.print_help()
