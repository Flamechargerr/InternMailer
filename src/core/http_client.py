"""HTTP client with retry and backoff."""
import requests
from time import sleep

class HTTPClient:
    def __init__(self, retries=3, backoff=1.0):
        self.retries = retries
        self.backoff = backoff
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "InternMailer/1.0"})
    
    def get(self, url, **kwargs):
        for attempt in range(self.retries):
            try:
                resp = self.session.get(url, timeout=15, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.RequestException:
                if attempt == self.retries - 1:
                    raise
                sleep(self.backoff * (2 ** attempt))
