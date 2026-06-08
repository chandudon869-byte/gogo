import requests
import pandas as pd
from datetime import datetime
from io import StringIO

def scrape_nepse_data():
    """Scrape IPO, dividend, and bonus announcements"""
    url = 'https://merolagani.com/handlers/webrequesthandler.ashx?type=stock_event&fromDate=6%2F1%2F2026&toDate=12%2F31%2F2026'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        
        results = {
            'ipos': [],
            'bonus_shares': [],
            'dividends': [],
            'right_shares': [],
            'last_updated': datetime.now().isoformat()
        }
        
        for item in data.get('detail', []):
            detail = item.get('announcementDetail', '')
            detail_lower = detail.lower()
            date = item.get('actionDate', '')
            
            # Categorize announcements
            if 'ipo' in detail_lower:
                results['ipos'].append({
                    'date': date,
                    'announcement': detail,
                    'type': 'IPO'
                })
            
            if 'bonus' in detail_lower:
                results['bonus_shares'].append({
                    'date': date,
                    'announcement': detail,
                    'type': 'Bonus Share'
                })
            
            if 'dividend' in detail_lower or 'cash dividend' in detail_lower:
                results['dividends'].append({
                    'date': date,
                    'announcement': detail,
                    'type': 'Dividend'
                })
            
            if 'right share' in detail_lower or 'right' in detail_lower:
                results['right_shares'].append({
                    'date': date,
                    'announcement': detail,
                    'type': 'Right Share'
                })
        
        return results
        
    except Exception as e:
        print(f"Scraping error: {e}")
        return {'error': str(e), 'last_updated': datetime.now().isoformat()}