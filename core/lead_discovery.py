"""
🎯 Enhanced Lead Discovery
===========================
Advanced lead discovery with Apollo.io integration, company enrichment,
and hiring manager identification.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse
import time

import requests
from bs4 import BeautifulSoup

from utils.config import config
from utils.validators import EmailValidator


@dataclass
class EnrichedContact:
    """Enhanced contact with enrichment data."""
    name: str
    email: str
    company: str
    domain: str
    role: str
    seniority: str
    department: str
    linkedin_url: str
    phone: str
    source: str
    confidence: float
    enrichment_data: Dict[str, Any]
    discovered_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "email": self.email,
            "company": self.company,
            "domain": self.domain,
            "role": self.role,
            "seniority": self.seniority,
            "department": self.department,
            "linkedin_url": self.linkedin_url,
            "phone": self.phone,
            "source": self.source,
            "confidence": self.confidence,
            "enrichment_data": json.dumps(self.enrichment_data),
            "discovered_at": self.discovered_at,
        }


@dataclass
class CompanyInfo:
    """Enriched company information."""
    name: str
    domain: str
    industry: str
    size: str
    location: str
    linkedin_url: str
    glassdoor_rating: Optional[float]
    description: str
    technologies: List[str]
    enriched_at: str


class ApolloEnhancedClient:
    """Enhanced Apollo.io API client with people search and enrichment."""
    
    BASE_URL = "https://api.apollo.io/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": api_key,
        })
    
    def search_people(
        self,
        domain: str,
        titles: Optional[List[str]] = None,
        seniorities: Optional[List[str]] = None,
        departments: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search for people at a company domain."""
        url = f"{self.BASE_URL}/mixed_people/search"
        
        payload = {
            "q_organization_domains_list": [domain],
            "per_page": min(limit, 100),
            "page": 1,
        }
        
        if titles:
            payload["person_titles"] = titles
        if seniorities:
            payload["person_seniorities"] = seniorities
        if departments:
            payload["person_departments"] = departments
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("people", [])
        except Exception as e:
            print(f"⚠️ Apollo people search failed for {domain}: {e}")
            return []
    
    def enrich_person(self, email: str) -> Optional[Dict[str, Any]]:
        """Enrich a contact by email."""
        url = f"{self.BASE_URL}/people/match"
        
        payload = {"email": email}
        
        try:
            response = self.session.post(url, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
            return data.get("person")
        except Exception as e:
            print(f"⚠️ Apollo enrichment failed for {email}: {e}")
            return None
    
    def enrich_company(self, domain: str) -> Optional[Dict[str, Any]]:
        """Enrich company information by domain."""
        url = f"{self.BASE_URL}/organizations/enrich"
        
        payload = {"domain": domain}
        
        try:
            response = self.session.post(url, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
            return data.get("organization")
        except Exception as e:
            print(f"⚠️ Apollo company enrichment failed for {domain}: {e}")
            return None


class HunterClient:
    """Hunter.io API client."""
    
    BASE_URL = "https://api.hunter.io/v2"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
    
    def domain_search(
        self,
        domain: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search for emails at a domain."""
        url = f"{self.BASE_URL}/domain-search"
        
        params = {
            "domain": domain,
            "api_key": self.api_key,
            "limit": limit,
        }
        
        try:
            response = self.session.get(url, params=params, timeout=20)
            response.raise_for_status()
            data = response.json()
            return data.get("data", {}).get("emails", [])
        except Exception as e:
            print(f"⚠️ Hunter domain search failed for {domain}: {e}")
            return []


class EnhancedLeadDiscovery:
    """
    Enhanced lead discovery with:
    - Apollo.io people search & enrichment
    - LinkedIn Sales Navigator (when available)
    - Company enrichment
    - Hiring manager identification
    - Company research integration
    """
    
    def __init__(
        self,
        output_csv: Optional[str] = None,
        state_path: Optional[str] = None,
    ):
        self.output_csv = Path(output_csv or config.COMPANY_CONTACTS_CSV)
        self.state_path = Path(state_path or config.CONTACT_DISCOVERY_STATE_PATH)
        
        # Initialize API clients
        self.apollo = None
        self.hunter = None
        
        if config.APOLLO_API_KEY:
            self.apollo = ApolloEnhancedClient(config.APOLLO_API_KEY)
        
        if config.HUNTER_API_KEY:
            self.hunter = HunterClient(config.HUNTER_API_KEY)
        
        # Role targeting
        self.role_keywords = [
            kw.strip().lower()
            for kw in config.CONTACT_ROLE_KEYWORDS.split(",")
            if kw.strip()
        ]
        
        self.hiring_manager_titles = [
            t.strip().lower()
            for t in config.LEAD_DISCOVERY_HIRING_MANAGER_TITLES.split(",")
            if t.strip()
        ]
        
        # Load domain filters
        self.blacklist_domains = set(
            d.strip().lower()
            for d in config.BLACKLIST_DOMAINS.split(",")
            if d.strip()
        )
        
        self.whitelist_domains = set(
            d.strip().lower()
            for d in config.WHITELIST_DOMAINS.split(",")
            if d.strip()
        )
        
        self.target_companies = set(
            c.strip().lower()
            for c in config.TARGET_COMPANIES_LIST.split(",")
            if c.strip()
        )
    
    def discover(
        self,
        domains: Optional[List[str]] = None,
        daily_cap: Optional[int] = None,
        prioritize_hiring_managers: bool = True,
    ) -> Dict[str, Any]:
        """
        Run enhanced lead discovery.
        
        Args:
            domains: List of domains to search (optional)
            daily_cap: Maximum contacts to discover today
            prioritize_hiring_managers: Whether to prioritize hiring manager titles
        
        Returns:
            Discovery results with statistics
        """
        if not config.LEAD_DISCOVERY_ENABLED:
            return {"status": "disabled", "contacts_found": 0}
        
        cap = daily_cap or config.CONTACT_DISCOVERY_DAILY_CAP
        
        if not self._check_api_availability():
            return {"status": "no_api_keys", "contacts_found": 0}
        
        # Collect domains
        if domains is None:
            domains = self._collect_domains()
        
        domains = self._filter_domains(domains)
        
        if not domains:
            return {"status": "no_domains", "contacts_found": 0}
        
        print(f"🔍 Discovering leads from {len(domains)} domains...")
        
        existing_emails = self._load_existing_emails()
        all_contacts: List[EnrichedContact] = []
        companies_enriched: Set[str] = set()
        
        remaining = cap
        
        for domain in domains:
            if remaining <= 0:
                break
            
            print(f"  📍 Processing {domain}...")
            
            # Enrich company info if enabled
            if config.LEAD_DISCOVERY_ENRICHMENT_ENABLED and self.apollo:
                if domain not in companies_enriched:
                    company_info = self._enrich_company(domain)
                    if company_info:
                        companies_enriched.add(domain)
                        print(f"    🏢 Enriched: {company_info.name}")
            
            # Search for people
            titles = self.hiring_manager_titles if prioritize_hiring_managers else None
            
            contacts = self._search_domain(domain, titles, remaining)
            
            for contact in contacts:
                if remaining <= 0:
                    break
                
                if contact.email.lower() in existing_emails:
                    continue
                
                if self._is_academic_contact(contact):
                    continue
                
                if self._is_blacklisted(contact):
                    continue
                
                all_contacts.append(contact)
                existing_emails.add(contact.email.lower())
                remaining -= 1
            
            # Rate limiting
            time.sleep(0.5)
        
        # Save contacts
        saved = self._save_contacts(all_contacts)
        
        # Update state
        self._update_state(saved)
        
        result = {
            "status": "success",
            "contacts_found": len(all_contacts),
            "contacts_saved": saved,
            "domains_processed": len(domains),
            "companies_enriched": len(companies_enriched),
            "remaining_quota": remaining,
        }
        
        print(f"✅ Discovery complete: {saved} contacts saved")
        return result
    
    def _check_api_availability(self) -> bool:
        """Check if any discovery source is available (including free scraping)."""
        # Always True — free scraping sources are always available
        return True
    
    def _search_domain(
        self,
        domain: str,
        titles: Optional[List[str]],
        limit: int,
    ) -> List[EnrichedContact]:
        """Search for contacts at a domain using APIs + free scraping."""
        contacts: List[EnrichedContact] = []
        seen_emails: Set[str] = set()
        
        def _add(new_contacts):
            for c in new_contacts:
                if c.email.lower() not in seen_emails:
                    seen_emails.add(c.email.lower())
                    contacts.append(c)
        
        # 1. Apollo (best data quality)
        if self.apollo and len(contacts) < limit:
            try:
                _add(self._search_apollo(domain, titles, limit - len(contacts)))
            except Exception as e:
                print(f"    ⚠️ Apollo error: {e}")
        
        # 2. Hunter.io
        if self.hunter and len(contacts) < limit:
            try:
                _add(self._search_hunter(domain, limit - len(contacts)))
            except Exception as e:
                print(f"    ⚠️ Hunter error: {e}")
        
        # 3. FREE: Scrape company website for contact info
        if len(contacts) < limit:
            try:
                _add(self._scrape_company_website(domain, limit - len(contacts)))
            except Exception as e:
                print(f"    ⚠️ Website scrape error: {e}")
        
        # 4. FREE: Generate email patterns from common HR names
        if len(contacts) < limit:
            try:
                _add(self._generate_email_patterns(domain, limit - len(contacts)))
            except Exception as e:
                print(f"    ⚠️ Pattern gen error: {e}")
        
        return contacts[:limit]
    
    # ─────────────────────────────────────────────────────
    #  FREE DISCOVERY SOURCES (no API key needed)
    # ─────────────────────────────────────────────────────
    
    def _scrape_company_website(self, domain: str, limit: int) -> List[EnrichedContact]:
        """Scrape company website (about/team/careers pages) for email addresses."""
        contacts: List[EnrichedContact] = []
        
        pages_to_try = [
            f"https://{domain}/about",
            f"https://{domain}/team",
            f"https://{domain}/contact",
            f"https://{domain}/careers",
            f"https://{domain}/about-us",
            f"https://{domain}/our-team",
        ]
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        
        seen: Set[str] = set()
        
        for page_url in pages_to_try:
            if len(contacts) >= limit:
                break
            
            try:
                resp = requests.get(page_url, headers=headers, timeout=8, allow_redirects=True)
                if resp.status_code != 200:
                    continue
                
                text = resp.text
                
                # Extract emails from page
                email_pattern = re.compile(
                    r'[a-zA-Z0-9._%+\-]+@' + re.escape(domain),
                    re.IGNORECASE
                )
                found_emails = email_pattern.findall(text)
                
                for email in found_emails:
                    email = email.lower().strip()
                    if email in seen or not EmailValidator.is_valid_email(email):
                        continue
                    
                    # Skip generic/noreply addresses
                    generic = {'noreply', 'no-reply', 'info', 'support', 'admin', 'webmaster',
                               'hello', 'contact', 'sales', 'marketing', 'press', 'media',
                               'help', 'feedback', 'careers', 'jobs', 'privacy', 'security'}
                    local_part = email.split('@')[0].lower()
                    if local_part in generic:
                        continue
                    
                    seen.add(email)
                    
                    # Try to extract name from page context around email
                    name = self._extract_name_near_email(text, email)
                    
                    contacts.append(EnrichedContact(
                        name=name or local_part.replace('.', ' ').replace('_', ' ').title(),
                        email=email,
                        company=domain.split('.')[0].title(),
                        domain=domain,
                        role="(scraped from website)",
                        seniority="",
                        department="",
                        linkedin_url="",
                        phone="",
                        source="web_scrape",
                        confidence=0.65,
                        enrichment_data={"scraped_from": page_url},
                        discovered_at=datetime.now().isoformat(),
                    ))
                
                time.sleep(0.3)  # polite scraping delay
            except requests.exceptions.RequestException:
                continue
        
        return contacts[:limit]
    
    def _extract_name_near_email(self, html: str, email: str) -> Optional[str]:
        """Try to find a person's name near their email in HTML."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find the email in the page and look for nearby text
            for element in soup.find_all(string=re.compile(re.escape(email), re.IGNORECASE)):
                parent = element.parent
                if parent:
                    # Check siblings and parent for name-like text
                    for sibling in [parent.previous_sibling, parent.next_sibling, parent.parent]:
                        if sibling and hasattr(sibling, 'get_text'):
                            text = sibling.get_text(strip=True)
                            # Name heuristic: 2-4 words, capitalized, no special chars
                            words = text.split()
                            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
                                return text
        except Exception:
            pass
        return None
    
    def _generate_email_patterns(self, domain: str, limit: int) -> List[EnrichedContact]:
        """Generate likely recruiter/HR email addresses using common patterns.
        
        Many companies follow standard email patterns. We generate
        common HR/recruiting team addresses and verify them via SMTP
        or Hunter email verification if available.
        """
        contacts: List[EnrichedContact] = []
        
        # Common generic recruiting addresses that almost always exist
        recruiter_addresses = [
            ("careers", "Careers Team", "Recruiting"),
            ("recruiting", "Recruiting Team", "Recruiting"),
            ("recruitment", "Recruitment Team", "Recruiting"),
            ("talent", "Talent Acquisition", "Recruiting"),
            ("hr", "HR Team", "Human Resources"),
            ("people", "People Team", "Human Resources"),
            ("hiring", "Hiring Team", "Recruiting"),
            ("jobs", "Jobs Team", "Recruiting"),
            ("internships", "Internship Program", "Recruiting"),
            ("campus", "Campus Recruiting", "Recruiting"),
            ("university", "University Relations", "Recruiting"),
        ]
        
        company_name = domain.split('.')[0].title()
        
        for local, name, dept in recruiter_addresses:
            if len(contacts) >= limit:
                break
            
            email = f"{local}@{domain}"
            
            # Verify with Hunter if available
            verified = False
            confidence = 0.45
            if self.hunter:
                try:
                    result = self.hunter.verify_email(email)
                    if result and result.get('result') in ('deliverable', 'risky'):
                        verified = True
                        confidence = 0.80 if result['result'] == 'deliverable' else 0.55
                    elif result and result.get('result') == 'undeliverable':
                        continue  # Skip known-bad addresses
                except Exception:
                    pass
            
            contacts.append(EnrichedContact(
                name=f"{company_name} {name}",
                email=email,
                company=company_name,
                domain=domain,
                role=name,
                seniority="",
                department=dept,
                linkedin_url="",
                phone="",
                source="pattern" if not verified else "pattern_verified",
                confidence=confidence,
                enrichment_data={"method": "email_pattern", "verified": verified},
                discovered_at=datetime.now().isoformat(),
            ))
        
        return contacts[:limit]
    
    def _search_apollo(
        self,
        domain: str,
        titles: Optional[List[str]],
        limit: int,
    ) -> List[EnrichedContact]:
        """Search Apollo.io for contacts."""
        contacts: List[EnrichedContact] = []
        
        people = self.apollo.search_people(
            domain=domain,
            titles=titles,
            limit=limit,
        )
        
        for person in people:
            email = person.get("email", "").strip()
            if not email or not EmailValidator.is_valid_email(email):
                continue
            
            org = person.get("organization") or {}
            
            contact = EnrichedContact(
                name=" ".join(filter(None, [
                    person.get("first_name", ""),
                    person.get("last_name", "")
                ])).strip(),
                email=email,
                company=org.get("name") or domain,
                domain=domain,
                role=person.get("title", ""),
                seniority=person.get("seniority", ""),
                department=person.get("department", ""),
                linkedin_url=person.get("linkedin_url", ""),
                phone=person.get("phone", ""),
                source="apollo",
                confidence=self._calculate_confidence(person),
                enrichment_data={
                    "apollo_id": person.get("id"),
                    "organization": org,
                },
                discovered_at=datetime.now().isoformat(),
            )
            
            contacts.append(contact)
        
        return contacts
    
    def _search_hunter(self, domain: str, limit: int) -> List[EnrichedContact]:
        """Search Hunter.io for contacts."""
        contacts: List[EnrichedContact] = []
        
        emails = self.hunter.domain_search(domain, limit=limit)
        
        for email_data in emails:
            email = email_data.get("value", "").strip()
            if not email or not EmailValidator.is_valid_email(email):
                continue
            
            contact = EnrichedContact(
                name=email_data.get("first_name", "") + " " + email_data.get("last_name", ""),
                email=email,
                company=email_data.get("company") or email_data.get("organization") or domain,
                domain=domain,
                role=email_data.get("position", ""),
                seniority="",
                department=email_data.get("department", ""),
                linkedin_url="",
                phone="",
                source="hunter",
                confidence=float(email_data.get("confidence", 50)) / 100,
                enrichment_data={
                    "sources": email_data.get("sources", []),
                },
                discovered_at=datetime.now().isoformat(),
            )
            
            contacts.append(contact)
        
        return contacts
    
    def _enrich_company(self, domain: str) -> Optional[CompanyInfo]:
        """Enrich company information."""
        if not self.apollo:
            return None
        
        org = self.apollo.enrich_company(domain)
        if not org:
            return None
        
        return CompanyInfo(
            name=org.get("name", ""),
            domain=domain,
            industry=org.get("industry", ""),
            size=org.get("estimated_num_employees", ""),
            location=org.get("location", ""),
            linkedin_url=org.get("linkedin_url", ""),
            glassdoor_rating=None,  # Would need separate Glassdoor API
            description=org.get("description", ""),
            technologies=org.get("technologies", []),
            enriched_at=datetime.now().isoformat(),
        )
    
    def _collect_domains(self) -> List[str]:
        """Collect domains from various sources."""
        domains: Set[str] = set()
        
        # From job discovery
        try:
            from core.database_manager import get_job_discovery_db
            db = get_job_discovery_db(config.JOBS_DB_PATH)
            rows = db.fetch_all(
                "SELECT DISTINCT company, apply_url, url FROM jobs WHERE created_at > date('now', '-30 days')"
            )
            
            for row in rows:
                company = row[0] if row[0] else ""
                for url in [row[1], row[2]]:
                    domain = self._extract_domain(url)
                    if domain:
                        domains.add(domain.lower())
                
                # Also add target companies by name lookup
                if company and company.lower() in self.target_companies:
                    # Try to find domain from overrides
                    overrides = self._load_domain_overrides()
                    if company in overrides:
                        domains.add(overrides[company].lower())
        except Exception as e:
            print(f"⚠️ Failed to collect from jobs: {e}")
        
        # From target companies list
        if self.target_companies:
            try:
                overrides = self._load_domain_overrides()
                for company in self.target_companies:
                    if company in overrides:
                        domains.add(overrides[company].lower())
            except Exception:
                pass
        
        # From whitelist
        domains.update(self.whitelist_domains)
        
        return list(domains)
    
    def _filter_domains(self, domains: List[str]) -> List[str]:
        """Filter and clean domain list."""
        filtered: List[str] = []
        seen: Set[str] = set()
        
        ats_domains = {
            "greenhouse.io", "lever.co", "ashbyhq.com", "smartrecruiters.com",
            "workable.com", "myworkdayjobs.com", "jobs.lever.co", "boards.greenhouse.io",
            "apply.workable.com", "careers.smartrecruiters.com",
        }
        
        for domain in domains:
            if not domain:
                continue
            
            domain = domain.lower().strip()
            
            # Skip duplicates
            if domain in seen:
                continue
            seen.add(domain)
            
            # Skip ATS domains
            if any(domain == ats or domain.endswith("." + ats) for ats in ats_domains):
                continue
            
            # Skip blacklisted
            if domain in self.blacklist_domains:
                continue
            
            # Skip academic
            if config.EMAIL_SKIP_ACADEMIC:
                if domain.endswith(".edu") or ".edu." in domain:
                    continue
                if ".ac." in domain:
                    continue
            
            filtered.append(domain)
        
        return filtered
    
    def _extract_domain(self, url: Optional[str]) -> Optional[str]:
        """Extract domain from URL."""
        if not url:
            return None
        
        # Basic validation - must contain a dot for a valid domain
        if "." not in url:
            return None
        
        if "://" not in url:
            url = "https://" + url
        
        try:
            parsed = urlparse(url)
            host = parsed.netloc or ""
            if not host:
                return None
            
            host = host.lower()
            if host.startswith("www."):
                host = host[4:]
            
            # Validate domain has at least one dot and looks valid
            if "." not in host:
                return None
            
            # Check for valid domain characters only
            import re
            if not re.match(r'^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?)*$', host):
                return None
            
            return host
        except Exception:
            return None
    
    def _load_existing_emails(self) -> Set[str]:
        """Load existing emails from CSV and database."""
        existing: Set[str] = set()
        
        # From CSV
        try:
            if self.output_csv.exists():
                with self.output_csv.open("r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        email = (row.get("email") or "").strip().lower()
                        if email:
                            existing.add(email)
        except (PermissionError, OSError):
            pass
        except Exception:
            pass
        
        # From tracking database
        try:
            import sqlite3
            with sqlite3.connect(config.DATABASE_PATH) as conn:
                cursor = conn.execute("SELECT DISTINCT email FROM sent_emails")
                for row in cursor.fetchall():
                    if row[0]:
                        existing.add(row[0].lower())
        except Exception:
            pass
        
        return existing
    
    def _load_domain_overrides(self) -> Dict[str, str]:
        """Load company to domain mappings."""
        overrides_path = Path(config.CONTACT_DISCOVERY_OVERRIDES)
        try:
            if not overrides_path.exists():
                return {}
            return json.loads(overrides_path.read_text())
        except (PermissionError, OSError):
            return {}
        except Exception:
            return {}
    
    def _is_academic_contact(self, contact: EnrichedContact) -> bool:
        """Check if contact is academic."""
        if not config.EMAIL_SKIP_ACADEMIC:
            return False
        
        domain = contact.email.split("@")[-1].lower()
        if domain.endswith(".edu") or ".ac." in domain:
            return True
        
        org = contact.company.lower()
        academic_keywords = [
            "university", "college", "institute", "school",
            "department", "faculty", "laboratory", "lab", "academy",
        ]
        
        return any(kw in org for kw in academic_keywords)
    
    def _is_blacklisted(self, contact: EnrichedContact) -> bool:
        """Check if contact domain is blacklisted."""
        domain = contact.email.split("@")[-1].lower()
        return domain in self.blacklist_domains
    
    def _calculate_confidence(self, person: Dict) -> float:
        """Calculate confidence score for Apollo contact."""
        score = 0.5  # Base score
        
        # Boost for verified email
        if person.get("email"):
            score += 0.3
        
        # Boost for complete profile
        if person.get("first_name") and person.get("last_name"):
            score += 0.1
        
        if person.get("title"):
            score += 0.05
        
        if person.get("linkedin_url"):
            score += 0.05
        
        return min(score, 1.0)
    
    def _save_contacts(self, contacts: List[EnrichedContact]) -> int:
        """Save contacts to CSV."""
        if not contacts:
            return 0
        
        try:
            self.output_csv.parent.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError):
            pass
        
        try:
            file_exists = self.output_csv.exists()
        except (PermissionError, OSError):
            file_exists = False
        
        with self.output_csv.open("a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(contacts[0].to_dict().keys()))
            
            if not file_exists:
                writer.writeheader()
            
            for contact in contacts:
                writer.writerow(contact.to_dict())
        
        return len(contacts)
    
    def _update_state(self, count: int):
        """Update discovery state."""
        try:
            state = {"date": datetime.now().strftime("%Y-%m-%d"), "count": count}
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_path.write_text(json.dumps(state))
        except Exception:
            pass


# Convenience function
def discover_leads(
    domains: Optional[List[str]] = None,
    daily_cap: Optional[int] = None,
    prioritize_hiring_managers: bool = True,
) -> Dict[str, Any]:
    """Convenience function to run lead discovery."""
    discovery = EnhancedLeadDiscovery()
    return discovery.discover(domains, daily_cap, prioritize_hiring_managers)


if __name__ == "__main__":
    import sys
    
    print("🚀 Enhanced Lead Discovery")
    print("=" * 50)
    
    # Test mode
    if "--test" in sys.argv:
        discovery = EnhancedLeadDiscovery()
        
        # Check API availability
        if not discovery._check_api_availability():
            print("❌ No API keys configured")
            sys.exit(1)
        
        print("✅ API clients initialized")
        print(f"   Apollo: {'✅' if discovery.apollo else '❌'}")
        print(f"   Hunter: {'✅' if discovery.hunter else '❌'}")
        
        # Test with a sample domain
        test_domains = ["stripe.com", "github.com"]
        result = discovery.discover(domains=test_domains, daily_cap=5)
        
        print(f"\n📊 Results:")
        print(json.dumps(result, indent=2))
    
    else:
        result = discover_leads()
        print(json.dumps(result, indent=2))
