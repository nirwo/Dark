#!/usr/bin/env python3
"""
Dark Web Intelligence Scanner - Cron Job Setup

This script helps set up cron jobs for scheduled dark web scans.
It creates the necessary crontab entries to run the scheduler daemon
and manage periodic scans.

Note: This script requires the 'python-crontab' package:
    pip install python-crontab
"""

import os
import sys
import argparse
from crontab import CronTab
import getpass

def setup_scheduler_cron(user=None, install_dir=None):
    """
    Set up a cron job to run the scheduler daemon.
    
    Args:
        user: Username to create cron job for (defaults to current user)
        install_dir: Directory where the Dark Web Scanner is installed
    
    Returns:
        bool: Success or failure
    """
    if not user:
        user = getpass.getuser()
    
    if not install_dir:
        install_dir = os.path.dirname(os.path.abspath(__file__))
    
    try:
        # Create a crontab for the user
        cron = CronTab(user=user)
        
        # Check if job already exists
        for job in cron:
            if 'scheduler.py' in job.command and '--daemon' in job.command:
                print("Scheduler cron job already exists. Removing old job.")
                cron.remove(job)
        
        # Create the job to run every reboot
        job = cron.new(command=f'cd {install_dir} && python3 {install_dir}/scheduler.py --daemon > {install_dir}/scheduler_cron.log 2>&1')
        job.every_reboot()
        
        # Create a job to run every hour as a fallback
        job = cron.new(command=f'cd {install_dir} && if ! pgrep -f "python3.*scheduler.py.*--daemon" > /dev/null; then python3 {install_dir}/scheduler.py --daemon > {install_dir}/scheduler_cron.log 2>&1; fi')
        job.setall('0 * * * *')  # Run at the top of every hour
        
        # Write the crontab
        cron.write()
        print("Successfully set up scheduler cron job.")
        return True
        
    except Exception as e:
        print(f"Error setting up cron job: {e}")
        return False

def setup_manual_scans(user=None, install_dir=None, queries=None):
    """
    Set up cron jobs for specific manual scans.
    
    Args:
        user: Username to create cron job for (defaults to current user)
        install_dir: Directory where the Dark Web Scanner is installed
        queries: List of tuples of (query, search_type, cron_schedule)
    
    Returns:
        bool: Success or failure
    """
    if not user:
        user = getpass.getuser()
    
    if not install_dir:
        install_dir = os.path.dirname(os.path.abspath(__file__))
    
    if not queries:
        return False
    
    try:
        # Create a crontab for the user
        cron = CronTab(user=user)
        
        for query, search_type, schedule in queries:
            # Create a comment to identify this job
            comment = f"dark_web_scan_{search_type}_{query}"
            
            # Check if job already exists
            for job in cron:
                if job.comment == comment:
                    print(f"Removing existing cron job for {query}")
                    cron.remove(job)
            
            # Create the new job
            job = cron.new(command=f'cd {install_dir} && python3 {install_dir}/darkweb_search.py --{search_type} "{query}" >> {install_dir}/cron_scans.log 2>&1', comment=comment)
            
            # Set the schedule
            if schedule == 'daily':
                job.setall('0 3 * * *')  # Run at 3 AM every day
            elif schedule == 'weekly':
                job.setall('0 3 * * 0')  # Run at 3 AM every Sunday
            elif schedule == 'monthly':
                job.setall('0 3 1 * *')  # Run at 3 AM on the 1st of each month
            else:
                # Custom schedule
                job.setall(schedule)
        
        # Write the crontab
        cron.write()
        print(f"Successfully set up {len(queries)} scan cron jobs.")
        return True
        
    except Exception as e:
        print(f"Error setting up cron jobs: {e}")
        return False

def remove_all_scan_jobs(user=None):
    """
    Remove all Dark Web Scanner related cron jobs.
    
    Args:
        user: Username to remove cron jobs for (defaults to current user)
    
    Returns:
        bool: Success or failure
    """
    if not user:
        user = getpass.getuser()
    
    try:
        # Create a crontab for the user
        cron = CronTab(user=user)
        
        # Find all related jobs
        jobs_to_remove = []
        for job in cron:
            if 'scheduler.py' in job.command or 'darkweb_search.py' in job.command:
                jobs_to_remove.append(job)
        
        # Remove the jobs
        for job in jobs_to_remove:
            cron.remove(job)
        
        # Write the crontab
        cron.write()
        print(f"Successfully removed {len(jobs_to_remove)} Dark Web Scanner cron jobs.")
        return True
        
    except Exception as e:
        print(f"Error removing cron jobs: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dark Web Scanner Cron Job Setup")
    parser.add_argument("--setup-scheduler", action="store_true", help="Set up scheduler daemon cron job")
    parser.add_argument("--add-scan", action="store_true", help="Add a manual scan cron job")
    parser.add_argument("--query", type=str, help="Query to search for")
    parser.add_argument("--type", type=str, choices=["email", "domain", "username", "phone"], help="Type of search")
    parser.add_argument("--schedule", type=str, choices=["daily", "weekly", "monthly"], default="weekly", help="Cron schedule")
    parser.add_argument("--custom-schedule", type=str, help="Custom cron schedule (e.g., '0 3 * * 0')")
    parser.add_argument("--remove-all", action="store_true", help="Remove all Dark Web Scanner cron jobs")
    parser.add_argument("--user", type=str, help="Username for crontab (defaults to current user)")
    parser.add_argument("--install-dir", type=str, help="Installation directory (defaults to current directory)")
    
    args = parser.parse_args()
    
    if args.setup_scheduler:
        setup_scheduler_cron(args.user, args.install_dir)
        
    elif args.add_scan:
        if not args.query or not args.type:
            print("Error: --query and --type are required for adding a scan")
            parser.print_help()
            exit(1)
            
        schedule = args.custom_schedule if args.custom_schedule else args.schedule
        queries = [(args.query, args.type, schedule)]
        setup_manual_scans(args.user, args.install_dir, queries)
        
    elif args.remove_all:
        remove_all_scan_jobs(args.user)
        
    else:
        parser.print_help()
