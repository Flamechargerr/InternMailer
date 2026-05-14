"""JSON API response parser for job boards."""
import json
from typing import Dict, Any, Optional

class JSONParser:
    @staticmethod
    def safe_load(text: str) -> Optional[Dict]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
    
    @staticmethod
    def extract(data: Dict, path: str, default=None):
        keys = path.split(".")
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key, default)
            else:
                return default
        return current
    
    @staticmethod
    def flatten_jobs(data: Dict, source: str) -> list:
        jobs = []
        items = data.get("jobs") or data.get("data") or []
        for item in items:
            jobs.append({
                "source": source,
                "title": item.get("title") or item.get("name", ""),
                "company": item.get("company") or item.get("company_name", ""),
                "url": item.get("url") or item.get("absolute_url", ""),
            })
        return jobs
