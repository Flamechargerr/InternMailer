#!/usr/bin/env python3
"""Run ATS-first Playwright application pipeline with optional multi-worker queue."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Sequence

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.apply_queue import ApplyQueueRunner
from core.atlas_sync import AtlasSyncClient
from core.job_apply import JobAutoApplier

ALLOWED_ATS_PROVIDERS = {
    "greenhouse",
    "lever",
    "ashby",
    "smartrecruiters",
    "workable",
    "linkedin",
    "workday",
    "generic",
}
DEFAULT_ROLE_KEYWORDS = [
    "sde",
    "software engineer",
    "data analyst",
    "business analyst",
    "intern",
]
DEFAULT_LOCATIONS = "India,Remote"
DEFAULT_SDE_RESUME = "/Users/anamay/Desktop/cv/amazon/anamay_sde_230968270.pdf"
DEFAULT_BUSINESS_RESUME = "/Users/anamay/Desktop/cv/amazon/Anamay_Business_230968270.pdf"
USA_HINTS = [
    "usa",
    "u.s.",
    "united states",
    "new york",
    "san francisco",
    "seattle",
    "austin",
    "chicago",
    "boston",
    "los angeles",
    "california",
    "texas",
]
SDE_TITLE_HINTS = [
    "sde",
    "software",
    "engineer",
    "developer",
    "backend",
    "frontend",
    "full stack",
    "ml engineer",
    "data engineer",
]
BUSINESS_TITLE_HINTS = [
    "analyst",
    "business",
    "operations",
    "compliance",
    "finance",
    "risk",
    "audit",
]


def str2bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def detect_provider(url: str) -> str:
    url_lower = (url or "").lower()
    if "greenhouse.io" in url_lower:
        return "greenhouse"
    if "gh_jid=" in url_lower:
        return "greenhouse"
    if "lever.co" in url_lower:
        return "lever"
    if "lever-job" in url_lower:
        return "lever"
    if "ashbyhq.com" in url_lower:
        return "ashby"
    if "smartrecruiters.com" in url_lower:
        return "smartrecruiters"
    if "workable.com" in url_lower:
        return "workable"
    if "linkedin.com" in url_lower:
        return "linkedin"
    if "myworkdayjobs.com" in url_lower or "workdayjobs.com" in url_lower:
        return "workday"
    return "generic"


def blocked_by_denylist(url: str, denylist: Sequence[str]) -> bool:
    lower = (url or "").lower()
    return any(token and token in lower for token in denylist)


def load_jobs(path: str) -> List[Dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [job for job in payload if isinstance(job, dict)]

    if isinstance(payload, dict):
        for key in ("jobs", "results", "items", "data"):
            if key in payload and isinstance(payload[key], list):
                return [job for job in payload[key] if isinstance(job, dict)]

    raise ValueError(f"Unsupported jobs input structure in {path}")


def _as_keywords(csv: str) -> List[str]:
    return [part.strip().lower() for part in csv.split(",") if part.strip()]


def _contains_any(text: str, patterns: Sequence[str]) -> bool:
    content = (text or "").lower()
    return any(pattern in content for pattern in patterns)


def role_matches(job: Dict[str, Any], role_keywords: Sequence[str]) -> bool:
    haystack = " ".join(
        [
            str(job.get("title", "")),
            str(job.get("role", "")),
            str(job.get("description", "")),
        ]
    ).lower()
    return any(keyword in haystack for keyword in role_keywords)


def location_matches(job: Dict[str, Any], locations: Sequence[str]) -> bool:
    if not locations:
        return True
    location = str(job.get("location", "")).lower()
    return any(loc.lower() in location for loc in locations)


def non_usa_matches(job: Dict[str, Any]) -> bool:
    explicit = job.get("non_usa_pass")
    if isinstance(explicit, bool):
        return explicit
    haystack = " ".join(
        [
            str(job.get("location", "")),
            str(job.get("title", "")),
            str(job.get("description", "")),
            str(job.get("apply_url") or job.get("url") or ""),
        ]
    )
    return not _contains_any(haystack, USA_HINTS)


def route_resume_for_job(
    job: Dict[str, Any],
    *,
    default_resume: str,
    sde_resume: str,
    business_resume: str,
) -> str:
    title_blob = " ".join([str(job.get("title", "")), str(job.get("description", ""))]).lower()

    # Prefer explicit SDE resume for engineering tracks.
    if _contains_any(title_blob, SDE_TITLE_HINTS) and Path(sde_resume).exists():
        return sde_resume
    if _contains_any(title_blob, BUSINESS_TITLE_HINTS) and Path(business_resume).exists():
        return business_resume

    # Fallback policy is SDE resume first, then default, then business.
    for candidate in (sde_resume, default_resume, business_resume):
        if candidate and Path(candidate).exists():
            return candidate
    return default_resume


def idempotency_key(job: Dict[str, Any]) -> str:
    company = str(job.get("company", "")).strip().lower()
    role = str(job.get("title", job.get("role", ""))).strip().lower()
    apply_url = str(job.get("apply_url") or job.get("url") or "").strip().lower()
    raw = f"{company}|{role}|{apply_url}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_ats_companies(job_sources_path: str) -> set[str]:
    path = Path(job_sources_path)
    if not path.exists():
        return set()

    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    companies: set[str] = set()
    for source in payload.get("ats_sources", []):
        for company in source.get("companies", []) or []:
            companies.add(str(company).strip().lower())
    return companies


def save_json(path: str, payload: Dict[str, Any]) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def build_candidates(
    jobs: List[Dict[str, Any]],
    role_keywords: Sequence[str],
    locations: Sequence[str],
    ats_companies: set[str],
    existing_applied: set[str],
    denylist_domains: Sequence[str],
    *,
    non_usa_only: bool = False,
    enforce_ats_allowlist: bool = False,
    default_resume: str = DEFAULT_BUSINESS_RESUME,
    sde_resume: str = DEFAULT_SDE_RESUME,
    business_resume: str = DEFAULT_BUSINESS_RESUME,
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for job in jobs:
        apply_url = str(job.get("apply_url") or job.get("url") or "")
        if blocked_by_denylist(apply_url, denylist_domains):
            continue
        provider = detect_provider(apply_url)
        if provider not in ALLOWED_ATS_PROVIDERS:
            continue

        if not role_matches(job, role_keywords):
            continue

        if not location_matches(job, locations):
            continue

        if non_usa_only and not non_usa_matches(job):
            continue

        if "internship_pass" in job and not bool(job.get("internship_pass")):
            continue

        company = str(job.get("company", "")).strip().lower()
        if enforce_ats_allowlist and ats_companies and company and company not in ats_companies:
            continue

        key = idempotency_key(job)
        if key in existing_applied:
            continue

        row = dict(job)
        row["_provider"] = provider
        row["_idempotency_key"] = key
        row["_resume_path"] = route_resume_for_job(
            row,
            default_resume=default_resume,
            sde_resume=sde_resume,
            business_resume=business_resume,
        )
        candidates.append(row)

    return candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ATS-first Playwright apply pipeline")
    parser.add_argument("--resume", default=DEFAULT_BUSINESS_RESUME, help="Absolute path to default resume file")
    parser.add_argument("--sde-resume", default=DEFAULT_SDE_RESUME, help="Resume path for SDE/engineering roles")
    parser.add_argument("--business-resume", default=DEFAULT_BUSINESS_RESUME, help="Resume path for analyst/business roles")
    parser.add_argument("--mode", choices=["human_verified", "full_auto", "draft_only"], default="human_verified", help="Submission mode")
    parser.add_argument("--roles", default="SDE Intern,Data Analyst Intern,Business Analyst Intern", help="Comma-separated role keywords")
    parser.add_argument("--locations", default=DEFAULT_LOCATIONS, help="Comma-separated locations")
    parser.add_argument("--non-usa-only", default="true", help="Enforce non-USA postings at runtime (true/false)")
    parser.add_argument("--max-applications", type=int, default=25, help="Max number of applications to attempt")
    parser.add_argument("--jobs-input", default="/Users/anamay/Desktop/Projects/internmailer_v3/output/jobs_ranked.json", help="Path to job list JSON")
    parser.add_argument("--results-out", default="/Users/anamay/Desktop/Projects/internmailer_v3/output/playwright/apply_results_YYYYMMDD.json", help="Path to output result JSON")
    parser.add_argument("--job-sources", default="/Users/anamay/Desktop/Projects/internmailer_v3/data/job_sources.yaml", help="Path to ATS job sources config")
    parser.add_argument("--enforce-ats-company-allowlist", default="false", help="Filter companies to data/job_sources.yaml entries (true/false)")
    parser.add_argument("--confirmation-selector", default="", help="Required confirmation selector in human_verified mode")
    parser.add_argument("--max-steps", type=int, default=6, help="Max form steps per job before failing")
    parser.add_argument("--max-retries", type=int, default=2, help="Max retries for transient failures per job")
    parser.add_argument("--retry-delay-seconds", type=float, default=2.0, help="Delay between retries")
    parser.add_argument("--idempotency-store", default="/Users/anamay/Desktop/Projects/internmailer_v3/output/playwright/applied_keys.json", help="Persistent applied-key store")
    parser.add_argument("--failures-dir", default="/Users/anamay/Desktop/Projects/internmailer_v3/output/playwright/failures", help="Directory for screenshot/html evidence")

    parser.add_argument("--workers", type=int, default=8, help="Number of parallel workers")
    parser.add_argument("--engine", choices=["playwright"], default="playwright", help="Automation engine")
    parser.add_argument("--review-mode", choices=["manual_submit"], default="manual_submit", help="Manual review mode")
    parser.add_argument("--state-store", default="/Users/anamay/Desktop/Projects/internmailer_v3/output/playwright/queue_state.json", help="Queue state persistence JSON")
    parser.add_argument("--events-out", default="/Users/anamay/Desktop/Projects/internmailer_v3/output/playwright/events_YYYYMMDD.jsonl", help="Queue event stream output")
    parser.add_argument("--atlas-sync", default="true", help="Enable Atlas sync (true/false)")
    parser.add_argument("--atlas-label-prefix", default="apply-review", help="Atlas label prefix")
    parser.add_argument("--submit-timeout-seconds", type=int, default=300, help="Timeout waiting for manual submit")
    parser.add_argument(
        "--blocked-flow-mode",
        choices=["mark_blocked", "pause_for_manual_solve"],
        default="pause_for_manual_solve",
        help="How to handle login/captcha blocked flows",
    )
    parser.add_argument(
        "--denylist-domains",
        default="job-boards.greenhouse.io/reddit,job-boards.greenhouse.io/twitch",
        help="Comma-separated URL substrings to skip for lower-friction runs",
    )

    args = parser.parse_args()

    resume_path = Path(args.resume)
    if not resume_path.exists():
        raise SystemExit(f"Resume file does not exist: {resume_path}")
    sde_resume_path = Path(args.sde_resume)
    business_resume_path = Path(args.business_resume)

    jobs = load_jobs(args.jobs_input)
    role_keywords = _as_keywords(args.roles)
    if not role_keywords:
        role_keywords = list(DEFAULT_ROLE_KEYWORDS)
    else:
        for keyword in DEFAULT_ROLE_KEYWORDS:
            if keyword not in role_keywords:
                role_keywords.append(keyword)

    locations = _as_keywords(args.locations)
    if str2bool(args.non_usa_only) and args.locations.strip().lower() == DEFAULT_LOCATIONS.lower():
        # In non-USA campaigns, default India/Remote is too restrictive for global non-USA lists.
        locations = []
    ats_companies = load_ats_companies(args.job_sources)
    denylist_domains = [s.strip().lower() for s in args.denylist_domains.split(",") if s.strip()]

    idempotency_store_path = Path(args.idempotency_store)
    if idempotency_store_path.exists():
        existing_applied = set(json.loads(idempotency_store_path.read_text(encoding="utf-8")))
    else:
        existing_applied = set()

    candidates = build_candidates(
        jobs,
        role_keywords,
        locations,
        ats_companies,
        existing_applied,
        denylist_domains,
        non_usa_only=str2bool(args.non_usa_only),
        enforce_ats_allowlist=str2bool(args.enforce_ats_company_allowlist),
        default_resume=str(resume_path),
        sde_resume=str(sde_resume_path),
        business_resume=str(business_resume_path),
    )

    applier = JobAutoApplier(
        submit_mode=args.mode,  # type: ignore[arg-type]
        max_steps_per_job=max(1, args.max_steps),
        required_confirmation_selector=args.confirmation_selector or None,
    )

    results_out = args.results_out
    events_out = args.events_out
    if "YYYYMMDD" in results_out:
        results_out = results_out.replace("YYYYMMDD", datetime.now(timezone.utc).strftime("%Y%m%d"))
    if "YYYYMMDD" in events_out:
        events_out = events_out.replace("YYYYMMDD", datetime.now(timezone.utc).strftime("%Y%m%d"))

    if args.workers > 1:
        atlas_client = AtlasSyncClient(
            enabled=str2bool(args.atlas_sync),
            label_prefix=args.atlas_label_prefix,
        )
        queue_runner = ApplyQueueRunner(
            jobs=candidates,
            applier=applier,
            workers=args.workers,
            state_store=args.state_store,
            events_out=events_out,
            failures_dir=args.failures_dir,
            resume_path=str(resume_path),
            submit_timeout_s=args.submit_timeout_seconds,
            submit_mode=args.mode,
            blocked_flow_mode=args.blocked_flow_mode,
            atlas_sync=atlas_client,
            submitted_keys=existing_applied,
        )
        queue_result = asyncio.run(queue_runner.run(max_applications=args.max_applications))
        results = queue_result["results"]
        attempted = queue_result["attempted"]
        applied_count = queue_result["applied"]
    else:
        attempted = 0
        applied_count = 0
        results: List[Dict[str, Any]] = []

        for job in candidates:
            if attempted >= args.max_applications:
                break

            attempted += 1
            key = job["_idempotency_key"]
            job_payload = dict(job)
            job_payload["resume_path"] = job.get("_resume_path") or str(resume_path)

            final_result = None
            for attempt in range(1, args.max_retries + 2):
                result = applier.apply(
                    job_payload,
                    submit_mode=args.mode,  # type: ignore[arg-type]
                    max_steps_per_job=max(1, args.max_steps),
                    required_confirmation_selector=args.confirmation_selector or None,
                    artifacts_dir=args.failures_dir,
                )
                final_result = result
                transient_failure = result.status == "error" and attempt <= args.max_retries
                if not transient_failure:
                    break
                time.sleep(max(0.0, args.retry_delay_seconds))

            if final_result is None:
                continue

            if final_result.applied:
                applied_count += 1
                existing_applied.add(key)

            results.append(
                {
                    "idempotency_key": key,
                    "company": job.get("company", ""),
                    "title": job.get("title", ""),
                    "location": job.get("location", ""),
                    "url": job.get("apply_url") or job.get("url"),
                    "provider": final_result.provider,
                    "status": final_result.status,
                    "details": final_result.details,
                    "applied": final_result.applied,
                    "evidence": final_result.evidence,
                }
            )

    idempotency_store_path.parent.mkdir(parents=True, exist_ok=True)
    idempotency_store_path.write_text(json.dumps(sorted(existing_applied), indent=2), encoding="utf-8")

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode,
        "workers": args.workers,
        "engine": args.engine,
        "review_mode": args.review_mode,
        "resume": str(resume_path),
        "sde_resume": str(sde_resume_path),
        "business_resume": str(business_resume_path),
        "roles": role_keywords,
        "locations": locations,
        "non_usa_only": str2bool(args.non_usa_only),
        "blocked_flow_mode": args.blocked_flow_mode,
        "enforce_ats_company_allowlist": str2bool(args.enforce_ats_company_allowlist),
        "max_applications": args.max_applications,
        "attempted": attempted,
        "applied": applied_count,
        "review_required": sum(1 for r in results if r["status"] == "review_required"),
        "blocked": sum(1 for r in results if r["status"] in {"blocked_captcha", "blocked_login"}),
        "errors": sum(1 for r in results if r["status"] == "error"),
        "results": results,
        "events_out": events_out,
        "state_store": args.state_store,
        "denylist_domains": denylist_domains,
    }
    save_json(results_out, payload)

    print(f"Candidates considered: {len(candidates)}")
    print(f"Attempted: {attempted}")
    print(f"Applied: {applied_count}")
    print(f"Results written: {results_out}")
    print(f"Events stream: {events_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
