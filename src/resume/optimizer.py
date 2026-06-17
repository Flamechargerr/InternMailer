"""
Canonical resume optimizer for InternMailer.

This module combines the locked resume rewrite flow from the v2 template
package with the existing cover-letter generator so the rest of the app can
call one stable entrypoint.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from .cv_rewriter import extract_jd_keywords, rewrite_cv
from .latex_builder import build_tailored_cv, load_template
from .pdf_compiler import compile_pdf
from utils.profile import get_profile


def _safe_slug(text: str) -> str:
    """Convert text into a filesystem-safe slug."""
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", str(text or "").strip().lower())
    return slug.strip("_") or "company"


def _coerce_profile(profile: Optional[Any] = None) -> dict[str, Any]:
    """Normalize profile objects into a plain dictionary."""
    if profile is None:
        profile = get_profile()
    if hasattr(profile, "data"):
        return dict(profile.data)
    if isinstance(profile, dict):
        return dict(profile)
    return dict(getattr(profile, "__dict__", {}))


def _calculate_score(content: str, keywords: list[str]) -> int:
    """Simple ATS-style keyword score on a 0-100 scale."""
    if not keywords:
        return 50

    content_lower = content.lower()
    matches = sum(1 for kw in keywords if kw.lower() in content_lower)
    return min(int((matches / max(len(keywords), 1)) * 100), 100)


def _build_cover_letter(
    *,
    job_description: str,
    profile: dict[str, Any],
    company_name: str,
    position_title: str,
    output_dir: Path,
    keywords: list[str],
) -> tuple[str, Optional[str]]:
    """
    Generate and compile a cover letter using the existing ATS optimizer.

    The resume package owns the canonical resume template, while the current
    cover-letter generator remains useful and production-ready.
    """
    from web.ats_optimizer import ATSOptimizer

    optimizer = ATSOptimizer()
    job_data = {
        "company_name": company_name,
        "position_title": position_title,
        "location": profile.get("location", ""),
        "description": job_description,
        "ats_keywords": keywords,
        "required_skills": keywords[:10],
        "preferred_skills": [],
        "tools_technologies": keywords[:8],
    }

    cover_letter_tex = optimizer.optimize_cover_letter(job_data, output_dir)
    cover_letter_pdf = optimizer.compile_latex(cover_letter_tex)
    return cover_letter_tex, cover_letter_pdf


def optimize_for_job(
    job_description: str,
    output_dir: str = "optimized_documents",
    company_name: Optional[str] = None,
    position: Optional[str] = None,
    profile: Optional[Any] = None,
) -> dict[str, Any]:
    """
    Optimize the resume and cover letter for a job description.

    Returns a dict compatible with the rest of InternMailer.
    """
    profile_dict = _coerce_profile(profile)
    company_name = company_name or "Company"
    position_title = position or profile_dict.get("title") or "Position"
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    rewrite_result = rewrite_cv(job_description, profile_dict)
    keywords = rewrite_result.get("keywords", {}) or {}
    keyword_list = list(keywords.get("tech", [])) + list(keywords.get("soft", []))

    safe_company = _safe_slug(company_name)
    resume_tex_path = output_path / f"resume_{safe_company}.tex"
    resume_tex = build_tailored_cv(rewrite_result, output_path=str(resume_tex_path))
    resume_pdf_result = compile_pdf(resume_tex)

    cover_letter_tex = ""
    cover_letter_pdf = None
    try:
        cover_letter_tex, cover_letter_pdf = _build_cover_letter(
            job_description=job_description,
            profile=profile_dict,
            company_name=company_name,
            position_title=position_title,
            output_dir=output_path,
            keywords=keyword_list,
        )
    except Exception:
        cover_letter_tex = ""
        cover_letter_pdf = None

    original_tex = load_template()
    optimized_tex = Path(resume_tex).read_text(encoding="utf-8")
    ats_score_before = _calculate_score(original_tex, keyword_list)
    ats_score_after = _calculate_score(optimized_tex, keyword_list)
    keywords_added = [
        kw
        for kw in keyword_list
        if kw.lower() in optimized_tex.lower() and kw.lower() not in original_tex.lower()
    ]

    return {
        "resume_path": resume_tex,
        "cover_letter_path": cover_letter_tex,
        "pdf_resume_path": resume_pdf_result.get("pdf_path"),
        "pdf_cover_letter_path": cover_letter_pdf,
        "keywords_found": keyword_list,
        "keywords_added": keywords_added,
        "ats_score_before": ats_score_before,
        "ats_score_after": ats_score_after,
        "company_name": company_name,
        "position_title": position_title,
    }
