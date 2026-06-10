"""Simple in-memory cache with TTL."""
import time
from typing import Dict, Any, Optional

class Cache:
    def __init__(self):
        self._data: Dict[str, dict] = {}
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        self._data[key] = {
            "value": value,
            "expires": time.time() + ttl,
        }
    
    def get(self, key: str) -> Optional[Any]:
        entry = self._data.get(key)
        if not entry:
            return None
        if time.time() > entry["expires"]:
            del self._data[key]
            return None
        return entry["value"]
    
    def clear(self):
        self._data.clear()
    
    def size(self) -> int:
        now = time.time()
        expired = [k for k, v in self._data.items() if now > v["expires"]]
        for k in expired:
            del self._data[k]
        return len(self._data)
