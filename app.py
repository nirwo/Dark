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
    
    def dark_web_search(query, search_type='email'):
        """Mock implementation for testing UI"""
        global search_results
        search_results[f"{search_type}:{query}"] = {
            'status': 'completed', 
            'results': {
                'Example Site': {
                    'risk_level': 'medium',
                    'description': f'Mock result for {search_type}: {query}',
                    'mentions': [
                        {'context': 'Example context for demonstration purposes', 'date': datetime.datetime.now().strftime('%Y-%m-%d')}
                    ]
                }
            },
            'sites_searched': 5
        }
    
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
    search_query = request.form.get('searchQuery')
    search_type = request.form.get('searchType', 'email')
    
    if not search_query:
        return jsonify({"status": "error", "message": "No search query provided"}), 400
    
    # Create a unique key based on type and query
    search_key = f"{search_type}:{search_query}"
    
    # Run search in a background thread
    threading.Thread(target=dark_web_search, args=(search_query, search_type)).start()
    
    return jsonify({"status": "success", "message": f"Searching for {search_query}..."}), 200

@app.route('/results')
def results():
    """Get search results"""
    search_query = request.args.get('searchQuery')
    search_type = request.args.get('searchType', 'email')
    
    if not search_query:
        return jsonify({"status": "error", "message": "No search query provided"}), 400
    
    # Create a unique key based on type and query
    search_key = f"{search_type}:{search_query}"
    
    all_results = get_search_results()
    
    # Check if we have results for this search
    if search_key in all_results:
        return jsonify(all_results[search_key])
    else:
        return jsonify({
            "status": "in_progress",
            "message": f"Search for {search_type}: {search_query} is still in progress..."
        })

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
    app.run(host='0.0.0.0', port=5001, debug=True)
