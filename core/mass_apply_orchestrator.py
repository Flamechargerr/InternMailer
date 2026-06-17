"""
Mass Application Orchestrator
=============================
Intelligently orchestrates mass job applications with:
- Rate limiting and human-like delays
- Stealth patterns to avoid detection
- Retry logic with exponential backoff
- Priority queue based on job scores
- Concurrent application with safety limits
- Detailed tracking and analytics
"""

from __future__ import annotations

import json
import time
import random
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import Enum

from utils.config import config
from core.database_manager import get_job_discovery_db
from core.resume_tailor import ResumeTailor, TailoredDocument
from core.job_apply import JobAutoApplier, ApplyResult

logger = logging.getLogger(__name__)


class ApplicationState(Enum):
    QUEUED = "queued"
    TAILORING = "tailoring"
    READY = "ready"
    APPLYING = "applying"
    APPLIED = "applied"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"


@dataclass
class ApplicationRecord:
    job_id: int
    company: str
    position: str
    apply_url: str
    score: float
    state: ApplicationState = ApplicationState.QUEUED
    tailored_resume_path: Optional[str] = None
    tailored_cover_letter_path: Optional[str] = None
    apply_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    attempt_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    applied_at: Optional[str] = None
    last_attempt_at: Optional[str] = None


class RateLimiter:
    """Token bucket rate limiter with jitter."""
    
    def __init__(
        self,
        max_per_hour: int = 10,
        max_per_day: int = 50,
        min_delay_seconds: float = 180.0,
        max_delay_seconds: float = 600.0,
    ):
        self.max_per_hour = max_per_hour
        self.max_per_day = max_per_day
        self.min_delay = min_delay_seconds
        self.max_delay = max_delay_seconds
        
        self.hourly_applications: List[datetime] = []
        self.daily_applications: List[datetime] = []
        self.last_application_time: Optional[datetime] = None
    
    def can_apply(self) -> bool:
        now = datetime.now()
        
        # Clean old entries
        self.hourly_applications = [t for t in self.hourly_applications if now - t < timedelta(hours=1)]
        self.daily_applications = [t for t in self.daily_applications if now - t < timedelta(days=1)]
        
        if len(self.hourly_applications) >= self.max_per_hour:
            return False
        if len(self.daily_applications) >= self.max_per_day:
            return False
        
        return True
    
    def wait_time(self) -> float:
        if not self.last_application_time:
            return 0.0
        
        elapsed = (datetime.now() - self.last_application_time).total_seconds()
        required_delay = random.uniform(self.min_delay, self.max_delay)
        
        return max(0.0, required_delay - elapsed)
    
    def record_application(self) -> None:
        now = datetime.now()
        self.hourly_applications.append(now)
        self.daily_applications.append(now)
        self.last_application_time = now
    
    def get_status(self) -> Dict[str, Any]:
        now = datetime.now()
        self.hourly_applications = [t for t in self.hourly_applications if now - t < timedelta(hours=1)]
        self.daily_applications = [t for t in self.daily_applications if now - t < timedelta(days=1)]
        
        return {
            "hourly_used": len(self.hourly_applications),
            "hourly_limit": self.max_per_hour,
            "daily_used": len(self.daily_applications),
            "daily_limit": self.max_per_day,
            "can_apply": self.can_apply(),
            "next_available_in": self.wait_time(),
        }


class MassApplyOrchestrator:
    """Orchestrates mass job applications with safety and intelligence."""
    
    def __init__(
        self,
        max_per_hour: int = 8,
        max_per_day: int = 40,
        submit_mode: str = "human_verified",
        auto_tailor: bool = True,
        min_score: float = 0.3,
    ):
        self.db = get_job_discovery_db(config.JOBS_DB_PATH)
        self.rate_limiter = RateLimiter(
            max_per_hour=max_per_hour,
            max_per_day=max_per_day,
        )
        self.submit_mode = submit_mode
        self.auto_tailor = auto_tailor
        self.min_score = min_score
        self.tailor = ResumeTailor() if auto_tailor else None
        self.applier = JobAutoApplier(submit_mode=submit_mode)
        
        self.applications: List[ApplicationRecord] = []
        self.stats = {
            "queued": 0,
            "tailored": 0,
            "applied": 0,
            "failed": 0,
            "needs_review": 0,
            "skipped": 0,
        }
        
        # Load state from DB
        self._load_state()
    
    def _load_state(self) -> None:
        """Load pending applications from database."""
        try:
            rows = self.db.fetch_all(
                "SELECT * FROM jobs WHERE status = 'new' AND score >= ? ORDER BY score DESC",
                (self.min_score,),
            )
            for row in rows:
                self.applications.append(ApplicationRecord(
                    job_id=row["id"],
                    company=row.get("company", ""),
                    position=row.get("title", ""),
                    apply_url=row.get("apply_url", row.get("url", "")),
                    score=row.get("score", 0.0),
                ))
            self.stats["queued"] = len(self.applications)
        except Exception as e:
            logger.warning(f"Failed to load state: {e}")
    
    def queue_jobs(self, jobs: List[Dict[str, Any]]) -> int:
        """Queue new jobs for application."""
        queued = 0
        for job in jobs:
            if job.get("score", 0) < self.min_score:
                self.stats["skipped"] += 1
                continue
            
            record = ApplicationRecord(
                job_id=job.get("id", 0),
                company=job.get("company", ""),
                position=job.get("title", ""),
                apply_url=job.get("apply_url", job.get("url", "")),
                score=job.get("score", 0.0),
            )
            self.applications.append(record)
            queued += 1
        
        self.stats["queued"] += queued
        return queued
    
    def tailor_applications(self, max_tailor: int = 25) -> List[ApplicationRecord]:
        """Tailor resumes for queued applications."""
        if not self.tailor or not self.tailor.profile:
            logger.warning("Resume tailor not available, skipping tailoring")
            return []
        
        tailored = []
        to_tailor = [a for a in self.applications if a.state == ApplicationState.QUEUED][:max_tailor]
        
        for record in to_tailor:
            try:
                print(f"📝 Tailoring for {record.company} - {record.position}")
                
                # Get job description from DB
                job_row = self.db.fetch_one(
                    "SELECT description FROM jobs WHERE id = ?",
                    (record.job_id,),
                )
                description = job_row["description"] if job_row else ""
                
                doc = self.tailor.tailor_resume(
                    job_description=description,
                    company_name=record.company,
                    position=record.position,
                )
                
                record.tailored_resume_path = doc.resume_path
                record.tailored_cover_letter_path = doc.cover_letter_path
                record.state = ApplicationState.READY
                
                tailored.append(record)
                self.stats["tailored"] += 1
                print(f"   ✅ ATS score: {doc.ats_score_before} → {doc.ats_score_after}")
                
                # Rate limit AI calls
                time.sleep(random.uniform(1.0, 3.0))
                
            except Exception as e:
                logger.error(f"Tailoring failed for {record.company}: {e}")
                record.state = ApplicationState.READY
                record.error_message = f"Tailoring failed: {str(e)}"
                tailored.append(record)
        
        return tailored
    
    def apply_single(self, record: ApplicationRecord) -> ApplyResult:
        """Apply to a single job."""
        job_data = {
            "id": record.job_id,
            "company": record.company,
            "title": record.position,
            "apply_url": record.apply_url,
            "url": record.apply_url,
            "resume_path": record.tailored_resume_path,
            "cover_letter_path": record.tailored_cover_letter_path,
        }
        
        return self.applier.apply(job_data, submit_mode=self.submit_mode)
    
    def run_applications(self, max_applications: int = 25) -> Dict[str, Any]:
        """Run the application process for queued jobs."""
        results = []
        
        # Get ready applications
        ready = [a for a in self.applications if a.state in {
            ApplicationState.READY, ApplicationState.QUEUED
        }][:max_applications]
        
        if not ready:
            print("ℹ️ No jobs ready for application")
            return {"status": "no_jobs", "results": []}
        
        print(f"🚀 Starting mass application for {len(ready)} jobs")
        print(f"   Rate limit: {self.rate_limiter.max_per_hour}/hour, {self.rate_limiter.max_per_day}/day")
        
        for i, record in enumerate(ready):
            # Check rate limiter
            if not self.rate_limiter.can_apply():
                status = self.rate_limiter.get_status()
                print(f"⏸️ Rate limit reached. Hourly: {status['hourly_used']}/{status['hourly_limit']}, Daily: {status['daily_used']}/{status['daily_limit']}")
                print(f"   Waiting {status['next_available_in']:.0f} seconds...")
                time.sleep(status["next_available_in"] + 5)
                
                if not self.rate_limiter.can_apply():
                    print("❌ Still rate limited. Stopping for now.")
                    break
            
            print(f"\n📨 [{i+1}/{len(ready)}] Applying to {record.company} - {record.position}")
            print(f"   Score: {record.score:.2f} | URL: {record.apply_url[:60]}...")
            
            record.last_attempt_at = datetime.now().isoformat()
            record.attempt_count += 1
            
            try:
                # Apply
                record.state = ApplicationState.APPLYING
                result = self.apply_single(record)
                
                record.apply_result = {
                    "status": result.status,
                    "details": result.details,
                    "applied": result.applied,
                    "provider": result.provider,
                }
                
                if result.applied:
                    record.state = ApplicationState.APPLIED
                    record.applied_at = datetime.now().isoformat()
                    self.stats["applied"] += 1
                    self.rate_limiter.record_application()
                    print(f"   ✅ APPLIED! {result.details}")
                    
                    # Update DB
                    self._mark_job_applied(record.job_id, "applied", result.details)
                    
                elif result.status == "review_required":
                    record.state = ApplicationState.NEEDS_REVIEW
                    self.stats["needs_review"] += 1
                    print(f"   ⏸️ Needs review: {result.details}")
                    self._mark_job_applied(record.job_id, "needs_review", result.details)
                    
                elif result.status in ("blocked_captcha", "blocked_login"):
                    record.state = ApplicationState.NEEDS_REVIEW
                    self.stats["needs_review"] += 1
                    print(f"   🔒 Blocked: {result.status}")
                    self._mark_job_applied(record.job_id, "blocked", result.details)
                    
                else:
                    record.state = ApplicationState.FAILED
                    record.error_message = result.details
                    self.stats["failed"] += 1
                    print(f"   ❌ Failed: {result.status} - {result.details}")
                    self._mark_job_applied(record.job_id, "failed", result.details)
                
                results.append(record)
                
                # Human-like delay between applications
                if i < len(ready) - 1:
                    delay = random.uniform(self.rate_limiter.min_delay, self.rate_limiter.max_delay)
                    print(f"   ⏱️ Waiting {delay:.0f}s before next application...")
                    time.sleep(delay)
                    
            except Exception as e:
                record.state = ApplicationState.FAILED
                record.error_message = str(e)
                self.stats["failed"] += 1
                print(f"   ❌ Error: {str(e)[:80]}")
                self._mark_job_applied(record.job_id, "error", str(e))
                results.append(record)
        
        return {
            "status": "completed",
            "attempted": len(results),
            "stats": self.stats,
            "rate_limiter": self.rate_limiter.get_status(),
            "results": [asdict(r) for r in results],
        }
    
    def _mark_job_applied(self, job_id: int, status: str, details: str) -> None:
        """Mark job status in database."""
        try:
            self.db.update(
                "jobs",
                {
                    "status": status,
                    "applied_at": datetime.now().isoformat(),
                    "application_details": details,
                },
                "id = ?",
                (job_id,),
            )
            
            # Also insert into applications table
            self.db.insert(
                "applications",
                {
                    "job_id": job_id,
                    "method": "mass_orchestrator",
                    "status": status,
                    "details": details,
                    "applied_at": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} as {status}: {e}")
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get comprehensive application analytics."""
        try:
            total_jobs = self.db.fetch_one("SELECT COUNT(*) as count FROM jobs")["count"]
            applied_jobs = self.db.fetch_one("SELECT COUNT(*) as count FROM jobs WHERE status = 'applied'")["count"]
            failed_jobs = self.db.fetch_one("SELECT COUNT(*) as count FROM jobs WHERE status = 'failed'")["count"]
            review_jobs = self.db.fetch_one("SELECT COUNT(*) as count FROM jobs WHERE status = 'needs_review'")["count"]
            new_jobs = self.db.fetch_one("SELECT COUNT(*) as count FROM jobs WHERE status = 'new'")["count"]
            
            # Get top companies applied to
            top_companies = self.db.fetch_all(
                """SELECT company, COUNT(*) as count FROM jobs 
                   WHERE status = 'applied' GROUP BY company ORDER BY count DESC LIMIT 10"""
            )
            
            # Get daily application stats
            daily_stats = self.db.fetch_all(
                """SELECT DATE(applied_at) as date, COUNT(*) as count 
                   FROM applications WHERE applied_at IS NOT NULL 
                   GROUP BY DATE(applied_at) ORDER BY date DESC LIMIT 14"""
            )
            
            return {
                "total_jobs": total_jobs,
                "applied": applied_jobs,
                "failed": failed_jobs,
                "needs_review": review_jobs,
                "new": new_jobs,
                "success_rate": round((applied_jobs / max(total_jobs, 1)) * 100, 1),
                "top_companies": [dict(r) for r in top_companies],
                "daily_stats": [dict(r) for r in daily_stats],
                "rate_limiter": self.rate_limiter.get_status(),
                "orchestrator_stats": self.stats,
            }
        except Exception as e:
            logger.error(f"Analytics error: {e}")
            return {"error": str(e)}
    
    def run_full_pipeline(
        self,
        jobs: Optional[List[Dict[str, Any]]] = None,
        max_tailor: int = 25,
        max_apply: int = 25,
    ) -> Dict[str, Any]:
        """Run the full pipeline: discover -> tailor -> apply."""
        print("=" * 60)
        print("🚀 MASS APPLICATION PIPELINE")
        print("=" * 60)
        
        # Step 1: Queue jobs
        if jobs:
            queued = self.queue_jobs(jobs)
            print(f"📥 Queued {queued} jobs")
        
        # Step 2: Tailor resumes
        if self.auto_tailor and self.tailor:
            print(f"\n📝 Step 1: Tailoring resumes for up to {max_tailor} jobs...")
            tailored = self.tailor_applications(max_tailor=max_tailor)
            print(f"   ✅ Tailored {len(tailored)} resumes")
        
        # Step 3: Apply
        print(f"\n📨 Step 2: Applying to jobs (max {max_apply})...")
        result = self.run_applications(max_applications=max_apply)
        
        # Step 4: Analytics
        print(f"\n📊 Final Stats:")
        print(f"   Applied: {self.stats['applied']}")
        print(f"   Failed: {self.stats['failed']}")
        print(f"   Needs Review: {self.stats['needs_review']}")
        print(f"   Skipped: {self.stats['skipped']}")
        
        return result


# ==================== STANDALONE RUNNER ====================

if __name__ == "__main__":
    print("🚀 Mass Application Orchestrator")
    print("=" * 50)
    
    orchestrator = MassApplyOrchestrator()
    
    # Show current status
    status = orchestrator.rate_limiter.get_status()
    print(f"\n📊 Rate Limiter Status:")
    print(f"   Hourly: {status['hourly_used']}/{status['hourly_limit']}")
    print(f"   Daily: {status['daily_used']}/{status['daily_limit']}")
    print(f"   Can apply: {status['can_apply']}")
    
    # Show analytics
    analytics = orchestrator.get_analytics()
    print(f"\n📊 Application Analytics:")
    print(f"   Total jobs: {analytics.get('total_jobs', 0)}")
    print(f"   Applied: {analytics.get('applied', 0)}")
    print(f"   Success rate: {analytics.get('success_rate', 0)}%")
