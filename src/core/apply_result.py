"""Application result tracking."""
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class ApplyResult:
    status: str
    details: str
    applied: bool
    provider: str = "generic"
    evidence: Optional[Dict] = None
    
    def is_success(self) -> bool:
        return self.applied and self.status == "applied"
    
    def is_blocked(self) -> bool:
        return self.status in ("blocked_captcha", "blocked_login")
