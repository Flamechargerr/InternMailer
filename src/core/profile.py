"""Candidate profile data model."""
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Profile:
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""
    summary: str = ""
    education: List[Dict] = field(default_factory=list)
    experience: List[Dict] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    projects: List[Dict] = field(default_factory=list)
    
    def skill_match(self, keywords: List[str]) -> float:
        if not keywords:
            return 0.0
        lower = [s.lower() for s in self.skills]
        hits = sum(1 for k in keywords if k.lower() in lower)
        return hits / len(keywords)
