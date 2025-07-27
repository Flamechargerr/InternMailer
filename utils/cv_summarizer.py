"""
Function: summarize_cv(cv_bytes: bytes) -> str
 - Use simple NLP to extract your top project bullet (Education+Projects)
 - Return a one‑sentence highlight, e.g. “Built an LSTM air‑quality predictor achieving 85% accuracy.”
"""

import re
from typing import Optional

def _extract_text(cv_bytes: bytes) -> str:
    """Decode bytes to text, fallback to empty string on error."""
    try:
        return cv_bytes.decode(errors='ignore')
    except Exception as e:
        print(f"Error decoding CV bytes: {e}")
        return ""

def _find_highlight(text: str) -> Optional[str]:
    """Find a project or education bullet as a highlight."""
    lines = text.split('\n')
    for line in lines:
        if 'project' in line.lower() or 'education' in line.lower():
            return line.strip()
    return None

def summarize_cv(cv_bytes: bytes) -> str:
    """
    Use simple NLP to extract your top project bullet (Education+Projects).
    Return a one‑sentence highlight.
    """
    text = _extract_text(cv_bytes)
    highlight = _find_highlight(text)
    if highlight:
        return highlight
    return "Top project/education highlight not found."
