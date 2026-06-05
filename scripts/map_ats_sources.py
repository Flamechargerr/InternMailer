#!/usr/bin/env python3
"""
ATS mapping - discover ATS providers for Fortune 500 companies.
Uses DuckDuckGo HTML search to find career/ATS URLs and extracts slugs.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
import os
import yaml
from urllib.parse import urlparse, parse_qs, unquote


ATS_PATTERNS = {
    "greenhouse": re.compile(r"https?://boards\\.greenhouse\\.io/([a-zA-Z0-9\\-_.]+)"),
    "lever": re.compile(r"https?://jobs\\.lever\\.co/([a-zA-Z0-9\\-_.]+)"),
    "ashby": re.compile(r"https?://jobs\\.ashbyhq\\.com/([a-zA-Z0-9\\-_.]+)"),
    "smartrecruiters": re.compile(r"https?://careers\\.smartrecruiters\\.com/([a-zA-Z0-9\\-_.]+)"),
    "workable": re.compile(r"https?://apply\\.workable\\.com/([a-zA-Z0-9\\-_.]+)"),
}


def _search_duckduckgo(query: str) -> List[str]:
    url = "https://duckduckgo.com/html/"
    resp = requests.post(url, data={"q": query}, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.select("a.result__a"):
        href = a.get("href", "")
        href = _normalize_ddg_url(href)
        if href:
            links.append(href)
    return links


def _normalize_ddg_url(url: str) -> str:
    """DuckDuckGo returns redirect URLs; extract the real target if present."""
    if "duckduckgo.com/l/" in url and "uddg=" in url:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
    return url


def _detect_ats(urls: List[str]) -> Optional[Tuple[str, str]]:
    for url in urls:
        for provider, pattern in ATS_PATTERNS.items():
            match = pattern.search(url)
            if match:
                return provider, match.group(1)
    return None


def _load_fortune500(csv_path: Path) -> List[str]:
    if not csv_path.exists():
        return []
    lines = csv_path.read_text(encoding="utf-8").splitlines()
    headers = lines[0].lower().split(",") if lines else []
    company_idx = None
    for idx, header in enumerate(headers):
        if "company" in header:
            company_idx = idx
            break
    if company_idx is None:
        return []
    companies = []
    for line in lines[1:]:
        parts = [p.strip().strip('"') for p in line.split(",")]
        if len(parts) > company_idx:
            companies.append(parts[company_idx])
    return companies


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=os.getenv("JOB_FORTUNE500_CSV", "data/fortune500_2019.csv"))
    parser.add_argument("--out", default="data/job_sources.yaml")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--cache", default="data/ats_mapping_cache.json")
    parser.add_argument("--flush-every", type=int, default=5)
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    companies = _load_fortune500(Path(args.csv))
    companies = companies[args.start : args.start + args.limit]

    cache_path = Path(args.cache)
    if cache_path.exists():
        cache = json.loads(cache_path.read_text())
    else:
        cache = {}

    ats_sources = []
    processed = 0
    for company in companies:
        if company in cache and not args.refresh:
            if cache[company]:
                ats_sources.append(cache[company])
            continue

        query = f"{company} careers greenhouse lever ashby smartrecruiters workable"
        try:
            links = _search_duckduckgo(query)
            match = _detect_ats(links)
            if match:
                provider, slug = match
                entry = {"type": provider, "company": slug}
                cache[company] = entry
                ats_sources.append(entry)
            else:
                cache[company] = None
        except Exception:
            cache[company] = None

        processed += 1
        if processed % args.flush_every == 0:
            cache_path.write_text(json.dumps(cache, indent=2))

    cache_path.write_text(json.dumps(cache, indent=2))

    out_path = Path(args.out)
    data = yaml.safe_load(out_path.read_text()) if out_path.exists() else {}
    data.setdefault("ats_sources", [])

    # merge unique
    existing = {(e.get("type"), e.get("company")) for e in data["ats_sources"]}
    for entry in ats_sources:
        key = (entry.get("type"), entry.get("company"))
        if key not in existing:
            data["ats_sources"].append(entry)
            existing.add(key)

    out_path.write_text(yaml.safe_dump(data, sort_keys=False))
    print(f"Added {len(ats_sources)} ATS sources to {out_path}")


if __name__ == "__main__":
    main()
