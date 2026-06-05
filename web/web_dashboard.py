#!/usr/bin/env python3
"""InternMailer Flask API and React app host."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional

from flask import Flask, jsonify, request, send_from_directory

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.bootstrap import bootstrap

bootstrap()

from utils.config import config

try:
    from flask_cors import CORS
except Exception:  # pragma: no cover - optional in constrained installs
    CORS = None


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
FRONTEND_ASSETS = FRONTEND_DIST / "assets"
TCC_DB_DIR = Path("/tmp/internmailer_db")

app = Flask(
    __name__,
    static_folder=str(FRONTEND_ASSETS) if FRONTEND_ASSETS.exists() else None,
    static_url_path="/assets",
)
app.secret_key = config.SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

if CORS:
    CORS(app, resources={r"/api/*": {"origins": config.FRONTEND_ORIGIN}})


daemon_process: Optional[subprocess.Popen] = None
background_tasks: dict[str, dict[str, Any]] = {}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _json_error(message: str, status_code: int = 500, **extra: Any):
    payload = {"status": "error", "message": message, **extra}
    return jsonify(payload), status_code


def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[dict[str, Any]]:
    return dict(row) if row is not None else None


def _safe_count(db, query: str, params: tuple[Any, ...] = ()) -> int:
    try:
        row = db.fetch_one(query, params)
        if row is None:
            return 0
        return int(row[0])
    except Exception:
        return 0


def _run_background(name: str, target: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    task_id = f"{name}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    background_tasks[task_id] = {
        "id": task_id,
        "name": name,
        "status": "running",
        "started_at": _now(),
        "finished_at": None,
        "result": None,
        "error": None,
    }

    def runner() -> None:
        try:
            background_tasks[task_id]["result"] = target()
            background_tasks[task_id]["status"] = "completed"
        except Exception as exc:
            background_tasks[task_id]["status"] = "failed"
            background_tasks[task_id]["error"] = str(exc)
        finally:
            background_tasks[task_id]["finished_at"] = _now()

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    return background_tasks[task_id]


def _job_db():
    from core.database_manager import get_job_discovery_db

    return get_job_discovery_db(config.JOBS_DB_PATH)


def _get_jobs(limit: int = 50, status: Optional[str] = None) -> list[dict[str, Any]]:
    db = _job_db()
    limit = max(1, min(int(limit or 50), 250))
    if status:
        rows = db.fetch_all(
            """
            SELECT * FROM jobs
            WHERE status = ?
            ORDER BY score DESC, updated_at DESC, created_at DESC, id DESC
            LIMIT ?
            """,
            (status, limit),
        )
    else:
        rows = db.fetch_all(
            """
            SELECT * FROM jobs
            ORDER BY score DESC, updated_at DESC, created_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        )
    return [dict(row) for row in rows]


def _job_stats() -> dict[str, int]:
    db = _job_db()
    return {
        "total": _safe_count(db, "SELECT COUNT(*) FROM jobs"),
        "new": _safe_count(db, "SELECT COUNT(*) FROM jobs WHERE status = 'new'"),
        "applied": _safe_count(db, "SELECT COUNT(*) FROM jobs WHERE status = 'applied'"),
        "needs_review": _safe_count(db, "SELECT COUNT(*) FROM jobs WHERE status = 'needs_review'"),
    }


def _reply_rows(limit: int = 50) -> list[dict[str, Any]]:
    db_path = Path(config.INBOX_DB_PATH)
    if not db_path.exists():
        return []

    try:
        with sqlite3.connect(str(db_path)) as conn:
            conn.row_factory = sqlite3.Row
            table_names = {
                row["name"]
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
            if "replies" not in table_names:
                return []
            rows = conn.execute(
                """
                SELECT sender, subject, received_date, category, sentiment
                FROM replies
                ORDER BY received_date DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]
    except Exception:
        return []


def _campaign_stats() -> dict[str, int]:
    db_path = Path(config.DATABASE_PATH)
    stats = {"emails_sent": 0, "emails_failed": 0, "contacts_contacted": 0}
    if not db_path.exists():
        return stats

    try:
        with sqlite3.connect(str(db_path)) as conn:
            tables = {
                row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
            if "sent_emails" in tables:
                stats["emails_sent"] = int(
                    conn.execute("SELECT COUNT(*) FROM sent_emails").fetchone()[0]
                )
                stats["contacts_contacted"] = int(
                    conn.execute("SELECT COUNT(DISTINCT email) FROM sent_emails").fetchone()[0]
                )
    except Exception:
        pass
    return stats


def _daemon_status() -> dict[str, Any]:
    if daemon_process and daemon_process.poll() is None:
        return {"running": True, "pid": daemon_process.pid, "mode": "process"}

    try:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "core" / "enhanced_daemon.py"), "--status"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=8,
        )
        details = {}
        if result.stdout.strip().startswith("{"):
            details = json.loads(result.stdout)
        return {
            "running": False,
            "pid": None,
            "mode": "stopped",
            "details": details,
            "stderr": result.stderr.strip()[-500:],
        }
    except Exception as exc:
        return {"running": False, "pid": None, "mode": "unavailable", "error": str(exc)}


@app.get("/api/health")
@app.get("/health")
def api_health():
    db_paths = {
        "jobs": config.JOBS_DB_PATH,
        "email": config.DATABASE_PATH,
        "inbox": config.INBOX_DB_PATH,
        "daemon": config.DAEMON_DB_PATH,
    }
    return jsonify(
        {
            "status": "ok",
            "service": "internmailer",
            "timestamp": _now(),
            "environment": config.ENV,
            "frontend_built": (FRONTEND_DIST / "index.html").exists(),
            "db_paths": db_paths,
            "warnings": {
                "resume_path": bool(config.RESUME_PATH),
                "gmail_configured": bool(config.GMAIL_USER and config.GMAIL_APP_PASSWORD),
                "ai_configured": bool(config.GROQ_API_KEY or config.OPENAI_API_KEY),
            },
        }
    )


@app.get("/metrics")
def metrics():
    stats = _job_stats() | _campaign_stats()
    lines = [f"internmailer_{key} {value}" for key, value in stats.items()]
    return "\n".join(lines) + "\n", 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.get("/api/stats")
def api_stats():
    jobs = _job_stats()
    replies = _reply_rows(limit=200)
    campaigns = _campaign_stats()
    response_rate = 0
    if campaigns["emails_sent"]:
        response_rate = round((len(replies) / campaigns["emails_sent"]) * 100, 1)

    return jsonify(
        {
            "status": "success",
            "jobs": jobs,
            "total_jobs": jobs["total"],
            "queued": jobs["new"],
            "applied": jobs["applied"],
            "needs_review": jobs["needs_review"],
            "emails": campaigns,
            "emails_sent": campaigns["emails_sent"],
            "replies": len(replies),
            "response_rate": response_rate,
            "daemon": _daemon_status(),
            "tasks": list(background_tasks.values())[-10:],
            "updated_at": _now(),
        }
    )


@app.get("/api/jobs")
def api_jobs():
    limit = request.args.get("limit", 50, type=int)
    status = request.args.get("status")
    return jsonify({"status": "success", "jobs": _get_jobs(limit=limit, status=status), "stats": _job_stats()})


@app.route("/api/jobs/discover", methods=["GET", "POST"])
def api_jobs_discover():
    if request.method == "GET":
        return jsonify({"status": "success", "message": "Discover jobs endpoint is online. Use POST to trigger."}), 200

    data = request.get_json(silent=True) or {}

    def discover() -> dict[str, Any]:
        from core.job_discovery import JobDiscovery

        return JobDiscovery().run()

    if data.get("sync"):
        return jsonify({"status": "success", "result": discover()})

    task = _run_background("job-discovery", discover)
    return jsonify({"status": "started", "message": "Job discovery started", "task": task})


@app.route("/api/jobs/apply", methods=["GET", "POST"])
def api_jobs_apply():
    if request.method == "GET":
        return jsonify({"status": "success", "message": "Apply queue endpoint is online. Use POST to trigger."}), 200

    data = request.get_json(silent=True) or {}
    limit = max(1, min(int(data.get("limit", 25)), 100))

    if not data.get("confirm"):
        pending = len(_get_jobs(limit=limit, status="new"))
        return jsonify(
            {
                "status": "needs_confirmation",
                "message": "Auto-apply is armed but not executed. Send confirm=true to run.",
                "pending": pending,
                "limit": limit,
            }
        )

    def apply() -> dict[str, Any]:
        from core.job_pipeline import JobPipeline

        return JobPipeline().apply_pending(limit=limit)

    if data.get("sync"):
        return jsonify({"status": "success", "result": apply()})

    task = _run_background("job-apply", apply)
    return jsonify({"status": "started", "message": "Apply queue started", "task": task})


@app.post("/send-emails")
def send_emails():
    data = request.get_json(silent=True) or {}
    count = max(1, min(int(data.get("count", 10)), 100))
    dry_run = not bool(data.get("confirm")) or bool(data.get("dry_run", False))

    try:
        from core.email_system import EmailSystem

        system = EmailSystem()
        result = system.send_campaign(count=count, use_ai=bool(data.get("use_ai", True)), dry_run=dry_run)
        return jsonify(
            {
                "status": "success",
                "mode": "dry_run" if dry_run else "sent",
                "message": "Preview run completed" if dry_run else "Email campaign completed",
                "result": result,
            }
        )
    except Exception as exc:
        return _json_error(str(exc), 500)


@app.get("/preview-emails")
def preview_emails():
    count = max(1, min(request.args.get("count", 3, type=int), 10))
    try:
        from core.email_system import EmailSystem

        previews = EmailSystem().preview(count=count)
        return jsonify({"status": "success", "previews": previews})
    except Exception as exc:
        return _json_error(str(exc), 500, previews=[])


@app.get("/api/replies")
def api_replies():
    replies = _reply_rows(limit=request.args.get("limit", 50, type=int))
    stats = {
        "total": len(replies),
        "interested": sum(1 for r in replies if str(r.get("category", "")).upper() == "INTERESTED"),
        "questions": sum(1 for r in replies if str(r.get("category", "")).upper() == "QUESTION"),
    }
    return jsonify({"status": "success", "replies": replies, "stats": stats})


@app.route("/api/contacts/discover", methods=["GET", "POST"])
def api_contacts_discover():
    if request.method == "GET":
        return jsonify({"status": "success", "message": "Contact discovery endpoint is online. Use POST to trigger."}), 200

    data = request.get_json(silent=True) or {}
    daily_cap = max(1, min(int(data.get("cap", config.CONTACT_DISCOVERY_DAILY_CAP)), 250))

    def discover() -> dict[str, Any]:
        from core.lead_discovery import discover_leads

        return discover_leads(daily_cap=daily_cap)

    if data.get("sync"):
        return jsonify({"status": "success", "result": discover()})

    task = _run_background("contact-discovery", discover)
    return jsonify({"status": "started", "message": "Contact discovery started", "task": task})


@app.get("/api/contacts/available")
def api_contacts_available():
    try:
        from core.email_system import EmailSystem
        system = EmailSystem()
        contacts = system.get_fresh_contacts(count=500)
        return jsonify({
            "status": "success",
            "count": len(contacts),
            "contacts": [{"name": c[0], "email": c[1], "company": c[2], "position": c[3]} for c in contacts[:25]]
        })
    except Exception as exc:
        return _json_error(str(exc), 500)


@app.get("/api/settings")
def api_settings():
    return jsonify(
        {
            "status": "success",
            "settings": {
                "gmail_user": config.GMAIL_USER,
                "groq_key": f"{config.GROQ_API_KEY[:8]}..." if config.GROQ_API_KEY else "",
                "max_emails_per_day": config.MAX_EMAILS_PER_DAY,
                "followup_days": config.FOLLOWUP_DELAY_DAYS,
                "resume_path": config.RESUME_PATH,
                "job_sources_path": config.JOB_SOURCES_PATH,
                "jobs_db_path": config.JOBS_DB_PATH,
                "email_db_path": config.DATABASE_PATH,
            },
        }
    )


@app.post("/api/ai/analyze-resume")
def api_ai_analyze_resume():
    data = request.get_json(silent=True) or {}
    job_description = data.get("job_description", "")
    resume_text = data.get("resume_text", "")
    
    try:
        from web.ats_optimizer import ATSOptimizer
        optimizer = ATSOptimizer()
        
        keywords_data = optimizer.extract_keywords_with_ai(job_description)
        keywords = keywords_data.get("ats_keywords", [])
        if not keywords:
            keywords = keywords_data.get("required_skills", [])
            
        matched = [word for word in keywords if word.lower() in resume_text.lower()]
        score = optimizer.calculate_ats_score(resume_text, keywords)
        missing = [word for word in keywords if word.lower() not in resume_text.lower()]
        
        return jsonify({
            "status": "success",
            "analysis": {
                "score": score,
                "keywords": keywords[:30],
                "matched_keywords": matched[:30],
                "missing_keywords": missing[:30]
            }
        })
    except Exception as exc:
        logger.warning(f"ATS Optimizer failed, using fallback resume analysis: {exc}")
        keywords = sorted(
            {
                token.lower()
                for token in job_description.replace("/", " ").replace(",", " ").split()
                if len(token) > 3 and token.isascii()
            }
        )[:30]
        matched = [word for word in keywords if word in resume_text.lower()]
        score = int((len(matched) / max(len(keywords), 1)) * 100)
        return jsonify(
            {
                "status": "success",
                "analysis": {
                    "score": score,
                    "keywords": keywords,
                    "matched_keywords": matched,
                    "missing_keywords": [word for word in keywords if word not in matched],
                },
            }
        )


@app.post("/api/ai/cover-letter")
def api_ai_cover_letter():
    data = request.get_json(silent=True) or {}
    company = data.get("company") or "the company"
    role = data.get("role") or data.get("position") or "the internship"
    
    try:
        from core.unified_ai_provider import get_unified_ai_provider
        ai = get_unified_ai_provider()
        
        prompt = f"Write a personalized, concise cover letter for Anamay Tripathy applying to the role of {role} at {company}."
        system_prompt = (
            "You are Anamay Tripathy, a Data Science Engineering student at MIT Manipal. "
            "Write a standard, professional, concise cover letter (max 200 words) using your real background: "
            "Led ML-powered systems (34% efficiency improvement) at YaanBarpe, processed 2.3M daily transactions at Intellect Design Arena. "
            "Do NOT invent fake details. Focus on facts. Format with clean newlines."
        )
        response = ai.complete(prompt=prompt, system_prompt=system_prompt)
        cover_letter = response.content
        if "Error:" in cover_letter or not cover_letter.strip():
            raise ValueError("AI generation failed or returned error")
    except Exception as exc:
        logger.warning(f"AI cover letter generation failed, using static template: {exc}")
        cover_letter = (
            f"Dear Hiring Team,\n\n"
            f"I am excited to apply for {role} at {company}. My background in data science, "
            "automation, and production-minded engineering has prepared me to contribute quickly "
            "while continuing to learn from a strong team.\n\n"
            "I would welcome the opportunity to discuss how my project experience and technical "
            "skills align with this role.\n\n"
            "Sincerely,\nAnamay Tripathy"
        )
        
    return jsonify({"status": "success", "cover_letter": cover_letter})


@app.post("/api/ai/interview-guide")
def api_ai_interview_guide():
    data = request.get_json(silent=True) or {}
    role = data.get("role") or "internship"
    
    try:
        from core.unified_ai_provider import get_unified_ai_provider
        ai = get_unified_ai_provider()
        
        prompt = f"Create a concise interview preparation guide for the role of {role}."
        system_prompt = (
            "You are an expert technical interviewer. Output a list of 4 high-yield, specific preparation bullet points "
            "for a candidate applying for this role. Each point should be technical and actionable. Output each point "
            "on a new line without numbers or dashes."
        )
        response = ai.complete(prompt=prompt, system_prompt=system_prompt)
        points = [p.strip() for p in response.content.split("\n") if p.strip()]
        guide = [p.lstrip("1234567890.-* \t") for p in points[:5]]
        if not guide:
            raise ValueError("AI generation returned empty guide")
    except Exception as exc:
        logger.warning(f"AI interview guide generation failed, using static guide: {exc}")
        guide = [
            f"Prepare a concise story for why this {role} fits your goals.",
            "Review one project where you owned debugging, tradeoffs, and measurable impact.",
            "Practice explaining data structures, APIs, and deployment decisions out loud.",
            "Prepare two company-specific questions about team workflow and intern ownership.",
        ]
        
    return jsonify({"status": "success", "guide": guide})


@app.get("/api/daemon/status")
def daemon_status():
    return jsonify({"status": "success", "daemon": _daemon_status()})


@app.post("/api/daemon/start")
def start_daemon():
    global daemon_process
    if daemon_process and daemon_process.poll() is None:
        return jsonify({"status": "success", "message": "Daemon already running", "pid": daemon_process.pid})

    try:
        daemon_process = subprocess.Popen(
            [sys.executable, str(PROJECT_ROOT / "core" / "enhanced_daemon.py"), "--start"],
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return jsonify({"status": "success", "message": "Daemon started", "pid": daemon_process.pid})
    except Exception as exc:
        return _json_error(str(exc), 500)


@app.post("/api/daemon/stop")
def stop_daemon():
    global daemon_process
    if daemon_process and daemon_process.poll() is None:
        daemon_process.terminate()
        daemon_process = None
        return jsonify({"status": "success", "message": "Daemon stopped"})
    daemon_process = None
    return jsonify({"status": "success", "message": "Daemon was not running"})


@app.get("/api/tasks")
def api_tasks():
    return jsonify({"status": "success", "tasks": list(background_tasks.values())})


@app.get("/download/<path:filename>")
def download_file(filename: str):
    safe_name = Path(filename).name
    directory = PROJECT_ROOT / "optimized_documents"
    target = directory / safe_name
    if not target.exists():
        return _json_error("File not found", 404)
    return send_from_directory(str(directory), safe_name, as_attachment=True)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react_app(path: str):
    if path.startswith("api/"):
        return _json_error("Endpoint not found", 404)

    asset_path = FRONTEND_DIST / path
    if path and asset_path.exists() and asset_path.is_file():
        return send_from_directory(str(FRONTEND_DIST), path)

    index_path = FRONTEND_DIST / "index.html"
    if index_path.exists():
        return send_from_directory(str(FRONTEND_DIST), "index.html")

    return (
        """
        <!doctype html>
        <html lang="en">
          <head><meta charset="utf-8"><title>InternMailer</title></head>
          <body style="font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; padding: 40px;">
            <h1>InternMailer API is running</h1>
            <p>The React dashboard has not been built yet. Run <code>cd frontend && npm install && npm run build</code>.</p>
            <p><a href="/api/health">API health</a></p>
          </body>
        </html>
        """,
        200,
        {"Content-Type": "text/html; charset=utf-8"},
    )


if __name__ == "__main__":
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=config.DEBUG)
