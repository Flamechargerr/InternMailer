"""
InternMailer - PDF Compiler

Compiles a tailored .tex file into a PDF and verifies the output page count.
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("internmailer.pdf_compiler")


def _count_pages(pdf_path: Path) -> int:
    """Count pages in a PDF file."""
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(str(pdf_path))
        return len(reader.pages)
    except ImportError:
        try:
            content = pdf_path.read_bytes()
            import re

            pages = re.findall(rb"/Type\s*/Page[^s]", content)
            return len(pages) if pages else 1
        except Exception:
            logger.warning("Could not count PDF pages - assuming 1")
            return 1
    except Exception as exc:
        logger.warning("Page count failed: %s", exc)
        return 1


def _cleanup_aux(p_tex_path: Path, output_dir: str) -> None:
    """Remove LaTeX auxiliary files."""
    stem = p_tex_path.stem
    for ext in [".aux", ".log", ".out", ".fls", ".fdb_latexmk", ".synctex.gz"]:
        aux_file = Path(output_dir) / f"{stem}{ext}"
        if aux_file.exists():
            try:
                aux_file.unlink()
            except Exception:
                pass


def compile_pdf(tex_path: str, output_dir: Optional[str] = None) -> dict[str, Any]:
    """
    Compile a .tex file to PDF using pdflatex.

    Returns:
        {
            "success": bool,
            "pdf_path": str (if success),
            "pdf_bytes": bytes (if success),
            "page_count": int,
            "error": str (if failed),
        }
    """
    p_tex = Path(tex_path)
    if not p_tex.exists():
        return {"success": False, "error": f"TeX file not found: {tex_path}"}

    if output_dir is None:
        output_dir = str(p_tex.parent)

    for run in range(2):
        try:
            result = subprocess.run(
                [
                    "pdflatex",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    f"-output-directory={output_dir}",
                    str(p_tex),
                ],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(p_tex.parent),
            )

            if result.returncode != 0:
                error_lines = [
                    line for line in result.stdout.split("\n")
                    if line.startswith("!") or "Error" in line
                ]
                error_msg = "\n".join(error_lines[:5]) if error_lines else result.stdout[-500:]
                logger.error("pdflatex run %s failed:\n%s", run + 1, error_msg)
                if run == 0:
                    return {"success": False, "error": f"pdflatex failed: {error_msg}"}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "pdflatex timed out (30s)"}
        except FileNotFoundError:
            return {
                "success": False,
                "error": "pdflatex not installed. Install a TeX distribution (e.g., MacTeX).",
            }

    pdf_path = Path(output_dir) / f"{p_tex.stem}.pdf"
    if not pdf_path.exists():
        return {"success": False, "error": f"PDF not generated at {pdf_path}"}

    page_count = _count_pages(pdf_path)
    if page_count > 1:
        logger.warning(
            "PDF has %s pages - one-page constraint violated! Bullets may need shortening.",
            page_count,
        )
        return {
            "success": False,
            "error": f"PDF is {page_count} pages (must be exactly 1). Reduce bullet length or content.",
            "pdf_path": str(pdf_path),
            "page_count": page_count,
        }

    pdf_bytes = pdf_path.read_bytes()
    _cleanup_aux(p_tex, output_dir)

    logger.info("PDF compiled successfully: %s (%s bytes, %s page)", pdf_path, len(pdf_bytes), page_count)
    return {
        "success": True,
        "pdf_path": str(pdf_path),
        "pdf_bytes": pdf_bytes,
        "page_count": page_count,
    }


def compile_from_rewrite(rewrite_result: dict[str, Any], job_id: Optional[int] = None) -> dict[str, Any]:
    """
    Convenience helper: build LaTeX from rewrite result and compile to PDF.
    """
    from .latex_builder import build_tailored_cv

    tex_path = f"/tmp/internmailer_cv_job_{job_id}.tex" if job_id else "/tmp/internmailer_tailored_cv.tex"
    tex_file = build_tailored_cv(rewrite_result, output_path=tex_path)
    return compile_pdf(tex_file)
