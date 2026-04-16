"""Spam score checker for email content."""
import re

SPAM_WORDS = ["free", "win", "click here", "limited time", "act now", "urgent"]

class SpamChecker:
    def __init__(self, threshold=0.3):
        self.threshold = threshold
    
    def score(self, text: str) -> float:
        text_lower = text.lower()
        hits = sum(1 for w in SPAM_WORDS if w in text_lower)
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        exclaim_count = text.count("!")
        return min(1.0, (hits * 0.15 + caps_ratio * 0.5 + exclaim_count * 0.05))
    
    def is_clean(self, text: str) -> bool:
        return self.score(text) < self.threshold
