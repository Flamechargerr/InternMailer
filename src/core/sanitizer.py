"""Input sanitization for security."""
import re
from typing import Optional

class Sanitizer:
    @staticmethod
    def text(value: str, max_length: int = 10000) -> str:
        if not isinstance(value, str):
            value = str(value)
        value = value.strip()
        return value[:max_length]
    
    @staticmethod
    def email(value: str) -> Optional[str]:
        value = value.strip().lower()
        if re.match(r"^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$", value):
            return value
        return None
    
    @staticmethod
    def url(value: str) -> Optional[str]:
        value = value.strip()
        if value.startswith("http://") or value.startswith("https://"):
            return value
        return None
    
    @staticmethod
    def sql_safe(value: str) -> str:
        return value.replace("'", """).replace(";", "").replace("--", "")
