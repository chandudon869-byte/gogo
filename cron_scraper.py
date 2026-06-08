#!/usr/bin/env python3
"""
Cron job script - Runs every 6 hours on Render
"""

from scraper import scrape_nepse_data
import json
from datetime import datetime

DATA_FILE = 'nepse_data.json'

def run_scrape():
    print(f"[{datetime.now().isoformat()}] Starting scheduled scrape...")
    
    try:
        data = scrape_nepse_data()
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"[{datetime.now().isoformat()}] ✅ Scrape successful!")
        print(f"  📊 Total: {data.get('total_count', 0)} announcements")
        print(f"  📈 IPOs: {len(data.get('ipos', []))}")
        print(f"  🎁 Bonus: {len(data.get('bonus_shares', []))}")
        print(f"  💰 Dividends: {len(data.get('dividends', []))}")
        print(f"  📄 Right Shares: {len(data.get('right_shares', []))}")
        print(f"  📅 AGM: {len(data.get('agm', []))}")
        
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] ❌ ERROR: {e}")
        raise

if __name__ == '__main__':
    run_scrape()