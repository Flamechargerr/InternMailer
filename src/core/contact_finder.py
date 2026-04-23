"""Contact discovery via email pattern matching."""
import re
from typing import List, Optional

class ContactFinder:
    PATTERNS = [
        "{first}.{last}@{domain}",
        "{first}{last}@{domain}",
        "{first}_{last}@{domain}",
        "{first}@{domain}",
        "{last}@{domain}",
    ]
    
    def guess(self, first: str, last: str, domain: str) -> List[str]:
        emails = []
        for pattern in self.PATTERNS:
            email = pattern.format(first=first.lower(), last=last.lower(), domain=domain)
            if re.match(r"[^@]+@[^@]+\.[^@]+", email):
                emails.append(email)
        return list(dict.fromkeys(emails))
