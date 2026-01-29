"""Input validation utilities."""
import re
from email.utils import parseaddr

def is_valid_email(email: str) -> bool:
    _, addr = parseaddr(email)
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", addr))

def is_safe_path(path: str) -> bool:
    return not any(p in path for p in ["..", "~", "|", ";"])
