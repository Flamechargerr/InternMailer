"""
Shared resume optimization adapter.

This module gives the dashboard, job pipeline, and resume optimizer agent a
single call path. It prefers a future canonical ``resume`` package if one is
available, and otherwise falls back to the existing ATS optimizer.
"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ResumeOptimizationResult:
    """Normalized result shape shared by the app."""

    resume_path: str
    cover_letter_path: str
    pdf_resume_path: Optional[str]
    pdf_cover_letter_path: Optional[str]
    keywords_found: list[str]
    keywords_added: list[str]
    ats_score_before: int
    ats_score_after: int
    company_name: str
    position_title: str


def _load_canonical_optimizer() -> Optional[Any]:
    """Load the canonical resume package if it exists."""
    try:
        canonical = importlib.import_module("resume")
    except ImportError:
        return None

    if hasattr(canonical, "optimize_for_job") or hasattr(canonical, "ATSOptimizer"):
        return canonical

    return None


def _fallback_optimizer():
    from web.ats_optimizer import ATSOptimizer

    return ATSOptimizer()


def _normalize_result(
    result: Any,
    *,
    company_name: str = "",
    position_title: str = "",
) -> ResumeOptimizationResult:
    """Convert dict/object results into the shared dataclass shape."""
    if isinstance(result, ResumeOptimizationResult):
        return result

    def _get(name: str, default: Any = None) -> Any:
        if isinstance(result, dict):
            return result.get(name, default)
        return getattr(result, name, default)

    return ResumeOptimizationResult(
        resume_path=str(_get("resume_path", "")),
        cover_letter_path=str(_get("cover_letter_path", "")),
        pdf_resume_path=_get("pdf_resume_path"),
        pdf_cover_letter_path=_get("pdf_cover_letter_path"),
        keywords_found=list(_get("keywords_found", []) or []),
        keywords_added=list(_get("keywords_added", []) or []),
        ats_score_before=int(_get("ats_score_before", 0) or 0),
        ats_score_after=int(_get("ats_score_after", 0) or 0),
        company_name=str(_get("company_name", company_name) or company_name),
        position_title=str(_get("position_title", position_title) or position_title),
    )


def optimize_for_job(
    job_description: str,
    output_dir: str = "optimized_documents",
    company_name: Optional[str] = None,
    position: Optional[str] = None,
) -> ResumeOptimizationResult:
    """
    Optimize resume + cover letter assets for a job description.

    If the canonical ``resume`` package exists, this adapter will use it.
    Otherwise it falls back to the existing web ATS optimizer so the current
    app keeps working until the new package lands.
    """
    company_name = company_name or "Company"
    position = position or "Position"

    canonical = _load_canonical_optimizer()
    if canonical is not None:
        try:
            if hasattr(canonical, "optimize_for_job"):
                result = canonical.optimize_for_job(
                    job_description=job_description,
                    output_dir=output_dir,
                    company_name=company_name,
                    position=position,
                )
                return _normalize_result(result, company_name=company_name, position_title=position)

            if hasattr(canonical, "ATSOptimizer"):
                optimizer = canonical.ATSOptimizer()
                result = optimizer.optimize_for_job(
                    job_description=job_description,
                    output_dir=output_dir,
                    company_name=company_name,
                )
                return _normalize_result(result, company_name=company_name, position_title=position)
        except Exception as exc:
            logger.warning("Canonical resume package failed, falling back to legacy optimizer: %s", exc)

    legacy = _fallback_optimizer()
    result = legacy.optimize_for_job(
        job_description=job_description,
        output_dir=output_dir,
        company_name=company_name,
    )
    return _normalize_result(result, company_name=company_name, position_title=position)
