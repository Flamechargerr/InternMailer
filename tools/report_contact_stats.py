#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import pandas as pd
from typing import Dict, Any

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
        if e.lower().startswith("http"):
            return False
        return bool(EMAIL_RE.match(e))
    def is_role_based(e: str) -> bool:
        roles = ["postmaster", "admin", "support", "info", "no-reply", "noreply", "webmaster"]
        return any(e.lower().startswith(r+"@") for r in roles)
    def is_url_like(e: str) -> bool:
        return isinstance(e, str) and e.lower().startswith(("http://", "https://"))


def count_professors() -> Dict[str, Any]:
    # Prefer curated final datasets if available
    candidates = [
        PROJECT_ROOT / 'data' / 'scraped_professors_final.csv',
        PROJECT_ROOT / 'professors_final.csv',
        PROJECT_ROOT / 'professors_database.csv',
        PROJECT_ROOT / 'professors_properly_cleaned.csv',
    ]
    df = None
    src = None
    for p in candidates:
        if p.exists():
            try:
                df = pd.read_csv(p)
                src = p
                break
            except Exception:
                continue
    if df is None:
        return {"source": None, "total_rows": 0, "with_email": 0, "valid_emails": 0,
                "role_based": 0, "to_contact": 0, "contacted": 0, "followups": 0}

    email_col = None
    for c in df.columns:
        if c.lower() in ("email", "emails"): email_col = c; break
    if email_col is None:
        return {"source": str(src), "total_rows": len(df), "with_email": 0, "valid_emails": 0,
                "role_based": 0, "to_contact": 0, "contacted": 0, "followups": 0}

    emails = df[email_col].fillna("").astype(str).str.strip()
    with_email = (emails != "").sum()
    valid_mask = emails.apply(lambda e: validate_email(e) and not is_role_based(e) and not is_url_like(e))
    valid_count = int(valid_mask.sum())

    # Infer contacted/followup from optional logs if present
    contacted = 0
    followups = 0
    # comprehensive log
    comp_log = PROJECT_ROOT / 'archive' / 'cleanup_backup_20250802_235723' / 'comprehensive_email_log.csv'
    if comp_log.exists():
        try:
            log_df = pd.read_csv(comp_log)
            # heuristics: status column may indicate Sent, Delivered, Follow-up
            if 'recipient_email' in log_df.columns:
                sent_set = set(log_df['recipient_email'].dropna().astype(str))
                contacted = sum(emails.isin(sent_set))
            if 'status' in log_df.columns:
                followups = int((log_df['status'].astype(str).str.contains('follow', case=False, na=False)).sum())
        except Exception:
            pass

    # to_contact approximated as valid - contacted
    to_contact = max(0, valid_count - contacted)

    return {
        "source": str(src),
        "total_rows": int(len(df)),
        "with_email": int(with_email),
        "valid_emails": int(valid_count),
        "role_based": int(sum(emails.apply(is_role_based))),
        "to_contact": int(to_contact),
        "contacted": int(contacted),
        "followups": int(followups),
    }


def count_hr() -> Dict[str, Any]:
    # Use hr_contacts_cleaned.csv if present
    candidates = [
        PROJECT_ROOT / 'hr_contacts_cleaned.csv',
        PROJECT_ROOT / 'archive' / 'cleanup_backup_20250802_235723' / 'hr_contacts_from_spreadsheet.csv',
    ]
    df = None
    src = None
    for p in candidates:
        if p.exists():
            try:
                df = pd.read_csv(p)
                src = p
                break
            except Exception:
                continue
    if df is None:
        return {"source": None, "total_rows": 0, "with_company": 0, "estimated_valid_emails": 0,
                "to_contact": 0, "contacted": 0, "followups": 0}

    # HR sheet may not have explicit email column; estimate from company website/social columns if emails exist
    email_col = None
    for c in df.columns:
        if c.lower() == 'email':
            email_col = c
            break
    estimated_valid = 0
    with_company = int((df.get('Company Name')
                         .astype(str)
                         .fillna('')
                         .str.strip() != '').sum()) if 'Company Name' in df.columns else len(df)

    if email_col:
        emails = df[email_col].fillna('').astype(str).str.strip()
        estimated_valid = int((emails.apply(lambda e: validate_email(e) and not is_role_based(e) and not is_url_like(e))).sum())
    else:
        estimated_valid = 0

    # Contacted/followups by Status column if present
    contacted = 0
    followups = 0
    if 'Status' in df.columns:
        status = df['Status'].astype(str).str.strip().str.lower()
        followups = int(status.str.startswith('follow-up').sum())
        # treat statuses indicating contact made
        contacted_statuses = ('invitation sent', 'in talks', 'lost', 'no openings')
        contacted = int(status.isin(contacted_statuses).sum()) + followups

    # Fallback to contacted_companies archive list
    contacted_companies = PROJECT_ROOT / 'archive' / 'cleanup_backup_20250802_235723' / 'contacted_companies.csv'
    if contacted_companies.exists():
        try:
            cc = pd.read_csv(contacted_companies)
            if 'Company Name' in cc.columns and 'Company Name' in df.columns:
                contacted += int(df['Company Name'].isin(set(cc['Company Name'].dropna().astype(str))).sum())
        except Exception:
            pass

    to_contact = max(0, with_company - contacted)

    return {
        "source": str(src),
        "total_rows": int(len(df)),
        "with_company": int(with_company),
        "estimated_valid_emails": int(estimated_valid),
        "to_contact": int(to_contact),
        "contacted": int(contacted),
        "followups": int(followups),
    }


def main():
    prof = count_professors()
    hr = count_hr()

    print("=== Contact Stats Report ===")
    print("Professors:")
    for k, v in prof.items():
        print(f"  {k}: {v}")
    print()
    print("HR:")
    for k, v in hr.items():
        print(f"  {k}: {v}")

if __name__ == '__main__':
    main()
