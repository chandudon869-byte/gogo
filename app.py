from flask import Flask, jsonify, request
from flask_cors import CORS
from scraper import scrape_nepse_data
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for your frontend

# File to cache scraped data
DATA_FILE = 'nepse_data.json'

def load_cached_data():
    """Load previously scraped data from cache"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return None

def save_data_to_cache(data):
    """Save scraped data to cache file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/', methods=['GET'])
def home():
    """API home endpoint"""
    return jsonify({
        'name': 'Nepal IPO Scraper API',
        'version': '1.0.0',
        'endpoints': {
            '/api/ipos': 'Get all IPO announcements',
            '/api/bonus': 'Get bonus share announcements',
            '/api/dividends': 'Get dividend announcements',
            '/api/right-shares': 'Get right share announcements',
            '/api/all': 'Get all data combined',
            '/api/latest': 'Get only most recent announcements',
            '/health': 'Check API status'
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/all', methods=['GET'])
def get_all_data():
    """Get all scraped data"""
    data = load_cached_data()
    
    if not data:
        # If no cache, scrape fresh
        data = scrape_nepse_data()
        save_data_to_cache(data)
    
    # Add metadata
    data['api_timestamp'] = datetime.now().isoformat()
    
    # Optional: filter by date range
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    
    if from_date or to_date:
        filtered_data = {'last_updated': data['last_updated']}
        for category in ['ipos', 'bonus_shares', 'dividends', 'right_shares']:
            filtered_data[category] = [
                item for item in data.get(category, [])
                if (not from_date or item['date'] >= from_date) and
                   (not to_date or item['date'] <= to_date)
            ]
        return jsonify(filtered_data)
    
    return jsonify(data)

@app.route('/api/ipos', methods=['GET'])
def get_ipos():
    """Get only IPO announcements"""
    data = load_cached_data() or scrape_nepse_data()
    return jsonify({
        'count': len(data.get('ipos', [])),
        'data': data.get('ipos', []),
        'last_updated': data.get('last_updated')
    })

@app.route('/api/bonus', methods=['GET'])
def get_bonus():
    """Get bonus share announcements"""
    data = load_cached_data() or scrape_nepse_data()
    return jsonify({
        'count': len(data.get('bonus_shares', [])),
        'data': data.get('bonus_shares', []),
        'last_updated': data.get('last_updated')
    })

@app.route('/api/dividends', methods=['GET'])
def get_dividends():
    """Get dividend announcements"""
    data = load_cached_data() or scrape_nepse_data()
    return jsonify({
        'count': len(data.get('dividends', [])),
        'data': data.get('dividends', []),
        'last_updated': data.get('last_updated')
    })

@app.route('/api/right-shares', methods=['GET'])
def get_right_shares():
    """Get right share announcements"""
    data = load_cached_data() or scrape_nepse_data()
    return jsonify({
        'count': len(data.get('right_shares', [])),
        'data': data.get('right_shares', []),
        'last_updated': data.get('last_updated')
    })

@app.route('/api/latest', methods=['GET'])
def get_latest():
    """Get latest 20 announcements across all categories"""
    data = load_cached_data() or scrape_nepse_data()
    
    all_announcements = []
    for category in ['ipos', 'bonus_shares', 'dividends', 'right_shares']:
        all_announcements.extend(data.get(category, []))
    
    # Sort by date (newest first)
    all_announcements.sort(key=lambda x: x['date'], reverse=True)
    
    return jsonify({
        'count': min(20, len(all_announcements)),
        'data': all_announcements[:20],
        'last_updated': data.get('last_updated')
    })

# Auto-scrape on startup (for cron jobs)
def auto_scrape():
    print(f"[{datetime.now()}] Running auto-scrape...")
    data = scrape_nepse_data()
    save_data_to_cache(data)
    print(f"[{datetime.now()}] Scrape complete. Found {len(data.get('ipos', []))} IPOs")

if __name__ == '__main__':
    # Run initial scrape on startup
    auto_scrape()
    
    # Start the Flask server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)