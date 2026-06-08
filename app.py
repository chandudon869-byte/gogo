from flask import Flask, jsonify, request
from flask_cors import CORS
from scraper import scrape_nepse_data
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATA_FILE = 'nepse_data.json'

def load_cached_data():
    """Load previously scraped data from cache"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

def save_data_to_cache(data):
    """Save scraped data to cache file"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.route('/', methods=['GET'])
def home():
    """API home endpoint"""
    return jsonify({
        'name': 'Nepal IPO Scraper API',
        'version': '1.0.0',
        'description': 'Real-time IPO, bonus, dividend, and right share data for Nepal share market',
        'endpoints': {
            '/api/ipos': 'Get all IPO announcements',
            '/api/bonus': 'Get bonus share announcements',
            '/api/dividends': 'Get dividend announcements',
            '/api/right-shares': 'Get right share announcements',
            '/api/agm': 'Get AGM announcements',
            '/api/all': 'Get all data combined',
            '/api/latest': 'Get only most recent announcements',
            '/api/summary': 'Get summary statistics',
            '/health': 'Check API status'
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/summary', methods=['GET'])
def get_summary():
    """Get summary statistics"""
    data = load_cached_data()
    
    if not data:
        data = scrape_nepse_data()
        save_data_to_cache(data)
    
    return jsonify({
        'last_updated': data.get('last_updated'),
        'statistics': {
            'total_announcements': data.get('total_count', 0),
            'ipos': len(data.get('ipos', [])),
            'bonus_shares': len(data.get('bonus_shares', [])),
            'dividends': len(data.get('dividends', [])),
            'right_shares': len(data.get('right_shares', [])),
            'agm': len(data.get('agm', []))
        }
    })

@app.route('/api/all', methods=['GET'])
def get_all_data():
    """Get all scraped data"""
    data = load_cached_data()
    
    if not data or 'error' in data:
        data = scrape_nepse_data()
        save_data_to_cache(data)
    
    # Add API timestamp
    response_data = data.copy()
    response_data['api_timestamp'] = datetime.now().isoformat()
    
    # Optional: filter by date
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    
    if from_date or to_date:
        for category in ['ipos', 'bonus_shares', 'dividends', 'right_shares', 'agm']:
            if category in response_data:
                response_data[category] = [
                    item for item in response_data.get(category, [])
                    if (not from_date or item['date'] >= from_date) and
                       (not to_date or item['date'] <= to_date)
                ]
    
    return jsonify(response_data)

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

@app.route('/api/agm', methods=['GET'])
def get_agm():
    """Get AGM announcements"""
    data = load_cached_data() or scrape_nepse_data()
    return jsonify({
        'count': len(data.get('agm', [])),
        'data': data.get('agm', []),
        'last_updated': data.get('last_updated')
    })

@app.route('/api/latest', methods=['GET'])
def get_latest():
    """Get latest 20 announcements across all categories"""
    data = load_cached_data() or scrape_nepse_data()
    
    all_announcements = []
    for category in ['ipos', 'bonus_shares', 'dividends', 'right_shares', 'agm']:
        all_announcements.extend(data.get(category, []))
    
    # Sort by date (newest first)
    all_announcements.sort(key=lambda x: x['date'], reverse=True)
    limit = request.args.get('limit', 20, type=int)
    
    return jsonify({
        'count': min(limit, len(all_announcements)),
        'data': all_announcements[:limit],
        'last_updated': data.get('last_updated')
    })

@app.route('/api/search', methods=['GET'])
def search():
    """Search announcements by keyword"""
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify({'error': 'Search query required'}), 400
    
    data = load_cached_data() or scrape_nepse_data()
    
    results = []
    for category in ['ipos', 'bonus_shares', 'dividends', 'right_shares', 'agm']:
        for item in data.get(category, []):
            if query in item.get('announcement', '').lower() or query in item.get('company', '').lower():
                results.append(item)
    
    return jsonify({
        'query': query,
        'count': len(results),
        'data': results,
        'last_updated': data.get('last_updated')
    })

# Auto-scrape on startup
def auto_scrape():
    print(f"[{datetime.now()}] Running auto-scrape on startup...")
    data = scrape_nepse_data()
    save_data_to_cache(data)
    print(f"[{datetime.now()}] Scrape complete. Found {data.get('total_count', 0)} announcements")

if __name__ == '__main__':
    # Run initial scrape on startup
    auto_scrape()
    
    # Start the Flask server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)