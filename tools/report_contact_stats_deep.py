#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from typing import List, Dict, Set, Tuple
import pandas as pd

# Allow running from repo root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

# Shared validator
try:
    from core.utils.email_validation import validate_email, is_role_based, is_url_like
except Exception:
    import re
    EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
    def validate_email(e: str) -> bool:
        if not e or not isinstance(e, str):
            return False
        if e.lower().startswith(("http://", "https://")):
            return False
        return bool(EMAIL_RE.match(e))
    def is_role_based(e: str) -> bool:
        roles = ["postmaster","admin","support","info","no-reply","noreply","webmaster"]
        e = (e or "").lower()
        return any(e.startswith(r+"@") for r in roles)
    def is_url_like(e: str) -> bool:
        return isinstance(e, str) and e.lower().startswith(("http://","https://"))


PROF_PATTERNS = (
    "professors_*.csv","*professor*.csv","scraped_professors*.csv","mass_professors*.csv",
    "enriched_professors*.csv","*professors*final*.csv","*professors*unified*.csv",
    "*professors*consolidated*.csv","*targeted_professors*.csv"
)

HR_PATTERNS = (
    "hr_contacts*.csv","*hr*contacts*.csv","*hr*emails*.csv"
)

LOG_PATTERNS = (
    "*comprehensive_email_log*.csv","*sent_log*.csv","*send_log*.csv","*contact_history*.csv"
)

SEARCH_DIRS = [PROJECT_ROOT, PROJECT_ROOT/"data", PROJECT_ROOT/"archive_to_review", PROJECT_ROOT/"archive"]


def find_files(patterns: Tuple[str, ...]) -> List[Path]:
    out: List[Path] = []
    for base in SEARCH_DIRS:
        if not base.exists():
            continue
        for pat in patterns:
            out.extend(base.rglob(pat))
    # Dedup paths while preserving order
    seen = set()
    uniq: List[Path] = []
    for p in out:
        if p not in seen:
            uniq.append(p)
            seen.add(p)
    return uniq


def load_emails_from_csv(p: Path) -> Tuple[Set[str], int]:
    try:
        df = pd.read_csv(p)
    except Exception:
        return set(), 0
    email_col = None
    for c in df.columns:
        lc = c.lower()
        if lc in ("email","emails","recipient","recipient_email"):
            email_col = c
            break
    emails: Set[str] = set()
    if email_col:
        series = df[email_col].fillna("").astype(str).str.strip()
        emails = set([e for e in series if e])
    return emails, len(df)


def aggregate_professors() -> Dict[str, int]:
    sources = find_files(PROF_PATTERNS)
    all_emails: Set[str] = set()
    total_rows = 0
    for p in sources:
        ems, n = load_emails_from_csv(p)
        total_rows += n
        all_emails.update(ems)

    # Valid filtering
    valid = set([e for e in all_emails if validate_email(e) and not is_role_based(e) and not is_url_like(e)])

    # Contacted/followups from logs
    contacted: Set[str] = set()
    followups = 0
    logs = find_files(LOG_PATTERNS)
    for lp in logs:
        try:
            df = pd.read_csv(lp)
        except Exception:
            continue
        # recipient columns
        for col in ("recipient_email","email","recipient","to"):
            if col in df.columns:
                contacted.update(df[col].dropna().astype(str).str.strip().tolist())
                break
        # followups by status
        for s_col in ("status","note","remarks"):
            if s_col in df.columns:
                followups += int(df[s_col].astype(str).str.contains("follow", case=False, na=False).sum())
                break

    contacted_valid = valid.intersection({e for e in contacted if validate_email(e)})
    to_contact = max(0, len(valid) - len(contacted_valid))

    return {
        "discovered_rows": total_rows,
        "unique_emails": len(all_emails),
        "valid_emails": len(valid),
        "contacted": len(contacted_valid),
        "followups": followups,
        "to_contact": to_contact,
    }


def aggregate_hr() -> Dict[str, int]:
    sources = find_files(HR_PATTERNS)
    all_emails: Set[str] = set()
    total_rows = 0
    for p in sources:
        ems, n = load_emails_from_csv(p)
        total_rows += n
        all_emails.update(ems)

    valid = set([e for e in all_emails if validate_email(e) and not is_role_based(e) and not is_url_like(e)])

    # Contacted from typical HR sheets with Status columns
    contacted = 0
    followups = 0
    for p in sources:
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        if 'Status' in df.columns:
            status = df['Status'].astype(str).str.strip().str.lower()
            followups += int(status.str.startswith('follow-up').sum())
            contacted_statuses = ('invitation sent','in talks','lost','no openings','responded','scheduled')
            contacted += int(status.isin(contacted_statuses).sum()) + int(status.str.contains('contacted', na=False).sum())

    to_contact = max(0, len(valid) - contacted)

    return {
        "discovered_rows": total_rows,
        "unique_emails": len(all_emails),
        "valid_emails": len(valid),
        "contacted": contacted,
        "followups": followups,
        "to_contact": to_contact,
    }


def main():
    print("=== Deep Contact Stats (All Sources) ===")
    prof = aggregate_professors()
    hr = aggregate_hr()

    print("Professors:")
    for k, v in prof.items():
        print(f"  {k}: {v}")
    print()
    print("HR:")
    for k, v in hr.items():
        print(f"  {k}: {v}")

    # Export JSON report
    try:
        import json
        reports_dir = PROJECT_ROOT / 'tools' / 'reports'
        reports_dir.mkdir(parents=True, exist_ok=True)
        out = {
            'professors': prof,
            'hr': hr,
        }
        with open(reports_dir / 'contact_stats_deep.json', 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print(f"\n📄 Saved detailed report to {reports_dir / 'contact_stats_deep.json'}")
    except Exception as e:
        print(f"\n⚠️ Failed to write JSON report: {e}")

if __name__ == "__main__":
    main()
