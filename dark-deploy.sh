#!/bin/bash
# darkweb_monitor.sh — Automate dark web monitoring for a specified email.

# --- Configuration ---
EMAIL="user@example.com"           # <<< CHANGE THIS to the email you want to monitor.
LOGFILE="$HOME/darkweb_monitor.log"  # Log file to record findings.

# --- 1. Install Tor if not present ---
if ! command -v tor >/dev/null; then
    echo "[*] Tor not found. Installing Tor..."
    sudo apt-get update && sudo apt-get install -y tor  # Using apt to install Tor&#8203;:contentReference[oaicite:6]{index=6}
fi

# Ensure Tor service is running
if ! pgrep -x "tor" >/dev/null; then
    echo "[*] Starting Tor service..."
    sudo service tor start
    # Wait a few seconds for Tor to fully bootstrap
    sleep 5
fi

# --- 2. Install Python dependencies if not present ---
# We need requests (with SOCKS support) and BeautifulSoup for parsing.
python3 -c "import requests, bs4" 2>/dev/null
if [[ $? -ne 0 ]]; then
    echo "[*] Installing Python dependencies (requests[socks] and beautifulsoup4)..."
    # Ensure pip is available
    if ! command -v pip3 >/dev/null; then
        sudo apt-get install -y python3-pip
    fi
    # Install requests with SOCKS support and BeautifulSoup4
    pip3 install --quiet requests[socks] beautifulsoup4
fi

# --- 3. Define the Python scraping script ---
PYTHON_SCRIPT="darkweb_search.py"
cat > "$PYTHON_SCRIPT" << 'PYCODE'
#!/usr/bin/env python3
import sys, requests, datetime
from bs4 import BeautifulSoup

# Read arguments
if len(sys.argv) < 3:
    print("Usage: darkweb_search.py <email> <logfile>")
    sys.exit(1)
email = sys.argv[1].strip()
log_path = sys.argv[2]

# Configure Tor proxy for requests
proxies = {
    "http": "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050"
}
# (The socks5h scheme ensures DNS and .onion resolution go through Tor&#8203;:contentReference[oaicite:7]{index=7})

# List of dark web search sites or forums to query
targets = [
    {
        "name": "Ahmia Search",
        "url": f"http://msydqstlz2kzerdg.onion/search?q={email}"
    },
    # You can add more target sites or search engines here, e.g. Torch, etc.
]

results = []  # to collect findings

for site in targets:
    try:
        res = requests.get(site["url"], proxies=proxies, timeout=30)
    except Exception as e:
        results.append(f"[{site['name']}] ERROR: {e}")
        continue
    if res.status_code != 200:
        results.append(f"[{site['name']}] HTTP {res.status_code} when searching.")
        continue

    html = res.text
    # Parse the search results page (HTML) for instances of the email or links
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text().lower()
    if email.lower() in text:
        # If the email appears on the results page text, record the context
        snippet_index = text.find(email.lower())
        snippet = text[max(0, snippet_index-50): snippet_index+50]
        results.append(f"[{site['name']}] Potential mention in search results: ...{snippet}...")

    # Find and follow result links (onion sites) on the search page
    links = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and '.onion' in href:
            # Only consider .onion links (could be results or ads)
            if href.startswith("http"):
                links.append(href)
    # Deduplicate and limit links to check
    links = list(dict.fromkeys(links))[:5]  # check up to 5 unique onion links
    for url in links:
        try:
            page = requests.get(url, proxies=proxies, timeout=30)
        except Exception as e:
            continue  # skip if cannot retrieve
        if page.status_code != 200:
            continue
        page_text = page.text.lower()
        if email.lower() in page_text:
            idx = page_text.find(email.lower())
            snippet = page_text[max(0, idx-50): idx+50]
            results.append(f"[Found on] {url} : ...{snippet}...")
            
# Write results to log file
with open(log_path, "a") as lf:
    lf.write(f"\n=== Dark Web Scan at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    if results:
        for line in results:
            lf.write(line + "\n")
    else:
        lf.write(f"No results found for {email}\n")
PYCODE

# Make the Python script executable
chmod +x "$PYTHON_SCRIPT"

# --- 4. Run the Python scraper ---
echo "[*] Running dark web search for ${EMAIL} ..."
python3 "$PYTHON_SCRIPT" "$EMAIL" "$LOGFILE"

echo "[*] Scan complete. Results (if any) are logged in $LOGFILE"
