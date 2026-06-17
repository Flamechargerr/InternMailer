#!/usr/bin/env python3
"""
Resume PDF ingestion - extract key info from a PDF and update profile.yaml.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Dict, Any, List

import os
import pdfplumber
import yaml


EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\s\-()]{7,}\d")
URL_RE = re.compile(r"https?://[^\s)]+")


def _extract_text(pdf_path: Path) -> str:
    text_chunks = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text_chunks.append(page.extract_text() or "")
    return "\n".join(text_chunks)


def _extract_texts_from_dir(pdf_dir: Path) -> List[str]:
    texts: List[str] = []
    for pdf_path in sorted(pdf_dir.rglob("*.pdf")):
        try:
            texts.append(_extract_text(pdf_path))
        except Exception:
            continue
    return texts


def _extract_fields(text: str) -> Dict[str, Any]:
    emails = EMAIL_RE.findall(text)
    phones = PHONE_RE.findall(text)
    urls = URL_RE.findall(text)

    linkedin = next((u for u in urls if "linkedin.com" in u), "")
    github = next((u for u in urls if "github.com" in u), "")
    portfolio = next((u for u in urls if "http" in u and u not in [linkedin, github]), "")

    return {
        "email": emails[0] if emails else "",
        "phone": phones[0] if phones else "",
        "linkedin": linkedin,
        "github": github,
        "portfolio": portfolio,
        "raw_resume_text": text,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", default=os.getenv("RESUME_PDF_PATH", "resume.pdf"))
    parser.add_argument("--dir", default="")
    parser.add_argument("--profile", default="data/profile.yaml")
    args = parser.parse_args()

    texts: List[str] = []
    if args.dir:
        pdf_dir = Path(args.dir)
        if not pdf_dir.exists():
            raise SystemExit(f"PDF directory not found: {pdf_dir}")
        texts = _extract_texts_from_dir(pdf_dir)
    else:
        pdf_path = Path(args.pdf)
        if not pdf_path.exists():
            raise SystemExit(f"PDF not found: {pdf_path}")
        texts = [_extract_text(pdf_path)]

    profile_path = Path(args.profile)
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    if profile_path.exists():
        data = yaml.safe_load(profile_path.read_text()) or {}
    else:
        data = {}

    combined_text = "\n".join(texts)
    fields = _extract_fields(combined_text)
    data.update({k: v for k, v in fields.items() if v})
    data["raw_resume_text"] = fields["raw_resume_text"]

    profile_path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    print(f"Updated profile at {profile_path}")


if __name__ == "__main__":
    main()
