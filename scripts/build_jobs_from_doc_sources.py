#!/usr/bin/env python3
"""Build internship jobs JSON from DOCX/ZIP source documents."""

from __future__ import annotations

import argparse
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

try:
    from bs4 import BeautifulSoup
except Exception:  # pragma: no cover
    BeautifulSoup = None

import xml.etree.ElementTree as ET

TRACKING_PARAMS = {"gclid", "fbclid", "ref", "ref_src"}
INTERNSHIP_INCLUDE = [
    "intern",
    "internship",
    "new grad",
    "new graduate",
    "entry level",
    "junior",
    "graduate",
    "trainee",
    "apprentice",
    "summer analyst",
    "student researcher",
]
SENIOR_EXCLUDE = ["senior", "staff", "principal", "manager", "director", "lead", "vp", "head"]
USA_HINTS = [
    "usa",
    "u.s.",
    "united states",
    "new york",
    "san francisco",
    "seattle",
    "austin",
    "chicago",
    "los angeles",
    "boston",
    "washington",
    "dallas",
    "atlanta",
    "miami",
    "california",
    "texas",
    "virginia",
]
KNOWN_PROVIDER_TOKENS = [
    "greenhouse.io",
    "lever.co",
    "ashbyhq.com",
    "smartrecruiters.com",
    "workable.com",
    "myworkdayjobs.com",
    "workdayjobs.com",
    "linkedin.com/jobs",
]
JOB_LINK_TOKENS = [
    "intern",
    "internship",
    "new-grad",
    "newgrad",
    "graduate",
    "entry-level",
    "entry",
    "job",
    "jobs",
    "position",
    "careers",
    "apply",
]
SECTOR_KEYWORDS = {
    "tech": {
        "anthropic",
        "openai",
        "deepmind",
        "google",
        "microsoft",
        "meta",
        "amazon",
        "apple",
        "nvidia",
        "tesla",
        "spacex",
        "x.ai",
        "palantir",
    },
    "banks": {
        "goldman",
        "morgan stanley",
        "jpmorgan",
        "ubs",
        "barclays",
        "citi",
        "citibank",
        "deutsche",
        "dbs",
        "natwest",
        "bnp",
        "societe generale",
    },
    "trading": {
        "jane street",
        "citadel",
        "citadel securities",
        "hudson river trading",
        "optiver",
        "imc",
        "flow traders",
        "jump trading",
        "akuna",
        "drw",
        "sig",
        "deshaw",
        "rentech",
    },
}


class SourceSection:
    def __init__(
        self,
        *,
        source_doc: str,
        source_url: str,
        company: str,
        title_hint: str,
        location_hint: str,
        description: str,
        sector_hint: str,
    ):
        self.source_doc = source_doc
        self.source_url = source_url
        self.company = company
        self.title_hint = title_hint
        self.location_hint = location_hint
        self.description = description
        self.sector_hint = sector_hint


def str2bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def canonicalize_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url.strip())
    host = (parsed.netloc or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/")
    query_pairs = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        low = key.lower()
        if low.startswith("utm_") or low in TRACKING_PARAMS:
            continue
        query_pairs.append((key, value))
    query = urlencode(query_pairs, doseq=True)
    rebuilt = urlunparse(("", host, path, "", query, ""))
    return rebuilt.lstrip("//")


def clean_url(url: str) -> str:
    text = (url or "").strip().strip(")],.>")
    if text.startswith("//"):
        text = f"https:{text}"
    if text and not urlparse(text).scheme:
        text = f"https://{text}"
    return text


def parse_sources_arg(sources: str) -> list[Path]:
    items = [Path(part.strip()) for part in (sources or "").split(",") if part.strip()]
    return items


def iter_docx_sources(path: Path) -> Iterator[tuple[str, bytes]]:
    if path.suffix.lower() == ".docx":
        yield (path.name, path.read_bytes())
        return

    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if name.lower().endswith(".docx"):
                    yield (f"{path.name}:{name}", archive.read(name))
        return

    raise ValueError(f"Unsupported source file type: {path}")


def _docx_paragraphs(docx_bytes: bytes) -> list[dict[str, Any]]:
    with zipfile.ZipFile(io.BytesIO(docx_bytes)) as docx:
        doc_xml = ET.fromstring(docx.read("word/document.xml"))
        rels: dict[str, str] = {}
        rel_path = "word/_rels/document.xml.rels"
        if rel_path in docx.namelist():
            rel_xml = ET.fromstring(docx.read(rel_path))
            rel_attr = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
            for rel in rel_xml:
                rid = rel.attrib.get(rel_attr)
                target = rel.attrib.get("Target", "")
                rel_type = rel.attrib.get("Type", "")
                if rid and "hyperlink" in rel_type:
                    rels[rid] = target

    ns = {
        "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    }

    paragraphs: list[dict[str, Any]] = []
    for para in doc_xml.findall(".//w:p", ns):
        text = "".join(node.text or "" for node in para.findall(".//w:t", ns)).strip()
        urls: list[str] = []
        for node in para.findall(".//w:hyperlink", ns):
            rid = node.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
            if rid and rid in rels:
                urls.append(clean_url(rels[rid]))
        if text:
            urls.extend(clean_url(match) for match in re.findall(r"https?://[^\s\]>\)\"']+", text))
        unique_urls: list[str] = []
        seen = set()
        for url in urls:
            if url and url not in seen:
                seen.add(url)
                unique_urls.append(url)
        paragraphs.append({"text": text, "urls": unique_urls})

    return paragraphs


def _normalize_company(line: str) -> str:
    text = (line or "").strip()
    text = re.sub(r"^#+\s*", "", text)
    text = re.sub(r"^\d+\.\s*", "", text)
    return text.strip(" -*")


def _match_company_heading(line: str) -> str:
    text = (line or "").strip()
    m1 = re.match(r"^###\s*\d+\.\s+(.+)$", text)
    if m1:
        return _normalize_company(m1.group(1))
    m2 = re.match(r"^\d+\.\s+(.+)$", text)
    if m2:
        return _normalize_company(m2.group(1))
    return ""


def _line_after_colon(line: str, key: str) -> str:
    low = line.lower()
    if key in low and ":" in line:
        return line.split(":", 1)[1].strip()
    return ""


def _infer_sector(company: str, text: str, source_url: str) -> str:
    hay = " ".join([company or "", text or "", source_url or ""]).lower()
    for sector, words in SECTOR_KEYWORDS.items():
        if any(word in hay for word in words):
            return sector
    if any(token in hay for token in ["trading", "quant", "market maker"]):
        return "trading"
    if any(token in hay for token in ["bank", "analyst program", "investment banking"]):
        return "banks"
    return "tech"


def _extract_sections_from_paragraphs(source_doc: str, paragraphs: list[dict[str, Any]]) -> list[SourceSection]:
    sections: list[SourceSection] = []
    current_company = ""
    current_roles = ""
    current_location = ""
    current_desc: list[str] = []
    current_sector_header = ""

    def flush(url: str) -> None:
        if not url:
            return
        description = "\n".join(current_desc[-8:]).strip()
        sections.append(
            SourceSection(
                source_doc=source_doc,
                source_url=url,
                company=current_company or company_from_url(url),
                title_hint=current_roles or "Internship Opportunity",
                location_hint=current_location,
                description=description,
                sector_hint=_infer_sector(current_company, f"{current_roles} {description} {current_sector_header}", url),
            )
        )

    for para in paragraphs:
        text = (para.get("text") or "").strip()
        urls = para.get("urls") or []

        company = _match_company_heading(text)
        if company:
            current_company = company
            current_roles = ""
            current_location = ""
            current_desc = []
            continue

        low = text.lower()
        if "trading" in low and "tier" in low:
            current_sector_header = "trading"
        elif "bank" in low and ("tier" in low or "europe" in low or "india" in low):
            current_sector_header = "banks"
        elif "tech" in low and ("tier" in low or "focus" in low):
            current_sector_header = "tech"

        roles_value = _line_after_colon(text, "roles")
        if roles_value:
            current_roles = roles_value

        if "location" in low:
            loc = _line_after_colon(text, "locations") or _line_after_colon(text, "location")
            if loc:
                current_location = loc

        if text and not roles_value:
            current_desc.append(text)

        if urls:
            for url in urls:
                flush(url)

    deduped: list[SourceSection] = []
    seen = set()
    for sec in sections:
        key = (sec.source_doc, canonicalize_url(sec.source_url), sec.company.lower(), sec.title_hint.lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(sec)
    return deduped


def company_from_url(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    parts = [part for part in re.split(r"[.-]", host) if part and part not in {"com", "co", "io", "org", "net"}]
    if not parts:
        return "Unknown"
    return " ".join(word.capitalize() for word in parts[:2])


def is_internship_entry_level(text: str) -> bool:
    content = (text or "").lower()
    if not any(token in content for token in INTERNSHIP_INCLUDE):
        return False
    if any(token in content for token in SENIOR_EXCLUDE):
        return False
    return True


def is_non_usa_job(text: str) -> bool:
    content = (text or "").lower()
    return not any(token in content for token in USA_HINTS)


def classify_discovery_method(url: str) -> str:
    lower = (url or "").lower()
    if any(token in lower for token in KNOWN_PROVIDER_TOKENS):
        return "known_api"
    if any(token in lower for token in ["intern", "jobs", "careers", "apply", "graduate"]):
        return "direct_link"
    return "crawl_extract"


def is_directish_apply_url(url: str, context_text: str) -> bool:
    lower = (url or "").lower()
    if any(token in lower for token in KNOWN_PROVIDER_TOKENS):
        return True
    if any(token in lower for token in ["/job", "/jobs", "careers", "intern", "graduate", "apply"]):
        return True
    return is_internship_entry_level(context_text)


def _extract_links_from_html(base_url: str, html: str) -> list[tuple[str, str]]:
    links: list[tuple[str, str]] = []
    if not html:
        return links

    if BeautifulSoup is None:
        for href in re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE):
            abs_url = clean_url(urljoin(base_url, href))
            links.append((abs_url, ""))
        return links

    soup = BeautifulSoup(html, "html.parser")
    for node in soup.select("a[href]"):
        href = str(node.get("href") or "").strip()
        if not href:
            continue
        abs_url = clean_url(urljoin(base_url, href))
        text = " ".join(node.get_text(" ", strip=True).split())
        links.append((abs_url, text))
    return links


def _crawl_expand_links(source_url: str, context_text: str, timeout_s: int = 15) -> list[tuple[str, str, str]]:
    if requests is None:
        return []

    if is_directish_apply_url(source_url, context_text):
        return [(source_url, "", classify_discovery_method(source_url))]

    try:
        response = requests.get(
            source_url,
            timeout=timeout_s,
            headers={"User-Agent": "Mozilla/5.0 (internmailer job builder)"},
            allow_redirects=True,
        )
        response.raise_for_status()
    except Exception:
        return []

    base_host = urlparse(response.url).netloc.lower()
    items: list[tuple[str, str, str]] = []
    seen = set()
    for url, anchor_text in _extract_links_from_html(response.url, response.text):
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            continue
        if parsed.netloc and base_host and base_host not in parsed.netloc.lower() and not any(
            token in parsed.netloc.lower() for token in KNOWN_PROVIDER_TOKENS
        ):
            continue

        hay = f"{url} {anchor_text}".lower()
        if not any(token in hay for token in JOB_LINK_TOKENS):
            continue

        canonical = canonicalize_url(url)
        if canonical in seen:
            continue
        seen.add(canonical)
        method = classify_discovery_method(url)
        items.append((url, anchor_text, method))
        if len(items) >= 60:
            break

    return items


def discover_jobs_from_sections(
    sections: Sequence[SourceSection],
    *,
    non_usa_only: bool,
    sectors: set[str],
) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    seen_apply = set()

    for section in sections:
        sector = section.sector_hint if section.sector_hint in {"tech", "banks", "trading"} else _infer_sector(section.company, section.description, section.source_url)
        if sectors and sector not in sectors:
            continue

        context = " ".join([section.company, section.title_hint, section.location_hint, section.description, section.source_url])
        discovered = _crawl_expand_links(section.source_url, context)
        if not discovered:
            discovered = [(section.source_url, section.title_hint, classify_discovery_method(section.source_url))]

        for apply_url, link_text, method in discovered:
            canonical = canonicalize_url(apply_url)
            if not canonical or canonical in seen_apply:
                continue
            seen_apply.add(canonical)

            title = section.title_hint or link_text or "Internship Opportunity"
            if link_text and len(link_text) >= 5 and len(link_text.split()) <= 16:
                title = link_text
            location = section.location_hint
            description = section.description or link_text
            internship_pass = is_internship_entry_level(" ".join([title, description, apply_url, section.title_hint]))
            if not internship_pass:
                continue

            non_usa_pass = is_non_usa_job(" ".join([title, location, description, apply_url, section.source_url]))
            if non_usa_only and not non_usa_pass:
                continue

            jobs.append(
                {
                    "title": title,
                    "company": section.company or company_from_url(apply_url),
                    "location": location,
                    "apply_url": apply_url,
                    "description": description,
                    "source_doc": section.source_doc,
                    "source_url": section.source_url,
                    "sector": sector,
                    "non_usa_pass": non_usa_pass,
                    "internship_pass": internship_pass,
                    "discovery_method": method,
                }
            )

    return jobs


def build_jobs_from_sources(
    source_paths: Sequence[Path],
    *,
    non_usa_only: bool,
    sectors: set[str],
) -> dict[str, Any]:
    all_sections: list[SourceSection] = []
    for source in source_paths:
        if not source.exists():
            raise FileNotFoundError(f"Source does not exist: {source}")
        for source_doc, docx_bytes in iter_docx_sources(source):
            paragraphs = _docx_paragraphs(docx_bytes)
            all_sections.extend(_extract_sections_from_paragraphs(source_doc, paragraphs))

    jobs = discover_jobs_from_sections(all_sections, non_usa_only=non_usa_only, sectors=sectors)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": [str(path) for path in source_paths],
        "non_usa_only": non_usa_only,
        "sectors": sorted(sectors),
        "section_count": len(all_sections),
        "jobs": jobs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build internship jobs JSON from DOCX sources")
    parser.add_argument(
        "--sources",
        default="/Users/anamay/Desktop/internship kimi.docx,/Users/anamay/Downloads/Kimi_Agent_Excluding USA_ Global openings.zip",
        help="Comma-separated list of DOCX or ZIP paths",
    )
    parser.add_argument("--non-usa-only", default="true", help="Enforce non-USA postings only (true/false)")
    parser.add_argument("--sectors", default="tech,banks,trading", help="Comma-separated sectors to keep")
    parser.add_argument(
        "--output",
        default="/Users/anamay/Desktop/Projects/internmailer_v3/output/jobs_doc_sources.json",
        help="Output JSON path",
    )

    args = parser.parse_args()

    source_paths = parse_sources_arg(args.sources)
    if not source_paths:
        raise SystemExit("No source paths provided")

    allowed_sectors = {part.strip().lower() for part in args.sectors.split(",") if part.strip()}
    payload = build_jobs_from_sources(
        source_paths,
        non_usa_only=str2bool(args.non_usa_only),
        sectors=allowed_sectors,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Sections parsed: {payload['section_count']}")
    print(f"Jobs discovered: {len(payload['jobs'])}")
    print(f"Output written: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
