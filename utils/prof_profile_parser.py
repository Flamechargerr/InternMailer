"""
Function: parse_profile(profile_url: str) -> {"lab_description": str, "keywords": List[str]}
 - Fetch their lab or Google Scholar page
 - Extract a 1–2 sentence lab description and 3–5 research keywords
"""

import requests
from bs4 import BeautifulSoup
from typing import List, Dict

def _fetch_profile_html(profile_url: str) -> str:
    """Fetch the HTML content of the profile page."""
    try:
        response = requests.get(profile_url, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching profile {profile_url}: {e}")
        return ""

def _extract_lab_description(soup: BeautifulSoup) -> str:
    """Extract a 1–2 sentence lab description from the soup."""
    # Placeholder: look for first substantial paragraph
    paragraphs = soup.find_all('p')
    for p in paragraphs:
        text = p.get_text(strip=True)
        if len(text) > 50:
            sentences = text.split('.')
            return '. '.join(sentences[:2]).strip() + '.'
    return "Lab description not found."

def _extract_keywords(soup: BeautifulSoup) -> List[str]:
    """Extract 3–5 research keywords from the soup."""
    # Placeholder: look for keywords in meta tags or bold text
    keywords = set()
    for tag in soup.find_all(['b', 'strong', 'em']):
        text = tag.get_text(strip=True)
        if 3 < len(text) < 30:
            keywords.add(text.lower())
    # Fallback: use some default keywords if not enough found
    if len(keywords) < 3:
        keywords.update(['machine learning', 'data science', 'ai'])
    return list(keywords)[:5]

def parse_profile(profile_url: str) -> Dict[str, object]:
    """
    Fetch the profile page and extract lab description and research keywords.
    """
    html = _fetch_profile_html(profile_url)
    if not html:
        return {"lab_description": "Lab description not found.", "keywords": []}
    soup = BeautifulSoup(html, 'html.parser')
    lab_description = _extract_lab_description(soup)
    keywords = _extract_keywords(soup)
    return {"lab_description": lab_description, "keywords": keywords}
