#!/bin/bash

echo "===== Fixing Dark Web Scanner Main Page ====="

# Create necessary directories
mkdir -p /home/nirwog/CascadeProjects/Dark/static/css
mkdir -p /home/nirwog/CascadeProjects/Dark/static/js
mkdir -p /home/nirwog/CascadeProjects/Dark/static/images
mkdir -p /home/nirwog/CascadeProjects/Dark/templates
mkdir -p /home/nirwog/CascadeProjects/Dark/modules

# Create simple minimal CSS file
echo "/* Dark Web Scanner - Main Stylesheet */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: #f8f9fa;
    color: #333333;
    line-height: 1.6;
    margin: 0;
    padding: 0;
}

.header {
    background-color: #2c3e50;
    color: white;
    padding: 15px 30px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 30px;
    width: 100%;
}

.search-section {
    margin-bottom: 30px;
    padding: 40px 20px;
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    text-align: center;
}

.status-ok { color: #2ecc71; }
.status-error { color: #e74c3c; }
" > /home/nirwog/CascadeProjects/Dark/static/css/styles.css

# Create minimal SVG icon
echo '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="32" height="32">
  <circle cx="12" cy="12" r="11" fill="#2c3e50" stroke="#1a2530" stroke-width="0.5"/>
  <circle cx="12" cy="12" r="5" fill="none" stroke="white" stroke-width="0.75" opacity="0.8"/>
  <path d="M12,1 L12,23" stroke="white" stroke-width="0.5" opacity="0.3"/>
  <path d="M1,12 L23,12" stroke="white" stroke-width="0.5" opacity="0.3"/>
  <circle cx="12" cy="7" r="1" fill="white" opacity="0.8"/>
  <circle cx="12" cy="17" r="1" fill="white" opacity="0.8"/>
  <circle cx="7" cy="12" r="1" fill="white" opacity="0.8"/>
  <circle cx="17" cy="12" r="1" fill="white" opacity="0.8"/>
</svg>' > /home/nirwog/CascadeProjects/Dark/static/images/dark-web-icon.svg

# Create placeholder images using simple SVGs that work everywhere
for img in background-pattern.png dark-web-bg.jpg world-map.png security-badge.png cyber-pattern.png; do
    echo "<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 200 200'>
    <rect width='200' height='200' fill='#2c3e50'/>
    <text x='100' y='100' font-family='Arial' font-size='14' fill='white' text-anchor='middle'>${img}</text>
    <text x='100' y='120' font-family='Arial' font-size='12' fill='white' text-anchor='middle'>Placeholder</text>
</svg>" > /home/nirwog/CascadeProjects/Dark/static/images/${img}
done

# Create basic modules/__init__.py
echo "# Initialize modules package" > /home/nirwog/CascadeProjects/Dark/modules/__init__.py

# Create minimal search_engine.py module if it doesn't exist
if [ ! -f "/home/nirwog/CascadeProjects/Dark/modules/search_engine.py" ]; then
    echo "# Basic search engine functionality

import time
import random

# Mock data for testing
_search_results = {}

def dark_web_search(email):
    """Mock implementation for testing UI"""
    _search_results[email] = {
        'status': 'Initializing search...',
        'results': []
    }
    
    # Simulate a search process
    time.sleep(2)
    _search_results[email]['status'] = 'Connecting to search engines...'
    
    time.sleep(2)
    _search_results[email]['status'] = 'Searching dark web...'
    
    time.sleep(2)
    _search_results[email]['status'] = 'Processing results...'
    
    # Simulate some results
    found_count = random.randint(0, 3)
    _search_results[email]['results'] = [
        {
            'source': 'Mock Search Engine',
            'snippet': f'Found email {email} in mock database',
            'type': 'found'
        }
    ] if found_count > 0 else []
    
    # Add some not found results
    _search_results[email]['results'].extend([
        {
            'source': f'Mock Site {i}',
            'message': 'No results found.',
            'type': 'not_found'
        } for i in range(1, 6)
    ])
    
    # Calculate summary
    found = len([r for r in _search_results[email]['results'] if r['type'] == 'found'])
    not_found = len([r for r in _search_results[email]['results'] if r['type'] == 'not_found'])
    _search_results[email]['summary'] = {
        'total': len(_search_results[email]['results']),
        'found': found,
        'not_found': not_found,
        'errors': 0,
        'has_breaches': found > 0
    }
    
    _search_results[email]['status'] = 'Completed'

def get_search_results():
    """Return the current search results"""
    return _search_results

def test_tor_connection():
    """Mock implementation for testing UI"""
    # Return connected 80% of the time
    if random.random() < 0.8:
        return True, 'Connected to Tor network successfully'
    else:
        return False, 'Could not connect to Tor network'
" > /home/nirwog/CascadeProjects/Dark/modules/search_engine.py
fi

# Fix app.py file to correctly handle static files
cat > /home/nirwog/CascadeProjects/Dark/app.py << 'EOF'
import os
import logging
import datetime
from flask import Flask, render_template, request, jsonify, url_for, send_from_directory
import threading

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# Import search functionality
try:
    from modules.search_engine import dark_web_search, get_search_results, test_tor_connection
except ImportError:
    # Simple mock if the module is not available
    logger.warning("Search engine module not found. Using mock implementation.")
    
    # Mock data for testing
    search_results = {}
    
    def dark_web_search(email):
        """Mock implementation for testing UI"""
        global search_results
        search_results[email] = {'status': 'Completed', 'results': []}
    
    def get_search_results():
        """Return the current search results"""
        return search_results
    
    def test_tor_connection():
        """Mock implementation for testing UI"""
        return True, 'Mock Tor connection'

# Configure Flask app
app = Flask(__name__, 
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR,
    static_url_path='/static')

# Explicitly serve static files
@app.route('/static/<path:filename>')
def serve_static(filename):
    logger.info(f"Serving static file: {filename}")
    return send_from_directory(STATIC_DIR, filename)

@app.route('/')
def index():
    """Render the main page"""
    logger.info("Rendering index template...")
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    """Handle search requests"""
    email = request.form.get('email')
    if not email:
        return jsonify({"error": "No email provided"}), 400
    
    # Run search in a background thread
    threading.Thread(target=dark_web_search, args=(email,)).start()
    
    return jsonify({"message": f"Searching for {email}..."}), 200

@app.route('/results')
def results():
    """Get search results"""
    return jsonify(get_search_results())

@app.route('/check_tor')
def check_tor():
    """Check Tor connection status"""
    is_connected, message = test_tor_connection()
    return jsonify({
        "success": is_connected,
        "message": message,
        "timestamp": str(datetime.datetime.now())
    })

@app.route('/debug')
def debug():
    """Debug endpoint"""
    return {
        'static_dir': STATIC_DIR,
        'template_dir': TEMPLATE_DIR,
        'static_url_path': app.static_url_path,
    }

if __name__ == '__main__':
    # Create required directories if they don't exist
    os.makedirs(os.path.join(STATIC_DIR, 'css'), exist_ok=True)
    os.makedirs(os.path.join(STATIC_DIR, 'js'), exist_ok=True)
    os.makedirs(os.path.join(STATIC_DIR, 'images'), exist_ok=True)
    
    logger.info(f"Starting app with static_dir: {STATIC_DIR}")
    app.run(host='0.0.0.0', port=5000, debug=True)
EOF

# Make the fix script executable
chmod +x /home/nirwog/CascadeProjects/Dark/fix_main_page.sh

echo "===== Main page fixed! ====="
echo "Run the app with: python3 /home/nirwog/CascadeProjects/Dark/app.py"
echo "Then visit: http://localhost:5000 in your browser"
