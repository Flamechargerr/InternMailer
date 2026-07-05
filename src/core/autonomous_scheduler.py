"""
Autonomous Job Application Scheduler
=====================================
Runs the full job application pipeline autonomously on a schedule:
1. Discover new jobs from all sources
2. Score and filter jobs
3. Tailor resumes for top matches
4. Apply to jobs with rate limiting
5. Track everything in the dashboard
"""

from __future__ import annotations

import json
import time
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.config import config
from core.enhanced_job_discovery import EnhancedJobDiscovery
from core.mass_apply_orchestrator import MassApplyOrchestrator
from core.database_manager import get_job_discovery_db

logger = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    discover_interval_hours: float = 6.0
    apply_interval_hours: float = 4.0
    max_jobs_per_discover: int = 500
    max_jobs_per_apply: int = 25
    max_jobs_to_tailor: int = 25
    min_score_threshold: float = 0.3
    auto_tailor: bool = True
    submit_mode: str = "full_auto"
    max_applications_per_hour: int = 8
    max_applications_per_day: int = 40
    active_hours_start: int = 0   # 12 AM (24/7 mode)
    active_hours_end: int = 24    # 12 AM next day (24/7 mode)
    skip_weekends: bool = False
    enabled: bool = True


@dataclass
class SchedulerRun:
    run_id: str
    started_at: str
    type: str  # "discover", "apply", "full_pipeline"
    status: str = "running"  # "running", "completed", "failed"
    jobs_found: int = 0
    jobs_saved: int = 0
    jobs_applied: int = 0
    jobs_failed: int = 0
    jobs_needs_review: int = 0
    error_message: Optional[str] = None
    finished_at: Optional[str] = None


class AutonomousScheduler:
    """Autonomous scheduler that runs the job application pipeline."""
    
    def __init__(self, scheduler_config: Optional[SchedulerConfig] = None):
        self.config = scheduler_config or SchedulerConfig()
        self.discovery = EnhancedJobDiscovery()
        self.orchestrator = MassApplyOrchestrator(
            max_per_hour=self.config.max_applications_per_hour,
            max_per_day=self.config.max_applications_per_day,
            submit_mode=self.config.submit_mode,
            auto_tailor=self.config.auto_tailor,
            min_score=self.config.min_score_threshold,
        )
        self.db = get_job_discovery_db(config.JOBS_DB_PATH)
        
        self.runs: List[SchedulerRun] = []
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        
        # Ensure runs table exists
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize scheduler tracking table."""
        try:
            self.db.execute("""
                CREATE TABLE IF NOT EXISTS scheduler_runs (
                    run_id TEXT PRIMARY KEY,
                    started_at TEXT,
                    finished_at TEXT,
                    type TEXT,
                    status TEXT,
                    jobs_found INTEGER DEFAULT 0,
                    jobs_saved INTEGER DEFAULT 0,
                    jobs_applied INTEGER DEFAULT 0,
                    jobs_failed INTEGER DEFAULT 0,
                    jobs_needs_review INTEGER DEFAULT 0,
                    error_message TEXT
                )
            """)
        except Exception as e:
            logger.error(f"Failed to init scheduler table: {e}")
    
    def _is_active_time(self) -> bool:
        """Check if current time is within active hours."""
        now = datetime.now()
        
        if self.config.skip_weekends and now.weekday() >= 5:
            return False
        
        if not (self.config.active_hours_start <= now.hour < self.config.active_hours_end):
            return False
        
        return True
    
    def _create_run(self, run_type: str) -> SchedulerRun:
        """Create a new run record."""
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        run = SchedulerRun(
            run_id=run_id,
            started_at=datetime.now().isoformat(),
            type=run_type,
        )
        self.runs.append(run)
        
        try:
            self.db.insert("scheduler_runs", {
                "run_id": run.run_id,
                "started_at": run.started_at,
                "type": run.type,
                "status": run.status,
            })
        except Exception:
            pass
        
        return run
    
    def _update_run(self, run: SchedulerRun) -> None:
        """Update run record in database."""
        try:
            self.db.update(
                "scheduler_runs",
                {
                    "status": run.status,
                    "finished_at": run.finished_at,
                    "jobs_found": run.jobs_found,
                    "jobs_saved": run.jobs_saved,
                    "jobs_applied": run.jobs_applied,
                    "jobs_failed": run.jobs_failed,
                    "jobs_needs_review": run.jobs_needs_review,
                    "error_message": run.error_message,
                },
                "run_id = ?",
                (run.run_id,),
            )
        except Exception:
            pass
    
    def discover(self) -> SchedulerRun:
        """Run job discovery."""
        run = self._create_run("discover")
        print(f"🔍 [{run.run_id}] Starting job discovery...")
        
        try:
            result = self.discovery.run()
            run.jobs_found = result.get("total_found", 0)
            run.jobs_saved = result.get("total_saved", 0)
            run.status = "completed"
            print(f"   ✅ Found {run.jobs_found} jobs, saved {run.jobs_saved}")
        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            print(f"   ❌ Discovery failed: {e}")
        
        run.finished_at = datetime.now().isoformat()
        self._update_run(run)
        return run
    
    def apply(self) -> SchedulerRun:
        """Run application pipeline."""
        run = self._create_run("apply")
        print(f"📨 [{run.run_id}] Starting application pipeline...")
        
        try:
            # Get pending jobs from DB
            rows = self.db.fetch_all(
                """SELECT * FROM jobs WHERE status = 'new' AND score >= ? 
                   ORDER BY score DESC LIMIT ?""",
                (self.config.min_score_threshold, self.config.max_jobs_per_apply),
            )
            jobs = [dict(row) for row in rows]
            
            if not jobs:
                print("   ℹ️ No jobs to apply to")
                run.status = "completed"
                run.finished_at = datetime.now().isoformat()
                self._update_run(run)
                return run
            
            # Run full pipeline
            result = self.orchestrator.run_full_pipeline(
                jobs=jobs,
                max_tailor=self.config.max_jobs_to_tailor,
                max_apply=self.config.max_jobs_per_apply,
            )
            
            stats = self.orchestrator.stats
            run.jobs_applied = stats.get("applied", 0)
            run.jobs_failed = stats.get("failed", 0)
            run.jobs_needs_review = stats.get("needs_review", 0)
            run.status = "completed"
            print(f"   ✅ Applied: {run.jobs_applied}, Failed: {run.jobs_failed}, Review: {run.jobs_needs_review}")
            
        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            print(f"   ❌ Application pipeline failed: {e}")
        
        run.finished_at = datetime.now().isoformat()
        self._update_run(run)
        return run
    
    def full_pipeline(self) -> SchedulerRun:
        """Run full pipeline: discover + apply."""
        run = self._create_run("full_pipeline")
        print(f"🚀 [{run.run_id}] Running FULL PIPELINE...")
        
        try:
            # Step 1: Discover
            print("\n📌 Step 1: Job Discovery")
            discover_result = self.discovery.run()
            run.jobs_found = discover_result.get("total_found", 0)
            run.jobs_saved = discover_result.get("total_saved", 0)
            
            # Step 2: Apply
            print("\n📌 Step 2: Application Pipeline")
            apply_result = self.orchestrator.run_full_pipeline(
                max_tailor=self.config.max_jobs_to_tailor,
                max_apply=self.config.max_jobs_per_apply,
            )
            
            stats = self.orchestrator.stats
            run.jobs_applied = stats.get("applied", 0)
            run.jobs_failed = stats.get("failed", 0)
            run.jobs_needs_review = stats.get("needs_review", 0)
            run.status = "completed"
            
        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            print(f"❌ Full pipeline failed: {e}")
        
        run.finished_at = datetime.now().isoformat()
        self._update_run(run)
        return run
    
    def run_scheduler_loop(self) -> None:
        """Main scheduler loop that runs continuously."""
        self._running = True
        
        last_discover = datetime.min
        last_apply = datetime.min
        
        print("🤖 Autonomous Scheduler Started")
        print(f"   Discovery interval: {self.config.discover_interval_hours}h")
        print(f"   Apply interval: {self.config.apply_interval_hours}h")
        print(f"   Active hours: {self.config.active_hours_start}:00 - {self.config.active_hours_end}:00")
        print(f"   Skip weekends: {self.config.skip_weekends}")
        print(f"   Press Ctrl+C to stop\n")
        
        while not self._stop_event.is_set():
            try:
                now = datetime.now()
                
                if not self._is_active_time():
                    next_active = self._get_next_active_time()
                    wait_seconds = (next_active - now).total_seconds()
                    print(f"⏸️ Outside active hours. Next active: {next_active.strftime('%Y-%m-%d %H:%M')}")
                    self._stop_event.wait(timeout=min(wait_seconds, 300))
                    continue
                
                # Check if it's time to discover
                discover_elapsed = (now - last_discover).total_seconds() / 3600
                if discover_elapsed >= self.config.discover_interval_hours:
                    print(f"\n{'='*60}")
                    print(f"🔍 Scheduled discovery triggered ({now.strftime('%H:%M')})")
                    print(f"{'='*60}")
                    self.discover()
                    last_discover = now
                
                # Check if it's time to apply
                apply_elapsed = (now - last_apply).total_seconds() / 3600
                if apply_elapsed >= self.config.apply_interval_hours:
                    print(f"\n{'='*60}")
                    print(f"📨 Scheduled application triggered ({now.strftime('%H:%M')})")
                    print(f"{'='*60}")
                    self.apply()
                    last_apply = now
                
                # Sleep for 1 minute
                self._stop_event.wait(timeout=60)
                
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                time.sleep(60)
        
        self._running = False
        print("\n🛑 Scheduler stopped")
    
    def _get_next_active_time(self) -> datetime:
        """Calculate next active time."""
        now = datetime.now()
        
        # If it's a weekend and we skip weekends, go to Monday
        if self.config.skip_weekends and now.weekday() >= 5:
            days_until_monday = 7 - now.weekday()
            next_active = now + timedelta(days=days_until_monday)
            next_active = next_active.replace(hour=self.config.active_hours_start, minute=0, second=0)
            return next_active
        
        # If before active hours, go to start time
        if now.hour < self.config.active_hours_start:
            return now.replace(hour=self.config.active_hours_start, minute=0, second=0)
        
        # If after active hours, go to start time tomorrow
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=self.config.active_hours_start, minute=0, second=0)
    
    def start(self) -> None:
        """Start the scheduler in a background thread."""
        if self._running:
            print("Scheduler already running")
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self.run_scheduler_loop, daemon=True)
        self._thread.start()
        print("✅ Scheduler started in background thread")
    
    def stop(self) -> None:
        """Stop the scheduler."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        print("🛑 Scheduler stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status."""
        # Get recent runs
        try:
            recent_runs = self.db.fetch_all(
                "SELECT * FROM scheduler_runs ORDER BY started_at DESC LIMIT 10"
            )
        except Exception:
            recent_runs = []
        
        return {
            "running": self._running,
            "config": {
                "discover_interval_hours": self.config.discover_interval_hours,
                "apply_interval_hours": self.config.apply_interval_hours,
                "max_jobs_per_apply": self.config.max_jobs_per_apply,
                "max_applications_per_hour": self.config.max_applications_per_hour,
                "max_applications_per_day": self.config.max_applications_per_day,
                "active_hours": f"{self.config.active_hours_start}:00 - {self.config.active_hours_end}:00",
                "skip_weekends": self.config.skip_weekends,
            },
            "is_active_time": self._is_active_time(),
            "next_active_time": self._get_next_active_time().isoformat(),
            "recent_runs": [dict(r) for r in recent_runs],
            "total_runs": len(self.runs),
        }
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics."""
        try:
            # Total runs
            total_runs = self.db.fetch_one("SELECT COUNT(*) as count FROM scheduler_runs")["count"]
            
            # Runs by type
            runs_by_type = self.db.fetch_all(
                "SELECT type, COUNT(*) as count FROM scheduler_runs GROUP BY type"
            )
            
            # Success rate
            completed_runs = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM scheduler_runs WHERE status = 'completed'"
            )["count"]
            failed_runs = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM scheduler_runs WHERE status = 'failed'"
            )["count"]
            
            # Total jobs
            total_jobs = self.db.fetch_one("SELECT COUNT(*) as count FROM jobs")["count"]
            total_applied = self.db.fetch_one(
                "SELECT COUNT(*) as count FROM jobs WHERE status = 'applied'"
            )["count"]
            
            # Jobs by source
            jobs_by_source = self.db.fetch_all(
                "SELECT source, COUNT(*) as count FROM jobs GROUP BY source ORDER BY count DESC LIMIT 10"
            )
            
            return {
                "total_runs": total_runs,
                "runs_by_type": [dict(r) for r in runs_by_type],
                "success_rate": round((completed_runs / max(total_runs, 1)) * 100, 1),
                "failed_runs": failed_runs,
                "total_jobs": total_jobs,
                "total_applied": total_applied,
                "application_rate": round((total_applied / max(total_jobs, 1)) * 100, 1),
                "jobs_by_source": [dict(r) for r in jobs_by_source],
                "orchestrator": self.orchestrator.get_analytics() if hasattr(self, 'orchestrator') else {},
            }
        except Exception as e:
            logger.error(f"Analytics error: {e}")
            return {"error": str(e)}


# ==================== STANDALONE RUNNER ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Autonomous Job Application Scheduler")
    parser.add_argument("--discover", action="store_true", help="Run discovery once")
    parser.add_argument("--apply", action="store_true", help="Run application pipeline once")
    parser.add_argument("--full", action="store_true", help="Run full pipeline once")
    parser.add_argument("--daemon", action="store_true", help="Run as continuous daemon")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--analytics", action="store_true", help="Show analytics")
    args = parser.parse_args()
    
    scheduler = AutonomousScheduler()
    
    if args.discover:
        scheduler.discover()
    elif args.apply:
        scheduler.apply()
    elif args.full:
        scheduler.full_pipeline()
    elif args.daemon:
        try:
            scheduler.run_scheduler_loop()
        except KeyboardInterrupt:
            print("\n\n👋 Stopped by user")
    elif args.status:
        print(json.dumps(scheduler.get_status(), indent=2))
    elif args.analytics:
        print(json.dumps(scheduler.get_analytics(), indent=2))
    else:
        print("Usage:")
        print("  python core/autonomous_scheduler.py --discover   # Run discovery once")
        print("  python core/autonomous_scheduler.py --apply      # Run apply once")
        print("  python core/autonomous_scheduler.py --full       # Run full pipeline")
        print("  python core/autonomous_scheduler.py --daemon     # Run continuous scheduler")
        print("  python core/autonomous_scheduler.py --status     # Show status")
        print("  python core/autonomous_scheduler.py --analytics  # Show analytics")
