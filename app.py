from flask import Flask, jsonify, request
from flask_cors import CORS
from scraper import scrape_nepse_data
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

DATA_FILE = 'nepse_data.json'

# Cache TTL (important for production)
CACHE_TTL_MINUTES = 30


# =========================
# CACHE HELPERS
# =========================

def load_cached_data():
    """Load cached data safely"""
    if not os.path.exists(DATA_FILE):
        return None

    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validate structure
        if not isinstance(data, dict):
            return None

        return data

    except Exception:
        return None


def is_cache_expired(data):
    """Check if cached data is older than TTL"""
    try:
        last_updated = data.get("last_updated")
        if not last_updated:
            return True

        last_time = datetime.fromisoformat(last_updated)
        return datetime.now() - last_time > timedelta(minutes=CACHE_TTL_MINUTES)

    except:
        return True


def save_data_to_cache(data):
    """Save scraped data"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_data(force_refresh=False):
    """
    Central data loader:
    - Uses cache if valid
    - Refreshes if expired or forced
    """
    data = load_cached_data()

    if force_refresh or not data or is_cache_expired(data):
        print("[SCRAPER] Refreshing data from source...")
        data = scrape_nepse_data()
        save_data_to_cache(data)

    return data or {
        "ipos": [],
        "bonus_shares": [],
        "dividends": [],
        "right_shares": [],
        "agm": [],
        "other": [],
        "total_count": 0,
        "last_updated": datetime.now().isoformat()
    }


# =========================
# ROUTES
# =========================

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'name': 'Nepal IPO Scraper API',
        'version': '2.0.0',
        'status': 'running',
        'endpoints': {
            '/api/all': 'All announcements',
            '/api/ipos': 'IPO data',
            '/api/bonus': 'Bonus shares',
            '/api/dividends': 'Dividends',
            '/api/right-shares': 'Rights shares',
            '/api/agm': 'AGM',
            '/api/latest': 'Latest announcements',
            '/api/search?q=': 'Search announcements',
            '/api/refresh': 'Force refresh data',
            '/api/summary': 'Stats'
        }
    })


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


# =========================
# SUMMARY
# =========================

@app.route('/api/summary', methods=['GET'])
def summary():
    data = get_data()

    return jsonify({
        'last_updated': data.get('last_updated'),
        'statistics': {
            'total': data.get('total_count', 0),
            'ipos': len(data.get('ipos', [])),
            'bonus': len(data.get('bonus_shares', [])),
            'dividends': len(data.get('dividends', [])),
            'rights': len(data.get('right_shares', [])),
            'agm': len(data.get('agm', []))
        }
    })


# =========================
# ALL DATA
# =========================

@app.route('/api/all', methods=['GET'])
def all_data():
    data = get_data()

    # Optional date filter
    from_date = request.args.get('from')
    to_date = request.args.get('to')

    if from_date or to_date:
        for key in ['ipos', 'bonus_shares', 'dividends', 'right_shares', 'agm', 'other']:
            items = data.get(key, [])

            filtered = []
            for item in items:
                date = item.get('date', '')

                if (not from_date or date >= from_date) and \
                   (not to_date or date <= to_date):
                    filtered.append(item)

            data[key] = filtered

    data['api_timestamp'] = datetime.now().isoformat()
    return jsonify(data)


# =========================
# CATEGORY ENDPOINTS
# =========================

@app.route('/api/ipos', methods=['GET'])
def ipos():
    data = get_data()
    return jsonify({
        'count': len(data.get('ipos', [])),
        'data': data.get('ipos', []),
        'last_updated': data.get('last_updated')
    })


@app.route('/api/bonus', methods=['GET'])
def bonus():
    data = get_data()
    return jsonify({
        'count': len(data.get('bonus_shares', [])),
        'data': data.get('bonus_shares', []),
        'last_updated': data.get('last_updated')
    })


@app.route('/api/dividends', methods=['GET'])
def dividends():
    data = get_data()
    return jsonify({
        'count': len(data.get('dividends', [])),
        'data': data.get('dividends', []),
        'last_updated': data.get('last_updated')
    })


@app.route('/api/right-shares', methods=['GET'])
def rights():
    data = get_data()
    return jsonify({
        'count': len(data.get('right_shares', [])),
        'data': data.get('right_shares', []),
        'last_updated': data.get('last_updated')
    })


@app.route('/api/agm', methods=['GET'])
def agm():
    data = get_data()
    return jsonify({
        'count': len(data.get('agm', [])),
        'data': data.get('agm', []),
        'last_updated': data.get('last_updated')
    })


# =========================
# LATEST
# =========================

@app.route('/api/latest', methods=['GET'])
def latest():
    data = get_data()

    all_items = []
    for k in ['ipos', 'bonus_shares', 'dividends', 'right_shares', 'agm']:
        all_items.extend(data.get(k, []))

    # Sort safely
    all_items.sort(key=lambda x: x.get('date', ''), reverse=True)

    limit = request.args.get('limit', 20, type=int)

    return jsonify({
        'count': min(limit, len(all_items)),
        'data': all_items[:limit],
        'last_updated': data.get('last_updated')
    })


# =========================
# SEARCH
# =========================

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '').lower()

    if not query:
        return jsonify({'error': 'Missing search query'}), 400

    data = get_data()

    results = []

    for k in ['ipos', 'bonus_shares', 'dividends', 'right_shares', 'agm']:
        for item in data.get(k, []):
            if query in item.get('announcement', '').lower() or \
               query in item.get('company', '').lower():
                results.append(item)

    return jsonify({
        'query': query,
        'count': len(results),
        'data': results,
        'last_updated': data.get('last_updated')
    })


# =========================
# MANUAL REFRESH
# =========================

@app.route('/api/refresh', methods=['GET'])
def refresh():
    data = get_data(force_refresh=True)

    return jsonify({
        'message': 'Data refreshed successfully',
        'total': data.get('total_count', 0),
        'last_updated': data.get('last_updated')
    })


# =========================
# STARTUP SCRAPE
# =========================

def auto_scrape():
    print(f"[STARTUP] Scraping data...")
    data = scrape_nepse_data()
    save_data_to_cache(data)
    print(f"[STARTUP] Done. Total: {data.get('total_count', 0)}")


if __name__ == '__main__':
    auto_scrape()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)