
"""
SAFETY MECHANISMS MODULE
Implements critical safeguards for the Email System.
"""
import os
import json
import time
import random
import requests
import re
from datetime import datetime

# --- CONFIGURATION ---
PORTFOLIO_URL = "https://anamay.vercel.app"
RESUME_PATH = "Resume_Anamay_Tripathy.pdf"
DAILY_LIMIT = 50
BLACKLIST_FILE = "data/blacklist.txt"
STATE_FILE = "data/campaign_state.json"
QUOTA_FILE = "data/daily_quota.json"

class SafetyManager:
    def __init__(self):
        self.ensure_data_dir()
    
    def ensure_data_dir(self):
        if not os.path.exists('data'):
            os.makedirs('data')

    # 1. LINK HEALTH CHECK (#5)
    def check_portfolio_health(self):
        print(f"🏥 Checking portfolio health: {PORTFOLIO_URL}...")
        try:
            response = requests.get(PORTFOLIO_URL, timeout=10)
            if response.status_code == 200:
                print("   ✅ Portfolio is ONLINE.")
                return True
            else:
                print(f"   ❌ Portfolio returned status {response.status_code}!")
                return False
        except Exception as e:
            print(f"   ❌ Portfolio unreachable: {e}")
            return False

    # 2. PDF VALIDATION (#18)
    def validate_resume(self):
        if not os.path.exists(RESUME_PATH):
            print(f"   ❌ Resume file not found: {RESUME_PATH}")
            return False
        size = os.path.getsize(RESUME_PATH)
        if size < 1000: # < 1KB is suspicious
            print(f"   ❌ Resume file too small ({size} bytes). Corrupted?")
            return False
        return True

    # 3. HALLUCINATION GUARD (#6)
    def scan_for_hallucinations(self, text):
        red_flags = [
            r"as an ai", 
            r"language model", 
            r"i cannot", 
            r"generating response",
            r"\[insert", 
            r"optimization_project", # placeholder leak
            r"waste classification" # Old project guard
        ]
        text_lower = text.lower()
        for flag in red_flags:
            if re.search(flag, text_lower):
                print(f"   ⚠️ HALLUCINATION DETECTED: Found prohibited term '{flag}'")
                return True # Alarm!
        return False

    # 4. STRICT DAILY QUOTA (#3)
    def check_quota(self):
        today = datetime.now().strftime("%Y-%m-%d")
        usage = 0
        if os.path.exists(QUOTA_FILE):
            try:
                with open(QUOTA_FILE, 'r') as f:
                    data = json.load(f)
                    if data.get('date') == today:
                        usage = data.get('count', 0)
            except:
                pass
        
        if usage >= DAILY_LIMIT:
            print(f"   ⛔ Daily limit reached ({usage}/{DAILY_LIMIT}). Stopping.")
            return False, usage
        return True, usage

    def increment_quota(self):
        today = datetime.now().strftime("%Y-%m-%d")
        usage = 0
        current_data = {}
        if os.path.exists(QUOTA_FILE):
            try:
                with open(QUOTA_FILE, 'r') as f:
                    current_data = json.load(f)
                    if current_data.get('date') == today:
                        usage = current_data.get('count', 0)
            except:
                pass
        
        usage += 1
        with open(QUOTA_FILE, 'w') as f:
            json.dump({'date': today, 'count': usage}, f)
        return usage

    # 5. GLOBAL BLACKLIST (#17)
    def is_blacklisted(self, email):
        if not os.path.exists(BLACKLIST_FILE):
            return False
        try:
            with open(BLACKLIST_FILE, 'r') as f:
                blocked = [line.strip().lower() for line in f]
                return email.lower() in blocked
        except:
            return False

    # 6. CRASH RECOVERY (#15)
    def load_state(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_state(self, index, processed_emails):
        with open(STATE_FILE, 'w') as f:
            json.dump({
                'last_index': index,
                'processed': processed_emails,
                'timestamp': str(datetime.now())
            }, f)

    def wait_human_delay(self):
        delay = random.uniform(0.01, 0.05) # TURBO MODE: Instant processing
        # print(f"   ⚡ Turbo speed: {delay:.3f}s...")
        time.sleep(delay)

# Singleton instance
safety = SafetyManager()
