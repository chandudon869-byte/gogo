#!/usr/bin/env python3
"""
Cron job script - Runs every 6 hours on Render
This script scrapes data and saves it to the cache
"""

from scraper import scrape_nepse_data
import json
from datetime import datetime

DATA_FILE = 'nepse_data.json'

def run_scrape():
    print(f"[{datetime.now().isoformat()}] Starting scheduled scrape...")
    
    try:
        data = scrape_nepse_data()
        
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"[{datetime.now().isoformat()}] Scrape successful!")
        print(f"  - IPOs: {len(data.get('ipos', []))}")
        print(f"  - Bonus: {len(data.get('bonus_shares', []))}")
        print(f"  - Dividends: {len(data.get('dividends', []))}")
        print(f"  - Right Shares: {len(data.get('right_shares', []))}")
        
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] ERROR: {e}")
        raise

if __name__ == '__main__':
    run_scrape()