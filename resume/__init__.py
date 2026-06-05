"""Canonical resume/ATS package for InternMailer.

This package contains the locked one-page ATS resume template and the
rewrite/compile helpers used to generate tailored application assets.
"""

from .cv_rewriter import extract_jd_keywords, rewrite_bullets, rewrite_cv
from .latex_builder import build_tailored_cv, load_template, replace_block, verify_template_integrity
from .pdf_compiler import compile_from_rewrite, compile_pdf
from .optimizer import optimize_for_job

__all__ = [
    "build_tailored_cv",
    "compile_from_rewrite",
    "compile_pdf",
    "extract_jd_keywords",
    "load_template",
    "optimize_for_job",
    "replace_block",
    "rewrite_bullets",
    "rewrite_cv",
    "verify_template_integrity",
]
