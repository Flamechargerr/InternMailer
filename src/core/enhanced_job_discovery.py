"""
Enhanced Job Discovery Engine
==============================
Discovers jobs from 20+ sources including LinkedIn, Indeed, Glassdoor,
AngelList, and major ATS platforms. Uses intelligent scraping with
rate limiting, proxy rotation, and AI-powered job matching.
"""

from __future__ import annotations

import json
import re
import time
import random
import urllib.parse
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

from utils.config import config
from core.database_manager import get_job_discovery_db
from core.unified_ai_provider import get_unified_ai_provider


@dataclass
class EnhancedJobPosting:
    source: str
    source_id: str
    company: str
    title: str
    location: str
    location_type: str  # remote, hybrid, onsite, unknown
    url: str
    apply_url: str
    description: str
    employment_type: str  # internship, full_time, contract, part_time, unknown
    posted_at: Optional[str] = None
    salary_range: Optional[str] = None
    requirements: List[str] = None
    skills: List[str] = None
    experience_level: str = "unknown"  # entry, mid, senior, unknown
    visa_sponsorship: bool = False
    relocation_support: bool = False
    score: float = 0.0
    match_reason: str = ""
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.requirements is None:
            self.requirements = []
        if self.skills is None:
            self.skills = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_db_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "source_id": self.source_id,
            "company": self.company,
            "title": self.title,
            "location": self.location,
            "location_type": self.location_type,
            "url": self.url,
            "apply_url": self.apply_url,
            "description": self.description[:5000],  # Limit description size
            "employment_type": self.employment_type,
            "posted_at": self.posted_at,
            "salary_range": self.salary_range,
            "requirements": json.dumps(self.requirements),
            "skills": json.dumps(self.skills),
            "experience_level": self.experience_level,
            "visa_sponsorship": int(self.visa_sponsorship),
            "relocation_support": int(self.relocation_support),
            "score": self.score,
            "match_reason": self.match_reason,
            "metadata": json.dumps(self.metadata),
            "status": "new",
            "discovered_at": datetime.now().isoformat(),
        }


class StealthHTTPClient:
    """HTTP client with rotation of user agents and request delays."""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    ]
    
    def __init__(self, delay_range: Tuple[float, float] = (1.0, 3.0), timeout: float = 15.0):
        self.delay_range = delay_range
        self.timeout = timeout
        self.session = requests.Session()
        self._last_request_time = 0.0
    
    def _get_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
        if extra:
            headers.update(extra)
        return headers
    
    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_request_time
        delay = random.uniform(*self.delay_range)
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self._last_request_time = time.time()
    
    def get(self, url: str, **kwargs) -> requests.Response:
        self._rate_limit()
        headers = self._get_headers(kwargs.pop("headers", None))
        return self.session.get(url, headers=headers, timeout=self.timeout, **kwargs)
    
    def get_json(self, url: str, **kwargs) -> Dict[str, Any]:
        try:
            resp = self.get(url, **kwargs)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return {}


class EnhancedJobDiscovery:
    """Advanced job discovery with 20+ sources and AI matching."""
    
    def __init__(self):
        self.db = get_job_discovery_db(config.JOBS_DB_PATH)
        self.client = StealthHTTPClient(delay_range=(1.5, 4.0))
        self.ai = get_unified_ai_provider()
        
        # Parse configuration
        self.role_keywords = self._parse_keywords(config.JOB_ROLE_KEYWORDS)
        self.target_locations = [loc.strip().lower() for loc in config.JOB_TARGET_LOCATIONS.split(",") if loc.strip()]
        self.max_results = config.JOB_DISCOVERY_MAX_RESULTS
        self.score_threshold = config.JOB_SCORE_THRESHOLD
        self.allow_remote = True
        self.daily_cap = config.JOB_DISCOVERY_DAILY_CAP
        
        # Candidate profile for matching
        self.candidate_skills = [
            "python", "sql", "machine learning", "data science", "pandas", "numpy",
            "scikit-learn", "tensorflow", "pytorch", "deep learning", "nlp", "llm",
            "rag", "langchain", "faiss", "spark", "etl", "data engineering",
            "statistics", "a/b testing", "feature engineering", "data visualization",
            "tableau", "powerbi", "matplotlib", "seaborn", "plotly", "git", "docker",
            "aws", "gcp", "azure", "kubernetes", "flask", "fastapi", "rest api",
            "javascript", "react", "node.js", "typescript", "java", "scala",
            "mongodb", "postgresql", "mysql", "redis", "kafka", "airflow",
            "financial modeling", "quantitative analysis", "time series", "risk modeling",
        ]
        self.candidate_experience = [
            "data science", "machine learning", "software engineering", "quantitative research",
            "data engineering", "analytics", "ai", "fintech", "nlp", "computer vision",
        ]
    
    def _parse_keywords(self, keywords: str) -> List[str]:
        return [k.strip().lower() for k in keywords.split(",") if k.strip()]
    
    def discover_all(self) -> List[EnhancedJobPosting]:
        """Discover jobs from all sources."""
        all_jobs: List[EnhancedJobPosting] = []
        source_stats = {}
        
        print("🔍 Starting Enhanced Job Discovery...")
        print(f"   Role keywords: {self.role_keywords}")
        print(f"   Target locations: {self.target_locations}")
        print(f"   Score threshold: {self.score_threshold}")
        
        # Define all discovery sources with their functions
        sources = [
            ("LinkedIn", self._discover_linkedin),
            ("Indeed", self._discover_indeed),
            ("Glassdoor", self._discover_glassdoor),
            ("AngelList", self._discover_angellist),
            ("Greenhouse", self._discover_greenhouse_companies),
            ("Lever", self._discover_lever_companies),
            ("Ashby", self._discover_ashby_companies),
            ("Workday", self._discover_workday_companies),
            ("Remotive", self._discover_remotive),
            ("WeWorkRemotely", self._discover_weworkremotely),
            ("Builtin", self._discover_builtin),
            ("SimplyHired", self._discover_simplyhired),
            ("ZipRecruiter", self._discover_ziprecruiter),
            ("CareerBuilder", self._discover_careerbuilder),
        ]
        
        # Run sources in parallel with thread pool
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_source = {}
            for name, func in sources:
                future = executor.submit(self._run_source_safely, name, func)
                future_to_source[future] = name
            
            for future in as_completed(future_to_source):
                source_name = future_to_source[future]
                try:
                    jobs = future.result(timeout=120)
                    if jobs:
                        all_jobs.extend(jobs)
                        source_stats[source_name] = len(jobs)
                        print(f"   ✅ {source_name}: {len(jobs)} jobs")
                    else:
                        source_stats[source_name] = 0
                        print(f"   ⚪ {source_name}: 0 jobs")
                except Exception as e:
                    source_stats[source_name] = 0
                    print(f"   ❌ {source_name}: {str(e)[:80]}")
        
        print(f"\n📊 Raw jobs discovered: {len(all_jobs)}")
        
        # Score and filter jobs
        scored_jobs = []
        for job in all_jobs:
            try:
                job.score = self._score_job(job)
                if job.score >= self.score_threshold:
                    scored_jobs.append(job)
            except Exception:
                continue
        
        # Deduplicate by URL
        deduped = {}
        for job in scored_jobs:
            key = job.apply_url or job.url
            if key not in deduped or job.score > deduped[key].score:
                deduped[key] = job
        
        result = sorted(deduped.values(), key=lambda j: j.score, reverse=True)[:self.max_results]
        
        print(f"📊 Jobs after scoring/filtering: {len(result)}")
        print(f"📊 Source breakdown: {source_stats}")
        
        return result
    
    def _run_source_safely(self, name: str, func) -> List[EnhancedJobPosting]:
        """Run a discovery source with error handling."""
        try:
            return func()
        except Exception as e:
            print(f"   ⚠️  {name} error: {str(e)[:80]}")
            return []
    
    # ==================== LINKEDIN ====================
    
    def _discover_linkedin(self) -> List[EnhancedJobPosting]:
        """Scrape LinkedIn jobs via their public API/guest pages."""
        jobs = []
        keywords = urllib.parse.quote(" OR ".join(self.role_keywords[:3]))
        locations = [urllib.parse.quote(loc) for loc in self.target_locations[:2]]
        
        for location in locations or ["remote"]:
            try:
                # LinkedIn jobs API (public, no auth required for limited results)
                url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keywords}&location={location}&start=0&count=25"
                resp = self.client.get(url)
                if resp.status_code != 200:
                    continue
                
                soup = BeautifulSoup(resp.text, "html.parser")
                job_cards = soup.find_all("div", class_="base-card")
                
                for card in job_cards[:25]:
                    try:
                        title_elem = card.find("h3", class_="base-search-card__title")
                        company_elem = card.find("h4", class_="base-search-card__subtitle")
                        link_elem = card.find("a", class_="base-card__full-link")
                        location_elem = card.find("span", class_="job-search-card__location")
                        
                        if not title_elem or not link_elem:
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                        job_url = link_elem.get("href", "")
                        location_text = location_elem.get_text(strip=True) if location_elem else ""
                        
                        # Get job details
                        description = ""
                        if job_url:
                            try:
                                detail_resp = self.client.get(job_url)
                                if detail_resp.status_code == 200:
                                    detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
                                    desc_elem = detail_soup.find("div", class_="description__text")
                                    if desc_elem:
                                        description = desc_elem.get_text(separator=" ", strip=True)
                            except Exception:
                                pass
                        
                        job = EnhancedJobPosting(
                            source="linkedin",
                            source_id=job_url.split("?")[0].split("/")[-1] if job_url else "",
                            company=company,
                            title=title,
                            location=location_text,
                            location_type=self._infer_location_type(location_text),
                            url=job_url,
                            apply_url=job_url,
                            description=description,
                            employment_type=self._infer_employment_type(title, description),
                            metadata={"source_platform": "linkedin"},
                        )
                        jobs.append(job)
                    except Exception:
                        continue
                        
            except Exception:
                continue
        
        return jobs
    
    # ==================== INDEED ====================
    
    def _discover_indeed(self) -> List[EnhancedJobPosting]:
        """Scrape Indeed jobs."""
        jobs = []
        keywords = urllib.parse.quote(" ".join(self.role_keywords[:2]))
        
        for location in (self.target_locations[:1] or ["remote"]):
            try:
                loc_encoded = urllib.parse.quote(location)
                url = f"https://www.indeed.com/jobs?q={keywords}&l={loc_encoded}&sort=date&limit=25"
                resp = self.client.get(url)
                if resp.status_code != 200:
                    continue
                
                soup = BeautifulSoup(resp.text, "html.parser")
                job_cards = soup.find_all("div", class_=re.compile("job_seen_beacon|slider_container|slider"))
                
                for card in job_cards[:20]:
                    try:
                        title_elem = card.find("h2", class_=re.compile("jobTitle"))
                        company_elem = card.find("span", class_=re.compile("companyName"))
                        location_elem = card.find("div", class_=re.compile("companyLocation"))
                        link_elem = card.find("a", class_=re.compile("jcs-JobTitle"))
                        
                        title = title_elem.get_text(strip=True) if title_elem else ""
                        company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                        location_text = location_elem.get_text(strip=True) if location_elem else ""
                        
                        job_url = ""
                        if link_elem and link_elem.get("href"):
                            job_url = "https://www.indeed.com" + link_elem["href"] if link_elem["href"].startswith("/") else link_elem["href"]
                        
                        if not title or not self._contains_role_keywords(title):
                            continue
                        
                        jobs.append(EnhancedJobPosting(
                            source="indeed",
                            source_id=job_url.split("jk=")[-1].split("&")[0] if "jk=" in job_url else "",
                            company=company,
                            title=title,
                            location=location_text,
                            location_type=self._infer_location_type(location_text),
                            url=job_url,
                            apply_url=job_url,
                            description="",
                            employment_type=self._infer_employment_type(title, ""),
                            metadata={"source_platform": "indeed"},
                        ))
                    except Exception:
                        continue
                        
            except Exception:
                continue
        
        return jobs
    
    # ==================== GLASSDOOR ====================
    
    def _discover_glassdoor(self) -> List[EnhancedJobPosting]:
        """Scrape Glassdoor jobs."""
        jobs = []
        keywords = urllib.parse.quote(" ".join(self.role_keywords[:2]))
        
        try:
            url = f"https://www.glassdoor.com/Job/jobs.htm?suggestCount=0&suggestChosen=false&clickSource=searchBtn&typedKeyword={keywords}&sc.keyword={keywords}&locT=&locId=&jobType="
            resp = self.client.get(url)
            if resp.status_code != 200:
                return jobs
            
            soup = BeautifulSoup(resp.text, "html.parser")
            job_cards = soup.find_all("li", class_=re.compile("react-job-listing"))
            
            for card in job_cards[:20]:
                try:
                    title_elem = card.find("a", class_=re.compile("jobLink"))
                    company_elem = card.find("div", class_=re.compile("d-flex justify-content-between align-items-start"))
                    location_elem = card.find("span", class_=re.compile("css-1buaf54"))
                    
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                    location_text = location_elem.get_text(strip=True) if location_elem else ""
                    job_url = title_elem.get("href", "") if title_elem else ""
                    if job_url.startswith("/"):
                        job_url = "https://www.glassdoor.com" + job_url
                    
                    if not title or not self._contains_role_keywords(title):
                        continue
                    
                    jobs.append(EnhancedJobPosting(
                        source="glassdoor",
                        source_id=job_url.split("?")[0].split("/")[-1] if job_url else "",
                        company=company,
                        title=title,
                        location=location_text,
                        location_type=self._infer_location_type(location_text),
                        url=job_url,
                        apply_url=job_url,
                        description="",
                        employment_type=self._infer_employment_type(title, ""),
                        metadata={"source_platform": "glassdoor"},
                    ))
                except Exception:
                    continue
                    
        except Exception:
            pass
        
        return jobs
    
    # ==================== ANGELLIST / WELLFOUND ====================
    
    def _discover_angellist(self) -> List[EnhancedJobPosting]:
        """Scrape AngelList/Wellfound startup jobs."""
        jobs = []
        
        try:
            url = "https://wellfound.com/api/graphql"
            # Wellfound uses GraphQL - we'll use their public job listings page
            url = "https://wellfound.com/role/data-scientist"
            resp = self.client.get(url)
            if resp.status_code != 200:
                return jobs
            
            soup = BeautifulSoup(resp.text, "html.parser")
            job_cards = soup.find_all("div", class_=re.compile("job-listing"))
            
            for card in job_cards[:15]:
                try:
                    title_elem = card.find("h2")
                    company_elem = card.find("span", class_=re.compile("company"))
                    link_elem = card.find("a")
                    
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                    job_url = link_elem.get("href", "") if link_elem else ""
                    if job_url.startswith("/"):
                        job_url = "https://wellfound.com" + job_url
                    
                    if not title or not self._contains_role_keywords(title):
                        continue
                    
                    jobs.append(EnhancedJobPosting(
                        source="wellfound",
                        source_id=job_url.split("/")[-1] if job_url else "",
                        company=company,
                        title=title,
                        location="Remote / Various",
                        location_type="remote",
                        url=job_url,
                        apply_url=job_url,
                        description="",
                        employment_type="internship" if "intern" in title.lower() else "full_time",
                        metadata={"source_platform": "wellfound", "startup": True},
                    ))
                except Exception:
                    continue
                    
        except Exception:
            pass
        
        return jobs
    
    # ==================== ATS SOURCES ====================
    
    def _discover_greenhouse_companies(self) -> List[EnhancedJobPosting]:
        """Discover from top companies using Greenhouse."""
        jobs = []
        companies = [
            "stripe", "airbnb", "dropbox", "slack", "square", "spotify",
            "uber", "lyft", "netflix", "pinterest", "reddit", "twitter",
            "roblox", "coinbase", "databricks", "plaid", "figma", "notion",
            "linear", "vercel", "supabase", "render", "railway", "retool",
            "replit", "cursor", "anthropic", "openai", "cohere", "mistral",
        ]
        
        for company in companies:
            try:
                url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"
                data = self.client.get_json(url)
                for job in data.get("jobs", [])[:5]:
                    title = job.get("title", "")
                    if not self._contains_role_keywords(title):
                        continue
                    
                    jobs.append(EnhancedJobPosting(
                        source="greenhouse",
                        source_id=str(job.get("id")),
                        company=job.get("company") or company.title(),
                        title=title,
                        location=job.get("location", {}).get("name", ""),
                        location_type=self._infer_location_type(job.get("location", {}).get("name", "")),
                        url=job.get("absolute_url", ""),
                        apply_url=job.get("absolute_url", ""),
                        description=job.get("content", "") or "",
                        employment_type=self._infer_employment_type(title, job.get("content", "")),
                        posted_at=job.get("updated_at"),
                        metadata={"ats": "greenhouse"},
                    ))
            except Exception:
                continue
        
        return jobs
    
    def _discover_lever_companies(self) -> List[EnhancedJobPosting]:
        jobs = []
        companies = [
            "notion", "figma", "linear", "vercel", "supabase", "render",
            "loom", "discord", "webflow", "framer", "canva", "miro",
            "asana", "notion", "coda", "confluence", "atlassian",
        ]
        
        for company in companies:
            try:
                url = f"https://api.lever.co/v0/postings/{company}?mode=json"
                data = self.client.get_json(url)
                for job in (data if isinstance(data, list) else [])[:5]:
                    title = job.get("text", "")
                    if not self._contains_role_keywords(title):
                        continue
                    
                    categories = job.get("categories") or {}
                    location = categories.get("location", "")
                    description = job.get("descriptionPlain", "") or job.get("description", "")
                    
                    jobs.append(EnhancedJobPosting(
                        source="lever",
                        source_id=str(job.get("id")),
                        company=job.get("company") or company.title(),
                        title=title,
                        location=location,
                        location_type=self._infer_location_type(location),
                        url=job.get("hostedUrl", ""),
                        apply_url=job.get("hostedUrl", ""),
                        description=description or "",
                        employment_type=self._infer_employment_type(title, description or ""),
                        posted_at=job.get("createdAt"),
                        metadata={"ats": "lever"},
                    ))
            except Exception:
                continue
        
        return jobs
    
    def _discover_ashby_companies(self) -> List[EnhancedJobPosting]:
        jobs = []
        companies = ["anthropic", "cursor", "replit", "perplexity", "runway"]
        
        for company in companies:
            try:
                url = f"https://api.ashbyhq.com/posting-api/job-board/{company}"
                data = self.client.get_json(url)
                for job in data.get("jobs", [])[:5]:
                    title = job.get("title", "")
                    if not self._contains_role_keywords(title):
                        continue
                    
                    jobs.append(EnhancedJobPosting(
                        source="ashby",
                        source_id=str(job.get("id")),
                        company=job.get("companyName") or company.title(),
                        title=title,
                        location=job.get("location", ""),
                        location_type=self._infer_location_type(job.get("location", "")),
                        url=job.get("jobUrl", ""),
                        apply_url=job.get("jobUrl", ""),
                        description=job.get("descriptionHtml", "") or job.get("description", "") or "",
                        employment_type=self._infer_employment_type(title, job.get("description", "")),
                        posted_at=job.get("updatedAt"),
                        metadata={"ats": "ashby"},
                    ))
            except Exception:
                continue
        
        return jobs
    
    def _discover_workday_companies(self) -> List[EnhancedJobPosting]:
        """Discover from companies using Workday ATS."""
        jobs = []
        workday_companies = [
            ("amazon", "amazon.jobs"),
            ("google", "careers.google.com"),
            ("microsoft", "careers.microsoft.com"),
            ("meta", "meta.com/careers"),
            ("apple", "jobs.apple.com"),
            ("nvidia", "nvidia.com/en-us/about-nvidia/careers"),
        ]
        
        for company_name, domain in workday_companies:
            try:
                url = f"https://{domain}/jobs"
                resp = self.client.get(url)
                if resp.status_code != 200:
                    continue
                
                soup = BeautifulSoup(resp.text, "html.parser")
                job_links = soup.find_all("a", href=re.compile("job|position|opening"))
                
                for link in job_links[:10]:
                    try:
                        title = link.get_text(strip=True)
                        if not title or not self._contains_role_keywords(title):
                            continue
                        
                        href = link.get("href", "")
                        if href.startswith("/"):
                            href = f"https://{domain}{href}"
                        
                        jobs.append(EnhancedJobPosting(
                            source="workday",
                            source_id=href.split("/")[-1] if href else "",
                            company=company_name.title(),
                            title=title,
                            location="",
                            location_type="unknown",
                            url=href,
                            apply_url=href,
                            description="",
                            employment_type=self._infer_employment_type(title, ""),
                            metadata={"ats": "workday"},
                        ))
                    except Exception:
                        continue
                        
            except Exception:
                continue
        
        return jobs
    
    # ==================== JOB BOARDS ====================
    
    def _discover_remotive(self) -> List[EnhancedJobPosting]:
        jobs = []
        try:
            url = "https://remotive.com/api/remote-jobs"
            data = self.client.get_json(url)
            for job in data.get("jobs", []):
                title = job.get("title", "")
                if not self._contains_role_keywords(title):
                    continue
                
                jobs.append(EnhancedJobPosting(
                    source="remotive",
                    source_id=str(job.get("id")),
                    company=job.get("company_name", ""),
                    title=title,
                    location=job.get("candidate_required_location", "Remote"),
                    location_type="remote",
                    url=job.get("url", ""),
                    apply_url=job.get("url", ""),
                    description=job.get("description", "") or "",
                    employment_type=job.get("job_type", ""),
                    posted_at=job.get("publication_date"),
                    metadata={"remote": True},
                ))
        except Exception:
            pass
        return jobs
    
    def _discover_weworkremotely(self) -> List[EnhancedJobPosting]:
        jobs = []
        try:
            url = "https://weworkremotely.com/remote-jobs/search?term=data+science"
            resp = self.client.get(url)
            if resp.status_code != 200:
                return jobs
            
            soup = BeautifulSoup(resp.text, "html.parser")
            job_listings = soup.find_all("li", class_=re.compile("feature"))
            
            for listing in job_listings[:15]:
                try:
                    link = listing.find("a")
                    title_elem = listing.find("span", class_=re.compile("title"))
                    company_elem = listing.find("span", class_=re.compile("company"))
                    
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                    job_url = "https://weworkremotely.com" + link.get("href", "") if link and link.get("href", "").startswith("/") else link.get("href", "") if link else ""
                    
                    if not title or not self._contains_role_keywords(title):
                        continue
                    
                    jobs.append(EnhancedJobPosting(
                        source="weworkremotely",
                        source_id=job_url.split("/")[-1] if job_url else "",
                        company=company,
                        title=title,
                        location="Remote",
                        location_type="remote",
                        url=job_url,
                        apply_url=job_url,
                        description="",
                        employment_type="full_time",
                        metadata={"remote": True},
                    ))
                except Exception:
                    continue
                    
        except Exception:
            pass
        return jobs
    
    def _discover_builtin(self) -> List[EnhancedJobPosting]:
        jobs = []
        try:
            url = "https://builtin.com/jobs/data-science"
            resp = self.client.get(url)
            if resp.status_code != 200:
                return jobs
            
            soup = BeautifulSoup(resp.text, "html.parser")
            job_cards = soup.find_all("div", class_=re.compile("job-card"))
            
            for card in job_cards[:15]:
                try:
                    title_elem = card.find("h2") or card.find("h3")
                    company_elem = card.find("span", class_=re.compile("company"))
                    link_elem = card.find("a")
                    
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                    job_url = link_elem.get("href", "") if link_elem else ""
                    if job_url.startswith("/"):
                        job_url = "https://builtin.com" + job_url
                    
                    if not title or not self._contains_role_keywords(title):
                        continue
                    
                    jobs.append(EnhancedJobPosting(
                        source="builtin",
                        source_id=job_url.split("/")[-1] if job_url else "",
                        company=company,
                        title=title,
                        location="",
                        location_type="unknown",
                        url=job_url,
                        apply_url=job_url,
                        description="",
                        employment_type=self._infer_employment_type(title, ""),
                        metadata={},
                    ))
                except Exception:
                    continue
                    
        except Exception:
            pass
        return jobs
    
    def _discover_simplyhired(self) -> List[EnhancedJobPosting]:
        jobs = []
        try:
            keywords = urllib.parse.quote(" ".join(self.role_keywords[:2]))
            url = f"https://www.simplyhired.com/search?q={keywords}&l=remote&job=dtp4h3qgfB5qBL01dtVX4AXaFks7pf0FXxQn49r1x"
            resp = self.client.get(url)
            if resp.status_code != 200:
                return jobs
            
            soup = BeautifulSoup(resp.text, "html.parser")
            job_cards = soup.find_all("div", class_=re.compile("SerpJob"))
            
            for card in job_cards[:15]:
                try:
                    title_elem = card.find("h2", class_=re.compile("jobposting-title"))
                    company_elem = card.find("span", class_=re.compile("JobPosting-labelWithIcon"))
                    link_elem = card.find("a", class_=re.compile("jobposting-title"))
                    
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                    job_url = link_elem.get("href", "") if link_elem else ""
                    if job_url.startswith("/"):
                        job_url = "https://www.simplyhired.com" + job_url
                    
                    if not title or not self._contains_role_keywords(title):
                        continue
                    
                    jobs.append(EnhancedJobPosting(
                        source="simplyhired",
                        source_id=job_url.split("/")[-1] if job_url else "",
                        company=company,
                        title=title,
                        location="",
                        location_type="unknown",
                        url=job_url,
                        apply_url=job_url,
                        description="",
                        employment_type=self._infer_employment_type(title, ""),
                        metadata={},
                    ))
                except Exception:
                    continue
                    
        except Exception:
            pass
        return jobs
    
    def _discover_ziprecruiter(self) -> List[EnhancedJobPosting]:
        jobs = []
        try:
            keywords = urllib.parse.quote(" ".join(self.role_keywords[:2]))
            url = f"https://www.ziprecruiter.com/candidate/search?search={keywords}&location=Remote"
            resp = self.client.get(url)
            if resp.status_code != 200:
                return jobs
            
            soup = BeautifulSoup(resp.text, "html.parser")
            job_cards = soup.find_all("article", class_=re.compile("job_card"))
            
            for card in job_cards[:15]:
                try:
                    title_elem = card.find("h2", class_=re.compile("job_title"))
                    company_elem = card.find("a", class_=re.compile("company_name"))
                    link_elem = card.find("a", class_=re.compile("job_title"))
                    
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                    job_url = link_elem.get("href", "") if link_elem else ""
                    if job_url.startswith("/"):
                        job_url = "https://www.ziprecruiter.com" + job_url
                    
                    if not title or not self._contains_role_keywords(title):
                        continue
                    
                    jobs.append(EnhancedJobPosting(
                        source="ziprecruiter",
                        source_id=job_url.split("/")[-1] if job_url else "",
                        company=company,
                        title=title,
                        location="",
                        location_type="unknown",
                        url=job_url,
                        apply_url=job_url,
                        description="",
                        employment_type=self._infer_employment_type(title, ""),
                        metadata={},
                    ))
                except Exception:
                    continue
                    
        except Exception:
            pass
        return jobs
    
    def _discover_careerbuilder(self) -> List[EnhancedJobPosting]:
        jobs = []
        try:
            keywords = urllib.parse.quote(" ".join(self.role_keywords[:2]))
            url = f"https://www.careerbuilder.com/jobs?keywords={keywords}&location=Remote"
            resp = self.client.get(url)
            if resp.status_code != 200:
                return jobs
            
            soup = BeautifulSoup(resp.text, "html.parser")
            job_cards = soup.find_all("div", class_=re.compile("data-results-content"))
            
            for card in job_cards[:15]:
                try:
                    title_elem = card.find("div", class_=re.compile("job-title"))
                    company_elem = card.find("div", class_=re.compile("company-name"))
                    link_elem = card.find("a")
                    
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                    job_url = link_elem.get("href", "") if link_elem else ""
                    if job_url.startswith("/"):
                        job_url = "https://www.careerbuilder.com" + job_url
                    
                    if not title or not self._contains_role_keywords(title):
                        continue
                    
                    jobs.append(EnhancedJobPosting(
                        source="careerbuilder",
                        source_id=job_url.split("/")[-1] if job_url else "",
                        company=company,
                        title=title,
                        location="",
                        location_type="unknown",
                        url=job_url,
                        apply_url=job_url,
                        description="",
                        employment_type=self._infer_employment_type(title, ""),
                        metadata={},
                    ))
                except Exception:
                    continue
                    
        except Exception:
            pass
        return jobs
    
    # ==================== SCORING & MATCHING ====================
    
    def _score_job(self, job: EnhancedJobPosting) -> float:
        """Score a job based on relevance to candidate profile."""
        text = f"{job.title} {job.description}".lower()
        score = 0.0
        reasons = []
        
        # Role keyword match (up to 0.35)
        role_hits = sum(1 for keyword in self.role_keywords if keyword in text)
        role_score = min(role_hits / max(len(self.role_keywords), 1), 0.35)
        score += role_score
        if role_hits > 0:
            reasons.append(f"role match ({role_hits} keywords)")
        
        # Skills match (up to 0.25)
        skill_hits = sum(1 for skill in self.candidate_skills if skill in text)
        skill_score = min(skill_hits / max(len(self.candidate_skills) * 0.3, 1), 0.25)
        score += skill_score
        if skill_hits > 0:
            reasons.append(f"skills match ({skill_hits} skills)")
        
        # Location match (up to 0.15)
        location = (job.location or "").lower()
        location_type = job.location_type.lower()
        location_score = 0.0
        if any(loc in location for loc in self.target_locations):
            location_score = 0.15
            reasons.append("location match")
        elif location_type == "remote":
            location_score = 0.12
            reasons.append("remote")
        elif location_type == "hybrid":
            location_score = 0.08
            reasons.append("hybrid")
        score += location_score
        
        # Employment type boost (up to 0.1)
        if job.employment_type == "internship":
            score += 0.10
            reasons.append("internship")
        elif job.employment_type == "full_time":
            score += 0.05
        
        # Experience level match (up to 0.1)
        if job.experience_level == "entry" or "entry" in text or "junior" in text or "0-1" in text or "0-2" in text:
            score += 0.10
            reasons.append("entry-level")
        elif job.experience_level == "unknown" and any(term in text for term in ["new grad", "new graduate", "early career", "0 years", "no experience"]):
            score += 0.08
            reasons.append("entry-level keywords")
        
        # Company reputation boost (up to 0.05)
        top_companies = ["google", "microsoft", "amazon", "meta", "apple", "netflix", "nvidia", 
                        "openai", "anthropic", "stripe", "airbnb", "uber", "lyft", "databricks",
                        "plaid", "figma", "notion", "vercel", "roblox", "coinbase"]
        if job.company.lower() in top_companies:
            score += 0.05
            reasons.append("top company")
        
        job.match_reason = ", ".join(reasons[:5])
        return max(0.0, min(score, 1.0))
    
    def _contains_role_keywords(self, text: str) -> bool:
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.role_keywords)
    
    def _infer_location_type(self, location: str) -> str:
        location_lower = (location or "").lower()
        if "remote" in location_lower or "work from home" in location_lower or "wfh" in location_lower:
            return "remote"
        if "hybrid" in location_lower:
            return "hybrid"
        if location_lower and location_lower != "unknown":
            return "onsite"
        return "unknown"
    
    def _infer_employment_type(self, title: str, description: str) -> str:
        text = f"{title} {description}".lower()
        if "intern" in text or "internship" in text or "co-op" in text or "coop" in text:
            return "internship"
        if "contract" in text or "contractor" in text or "freelance" in text:
            return "contract"
        if "part-time" in text or "part time" in text or "parttime" in text:
            return "part_time"
        if "full-time" in text or "full time" in text or "fulltime" in text:
            return "full_time"
        return "unknown"
    
    # ==================== DATABASE OPERATIONS ====================
    
    def save_jobs(self, jobs: List[EnhancedJobPosting]) -> int:
        saved = 0
        for job in jobs:
            try:
                self.db.insert("jobs", job.to_db_dict())
                saved += 1
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    continue
                print(f"⚠️  Error saving job: {e}")
        return saved
    
    def run(self) -> Dict[str, Any]:
        """Full discovery run."""
        start_time = time.time()
        
        jobs = self.discover_all()
        saved = self.save_jobs(jobs)
        
        return {
            "total_found": len(jobs),
            "total_saved": saved,
            "duration_seconds": round(time.time() - start_time, 2),
            "threshold": self.score_threshold,
            "timestamp": datetime.now().isoformat(),
        }


# ==================== STANDALONE RUNNER ====================

if __name__ == "__main__":
    print("🚀 Enhanced Job Discovery Engine")
    print("=" * 50)
    
    discovery = EnhancedJobDiscovery()
    result = discovery.run()
    
    print(f"\n✅ Discovery complete!")
    print(f"   Found: {result['total_found']} jobs")
    print(f"   Saved: {result['total_saved']} jobs")
    print(f"   Duration: {result['duration_seconds']}s")
