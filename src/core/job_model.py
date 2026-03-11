"""Job posting data model."""
from dataclasses import dataclass, field
from typing import Optional, Dict
from datetime import datetime

@dataclass
class JobPosting:
    source: str
    source_id: str
    company: str
    title: str
    location: str
    location_type: str = "unknown"
    url: str = ""
    apply_url: str = ""
    description: str = ""
    employment_type: str = "unknown"
    posted_at: Optional[str] = None
    score: float = 0.0
    status: str = "new"
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            k: v for k, v in self.__dict__.items()
        }
