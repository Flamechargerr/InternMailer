"""
📄 Resume Optimizer Agent - AI-Powered Resume Tailoring
=======================================================
Optimizes resume content based on job descriptions.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.agents.base_agent import BaseAgent, AgentContext, AgentResponse
from core.resume_service import optimize_for_job
from utils.config import config


class ResumeOptimizerAgent(BaseAgent):
    """
    Specialized agent for optimizing resumes.
    
    Capabilities:
    - Extract keywords from job descriptions
    - Rewrite bullets to match JD keywords
    - Generate multiple resume variants
    - ATS score prediction
    - LaTeX PDF generation
    """
    
    def __init__(self):
        super().__init__("ResumeOptimizer")
        self.output_dir = Path("optimized_documents")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run(self, context: AgentContext, **kwargs) -> AgentResponse:
        """
        Optimize resume for a specific job.
        
        Kwargs:
            job: Job dict with title, company, description
            generate_pdf: Whether to generate PDF (default: True)
        """
        job = kwargs.get("job")
        generate_pdf = kwargs.get("generate_pdf", True)
        
        if not job:
            return AgentResponse(
                success=False,
                agent_name=self.name,
                action_taken="optimize_resume",
                message="No job provided",
            )
        
        profile = context.profile
        
        # Extract keywords from JD
        keywords = self._extract_keywords(job.get("description", ""))
        
        # Optimize resume sections
        optimized = self._optimize_sections(profile, job, keywords)
        
        shared_result = None
        if job.get("description"):
            try:
                shared_result = optimize_for_job(
                    job_description=job.get("description", ""),
                    output_dir=str(self.output_dir),
                    company_name=job.get("company", ""),
                    position=job.get("title", ""),
                )
            except Exception as e:
                self.log("optimize_resume", "warning", f"Shared resume optimization failed: {e}")

        # Calculate ATS score
        ats_score = self._calculate_ats_score(optimized, job)
        if shared_result:
            ats_score = max(ats_score, shared_result.ats_score_after)
        
        # Generate PDF if requested
        pdf_path = None
        if generate_pdf:
            if shared_result and (shared_result.pdf_resume_path or shared_result.resume_path):
                pdf_path = Path(shared_result.pdf_resume_path or shared_result.resume_path)
            else:
                pdf_path = self._generate_pdf(optimized, job)
        
        return AgentResponse(
            success=True,
            agent_name=self.name,
            action_taken="optimize_resume",
            result={
                "optimized_profile": optimized,
                "ats_score": ats_score,
                "pdf_path": str(pdf_path) if pdf_path else None,
            },
            message=f"Optimized resume for {job.get('company', 'company')} (ATS: {ats_score}%)",
            data={
                "keywords_added": keywords[:10],
                "ats_score": ats_score,
                "company": job.get("company"),
            },
        )
    
    def _extract_keywords(self, description: str) -> List[str]:
        """Extract important keywords from job description."""
        if not description:
            return []
        
        # Common tech keywords to look for
        tech_keywords = [
            "python", "java", "javascript", "typescript", "sql", "nosql",
            "react", "angular", "vue", "node.js", "express", "flask", "django",
            "aws", "gcp", "azure", "docker", "kubernetes", "ci/cd",
            "git", "github", "gitlab", "agile", "scrum",
            "machine learning", "ml", "ai", "data science", "analytics",
            "api", "rest", "graphql", "microservices",
            "testing", "tdd", "unit testing", "integration testing",
            "postgresql", "mysql", "mongodb", "redis",
            "etl", "data pipeline", "data modeling",
        ]
        
        # Soft skill keywords
        soft_keywords = [
            "collaboration", "communication", "leadership", "problem-solving",
            "analytical", "detail-oriented", "fast-paced", "cross-functional",
        ]
        
        description_lower = description.lower()
        found_keywords = []
        
        for keyword in tech_keywords + soft_keywords:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, description_lower):
                found_keywords.append(keyword)
        
        # Use AI for deeper extraction if available
        if self.ai_provider and len(found_keywords) < 5:
            ai_keywords = self._ai_extract_keywords(description)
            found_keywords.extend(ai_keywords)
        
        return list(set(found_keywords))[:20]
    
    def _ai_extract_keywords(self, description: str) -> List[str]:
        """Use AI to extract additional keywords."""
        prompt = f"""Extract the top 10 most important skills/keywords from this job description.
Return as JSON array of strings.

Job Description:
{description[:2000]}

Return format: ["keyword1", "keyword2", ...]"""
        
        try:
            result = self.call_ai_json(prompt)
            if isinstance(result, list):
                return result
            return result.get("keywords", [])
        except Exception:
            return []
    
    def _optimize_sections(self, profile: Dict, job: Dict, keywords: List[str]) -> Dict:
        """Optimize resume sections to include keywords."""
        optimized = dict(profile)
        
        # Optimize summary
        if self.ai_provider:
            optimized["ats"] = dict(profile.get("ats", {}))
            optimized["ats"]["summary"] = self._optimize_summary(
                profile.get("ats", {}).get("summary", ""),
                job,
                keywords,
            )
        
        # Optimize experience bullets
        experience = profile.get("ats", {}).get("experience", [])
        optimized_experience = []
        
        for exp in experience:
            optimized_exp = dict(exp)
            optimized_bullets = []
            
            for bullet in exp.get("bullets", []):
                optimized_bullet = self._optimize_bullet(bullet, keywords)
                optimized_bullets.append(optimized_bullet)
            
            optimized_exp["bullets"] = optimized_bullets
            optimized_experience.append(optimized_exp)
        
        if "ats" in optimized:
            optimized["ats"]["experience"] = optimized_experience
        
        # Add keywords to skills if missing
        current_skills = profile.get("skills", [])
        if isinstance(current_skills, dict):
            flat = []
            for cat in current_skills.values():
                if isinstance(cat, list):
                    flat.extend(cat)
            current_skills = flat
        current_skills_lower = [s.lower() for s in current_skills]
        
        new_skills = [k for k in keywords if k.lower() not in current_skills_lower]
        if new_skills:
            optimized["added_skills"] = new_skills[:5]
        
        return optimized
    
    def _optimize_summary(self, summary: str, job: Dict, keywords: List[str]) -> str:
        """Optimize summary using AI."""
        if not self.ai_provider:
            return summary
        
        role = job.get("title", "Software Engineer")
        company = job.get("company", "the company")
        
        prompt = f"""Rewrite this resume summary to better match the job, incorporating these keywords naturally: {', '.join(keywords[:8])}

Current Summary:
{summary}

Target Role: {role} at {company}

Requirements:
- Keep it 2-3 sentences
- Highlight relevant experience
- Include 3-5 keywords naturally
- Maintain professional tone
- Don't make up experience

Return only the optimized summary text."""
        
        try:
            result = self.call_ai(prompt)
            return result.strip()
        except Exception:
            return summary
    
    def _optimize_bullet(self, bullet: str, keywords: List[str]) -> str:
        """Optimize a single bullet point."""
        # Simple keyword insertion for relevant bullets
        bullet_lower = bullet.lower()
        
        for keyword in keywords:
            # If keyword concept is present but not the exact word
            synonyms = {
                "python": ["py", "scripting"],
                "sql": ["database", "queries"],
                "ci/cd": ["automation", "deployment"],
                "api": ["endpoint", "service"],
            }
            
            for kw, syns in synonyms.items():
                if kw in keywords and any(s in bullet_lower for s in syns) and kw not in bullet_lower:
                    # Could enhance but keep original for safety
                    pass
        
        return bullet
    
    def _calculate_ats_score(self, optimized: Dict, job: Dict) -> int:
        """Calculate estimated ATS compatibility score."""
        score = 50  # Base score
        
        description = (job.get("description") or "").lower()
        
        # Check skills match
        skills = optimized.get("skills", [])
        if isinstance(skills, dict):
            skills = [s for cat in skills.values() for s in (cat if isinstance(cat, list) else [])]
        
        skills_in_jd = 0
        for skill in skills:
            if skill.lower() in description:
                skills_in_jd += 1
        
        skill_ratio = skills_in_jd / max(len(skills), 1)
        score += int(skill_ratio * 30)
        
        # Check experience highlights match
        experience_highlights = optimized.get("experience_highlights", [])
        highlights_match = 0
        for highlight in experience_highlights:
            highlight_words = highlight.lower().split()
            if any(word in description for word in highlight_words if len(word) > 4):
                highlights_match += 1
        
        highlight_ratio = highlights_match / max(len(experience_highlights), 1)
        score += int(highlight_ratio * 20)
        
        return min(score, 100)
    
    def _generate_pdf(self, optimized: Dict, job: Dict) -> Optional[Path]:
        """Generate optimized PDF resume."""
        try:
            result = optimize_for_job(
                job_description=job.get("description", ""),
                output_dir=str(self.output_dir),
                company_name=job.get("company", ""),
                position=job.get("title", ""),
            )
            
            if result and (result.pdf_resume_path or result.resume_path):
                return Path(result.pdf_resume_path or result.resume_path)
            
        except Exception as e:
            self.log("generate_pdf", "error", f"PDF generation failed: {e}")
        
        return None
    
    def batch_optimize(self, context: AgentContext, jobs: List[Dict]) -> List[Dict]:
        """Optimize resume for multiple jobs."""
        results = []
        
        for job in jobs:
            response = self.execute(context, job=job, generate_pdf=False)
            results.append({
                "job": job.get("title"),
                "company": job.get("company"),
                "success": response.success,
                "ats_score": response.data.get("ats_score"),
            })
        
        return results
