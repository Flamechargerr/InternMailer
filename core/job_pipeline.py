"""
Job Pipeline - Apply to discovered jobs and track status.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, List

from utils.config import config
from core.database_manager import get_job_discovery_db
from core.job_apply import JobAutoApplier
from core.resume_service import optimize_for_job

logger = logging.getLogger(__name__)


class JobPipeline:
    def __init__(self):
        self.db = get_job_discovery_db(config.JOBS_DB_PATH)
        self.applier = JobAutoApplier()

    def get_pending_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        rows = self.db.fetch_all(
            "SELECT * FROM jobs WHERE status = 'new' AND score >= ? ORDER BY score DESC LIMIT ?",
            (config.JOB_SCORE_THRESHOLD, limit),
        )
        return [dict(row) for row in rows]

    def apply_pending(self, limit: int = 50) -> Dict[str, Any]:
        jobs = self.get_pending_jobs(limit=limit)
        results = []
        for job in jobs:
            resume_path = None
            cover_letter_path = None
            if job.get("description"):
                try:
                    optimization = optimize_for_job(
                        job["description"],
                        output_dir="optimized_documents",
                        company_name=job.get("company"),
                        position=job.get("title"),
                    )
                    resume_path = optimization.pdf_resume_path or optimization.resume_path
                    cover_letter_path = (
                        optimization.pdf_cover_letter_path or optimization.cover_letter_path
                    )
                    job["resume_path"] = resume_path
                    job["cover_letter_path"] = cover_letter_path
                except Exception as e:
                    logger.warning(f"Failed to optimize resume/cover letter for job {job.get('id', 'unknown')}: {e}")
                    resume_path = None
                    cover_letter_path = None

            result = self.applier.apply(job)
            results.append({
                "job_id": job["id"],
                "status": result.status,
                "details": result.details,
                "applied": result.applied,
            })
            self.db.insert(
                "applications",
                {
                    "job_id": job["id"],
                    "method": "playwright",
                    "status": result.status,
                    "details": result.details,
                },
            )
            self.db.update(
                "jobs",
                {"status": "applied" if result.applied else "needs_review"},
                "id = ?",
                (job["id"],),
            )

        return {"attempted": len(jobs), "results": results}
