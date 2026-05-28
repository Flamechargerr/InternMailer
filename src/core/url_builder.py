"""URL builder for job board APIs."""
import urllib.parse
from typing import List, Optional

class URLBuilder:
    @staticmethod
    def greenhouse(company: str) -> str:
        return f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"
    
    @staticmethod
    def lever(company: str) -> str:
        return f"https://api.lever.co/v0/postings/{company}?mode=json"
    
    @staticmethod
    def ashby(company: str) -> str:
        return f"https://api.ashbyhq.com/posting-api/job-board/{company}"
    
    @staticmethod
    def linkedin_search(keywords: str, location: str) -> str:
        q = urllib.parse.quote(keywords)
        loc = urllib.parse.quote(location)
        return f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={q}&location={loc}&count=25"
    
    @staticmethod
    def indeed_search(keywords: str, location: str) -> str:
        q = urllib.parse.quote(keywords)
        loc = urllib.parse.quote(location)
        return f"https://www.indeed.com/jobs?q={q}&l={loc}&sort=date"
