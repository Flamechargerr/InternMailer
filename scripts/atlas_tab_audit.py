#!/usr/bin/env python3
"""Audit live Atlas tabs and report duplicate URLs/domains."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

TRACKING_KEYS = {"gclid", "fbclid", "ref", "ref_src"}


class AtlasTabAuditError(RuntimeError):
    """Raised when Atlas tab audit cannot continue."""


def _default_atlas_cli() -> str:
    codex_home = os.getenv("CODEX_HOME", os.path.join(Path.home(), ".codex"))
    return os.path.join(codex_home, "skills", "atlas", "scripts", "atlas_cli.py")


def _run_atlas(atlas_cli: str, command: str, timeout_seconds: int = 20) -> str:
    cmd = [
        "uv",
        "run",
        "--python",
        "3.12",
        "python",
        atlas_cli,
        command,
        "--json",
    ]
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise AtlasTabAuditError(
            "Atlas command timed out. Grant Automation access: System Settings -> Privacy & Security "
            "-> Automation -> allow your terminal app to control ChatGPT Atlas."
        ) from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise AtlasTabAuditError(f"Atlas command failed: {stderr or 'unknown error'}") from exc

    return result.stdout.strip()


def _preflight(atlas_cli: str, timeout_seconds: int = 10) -> None:
    cmd = ["uv", "run", "--python", "3.12", "python", atlas_cli, "app-name"]
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise AtlasTabAuditError("Atlas preflight timed out while checking app availability.") from exc
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise AtlasTabAuditError(f"Atlas app preflight failed: {stderr or 'unknown error'}") from exc

    app_name = result.stdout.strip()
    if not app_name:
        raise AtlasTabAuditError("Atlas app preflight returned no app name.")


def _canonicalize_url(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/")

    query_pairs = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        key_lower = key.lower()
        if key_lower.startswith("utm_") or key_lower in TRACKING_KEYS:
            continue
        query_pairs.append((key, value))

    canonical = parsed._replace(
        scheme="",
        netloc=host,
        path=path,
        query=urlencode(query_pairs, doseq=True),
        fragment="",
    )
    normalized = urlunparse(canonical)
    if normalized.startswith("//"):
        normalized = normalized[2:]
    return normalized


def _domain(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    return host[4:] if host.startswith("www.") else host


def _collect_duplicate_groups(tabs: List[Dict[str, Any]], key_name: str) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for tab in tabs:
        key_value = tab.get(key_name, "")
        if key_value:
            grouped[key_value].append(tab)

    output = []
    for key_value, group in grouped.items():
        if len(group) > 1:
            output.append(
                {
                    "key": key_value,
                    "count": len(group),
                    "tabs": [
                        {
                            "title": tab.get("title", ""),
                            "url": tab.get("url", ""),
                            "window_id": tab.get("window_id"),
                            "tab_index": tab.get("tab_index"),
                            "is_active": bool(tab.get("is_active", False)),
                        }
                        for tab in group
                    ],
                }
            )

    output.sort(key=lambda item: (-item["count"], item["key"]))
    return output


def _build_report(tabs: List[Dict[str, Any]]) -> Dict[str, Any]:
    normalized_tabs: List[Dict[str, Any]] = []
    for tab in tabs:
        url = tab.get("url", "")
        normalized_tabs.append(
            {
                "title": tab.get("title", ""),
                "url": url,
                "window_id": tab.get("window_id"),
                "tab_index": tab.get("tab_index"),
                "is_active": bool(tab.get("is_active", False)),
                "canonical_url": _canonicalize_url(url) if url else "",
                "domain": _domain(url) if url else "",
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tab_count": len(normalized_tabs),
        "tabs": [
            {
                "title": tab["title"],
                "url": tab["url"],
                "window_id": tab["window_id"],
                "tab_index": tab["tab_index"],
                "is_active": tab["is_active"],
            }
            for tab in normalized_tabs
        ],
        "duplicates": {
            "exact_url": _collect_duplicate_groups(normalized_tabs, "url"),
            "canonical_url": _collect_duplicate_groups(normalized_tabs, "canonical_url"),
            "domain": _collect_duplicate_groups(normalized_tabs, "domain"),
        },
    }


def _report_to_markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# Atlas Tab Audit",
        "",
        f"Generated: {report['generated_at']}",
        f"Open tabs: {report['tab_count']}",
        "",
    ]

    for section, title in [
        ("exact_url", "Exact URL duplicates"),
        ("canonical_url", "Canonical URL duplicates"),
        ("domain", "Domain duplicates"),
    ]:
        groups = report["duplicates"].get(section, [])
        lines.append(f"## {title}")
        if not groups:
            lines.append("None")
            lines.append("")
            continue

        for group in groups:
            lines.append(f"- `{group['key']}` ({group['count']} tabs)")
            for tab in group["tabs"]:
                marker = "*" if tab["is_active"] else "-"
                lines.append(
                    f"  {marker} window={tab['window_id']} tab={tab['tab_index']} | "
                    f"{tab['title']} | {tab['url']}"
                )
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Atlas tabs and find duplicates.")
    parser.add_argument(
        "--json-out",
        default="/Users/anamay/Desktop/Projects/internmailer_v3/output/atlas/tab_report.json",
        help="Absolute path to JSON output report.",
    )
    parser.add_argument(
        "--md-out",
        default="/Users/anamay/Desktop/Projects/internmailer_v3/output/atlas/tab_report.md",
        help="Absolute path to Markdown output report.",
    )
    parser.add_argument(
        "--strict-live-tabs",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="If true, fail immediately when live tab retrieval cannot complete.",
    )
    parser.add_argument(
        "--atlas-cli",
        default=_default_atlas_cli(),
        help="Path to atlas_cli.py",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=20,
        help="Timeout for Atlas tab command.",
    )
    args = parser.parse_args()

    try:
        _preflight(args.atlas_cli)
        raw_tabs = _run_atlas(args.atlas_cli, "tabs", timeout_seconds=args.timeout_seconds)
        tabs = json.loads(raw_tabs) if raw_tabs else []
        if not isinstance(tabs, list):
            raise AtlasTabAuditError("Atlas tabs payload was not a JSON list.")
    except (AtlasTabAuditError, json.JSONDecodeError) as exc:
        if args.strict_live_tabs:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

        tabs = []

    report = _build_report(tabs)

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)

    json_out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_out.write_text(_report_to_markdown(report), encoding="utf-8")

    print(f"Wrote JSON report: {json_out}")
    print(f"Wrote Markdown report: {md_out}")
    print(f"Tab count: {report['tab_count']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
