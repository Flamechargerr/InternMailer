"""Domain resolution for company names."""
from typing import Optional

DOMAIN_MAP = {
    "google": "google.com",
    "microsoft": "microsoft.com",
    "amazon": "amazon.com",
    "meta": "meta.com",
    "apple": "apple.com",
    "stripe": "stripe.com",
    "openai": "openai.com",
    "anthropic": "anthropic.com",
    "databricks": "databricks.com",
    "figma": "figma.com",
}

class DomainResolver:
    @staticmethod
    def resolve(company: str) -> Optional[str]:
        key = company.lower().replace(" ", "").replace(".", "")
        return DOMAIN_MAP.get(key)
    
    @staticmethod
    def add_alias(company: str, domain: str):
        DOMAIN_MAP[company.lower()] = domain
