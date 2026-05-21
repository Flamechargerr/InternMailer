"""Generic web scraper with stealth headers."""
import random
from typing import Dict, Optional
import requests

class StealthScraper:
    HEADERS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    ]
    
    def __init__(self, delay=(1.0, 3.0)):
        self.delay = delay
        self.session = requests.Session()
    
    def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        self.session.headers.update({"User-Agent": random.choice(self.HEADERS)})
        try:
            resp = self.session.get(url, timeout=15, **kwargs)
            resp.raise_for_status()
            return resp
        except requests.RequestException:
            return None
    
    def get_json(self, url: str) -> Optional[Dict]:
        resp = self.get(url)
        return resp.json() if resp and resp.status_code == 200 else None
