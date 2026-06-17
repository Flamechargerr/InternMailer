"""
🎯 Job Matcher Agent - AI-Powered Job Scoring
=============================================
Intelligently scores and matches jobs to your profile.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.agents.base_agent import BaseAgent, AgentContext, AgentResponse
from utils.config import config


class JobMatcherAgent(BaseAgent):
    """
    Specialized agent for intelligent job matching.
    
    Capabilities:
    - AI-powered job description analysis
    - Profile-to-job matching
    - Skills gap identification
    - Priority ranking of opportunities
    """
    
    def __init__(self):
        super().__init__("JobMatcher")
    
    def run(self, context: AgentContext, **kwargs) -> AgentResponse:
        """
        Score and rank jobs against the profile.
        
        Kwargs:
            job_ids: Specific job IDs to score (optional)
            limit: Max jobs to process (default: 50)
            min_score: Minimum score threshold (default: 0.6)
        """
        job_ids = kwargs.get("job_ids", [])
        limit = kwargs.get("limit", 50)
        min_score = kwargs.get("min_score", config.JOB_SCORE_THRESHOLD)
        
        # Get jobs from database
        jobs = self._get_pending_jobs(job_ids, limit)
        
        if not jobs:
            return AgentResponse(
                success=True,
                agent_name=self.name,
                action_taken="match_jobs",
                message="No jobs to process",
                data={"jobs_processed": 0},
            )
        
        self.log("match_jobs", "info", f"Processing {len(jobs)} jobs")
        
        profile = context.profile
        scored_jobs = []
        
        for job in jobs:
            score_result = self._score_job(job, profile)
            job["ai_score"] = score_result["score"]
            job["match_reasons"] = score_result["reasons"]
            job["skills_matched"] = score_result["skills_matched"]
            job["skills_missing"] = score_result["skills_missing"]
            
            if job["ai_score"] >= min_score:
                scored_jobs.append(job)
        
        # Sort by score
        scored_jobs.sort(key=lambda x: x["ai_score"], reverse=True)
        
        # Update jobs in database
        self._update_job_scores(scored_jobs)
        
        return AgentResponse(
            success=True,
            agent_name=self.name,
            action_taken="match_jobs",
            result=scored_jobs[:10],  # Top 10 for response
            message=f"Scored {len(jobs)} jobs, {len(scored_jobs)} above threshold",
            data={
                "jobs_processed": len(jobs),
                "jobs_matched": len(scored_jobs),
                "top_score": scored_jobs[0]["ai_score"] if scored_jobs else 0,
            },
        )
    
    def _get_pending_jobs(self, job_ids: List[int], limit: int) -> List[Dict]:
        """Get jobs from the discovery database."""
        try:
            from core.database_manager import get_job_discovery_db
            db = get_job_discovery_db(config.JOBS_DB_PATH)
            
            if job_ids:
                placeholders = ",".join("?" * len(job_ids))
                rows = db.fetch_all(
                    f"SELECT * FROM jobs WHERE id IN ({placeholders})",
                    tuple(job_ids),
                )
            else:
                rows = db.fetch_all(
                    """
                    SELECT * FROM jobs 
                    WHERE (status IS NULL OR status IN ('new', 'pending'))
                    ORDER BY score DESC, created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
            
            return [dict(row) for row in rows]
        except Exception as e:
            self.log("get_jobs", "error", f"Failed to get jobs: {e}")
            return []
    
    def _score_job(self, job: Dict, profile: Dict) -> Dict[str, Any]:
        """
        Score a job against the profile using AI + rules.
        
        Returns:
            Dict with score, reasons, skills_matched, skills_missing
        """
        # Extract job info
        title = job.get("title", "")
        description = job.get("description", "")
        company = job.get("company", "")
        location = job.get("location", "")
        
        # Get profile skills
        profile_skills = profile.get("skills", [])
        if isinstance(profile_skills, dict):
            flat_skills = []
            for category in profile_skills.values():
                if isinstance(category, list):
                    flat_skills.extend(category)
            profile_skills = flat_skills
        profile_skills = [s.lower() for s in profile_skills if isinstance(s, str)]
        
        # Rule-based scoring
        rule_score = self._rule_based_score(job, profile)
        
        # Skills matching
        skills_result = self._match_skills(description, profile_skills)
        
        # AI scoring (if available)
        ai_score = None
        ai_reasons = []
        
        if self.ai_provider and description:
            ai_result = self._ai_score_job(job, profile)
            ai_score = ai_result.get("score")
            ai_reasons = ai_result.get("reasons", [])
        
        # Combine scores
        if ai_score is not None:
            final_score = (rule_score * 0.4) + (ai_score * 0.4) + (skills_result["match_ratio"] * 0.2)
        else:
            final_score = (rule_score * 0.6) + (skills_result["match_ratio"] * 0.4)
        
        reasons = []
        
        # Add rule-based reasons
        if "intern" in title.lower():
            reasons.append("Internship position")
        if any(loc.lower() in location.lower() for loc in config.JOB_TARGET_LOCATIONS.split(",")):
            reasons.append("Target location")
        if skills_result["skills_matched"]:
            reasons.append(f"Skills match: {', '.join(skills_result['skills_matched'][:3])}")
        
        # Add AI reasons
        reasons.extend(ai_reasons)
        
        return {
            "score": round(final_score, 2),
            "reasons": reasons[:5],
            "skills_matched": skills_result["skills_matched"],
            "skills_missing": skills_result["skills_missing"],
        }
    
    def _rule_based_score(self, job: Dict, profile: Dict) -> float:
        """Calculate rule-based score."""
        score = 0.5  # Base score
        
        title = (job.get("title") or "").lower()
        description = (job.get("description") or "").lower()
        location = (job.get("location") or "").lower()
        
        # Role keyword match
        role_keywords = [k.strip().lower() for k in config.JOB_ROLE_KEYWORDS.split(",")]
        for keyword in role_keywords:
            if keyword in title:
                score += 0.15
                break
        
        # Location match
        target_locations = [loc.strip().lower() for loc in config.JOB_TARGET_LOCATIONS.split(",")]
        for loc in target_locations:
            if loc in location or "remote" in location:
                score += 0.1
                break
        
        # Internship boost
        if "intern" in title:
            score += 0.1
        
        # Experience level check
        if any(x in title for x in ["senior", "staff", "principal", "lead"]):
            score -= 0.2  # Penalize senior roles for intern search
        
        # Visa sponsorship (if mentioned positively)
        if "visa" in description and ("sponsor" in description or "h1b" in description):
            if config.JOB_ALLOW_USA_WITH_VISA:
                score += 0.05
        
        return max(0, min(1, score))
    
    def _match_skills(self, description: str, profile_skills: List[str]) -> Dict:
        """Match profile skills against job description."""
        description_lower = description.lower()
        
        matched = []
        for skill in profile_skills:
            # Create pattern for skill matching
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, description_lower):
                matched.append(skill)
        
        # Extract required skills from JD that we don't have
        common_skills = [
            "python", "java", "javascript", "sql", "react", "node.js",
            "aws", "docker", "kubernetes", "git", "ci/cd", "agile",
            "machine learning", "data science", "api", "rest", "graphql",
        ]
        
        missing = []
        for skill in common_skills:
            pattern = r"\b" + re.escape(skill) + r"\b"
            if re.search(pattern, description_lower) and skill not in profile_skills:
                missing.append(skill)
        
        match_ratio = len(matched) / max(len(profile_skills), 1)
        
        return {
            "skills_matched": matched,
            "skills_missing": missing[:5],  # Top 5 missing
            "match_ratio": min(match_ratio, 1.0),
        }
    
    def _ai_score_job(self, job: Dict, profile: Dict) -> Dict:
        """Use AI to score job fit."""
        title = job.get("title", "")
        company = job.get("company", "")
        description = job.get("description", "")[:2000]  # Truncate for API
        
        # Build profile summary
        skills = profile.get("skills", [])
        if isinstance(skills, dict):
            skills = [s for cat in skills.values() for s in (cat if isinstance(cat, list) else [])]
        skills_str = ", ".join(skills[:15])
        
        experience = profile.get("experience_highlights", [])
        exp_str = "; ".join(experience[:3])
        
        prompt = f"""Score how well this job matches the candidate profile.

JOB:
Title: {title}
Company: {company}
Description: {description[:1500]}

CANDIDATE:
Skills: {skills_str}
Experience: {exp_str}

Return JSON:
{{
    "score": 0.0-1.0,
    "reasons": ["reason1", "reason2"],
    "fit_summary": "one sentence"
}}"""
        
        try:
            result = self.call_ai_json(prompt)
            return {
                "score": float(result.get("score", 0.5)),
                "reasons": result.get("reasons", []),
            }
        except Exception as e:
            self.log("ai_score", "error", f"AI scoring failed: {e}")
            return {"score": None, "reasons": []}
    
    def _update_job_scores(self, jobs: List[Dict]) -> None:
        """Update job scores in database."""
        try:
            from core.database_manager import get_job_discovery_db
            db = get_job_discovery_db(config.JOBS_DB_PATH)
            
            for job in jobs:
                db.update(
                    "jobs",
                    {
                        "score": job["ai_score"],
                        "metadata": json.dumps({
                            "match_reasons": job.get("match_reasons", []),
                            "skills_matched": job.get("skills_matched", []),
                            "skills_missing": job.get("skills_missing", []),
                        }),
                        "updated_at": datetime.now().isoformat(),
                    },
                    "id = ?",
                    (job["id"],),
                )
        except Exception as e:
            self.log("update_scores", "error", f"Failed to update job scores: {e}")
    
    def get_top_matches(self, context: AgentContext, limit: int = 10) -> List[Dict]:
        """Get top matching jobs."""
        try:
            from core.database_manager import get_job_discovery_db
            db = get_job_discovery_db(config.JOBS_DB_PATH)
            
            rows = db.fetch_all(
                """
                SELECT * FROM jobs 
                WHERE score >= ?
                ORDER BY score DESC
                LIMIT ?
                """,
                (config.JOB_SCORE_THRESHOLD, limit),
            )
            
            return [dict(row) for row in rows]
        except Exception as e:
            self.log("get_top_matches", "error", f"Failed: {e}")
            return []
