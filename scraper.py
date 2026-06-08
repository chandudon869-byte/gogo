import requests
import json
from datetime import datetime

def scrape_nepse_data():
    """Scrape IPO, dividend, and bonus announcements - No pandas needed"""
    url = 'https://merolagani.com/handlers/webrequesthandler.ashx?type=stock_event&fromDate=1%2F1%2F2026&toDate=12%2F31%2F2026'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        
        results = {
            'ipos': [],
            'bonus_shares': [],
            'dividends': [],
            'right_shares': [],
            'agm': [],
            'other': [],
            'last_updated': datetime.now().isoformat(),
            'total_count': 0
        }
        
        for item in data.get('detail', []):
            detail = item.get('announcementDetail', '')
            detail_lower = detail.lower()
            date = item.get('actionDate', '')
            
            announcement = {
                'date': date,
                'announcement': detail,
                'company': extract_company(detail)
            }
            
            # Categorize announcements
            if 'ipo' in detail_lower:
                announcement['category'] = 'IPO'
                results['ipos'].append(announcement)
            elif 'bonus' in detail_lower:
                announcement['category'] = 'Bonus Share'
                results['bonus_shares'].append(announcement)
            elif 'dividend' in detail_lower or 'cash dividend' in detail_lower:
                announcement['category'] = 'Dividend'
                results['dividends'].append(announcement)
            elif 'right share' in detail_lower or 'right share' in detail_lower:
                announcement['category'] = 'Right Share'
                results['right_shares'].append(announcement)
            elif 'agm' in detail_lower:
                announcement['category'] = 'AGM'
                results['agm'].append(announcement)
            else:
                # Include other share-related announcements
                if any(word in detail_lower for word in ['share', 'issue', 'fpo', 'offering']):
                    announcement['category'] = 'Other'
                    results['other'].append(announcement)
        
        # Calculate totals
        results['total_count'] = len(results['ipos']) + len(results['bonus_shares']) + \
                                  len(results['dividends']) + len(results['right_shares'])
        
        return results
        
    except Exception as e:
        print(f"Scraping error: {e}")
        return {'error': str(e), 'last_updated': datetime.now().isoformat()}

def extract_company(text):
    """Extract company name from announcement text"""
    # Common company patterns
    import re
    # Look for company name pattern (usually at start before verbs)
    patterns = [
        r'^([^-]+?)(?:\s+has|\s+is|\s+notified|\s+published|\s+limited)',
        r'^([^-]+?)(?:\s+to|\s+for|\s+-\s+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            if len(company) > 5 and len(company) < 100:
                return company
    
    # Fallback: take first 50 characters
    return text[:50] + '...' if len(text) > 50 else text