"""HTML parsing utilities for job boards."""
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

class HTMLParser:
    @staticmethod
    def extract_text(html: str, selector: str) -> Optional[str]:
        soup = BeautifulSoup(html, "html.parser")
        elem = soup.select_one(selector)
        return elem.get_text(strip=True) if elem else None
    
    @staticmethod
    def extract_links(html: str, pattern: str) -> List[str]:
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            if pattern in a["href"]:
                links.append(a["href"])
        return links
    
    @staticmethod
    def clean_text(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(separator=" ", strip=True)
