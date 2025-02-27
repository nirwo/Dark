import os
import requests
import threading
import datetime
import time
import re
import json
import logging
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory, session
from flask_login import LoginManager, login_required, current_user
from flask_migrate import Migrate
import time
import random

# Import our modules
from models import db, User, init_db, SearchHistory
from auth import auth
from history import history

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-testing-only')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dark_web_scanner.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
init_db(app)

# Setup Flask-Migrate
migrate = Migrate(app, db)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register blueprints
app.register_blueprint(auth)
app.register_blueprint(history)

# --- Tor Proxy Configuration ---
TOR_PROXY = {
    "http": "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050"
}

# --- User Agent Rotation ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0"
]

# --- Dark Web Search Engines ---
TARGETS = [
    # Dark Web Search Engines (General Dark Web Content)
    {
        "name": "Ahmia",
        "url": "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search?q={query}",
        "type": "general",
        "description": "One of the most reliable dark web search engines that indexes .onion pages. Can be used to search for leaks."
    },
    {
        "name": "Torch",
        "url": "http://xmh57jrknzkhv6y3ls3ubitzfqnkrwxhopf5aygthi7d6rplyvk3noyd.onion/search?q={query}",
        "type": "general",
        "description": "One of the largest .onion search engines, indexes many hidden services."
    },
    {
        "name": "Haystak",
        "url": "http://haystak5njsmn2hqkewecpaxetahtwhsbsa64jom2k22z5afxhnpxfid.onion/search?q={query}",
        "type": "general",
        "description": "A deep index of .onion sites, useful for finding hidden leak pages."
    },
    {
        "name": "Deep Search",
        "url": "http://search7tdrcvri22rieiwgi5g46qnwsesvnubqav2xakhezv4hjzkkad.onion/search?q={query}",
        "type": "general",
        "description": "A reliable search engine that indexes .onion sites in a more structured way."
    },
    {
        "name": "TorDex",
        "url": "http://tordexyb63aknnvuzyqabeqx6l7zdiesfos22nisv6zbj6c6o3h6ijyd.onion/search?q={query}",
        "type": "general",
        "description": "A search engine specifically for .onion domains."
    },
    
    # Dark Web Breach Databases (Check Email/User Breaches)
    {
        "name": "OnionSearch",
        "url": "http://onionsearchservlty4vzd4z6s2nqwe5vt2vqspj46sw36w3b3xrsd77yd.onion/search?q={query}",
        "type": "breach",
        "description": "A search engine specialized in finding breach dumps and leaked data on the dark web."
    },
    {
        "name": "Hacked Emails Lookup",
        "url": "http://hackedemailsb4dnvmaic55h5kqgmoylye6s3vczhj4zzb62adttyd.onion/search?q={query}",
        "type": "breach",
        "description": "Lets you check if an email address appears in a known breach dump."
    },
    {
        "name": "IntelX Dark Web Search",
        "url": "http://kuddyrdtftnkgzmlmbmxlizwi77h3zxtom5vgu65cmxkrxnpxhv6toyd.onion/search?q={query}",
        "type": "breach",
        "description": "Search engine indexing leaked credentials and sensitive documents."
    },
    {
        "name": "DarkBing",
        "url": "http://darkbing7mfomaavciwltpnuwtv7bymjsoaj5ltkjqizdcwvwma6tyd.onion/search?q={query}",
        "type": "breach",
        "description": "Focuses on breached databases, often including credential leaks."
    },
    
    # Marketplaces for Stolen Data (Leaked Credentials, Financial Data)
    {
        "name": "Brian's Club",
        "url": "http://briansclcfyc5xpe73xlvwsujp2ujlg7wdm7vkk33wv4b75yhyzdwioyd.onion/search?q={query}",
        "type": "market",
        "description": "One of the largest stolen credit card markets, frequently targeted by law enforcement."
    },
    {
        "name": "BidenCash",
        "url": "http://bidencash7srks2wmb6ksmow4ktswio7l2w6we4pycicnww2dfjzzkyd.onion/search?q={query}",
        "type": "market",
        "description": "Stolen credit card and banking data; occasionally releases free leaks."
    },
    {
        "name": "Russian Market",
        "url": "http://russianmarketuvklb5p4rhwnrrn3kyooyhlf52fsbvfr3yp5u3zy67cid.onion/search?q={query}",
        "type": "market",
        "description": "Specializes in hacked PayPal accounts, bank logs, and financial credentials."
    },
    {
        "name": "AllWorld.Cards",
        "url": "http://awcardsybzcmmzqkbzmwfwjht7x6tupvrz6foztfuowumgi2bq5joiqd.onion/search?q={query}",
        "type": "market",
        "description": "Stolen credit cards and bank account credentials, with occasional public leaks."
    },
    
    # Ransomware Leak Sites (Corporate & Personal Leaks)
    {
        "name": "ALPHV (BlackCat) Ransomware Leaks",
        "url": "http://alphvmmf3wzhvf5ty7yqgt5hcbqfndfqkrbsllhncjh6sziqfrp4j5yd.onion/posts?q={query}",
        "type": "ransomware",
        "description": "A ransomware gang that leaks stolen corporate and user data."
    },
    {
        "name": "LockBit Leaks",
        "url": "http://lockbitdrja3rx4ffxvqhbwx5jbf5xckie6mnb2zvvykv5qdmgbt3mad.onion/search?q={query}",
        "type": "ransomware",
        "description": "One of the most active ransomware gangs publishing corporate and personal data leaks."
    },
    {
        "name": "Medusa Blog",
        "url": "http://medusa5j6xjwp7qopuwjrnvbhnqcxj2bg3tntcz7plhkjlgbhfc3dyd.onion/search?q={query}",
        "type": "ransomware",
        "description": "Leaks company databases including user account info from hacked companies."
    },
    
    # Forums Where Leaked Data is Shared
    {
        "name": "BreachForums (Rebuilt)",
        "url": "http://breachforums76tdp26mpxvc2wr5edfg4eqme6d6uhc7gbkr46iyd.onion/search?q={query}",
        "type": "forum",
        "description": "A revival of the BreachForums site, where stolen data is shared and sold."
    },
    {
        "name": "Exploit Forum",
        "url": "http://exploit5f5zhr53ntuvkaigc2yaz7xuf7rohtdqvvy6hwgvlba2vid.onion/search?q={query}",
        "type": "forum",
        "description": "A Russian hacking forum with stolen logins, bank access, and exploits."
    },
    {
        "name": "XSS Forum",
        "url": "http://xss6al27uwo2o2ry4br6bkyrvye24jdu5p2twe5hhlkivwdn7xil7iid.onion/search?q={query}",
        "type": "forum",
        "description": "A hacking and data trading forum, often has leaks from major breaches."
    },
    
    # Anonymous Paste Sites (Unstructured Data Dumps)
    {
        "name": "Doxbin",
        "url": "http://doxbinwruaxknfyzxzwbjxb6vvf7uukpzbhdeqrzg6qtp7zrvl6vmyyd.onion/search?q={query}",
        "type": "paste",
        "description": "A notorious doxing site containing personal data leaks, passwords, and addresses."
    },
    {
        "name": "DeepPaste",
        "url": "http://deeppastezxi2xmnznwfxcmmoi3nn5udl6dgsqk3pzu3uk2p4qmyd.onion/search?q={query}",
        "type": "paste",
        "description": "A pastebin-style site where leaked passwords and databases appear."
    },
    {
        "name": "OnionPaste",
        "url": "http://onionpastemw3tcypztu3h7hnm4zzir2d4qvc7e6w3ly2xekrdufnjyid.onion/search?q={query}",
        "type": "paste",
        "description": "Another anonymous pasting service, often used for sharing stolen credentials."
    }
]

# --- Store Search Results ---
search_results = {}

# Enhanced structure for tracking site-specific search progress
search_engines_status = {}

# --- Breach and Paste Patterns ---
BREACH_PATTERNS = [
    r'breach',
    r'leak',
    r'dump',
    r'hack',
    r'pwn',
    r'compromise',
    r'data\s*breach',
    r'account\s*breach',
    r'password\s*breach',
    r'credential'
]

def get_headers():
    """Get randomized headers to avoid detection"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }

def extract_breach_context(text, email, site_type="general"):
    """Extract breach context from surrounding text with enhanced risk assessment"""
    email_pattern = re.escape(email.lower())
    breach_context = None
    risk_level = "medium"
    
    # Look for email with surrounding breach indicators
    for pattern in BREACH_PATTERNS:
        regex = rf'(.{{0,100}})({pattern})(.{{0,100}})({email_pattern})(.{{0,100}})'
        match = re.search(regex, text.lower(), re.IGNORECASE)
        if match:
            breach_context = f"...{match.group(1)}{match.group(2)}{match.group(3)}{match.group(4)}{match.group(5)}..."
            
            # Adjust risk level based on site type and breach pattern
            if site_type == "ransomware":
                risk_level = "critical"
            elif site_type == "breach" or site_type == "market":
                risk_level = "high"
            elif site_type == "forum" or site_type == "paste":
                risk_level = "medium-high"
            else:
                risk_level = "medium"
                
            break
            
    # If no breach context found, just return surrounding text
    if not breach_context:
        idx = text.lower().find(email.lower())
        if idx >= 0:
            start = max(0, idx-100)
            end = min(len(text), idx+100)
            breach_context = f"...{text[start:end]}..."
    
    return {
        "context": breach_context,
        "risk_level": risk_level
    }

def assess_onion_sites(email, onion_links):
    """
    Visits extracted .onion links to assess their content for email presence.
    Enhanced to look for breach indicators.
    """
    global search_results
    
    for link in onion_links:
        # Skip non-onion links
        if ".onion" not in link:
            continue
            
        # Normalize link
        if not link.startswith("http"):
            link = "http://" + link
            
        # Skip if already processed
        processed = False
        for site_data in search_results[email]["results"].values():
            for mention in site_data.get("mentions", []):
                if link in mention.get("context", ""):
                    processed = True
                    break
            if processed:
                break
                
        if processed:
            continue
            
        try:
            # Make the request
            headers = get_headers()
            response = requests.get(link, headers=headers, proxies=TOR_PROXY, timeout=20)
            
            if response.status_code != 200:
                logger.debug(f"Failed to access onion site: {link} - Status code: {response.status_code}")
                continue
                
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text().lower()
            
            # Check if email appears in the page
            if email.lower() in page_text:
                # Extract site title
                title = "Unknown Onion Site"
                if soup.title and soup.title.string:
                    title = soup.title.string.strip()
                elif soup.find('h1'):
                    title = soup.find('h1').get_text().strip()
                    
                # Format as domain if no better title
                if title == "Unknown Onion Site" and ".onion" in link:
                    domain = link.split("//")[-1].split("/")[0]
                    title = f"Onion Site: {domain}"
                
                # Limit title length
                if len(title) > 50:
                    title = title[:47] + "..."
                    
                # Create or update site data
                if title not in search_results[email]["results"]:
                    search_results[email]["results"][title] = {
                        "risk_level": "high",  # Onion sites with direct email mentions are high risk
                        "description": "This is a dark web (.onion) site containing a direct mention of the target email.",
                        "type": "onion_site",
                        "mentions": []
                    }
                
                # Extract snippet
                idx = page_text.find(email.lower())
                start = max(0, idx - 100)
                end = min(len(page_text), idx + 100)
                snippet = page_text[start:end]
                
                # Add mention
                mention = {
                    "context": f"Found on onion site: {link}\n{snippet}",
                    "date": datetime.datetime.now().strftime('%Y-%m-%d')
                }
                search_results[email]["results"][title]["mentions"].append(mention)
                
                # Check for breach patterns
                for pattern in BREACH_PATTERNS:
                    if re.search(pattern, snippet, re.IGNORECASE):
                        search_results[email]["results"][title]["risk_level"] = "critical"
                        search_results[email]["results"][title]["breach_indicator"] = pattern
                        break
                
                # Log the finding
                logger.warning(f"Found mention of {email} on onion site: {link}")
                
                # Extract additional data points for enhanced analysis
                extracted_data = {
                    "site_url": link,
                    "snippet": snippet,
                    "context_length": len(snippet),
                    "surrounding_terms": [term for term in BREACH_PATTERNS if term.lower() in snippet.lower()],
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                # Add to the mention for JSON logging
                mention["extracted_data"] = extracted_data
                
                # Log the finding
                with open(os.path.join(os.path.dirname(__file__), 'search_log.txt'), 'a') as log_file:
                    log_file.write(f"[Onion Site: {title}] Found mention: {snippet}\n")
                    
        except Exception as e:
            logger.error(f"Error assessing onion site {link}: {str(e)}")

def process_search_result(idx, site, search_query, search_type, thread_results, target_type):
    result = search_site(search_query, search_type, site)
    thread_results[idx] = result
    
    # Update search engine status
    global search_engines_status
    search_engines_status[search_query][site["name"]]["status"] = "completed"
    search_engines_status[search_query][site["name"]]["end_time"] = datetime.datetime.now().strftime('%H:%M:%S')
    
    # Update progress counters
    global search_results
    search_results[search_query]["engines_progress"][target_type]["completed"] += 1
    
    if result and result.get("found", False):
        search_results[search_query]["engines_progress"][target_type]["found_results"] += 1

def search_site(email, search_type, site):
    """Search a specific site for the specified identifier"""
    try:
        url = site["url"].format(query=email)
        result = {"source": site["name"], "type": site["type"], "found": False}
        
        # Determine risk level based on site type
        if site["type"] == "breach":
            result["risk_level"] = "high"
        elif site["type"] == "paste":
            result["risk_level"] = "medium-high"
        elif site["type"] == "forum":
            result["risk_level"] = "medium"
        elif site["type"] == "market":
            result["risk_level"] = "high"
        elif site["type"] == "ransomware":
            result["risk_level"] = "critical"
        else:
            result["risk_level"] = "medium"
        
        # Generic description based on site type
        type_descriptions = {
            "breach": f"This is a known data breach repository that may contain leaked credentials.",
            "paste": f"This is a paste site often used to anonymously share text content, including leaked data.",
            "forum": f"This is a hacking-focused discussion forum where sensitive information may be shared or traded.",
            "market": f"This is a darknet marketplace where data and credentials may be bought and sold.",
            "general": f"This is a general dark web search engine that indexes .onion sites.",
            "specialized": f"This is a specialized search service focused on specific types of dark web content.",
            "ransomware": f"This is a ransomware leak site where stolen corporate and personal data is published."
        }
        result["description"] = type_descriptions.get(site["type"], "A dark web resource that may contain sensitive information.")
        
        # Log the attempt
        logger.debug(f"Searching {site['name']} for {search_type}: {email}")
        
        try:
            # Make the request
            headers = get_headers()
            response = requests.get(url, headers=headers, proxies=TOR_PROXY, timeout=30)
            
            if response.status_code != 200:
                result["message"] = f"Error: Site returned status code {response.status_code}"
                return result
                
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract text content and look for the email
            page_text = soup.get_text()
            
            # Check if email appears in the page
            if email.lower() in page_text.lower():
                result["found"] = True
                
                # Special handling for ransomware leak sites
                if site["type"] == "ransomware":
                    # Extract more comprehensive context for ransomware sites
                    # Look for data breach details and company information
                    breach_details = {}
                    
                    # Look for date patterns (common in ransomware posts)
                    date_matches = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}', page_text)
                    if date_matches:
                        breach_details["date"] = date_matches[0]
                        
                    # Look for data size indicators
                    size_matches = re.findall(r'\d+(?:\.\d+)?\s*(?:GB|MB|TB|kb|mb|gb|tb)', page_text)
                    if size_matches:
                        breach_details["data_size"] = size_matches[0]
                        
                    # Look for victim organization name (near the email)
                    org_patterns = [
                        r'(?:company|organization|victim|target):\s*([A-Za-z0-9\s\.]+)',
                        r'([A-Za-z0-9\s\.]+)(?:\s+was\s+hacked|\s+breach|\s+leak)'
                    ]
                    
                    for pattern in org_patterns:
                        org_match = re.search(pattern, page_text, re.IGNORECASE)
                        if org_match:
                            breach_details["organization"] = org_match.group(1).strip()
                            break
                            
                    # Enhance risk level based on context
                    result["risk_level"] = "critical"
                    
                    # Create detailed context
                    if breach_details:
                        context_parts = ["RANSOMWARE LEAK DETAILS:"]
                        if "organization" in breach_details:
                            context_parts.append(f"Organization: {breach_details['organization']}")
                        if "date" in breach_details:
                            context_parts.append(f"Date: {breach_details['date']}")
                        if "data_size" in breach_details:
                            context_parts.append(f"Data Size: {breach_details['data_size']}")
                            
                        result["breach_details"] = breach_details
                        result["enhanced_context"] = "\n".join(context_parts)
                
                # Special handling for OnionLand Search
                if site["name"] == "OnionLand Search":
                    # Process search results
                    search_info = None
                    search_results_items = []
                    
                    # Extract search info (About X results found)
                    info_text = re.search(r"About (\d+) results found", page_text)
                    if info_text:
                        search_info = info_text.group(0)
                        
                    # Find all search result items
                    result_items = soup.select('.result-item')
                    if not result_items:  # Alternative selector if needed
                        result_items = soup.select('.search-result')
                    
                    if not result_items:  # Generic approach
                        # Try to find results by looking for common patterns
                        for div in soup.find_all('div', class_=True):
                            if 'result' in div.get('class', [''])[0].lower():
                                result_items.append(div)
                    
                    # Process each result item
                    for item in result_items:
                        item_title = item.find('h4')
                        item_url = item.find('a')
                        item_desc = item.find('p')
                        
                        title = item_title.get_text() if item_title else "Untitled Result"
                        url = item_url.get('href') if item_url else "#"
                        description = item_desc.get_text() if item_desc else ""
                        
                        if email.lower() in (title + " " + description).lower():
                            search_results_items.append({
                                "title": title,
                                "url": url,
                                "description": description
                            })
                    
                    # Create mention entries for each search result
                    for idx, item in enumerate(search_results_items):
                        context = f"[Result {idx+1}] Title: {item['title']}\nURL: {item['url']}\nDescription: {item['description']}"
                        
                        # If we don't have specific search results, at least include the search info
                        if not search_results_items and search_info:
                            context = f"{search_info}. The individual results couldn't be parsed automatically."
                        
                        mention = {
                            "context": context,
                            "date": datetime.datetime.now().strftime('%Y-%m-%d')
                        }
                        
                        if "mentions" not in result:
                            result["mentions"] = []
                            
                        result["mentions"].append(mention)
                
                # Standard extraction for other sites
                if "mentions" not in result:
                    # Extract the entire page text or a much larger context window
                    # Instead of just a few words before and after
                    words = page_text.split()
                    email_idx = -1
                    
                    for i, word in enumerate(words):
                        if email.lower() in word.lower():
                            email_idx = i
                            break
                            
                    if email_idx >= 0:
                        start_idx = max(0, email_idx - 75)  # Increased from 15 words to 75 words
                        end_idx = min(len(words), email_idx + 75)  # Increased from 15 words to 75 words
                        context = " ".join(words[start_idx:end_idx])
                        
                        # Store the full URL and full context without truncating with ellipses
                        result["snippet"] = context
                        result["url"] = url
                        
                        # Check for breach patterns
                        for pattern in BREACH_PATTERNS:
                            if re.search(pattern, context, re.IGNORECASE):
                                result["risk_level"] = "high"
                                result["breach_indicator"] = pattern
                                break
                
                # Extract any .onion links for further assessment
                onion_links = []
                for link in soup.find_all('a'):
                    href = link.get('href')
                    if href and '.onion' in href:
                        onion_links.append(href)
                        
                if onion_links:
                    result["links"] = onion_links
                    
                # Log the success
                logger.debug(f"Found mention of {search_type}: {email} on {site['name']}")
                
            return result
                
        except requests.RequestException as e:
            logger.error(f"Error searching {site['name']}: {str(e)}")
            result["message"] = f"Error: {str(e)}"
            return result
            
    except Exception as e:
        logger.error(f"Unexpected error searching {site['name']}: {str(e)}")
        return {"source": site["name"], "message": f"Error: {str(e)}", "found": False}

def dark_web_search(search_query, search_type):
    """
    Searches for the specified identifier in multiple dark web search engines
    and follows extracted .onion links for further assessment.
    Enhanced to search more sources and analyze breach context.
    """
    global search_results, search_engines_status
    search_results[search_query] = {
        "status": "processing",
        "message": "Searching dark web sources...",
        "results": {},
        "sites_searched": len(TARGETS),
        "started_at": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "engines_progress": {}  # Will track progress of each search engine category
    }
    
    # Initialize the search engine status tracker for this query
    search_engines_status[search_query] = {}

    all_onion_links = []
    
    # Group targets by type for better status reporting
    target_types = {
        "general": "general search engines",
        "breach": "breach databases",
        "paste": "paste sites",
        "forum": "hacking forums",
        "market": "dark web marketplaces",
        "ransomware": "ransomware leak sites",
        "specialized": "specialized search services"
    }
    
    # Initialize progress for each target type
    for target_type, description in target_types.items():
        search_results[search_query]["engines_progress"][target_type] = {
            "description": description,
            "status": "pending",
            "total": len([site for site in TARGETS if site["type"] == target_type]),
            "completed": 0,
            "in_progress": 0,
            "found_results": 0
        }
    
    # Log the search
    with open(os.path.join(os.path.dirname(__file__), 'search_log.txt'), 'a') as log_file:
        log_file.write(f"\n=== Dark Web Scan for {search_type}: {search_query} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    
    # Search each type of target
    for target_type, description in target_types.items():
        search_results[search_query]["message"] = f"Searching {description}..."
        
        # Update category status to in_progress
        search_results[search_query]["engines_progress"][target_type]["status"] = "in_progress"
        
        # Find all targets of this type
        type_targets = [site for site in TARGETS if site["type"] == target_type]
        
        if not type_targets:
            # Skip if no targets of this type
            search_results[search_query]["engines_progress"][target_type]["status"] = "completed"
            continue
            
        # Create threads for parallel searching
        threads = []
        thread_results = [None] * len(type_targets)
        
        for i, site in enumerate(type_targets):
            # Update search engine status
            search_engines_status[search_query][site["name"]] = {
                "status": "in_progress",
                "type": target_type,
                "start_time": datetime.datetime.now().strftime('%H:%M:%S')
            }
            
            # Increment in_progress counter
            search_results[search_query]["engines_progress"][target_type]["in_progress"] += 1
            
            thread = threading.Thread(
                target=lambda idx, s: process_search_result(idx, s, search_query, search_type, thread_results, target_type),
                args=(i, site)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Update category status to completed
        search_results[search_query]["engines_progress"][target_type]["status"] = "completed"
        search_results[search_query]["engines_progress"][target_type]["in_progress"] = 0
        
        # Process results from each thread
        for result in thread_results:
            if result and result.get("found", False):
                site_name = result.get("source", "Unknown Source")
                
                # Format for frontend
                if site_name not in search_results[search_query]["results"]:
                    search_results[search_query]["results"][site_name] = {
                        "risk_level": result.get("risk_level", "medium"),
                        "description": result.get("description", ""),
                        "type": result.get("type", "unknown"),
                        "mentions": []
                    }
                
                # Add pre-processed mentions if available
                if "mentions" in result:
                    search_results[search_query]["results"][site_name]["mentions"].extend(result["mentions"])
                # Add mention from snippet if available
                elif "snippet" in result:
                    mention = {
                        "context": result["snippet"],
                        "date": result.get("date", datetime.datetime.now().strftime('%Y-%m-%d'))
                    }
                    search_results[search_query]["results"][site_name]["mentions"].append(mention)
                
                # Extract onion links for further investigation
                if "links" in result:
                    all_onion_links.extend(result["links"])
                
                # Log significant findings
                with open(os.path.join(os.path.dirname(__file__), 'search_log.txt'), 'a') as log_file:
                    context = result.get('snippet', 'No context available')
                    if "mentions" in result and result["mentions"]:
                        context = ', '.join([m.get('context', 'No context') for m in result["mentions"][:3]])
                        if len(result["mentions"]) > 3:
                            context += f" (and {len(result['mentions']) - 3} more...)"
                    log_file.write(f"[{site_name}] Found: {context}\n")
            elif result and "message" in result and "Error" in result["message"]:
                with open(os.path.join(os.path.dirname(__file__), 'search_log.txt'), 'a') as log_file:
                    log_file.write(f"[{result.get('source', 'Unknown')}] {result['message']}\n")

    # Deduplicate onion links
    all_onion_links = list(set(all_onion_links))

    # Assess found onion links for more context
    if all_onion_links:
        search_results[search_query]["message"] = "Assessing extracted onion sites..."
        assess_onion_sites(search_query, all_onion_links[:20])  # Limit to 20 links to avoid excessive time

    search_results[search_query]["status"] = "completed"
    search_results[search_query]["message"] = "Dark web scan completed"

    # Log completion
    with open(os.path.join(os.path.dirname(__file__), 'search_log.txt'), 'a') as log_file:
        log_file.write(f"=== Scan completed with {len(search_results[search_query]['results'])} sources having hits ===\n")

    # Record search in database
    if hasattr(current_user, 'id'):  # Make sure user is authenticated
        try:
            # Create a new search history entry
            search_history = SearchHistory(
                user_id=current_user.id,
                result_count=len(search_results[search_query]['results']),
                results_json=json.dumps(search_results[search_query]),
                search_duration=(datetime.datetime.now() - datetime.datetime.strptime(
                    search_results[search_query].get('started_at', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    '%Y-%m-%d %H:%M:%S'
                )).total_seconds()
            )
            
            # Determine highest risk level
            highest_risk = 'low'
            risk_levels = {'critical': 4, 'high': 3, 'medium-high': 2, 'medium': 1, 'low': 0}
            
            for site_data in search_results[search_query]['results'].values():
                site_risk = site_data.get('risk_level', 'low')
                if risk_levels.get(site_risk, 0) > risk_levels.get(highest_risk, 0):
                    highest_risk = site_risk
                    
            search_history.risk_level = highest_risk
            
            # Handle both new and old database structures
            if hasattr(search_history, 'search_query'):
                search_history.search_query = search_query
                search_history.search_type = search_type
            else:
                search_history.email_searched = search_query
                
            db.session.add(search_history)
            db.session.commit()
            logger.info(f"Recorded search history for {search_query}")
        except Exception as e:
            logger.error(f"Error recording search history: {str(e)}")
            db.session.rollback()

    # Save results to JSON
    save_results_to_json(search_query)

    # Analyze results
    analysis = analyze_results(search_query)
    logger.info(f"Analysis results for {search_query}: {analysis}")

def save_results_to_json(email, timestamp=None):
    """
    Save search results to a JSON file for archiving and further analysis.
    
    Args:
        email: The search query email/identifier
        timestamp: Optional custom timestamp, defaults to current time
    
    Returns:
        str: Path to the saved JSON file
    """
    if not timestamp:
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create results directory if it doesn't exist
    results_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    
    # Sanitize filename
    safe_email = re.sub(r'[^\w\-\.]', '_', email)
    filename = f"{safe_email}_{timestamp}.json"
    filepath = os.path.join(results_dir, filename)
    
    # Add metadata
    results_with_metadata = {
        "search_query": email,
        "search_timestamp": timestamp,
        "search_results": search_results.get(email, {}),
        "analysis_version": "1.0"
    }
    
    # Save to file
    with open(filepath, 'w') as f:
        json.dump(results_with_metadata, f, indent=2, default=str)
    
    logging.info(f"Search results for {email} saved to {filepath}")
    return filepath

def analyze_results(email):
    """
    Analyze search results to extract insights and patterns.
    
    Args:
        email: The search query email/identifier
    
    Returns:
        dict: Analysis results
    """
    if email not in search_results:
        return {"error": "No results found for this query"}
    
    results = search_results[email]
    analysis = {
        "query": email,
        "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "total_mentions": 0,
        "risk_levels": {"low": 0, "medium": 0, "high": 0, "critical": 0},
        "source_breakdown": {},
        "most_concerning_sites": [],
        "breach_indicators": []
    }
    
    # Count mentions and categorize by risk
    for site_name, site_data in results.get("results", {}).items():
        mentions_count = len(site_data.get("mentions", []))
        analysis["total_mentions"] += mentions_count
        
        # Categorize by risk level
        risk_level = site_data.get("risk_level", "low")
        analysis["risk_levels"][risk_level] += 1
        
        # Source breakdown
        site_type = site_data.get("type", "unknown")
        if site_type not in analysis["source_breakdown"]:
            analysis["source_breakdown"][site_type] = 0
        analysis["source_breakdown"][site_type] += 1
        
        # Track concerning sites
        if risk_level in ["high", "critical"] and mentions_count > 0:
            analysis["most_concerning_sites"].append({
                "name": site_name,
                "risk_level": risk_level,
                "mentions": mentions_count
            })
        
        # Track breach indicators
        if "breach_indicator" in site_data:
            analysis["breach_indicators"].append({
                "site": site_name,
                "indicator": site_data["breach_indicator"]
            })
    
    # Sort concerning sites by risk level
    analysis["most_concerning_sites"].sort(
        key=lambda x: (["high", "critical"].index(x["risk_level"]) if x["risk_level"] in ["high", "critical"] else -1, x["mentions"]), 
        reverse=True
    )
    
    return analysis

@app.route('/')
@login_required
def index():
    """
    Web UI: Displays the search form and results.
    """
    # Pass the email parameter if it was provided
    email = request.args.get('email', '')
    logger.debug(f"Rendering index template with Flask...")
    return render_template('index.html', email=email)

@app.route('/search', methods=['POST'])
@login_required
def search():
    """
    Initiates a dark web search for the specified identifier.
    """
    search_query = request.form.get('searchQuery')
    search_type = request.form.get('searchType', 'email')
    
    if not search_query:
        return jsonify({"status": "error", "message": "No search query provided"})
    
    # Store the current search info in the session
    session['current_search'] = {
        'query': search_query,
        'type': search_type,
        'started_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'in_progress'
    }
    
    # Start a new thread for the search to prevent blocking
    search_thread = threading.Thread(target=dark_web_search, args=(search_query, search_type))
    search_thread.daemon = True
    search_thread.start()
    
    return jsonify({
        "status": "started", 
        "message": f"Search started for {search_type}: {search_query}"
    })

@app.route('/results')
@login_required
def get_results():
    """
    Fetches the latest search results.
    """
    search_query = request.args.get('searchQuery')
    search_type = request.args.get('searchType', 'email')
    
    if not search_query:
        return jsonify({"status": "error", "message": "No search query provided"})
    
    # Check if a search is in progress from the session
    current_search = session.get('current_search', {})
    if current_search.get('query') != search_query or current_search.get('type') != search_type:
        return jsonify({"status": "error", "message": "No search in progress for this query"})
    
    if search_query in search_results:
        try:
            return jsonify(search_results[search_query])
        except Exception as e:
            logger.error(f"Error reading results: {str(e)}")
    
    # If we're here, either no results yet or error reading file
    return jsonify({
        "status": "in_progress",
        "message": f"Search in progress for {search_type}: {search_query}",
        "progress": random.randint(10, 90),  # Fake progress
        "query": search_query,
        "type": search_type
    })

@app.route("/test_static")
def test_static():
    """Test if static files are accessible."""
    return """
    <html>
    <head><title>Static File Test</title></head>
    <body>
        <h1>Testing Static Files</h1>
        <p>Background pattern:</p>
        <img src="/static/images/background-pattern.png" width="200" alt="Background Pattern">
        <p>Dark web background:</p>
        <img src="/static/images/dark-web-bg.jpg" width="200" alt="Dark Web Background">
        <p>World map:</p>
        <img src="/static/images/world-map.png" width="200" alt="World Map">
        <p>Security badge:</p>
        <img src="/static/images/security-badge.png" width="200" alt="Security Badge">
        <p>Cyber pattern:</p>
        <img src="/static/images/cyber-pattern.png" width="200" alt="Cyber Pattern">
        <p>Dark web icon:</p>
        <img src="/static/images/dark-web-icon.svg" width="200" alt="Dark Web Icon">
        <p>Cyber search:</p>
        <img src="/static/images/cyber-search.svg" width="200" alt="Cyber Search">
    </body>
    </html>
    """

@app.route('/debug')
def debug_info():
    """Debug endpoint to check configuration"""
    static_files = []
    for root, dirs, files in os.walk(static_dir):
        for file in files:
            static_files.append(os.path.join(root, file).replace(static_dir, ''))
    
    return {
        'static_folder': static_dir,
        'static_url_path': app.static_url_path,
        'static_files': static_files,
        'image_url': url_for('static', filename='images/dark-web-icon.svg')
    }

@app.route('/static_test/<path:filename>')
def static_test(filename):
    """Test endpoint to serve static files directly"""
    return send_from_directory(static_dir, filename)

@app.route("/test")
def test_page():
    """Test page for static files and CSS/JS"""
    return render_template('test.html')

@app.route('/log')
@login_required
def view_search_log():
    """View the search log"""
    # Only allow admins to view the log
    if not current_user.is_admin:
        flash('You do not have permission to view the log.')
        return redirect(url_for('index'))
        
    log_path = os.path.join(os.path.dirname(__file__), 'search_log.txt')
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            log_content = f.read()
    else:
        log_content = "Log file not found."
        
    return render_template('log.html', log_content=log_content)

if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Dark Web Intelligence Scanner')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the web server on')
    args = parser.parse_args()
    
    logger.info(f"Starting Dark Web Intelligence Scanner on port {args.port}...")
    app.run(host="0.0.0.0", port=args.port, debug=True)
