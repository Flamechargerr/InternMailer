"""
Job Discovery Engine
Fetches job postings from ATS APIs, job board APIs, and custom pages.
Normalizes, scores, filters, and stores job postings.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from utils.config import config
from core.database_manager import get_job_discovery_db
from utils.http_client import get_http_client, HTTPConfig

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None


@dataclass
class JobPosting:
    source: str
    source_id: str
    company: str
    title: str
    location: str
    location_type: str
    url: str
    apply_url: str
    description: str
    employment_type: str
    posted_at: Optional[str] = None
    season_match: bool = False
    visa_sponsorship: bool = False
    relocation_support: bool = False
    score: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

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
            "description": self.description,
            "employment_type": self.employment_type,
            "posted_at": self.posted_at,
            "season_match": int(self.season_match),
            "visa_sponsorship": int(self.visa_sponsorship),
            "relocation_support": int(self.relocation_support),
            "score": self.score,
            "status": "new",  # Default status for new jobs
            "metadata": json.dumps(self.metadata or {}),
        }


class JobDiscovery:
    """Main job discovery orchestrator."""

    def __init__(self):
        self.db = get_job_discovery_db(config.JOBS_DB_PATH)
        self.sources = self._load_sources()
        self.role_keywords = self._parse_keywords(config.JOB_ROLE_KEYWORDS)
        self.target_locations = [loc.strip().lower() for loc in config.JOB_TARGET_LOCATIONS.split(",") if loc.strip()]
        self.max_results = config.JOB_DISCOVERY_MAX_RESULTS
        self.score_threshold = config.JOB_SCORE_THRESHOLD
        self.allow_us_with_visa = config.JOB_ALLOW_USA_WITH_VISA
        self.allow_long_term = config.JOB_ALLOW_LONG_TERM
        self.fortune500 = self._load_fortune500_list(config.JOB_FORTUNE500_CSV)
        # Initialize HTTP client with retry logic
        self.http_client = get_http_client(HTTPConfig(
            timeout=15.0,
            max_retries=3,
            backoff_factor=0.5,
        ))

    def _load_sources(self) -> Dict[str, Any]:
        sources_path = Path(config.JOB_SOURCES_PATH)
        if not sources_path.exists():
            print(f"⚠️  WARNING: Job sources file not found at {sources_path}")
            print(f"   Expected location: {sources_path.absolute()}")
            print(f"   Please create {sources_path} with job source configurations")
            print(f"   See data/job_sources.yaml.example for reference")
            return {
                "ats_sources": [],
                "job_board_apis": [],
                "custom_company_urls": [],
                "login_required_sources": [],
            }

        if sources_path.suffix in [".yaml", ".yml"]:
            if not yaml:
                raise RuntimeError("PyYAML is required for job sources config.")
            raw_sources = yaml.safe_load(sources_path.read_text()) or {}
            return self._normalize_sources_structure(raw_sources)

        if sources_path.suffix == ".json":
            raw_sources = json.loads(sources_path.read_text())
            return self._normalize_sources_structure(raw_sources)

        raise ValueError("JOB_SOURCES_PATH must be a .yaml/.yml/.json file")
    
    def _normalize_sources_structure(self, raw_sources: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize job sources structure to be compatible with both old and new formats
        
        Args:
            raw_sources: Raw sources dictionary from YAML/JSON
            
        Returns:
            Normalized sources dictionary
        """
        normalized = {
            "ats_sources": [],
            "job_board_apis": [],
            "custom_company_urls": [],
            "login_required_sources": [],
        }
        
        # Handle ATS sources (new format with 'name' and 'companies' list)
        raw_ats_sources = raw_sources.get("ats_sources", [])
        if isinstance(raw_ats_sources, list):
            for source in raw_ats_sources:
                if isinstance(source, dict):
                    # New format: {"name": "greenhouse", "companies": ["GitHub", "Shopify"]}
                    if "name" in source and "companies" in source:
                        ats_type = source["name"].lower()
                        companies = source["companies"]
                        if isinstance(companies, list):
                            for company in companies:
                                normalized["ats_sources"].append({
                                    "type": ats_type,
                                    "company": company
                                })
                    # Old format: {"type": "greenhouse", "company": "GitHub"}
                    elif "type" in source and "company" in source:
                        normalized["ats_sources"].append(source)
        
        # Handle job board APIs
        raw_apis = raw_sources.get("job_board_apis", [])
        if isinstance(raw_apis, list):
            for api in raw_apis:
                if isinstance(api, dict) and "url" in api:
                    normalized["job_board_apis"].append({
                        "name": api.get("name", "unknown"),
                        "url": api["url"]
                    })
        
        # Handle custom company URLs
        raw_urls = raw_sources.get("custom_company_urls", [])
        if isinstance(raw_urls, list):
            for url in raw_urls:
                if isinstance(url, str) and url.startswith("http"):
                    normalized["custom_company_urls"].append(url)
        
        # Handle login required sources
        raw_login_sources = raw_sources.get("login_required_sources", [])
        if isinstance(raw_login_sources, list):
            for source in raw_login_sources:
                if isinstance(source, str):
                    normalized["login_required_sources"].append(source.lower())
        
        return normalized

    def _parse_keywords(self, keywords: str) -> List[str]:
        return [k.strip().lower() for k in keywords.split(",") if k.strip()]

    def _load_fortune500_list(self, csv_path: str) -> List[str]:
        path = Path(csv_path)
        if not path.exists():
            return []
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            return []

        headers = lines[0].lower().split(",") if lines else []
        company_idx = None
        for idx, header in enumerate(headers):
            if "company" in header:
                company_idx = idx
                break
        if company_idx is None:
            return []

        companies = []
        for line in lines[1:]:
            parts = [p.strip().strip('"') for p in line.split(",")]
            if len(parts) > company_idx:
                companies.append(parts[company_idx].lower())
        return companies

    def discover(self) -> List[JobPosting]:
        jobs: List[JobPosting] = []
        source_errors = []
        
        # Check if we have any sources configured
        total_sources = (
            len(self.sources.get("ats_sources", [])) +
            len(self.sources.get("job_board_apis", [])) +
            len(self.sources.get("custom_company_urls", []))
        )
        
        if total_sources == 0:
            print("❌ No job sources configured!")
            print(f"   Check that {config.JOB_SOURCES_PATH} exists and contains sources")
            print("   Run: python3 -m utils.validate_setup to check configuration")
            return []

        print(f"🔍 Discovering jobs from {total_sources} source(s)...")

        # Discover from ATS sources with error handling
        ats_count = len(self.sources.get("ats_sources", []))
        if ats_count > 0:
            print(f"   Checking {ats_count} ATS source(s)...")
        for source in self.sources.get("ats_sources", []):
            try:
                source_jobs = self._discover_from_ats(source)
                jobs.extend(source_jobs)
                if source_jobs:
                    print(f"   ✅ Found {len(source_jobs)} jobs from {source.get('type', 'unknown')}/{source.get('company', 'unknown')}")
            except Exception as e:
                source_type = source.get("type", "unknown")
                company = source.get("company", "unknown")
                error_msg = f"ATS {source_type}/{company}: {str(e)}"
                source_errors.append(error_msg)
                print(f"   ⚠️  {error_msg}")

        # Discover from job board APIs with error handling
        api_count = len(self.sources.get("job_board_apis", []))
        if api_count > 0:
            print(f"   Checking {api_count} job board API(s)...")
        for board in self.sources.get("job_board_apis", []):
            try:
                board_jobs = self._discover_from_job_board(board)
                jobs.extend(board_jobs)
                if board_jobs:
                    print(f"   ✅ Found {len(board_jobs)} jobs from {board.get('name', 'unknown')}")
            except Exception as e:
                board_name = board.get("name", "unknown")
                error_msg = f"API {board_name}: {str(e)}"
                source_errors.append(error_msg)
                print(f"   ⚠️  {error_msg}")

        # Discover from custom company pages with error handling
        url_count = len(self.sources.get("custom_company_urls", []))
        if url_count > 0:
            print(f"   Checking {url_count} custom URL(s)...")
        for url in self.sources.get("custom_company_urls", []):
            try:
                url_jobs = self._discover_from_custom_page(url)
                jobs.extend(url_jobs)
                if url_jobs:
                    print(f"   ✅ Found {len(url_jobs)} jobs from {url}")
            except Exception as e:
                error_msg = f"URL {url}: {str(e)}"
                source_errors.append(error_msg)
                print(f"   ⚠️  {error_msg}")

        # Log source errors if any
        if source_errors:
            print(f"\n⚠️  Job discovery encountered {len(source_errors)} source error(s)")
            if len(source_errors) <= 5:
                for error in source_errors:
                    print(f"  - {error}")
            else:
                for error in source_errors[:5]:
                    print(f"  - {error}")
                print(f"  ... and {len(source_errors) - 5} more error(s)")
        
        print(f"\n📊 Total jobs discovered: {len(jobs)}")

        # Normalize and score
        normalized = []
        for job in jobs:
            try:
                job.score = self._score_job(job)
                if job.score >= self.score_threshold:
                    normalized.append(job)
            except Exception as e:
                # Skip jobs that fail scoring
                continue

        # Deduplicate by URL
        deduped = {}
        for job in normalized:
            deduped[job.url] = job

        result = list(deduped.values())[: self.max_results]
        
        # Log discovery results
        if len(result) == 0 and len(jobs) > 0:
            print(f"⚠️  Found {len(jobs)} jobs but all filtered out (threshold: {self.score_threshold})")
        elif len(result) == 0:
            print("⚠️  No jobs found from any source")
        
        return result

    def save_jobs(self, jobs: List[JobPosting]) -> int:
        saved = 0
        import sqlite3
        
        for job in jobs:
            try:
                # Ensure job has all required fields for database
                db_dict = job.to_db_dict()
                # Add status field if not present (database has default 'new')
                if 'status' not in db_dict:
                    db_dict['status'] = 'new'
                
                self.db.insert("jobs", db_dict)
                saved += 1
            except sqlite3.IntegrityError as e:
                # Specifically handle duplicate URL errors
                if "UNIQUE constraint failed" in str(e) and "jobs.url" in str(e):
                    # Silently ignore duplicate URLs
                    continue
                else:
                    # Log other integrity errors
                    print(f"⚠️  Database integrity error saving job {job.url}: {e}")
                    continue
            except Exception as e:
                # Log other errors but continue with remaining jobs
                print(f"⚠️  Error saving job {job.url}: {e}")
                continue
        return saved

    def run(self) -> Dict[str, Any]:
        run_id = self.db.insert("job_runs", {"filters": self._filters_summary(), "status": "running"})
        start_time = time.time()

        jobs = self.discover()
        saved = self.save_jobs(jobs)

        self.db.update(
            "job_runs",
            {
                "finished_at": datetime.now().isoformat(),
                "total_found": len(jobs),
                "total_saved": saved,
                "status": "completed",
                "notes": f"Duration: {time.time() - start_time:.2f}s",
            },
            "id = ?",
            (run_id,),
        )

        return {
            "run_id": run_id,
            "total_found": len(jobs),
            "total_saved": saved,
        }

    def _filters_summary(self) -> str:
        return json.dumps(
            {
                "role_keywords": self.role_keywords,
                "locations": self.target_locations,
                "score_threshold": self.score_threshold,
                "season_start": config.JOB_SEASON_START,
                "season_end": config.JOB_SEASON_END,
                "allow_long_term": self.allow_long_term,
                "allow_us_with_visa": self.allow_us_with_visa,
            }
        )

    def _discover_from_ats(self, source: Dict[str, Any]) -> List[JobPosting]:
        source_type = (source.get("type") or "").lower()
        company = source.get("company", "")

        if source_type == "greenhouse":
            return self._fetch_greenhouse(company)
        if source_type == "lever":
            return self._fetch_lever(company)
        if source_type == "ashby":
            return self._fetch_ashby(company)
        if source_type == "smartrecruiters":
            return self._fetch_smartrecruiters(company)
        if source_type == "workable":
            return self._fetch_workable(company)

        return []

    def _company_candidates(self, company: str) -> List[str]:
        if not company:
            return []
        base = company.strip()
        lowered = base.lower()
        compact = re.sub(r"[^a-z0-9]", "", lowered)
        dashed = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
        underscored = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
        candidates = [base, lowered, compact, dashed, underscored]
        seen = set()
        ordered: List[str] = []
        for c in candidates:
            if c and c not in seen:
                seen.add(c)
                ordered.append(c)
        return ordered

    def _discover_from_job_board(self, board: Dict[str, Any]) -> List[JobPosting]:
        name = (board.get("name") or "").lower()
        url = board.get("url", "")
        if not url:
            return []

        if name == "remotive":
            return self._fetch_remotive(url)
        if name == "arbeitnow":
            return self._fetch_arbeitnow(url)

        return self._fetch_generic_job_board(name or "job_board", url)

    def _discover_from_custom_page(self, url: str) -> List[JobPosting]:
        jobs: List[JobPosting] = []
        try:
            response = self.http_client.get(url)
            if response.status_code != 200:
                return jobs

            soup = BeautifulSoup(response.text, "html.parser")
            anchors = soup.find_all("a", href=True)
            for anchor in anchors:
                text = anchor.get_text(" ", strip=True)
                href = anchor["href"]
                if not text:
                    continue
                if not self._contains_role_keywords(text):
                    continue
                if href.startswith("/"):
                    href = url.rstrip("/") + href

                jobs.append(
                    JobPosting(
                        source="custom",
                        source_id=href,
                        company=self._guess_company_from_url(url),
                        title=text,
                        location="",
                        location_type="unknown",
                        url=href,
                        apply_url=href,
                        description=text,
                        employment_type="internship" if "intern" in text.lower() else "unknown",
                        metadata={"source_page": url},
                    )
                )
        except Exception:
            return jobs

        return jobs

    def _fetch_greenhouse(self, company: str) -> List[JobPosting]:
        if not company:
            return []
        for candidate in self._company_candidates(company):
            jobs: List[JobPosting] = []
            url = f"https://boards-api.greenhouse.io/v1/boards/{candidate}/jobs?content=true"
            data = self._get_json(url)
            for job in data.get("jobs", []):
                jobs.append(
                    JobPosting(
                        source="greenhouse",
                        source_id=str(job.get("id")),
                        company=job.get("company") or company,
                        title=job.get("title", ""),
                        location=job.get("location", {}).get("name", ""),
                        location_type=self._infer_location_type(job.get("location", {}).get("name", "")),
                        url=job.get("absolute_url", ""),
                        apply_url=job.get("absolute_url", ""),
                        description=job.get("content", "") or "",
                        employment_type=self._infer_employment_type(job.get("title", ""), job.get("content", "")),
                        posted_at=job.get("updated_at"),
                    )
                )
            if jobs:
                return jobs
        return []

    def _fetch_lever(self, company: str) -> List[JobPosting]:
        if not company:
            return []
        for candidate in self._company_candidates(company):
            jobs: List[JobPosting] = []
            url = f"https://api.lever.co/v0/postings/{candidate}?mode=json"
            data = self._get_json(url)
            for job in data if isinstance(data, list) else []:
                categories = job.get("categories") or {}
                location = categories.get("location", "")
                description = job.get("descriptionPlain", "") or job.get("description", "")
                jobs.append(
                    JobPosting(
                        source="lever",
                        source_id=str(job.get("id")),
                        company=job.get("company") or company,
                        title=job.get("text", ""),
                        location=location,
                        location_type=self._infer_location_type(location),
                        url=job.get("hostedUrl", ""),
                        apply_url=job.get("hostedUrl", ""),
                        description=description or "",
                        employment_type=self._infer_employment_type(job.get("text", ""), description or ""),
                        posted_at=job.get("createdAt"),
                    )
                )
            if jobs:
                return jobs
        return []

    def _fetch_ashby(self, company: str) -> List[JobPosting]:
        if not company:
            return []
        for candidate in self._company_candidates(company):
            jobs: List[JobPosting] = []
            url = f"https://api.ashbyhq.com/posting-api/job-board/{candidate}"
            data = self._get_json(url)
            for job in data.get("jobs", []):
                jobs.append(
                    JobPosting(
                        source="ashby",
                        source_id=str(job.get("id")),
                        company=job.get("companyName") or company,
                        title=job.get("title", ""),
                        location=job.get("location", ""),
                        location_type=self._infer_location_type(job.get("location", "")),
                        url=job.get("jobUrl", ""),
                        apply_url=job.get("jobUrl", ""),
                        description=job.get("descriptionHtml", "") or job.get("description", ""),
                        employment_type=self._infer_employment_type(job.get("title", ""), job.get("description", "")),
                        posted_at=job.get("updatedAt"),
                    )
                )
            if jobs:
                return jobs
        return []

    def _fetch_smartrecruiters(self, company: str) -> List[JobPosting]:
        if not company:
            return []
        for candidate in self._company_candidates(company):
            jobs: List[JobPosting] = []
            url = f"https://api.smartrecruiters.com/v1/companies/{candidate}/postings?limit=100"
            data = self._get_json(url)
            for posting in data.get("content", []):
                location = posting.get("location", {}).get("city", "")
                country = posting.get("location", {}).get("country", "")
                full_location = ", ".join([part for part in [location, country] if part])
                jobs.append(
                    JobPosting(
                        source="smartrecruiters",
                        source_id=str(posting.get("id")),
                        company=posting.get("company", {}).get("name") or company,
                        title=posting.get("name", ""),
                        location=full_location,
                        location_type=self._infer_location_type(full_location),
                        url=posting.get("ref", ""),
                        apply_url=posting.get("ref", ""),
                        description=posting.get("description", "") or "",
                        employment_type=self._infer_employment_type(posting.get("name", ""), posting.get("description", "")),
                        posted_at=posting.get("releasedDate"),
                    )
                )
            if jobs:
                return jobs
        return []

    def _fetch_workable(self, company: str) -> List[JobPosting]:
        if not company:
            return []
        for candidate in self._company_candidates(company):
            jobs: List[JobPosting] = []
            urls = [
                f"https://{candidate}.workable.com/api/v1/jobs",
                f"https://apply.workable.com/api/v1/accounts/{candidate}/jobs",
            ]
            for url in urls:
                data = self._get_json(url)
                for job in data.get("jobs", []) if isinstance(data, dict) else []:
                    location = job.get("location", {}).get("city", "") if isinstance(job.get("location"), dict) else job.get("location", "")
                    jobs.append(
                        JobPosting(
                            source="workable",
                            source_id=str(job.get("id")),
                            company=job.get("company") or company,
                            title=job.get("title", ""),
                            location=location,
                            location_type=self._infer_location_type(location),
                            url=job.get("url", ""),
                            apply_url=job.get("url", ""),
                            description=job.get("description", "") or "",
                            employment_type=self._infer_employment_type(job.get("title", ""), job.get("description", "")),
                            posted_at=job.get("published_at"),
                        )
                    )
                if jobs:
                    break
            if jobs:
                return jobs
        return []

    def _fetch_remotive(self, url: str) -> List[JobPosting]:
        jobs: List[JobPosting] = []
        data = self._get_json(url)
        for job in data.get("jobs", []):
            jobs.append(
                JobPosting(
                    source="remotive",
                    source_id=str(job.get("id")),
                    company=job.get("company_name", ""),
                    title=job.get("title", ""),
                    location=job.get("candidate_required_location", "Remote"),
                    location_type=self._infer_location_type(job.get("candidate_required_location", "Remote")),
                    url=job.get("url", ""),
                    apply_url=job.get("url", ""),
                    description=job.get("description", "") or "",
                    employment_type=job.get("job_type", ""),
                    posted_at=job.get("publication_date"),
                )
            )
        return jobs

    def _fetch_arbeitnow(self, url: str) -> List[JobPosting]:
        jobs: List[JobPosting] = []
        data = self._get_json(url)
        for job in data.get("data", []):
            jobs.append(
                JobPosting(
                    source="arbeitnow",
                    source_id=job.get("slug", ""),
                    company=job.get("company_name", ""),
                    title=job.get("title", ""),
                    location=job.get("location", ""),
                    location_type=self._infer_location_type(job.get("location", "")),
                    url=job.get("url", ""),
                    apply_url=job.get("url", ""),
                    description=job.get("description", "") or "",
                    employment_type="internship" if "intern" in job.get("title", "").lower() else "unknown",
                    posted_at=None,
                )
            )
        return jobs

    def _fetch_generic_job_board(self, name: str, url: str) -> List[JobPosting]:
        jobs: List[JobPosting] = []
        data = self._get_json(url)
        if not data:
            return jobs

        items = data.get("jobs") or data.get("data") or []
        for job in items:
            title = job.get("title") or job.get("name") or ""
            company = job.get("company") or job.get("company_name") or name
            location = job.get("location") or job.get("candidate_required_location") or ""
            job_url = job.get("url") or job.get("apply_url") or ""
            jobs.append(
                JobPosting(
                    source=name,
                    source_id=str(job.get("id") or job.get("slug") or job_url),
                    company=company,
                    title=title,
                    location=location,
                    location_type=self._infer_location_type(location),
                    url=job_url,
                    apply_url=job_url,
                    description=job.get("description", "") or "",
                    employment_type=self._infer_employment_type(title, job.get("description", "")),
                    posted_at=job.get("posted_at"),
                )
            )
        return jobs

    def _get_json(self, url: str) -> Dict[str, Any]:
        """
        Fetch JSON from URL with retry logic
        
        Args:
            url: URL to fetch
            
        Returns:
            JSON response as dictionary (empty dict on error)
        """
        return self.http_client.get_json(url)

    def _guess_company_from_url(self, url: str) -> str:
        domain = url.split("//")[-1].split("/")[0]
        return domain.replace("www.", "")

    def _infer_location_type(self, location: str) -> str:
        location_lower = (location or "").lower()
        if "remote" in location_lower:
            return "remote"
        if "hybrid" in location_lower:
            return "hybrid"
        if location_lower:
            return "onsite"
        return "unknown"

    def _infer_employment_type(self, title: str, description: str) -> str:
        text = f"{title} {description}".lower()
        if "intern" in text:
            return "internship"
        if "contract" in text:
            return "contract"
        if "full-time" in text or "full time" in text:
            return "full_time"
        return "unknown"

    def _contains_role_keywords(self, text: str) -> bool:
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.role_keywords)

    def _score_job(self, job: JobPosting) -> float:
        text = f"{job.title} {job.description}".lower()
        score = 0.0

        # Role match
        role_hits = sum(1 for keyword in self.role_keywords if keyword in text)
        score += min(role_hits / max(len(self.role_keywords), 1), 0.4)

        # Location match
        location = (job.location or "").lower()
        location_type = job.location_type.lower()
        location_score = 0.0
        if any(loc in location for loc in self.target_locations):
            location_score = 0.3
        elif location_type == "remote":
            location_score = 0.25
        score += location_score

        # Visa/relocation checks for US
        is_us = any(term in location for term in ["united states", "usa", "us", "u.s."])
        visa_keywords = ["visa", "sponsorship", "sponsor", "h1b"]
        relocation_keywords = ["relocation", "relocate", "moving assistance"]
        negations = [
            "no visa",
            "without visa",
            "without any visa",
            "no sponsorship",
            "without sponsorship",
            "not sponsor",
            "does not sponsor",
            "do not sponsor",
            "no relocation",
            "without relocation",
        ]
        has_negation = any(n in text for n in negations) or ("without" in text and "visa" in text)
        job.visa_sponsorship = any(k in text for k in visa_keywords) and not has_negation
        job.relocation_support = any(k in text for k in relocation_keywords) and not has_negation
        if is_us and self.allow_us_with_visa:
            if job.visa_sponsorship or job.relocation_support:
                score += 0.15
            else:
                score -= 0.6

        # Season match
        job.season_match = self._matches_season(text)
        if job.season_match:
            score += 0.2

        # Employment type boost
        if job.employment_type == "internship":
            score += 0.1

        # Fortune 500 boost (if list available)
        if self.fortune500 and job.company:
            if job.company.lower() in self.fortune500:
                score += 0.1

        return max(0.0, min(score, 1.0))

    def _matches_season(self, text: str) -> bool:
        if "summer" in text or "2026" in text:
            return True
        if self.allow_long_term and any(term in text for term in ["12 month", "1 year", "year-long", "long-term"]):
            return True
        return False
    
    def get_diagnostic_info(self) -> Dict[str, Any]:
        """
        Get diagnostic information about the job discovery configuration
        
        Returns:
            Dictionary with diagnostic information
        """
        return {
            "config": {
                "score_threshold": self.score_threshold,
                "target_locations": self.target_locations,
                "role_keywords": self.role_keywords,
                "max_results": self.max_results,
                "allow_us_with_visa": self.allow_us_with_visa,
                "allow_long_term": self.allow_long_term,
            },
            "sources": {
                "ats_count": len(self.sources.get("ats_sources", [])),
                "api_count": len(self.sources.get("job_board_apis", [])),
                "custom_url_count": len(self.sources.get("custom_company_urls", [])),
                "login_required_count": len(self.sources.get("login_required_sources", [])),
            },
            "paths": {
                "job_sources_path": config.JOB_SOURCES_PATH,
                "fortune500_csv": config.JOB_FORTUNE500_CSV,
            },
        }
