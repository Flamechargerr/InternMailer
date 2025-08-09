import re
from typing import Optional

_ROLE_PREFIXES = (
    'postmaster', 'no-reply', 'noreply', 'admin', 'info', 'support', 'mailer-daemon'
)

_EMAIL_RE = re.compile(
    r"^[A-Za-z0-9!#$%&'*+\-/=?^_`{|}~.]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)


def looks_like_url(s: str) -> bool:
    if not s:
        return False
    s = s.strip().lower()
    return s.startswith('http://') or s.startswith('https://') or s.startswith('www.')


def is_role_email(s: str) -> bool:
    if not s or '@' not in s:
        return False
    local = s.split('@', 1)[0].lower()
    return any(local.startswith(pfx) for pfx in _ROLE_PREFIXES)


def is_valid_email(s: Optional[str]) -> bool:
    if not s or not isinstance(s, str):
        return False
    s = s.strip()
    if looks_like_url(s):
        return False
    if not _EMAIL_RE.match(s):
        return False
    return True


def validate_recipient(email: Optional[str]) -> Optional[str]:
    """Return cleaned email if valid and not role-based; else None."""
    if not is_valid_email(email):
        return None
    if is_role_email(email):
        return None
    return email.strip()
