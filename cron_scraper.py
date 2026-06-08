#!/usr/bin/env python3
"""
Production Cron Job - NEPSE Scraper (Render safe)
Runs every 6 hours or via scheduler
"""

import json
import os
import time
from datetime import datetime
from scraper import scrape_nepse_data


DATA_FILE = "nepse_data.json"
BACKUP_FILE = "nepse_data_backup.json"
LOCK_FILE = "scrape.lock"


# =========================
# LOCK SYSTEM (PREVENT DUPLICATES)
# =========================

def acquire_lock():
    if os.path.exists(LOCK_FILE):
        print("⚠️ Scraper already running. Exiting.")
        return False

    with open(LOCK_FILE, "w") as f:
        f.write(str(datetime.now()))
    return True


def release_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


# =========================
# SAFE FILE SAVE
# =========================

def save_data(data):
    """Save with backup protection"""

    # Backup old data first
    if os.path.exists(DATA_FILE):
        try:
            os.replace(DATA_FILE, BACKUP_FILE)
        except:
            pass

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# =========================
# VALIDATION
# =========================

def is_valid_data(data):
    """Basic validation to avoid saving bad scraper output"""
    if not isinstance(data, dict):
        return False

    if "last_updated" not in data:
        return False

    if "error" in data:
        return False

    return True


# =========================
# RETRY WRAPPER
# =========================

def safe_scrape(retries=3):
    for attempt in range(retries):
        try:
            print(f"🔄 Scrape attempt {attempt + 1}/{retries}")

            data = scrape_nepse_data()

            if is_valid_data(data):
                return data

            print("⚠️ Invalid data received, retrying...")

        except Exception as e:
            print(f"❌ Attempt {attempt + 1} failed: {e}")

        time.sleep(3)

    return None


# =========================
# MAIN JOB
# =========================

def run_scrape():
    start = datetime.now()
    print(f"\n[{start.isoformat()}] 🚀 Starting NEPSE cron job...")

    if not acquire_lock():
        return

    try:
        data = safe_scrape()

        if not data:
            print("❌ Scrape failed after retries")
            return

        save_data(data)

        print(f"\n[{datetime.now().isoformat()}] ✅ SCRAPE SUCCESSFUL")
        print(f"📊 Total: {data.get('total_count', 0)}")
        print(f"🏢 IPOs: {len(data.get('ipos', []))}")
        print(f"🎁 Bonus: {len(data.get('bonus_shares', []))}")
        print(f"💰 Dividends: {len(data.get('dividends', []))}")
        print(f"📄 Rights: {len(data.get('right_shares', []))}")
        print(f"📅 AGM: {len(data.get('agm', []))}")

    except Exception as e:
        print(f"❌ CRON ERROR: {e}")

    finally:
        release_lock()

        duration = (datetime.now() - start).total_seconds()
        print(f"⏱️ Completed in {duration:.2f}s\n")


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    run_scrape()