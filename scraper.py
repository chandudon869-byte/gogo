import requests
import json
import re
import hashlib
from datetime import datetime


URL_TEMPLATE = "https://merolagani.com/handlers/webrequesthandler.ashx?type=stock_event&fromDate={from_date}&toDate={to_date}"


def build_url():
    """Generate dynamic yearly range instead of hardcoded 2026"""
    year = datetime.today().year
    from_date = f"1/1/{year}"
    to_date = f"12/31/{year}"
    return URL_TEMPLATE.format(from_date=from_date, to_date=to_date)


def make_id(text, date):
    """Create unique hash for deduplication"""
    return hashlib.md5((text + date).encode()).hexdigest()


def extract_company(text):
    """Improved company name extraction"""
    if not text:
        return "Unknown"

    text = re.sub(r'\s+', ' ', text).strip()

    split_patterns = [
        r' has ',
        r' is ',
        r' will ',
        r' has announced ',
        r' has notified ',
        r' publishes ',
        r' declares ',
        r' - ',
        r' for ',
        r' to '
    ]

    for pattern in split_patterns:
        parts = re.split(pattern, text, flags=re.IGNORECASE)
        if len(parts) > 1:
            company = parts[0].strip()
            if 3 < len(company) < 100:
                return company

    return text[:80]


def classify_announcement(text_lower):
    """Better classification logic"""
    if any(word in text_lower for word in ['ipo', 'initial public offering', 'public issue', 'fpo']):
        return "IPO"

    if 'bonus' in text_lower:
        return "Bonus Share"

    if 'dividend' in text_lower or 'cash dividend' in text_lower:
        return "Dividend"

    if 'right share' in text_lower or 'rights share' in text_lower:
        return "Right Share"

    if 'agm' in text_lower:
        return "AGM"

    if any(word in text_lower for word in ['share', 'issue', 'offering']):
        return "Other"

    return None


def scrape_nepse_data():
    url = build_url()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)

        # Safety check (VERY IMPORTANT)
        if not response.headers.get('Content-Type', '').startswith('application/json'):
            raise Exception("Blocked or invalid response (not JSON)")

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
            date = item.get('actionDate', '')

            if not detail:
                continue

            detail_lower = detail.lower()

            category = classify_announcement(detail_lower)

            announcement = {
                'id': make_id(detail, date),
                'date': date,
                'company': extract_company(detail),
                'announcement': detail,
                'category': category
            }

            if category == "IPO":
                results['ipos'].append(announcement)

            elif category == "Bonus Share":
                results['bonus_shares'].append(announcement)

            elif category == "Dividend":
                results['dividends'].append(announcement)

            elif category == "Right Share":
                results['right_shares'].append(announcement)

            elif category == "AGM":
                results['agm'].append(announcement)

            elif category == "Other":
                results['other'].append(announcement)

        # FIXED TOTAL COUNT (ALL CATEGORIES)
        results['total_count'] = sum(
            len(results[k]) for k in results
            if isinstance(results[k], list)
        )

        return results

    except Exception as e:
        return {
            'error': str(e),
            'last_updated': datetime.now().isoformat()
        }


# Optional test run
if __name__ == "__main__":
    data = scrape_nepse_data()
    print(json.dumps(data, indent=2, ensure_ascii=False))