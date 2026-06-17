"""Concurrent apply queue runner for multi-tab human-verified workflow."""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from core.atlas_sync import AtlasSyncClient
from core.job_apply import JobAutoApplier

try:
    from playwright.async_api import async_playwright
except Exception:  # pragma: no cover
    async_playwright = None

JobState = Literal[
    "queued",
    "loading",
    "filling",
    "paused_review",
    "submitted",
    "blocked_captcha",
    "blocked_login",
    "failed_validation",
    "error",
]

WorkerState = Literal["idle", "busy", "paused", "blocked"]


ALLOWED_TRANSITIONS = {
    "queued": {"loading", "error"},
    "loading": {"filling", "blocked_captcha", "blocked_login", "failed_validation", "error"},
    "filling": {"paused_review", "blocked_captcha", "blocked_login", "failed_validation", "error"},
    "paused_review": {"submitted", "failed_validation", "blocked_captcha", "blocked_login", "error"},
    "submitted": set(),
    "blocked_captcha": set(),
    "blocked_login": set(),
    "failed_validation": set(),
    "error": set(),
}


def is_valid_transition(old: JobState, new: JobState) -> bool:
    if old == new:
        return True
    return new in ALLOWED_TRANSITIONS.get(old, set())


@dataclass
class QueueEvent:
    ts: str
    worker_id: int
    job_idempotency_key: str
    provider: str
    state_from: str
    state_to: str
    url: str
    message: str
    evidence: Optional[Dict[str, str]] = None


@dataclass
class JobRecord:
    key: str
    provider: str
    payload: Dict[str, Any]
    state: JobState = "queued"
    worker_id: Optional[int] = None
    evidence: Optional[Dict[str, str]] = None
    attempts: int = 0
    last_message: str = ""


@dataclass
class WorkerRecord:
    worker_id: int
    state: WorkerState = "idle"
    job_key: Optional[str] = None


@dataclass
class QueueRuntime:
    attempted: int = 0
    applied: int = 0
    blocked: int = 0
    errors: int = 0
    review_required: int = 0
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ApplyQueueRunner:
    """Runs concurrent workers that prepare jobs and wait for manual submit."""

    def __init__(
        self,
        *,
        jobs: list[Dict[str, Any]],
        applier: JobAutoApplier,
        workers: int,
        state_store: str,
        events_out: str,
        failures_dir: str,
        resume_path: str,
        submit_timeout_s: int = 300,
        submit_mode: str = "human_verified",
        blocked_flow_mode: str = "mark_blocked",
        atlas_sync: Optional[AtlasSyncClient] = None,
        submitted_keys: Optional[set[str]] = None,
    ):
        self.jobs_input = jobs
        self.applier = applier
        self.workers = max(1, workers)
        self.state_store = Path(state_store)
        self.events_out = Path(events_out)
        self.failures_dir = failures_dir
        self.resume_path = resume_path
        self.submit_timeout_s = max(30, submit_timeout_s)
        self.submit_mode = submit_mode
        self.blocked_flow_mode = blocked_flow_mode
        self.atlas_sync = atlas_sync
        self.submitted_keys = submitted_keys or set()

        self.runtime = QueueRuntime()
        self.workers_state: Dict[int, WorkerRecord] = {i: WorkerRecord(i) for i in range(self.workers)}
        self.jobs: Dict[str, JobRecord] = {}
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self.results: list[Dict[str, Any]] = []
        self._lock = asyncio.Lock()

    def _save_state(self) -> None:
        payload = {
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "runtime": asdict(self.runtime),
            "workers": {str(k): asdict(v) for k, v in self.workers_state.items()},
            "jobs": {k: asdict(v) for k, v in self.jobs.items()},
        }
        self.state_store.parent.mkdir(parents=True, exist_ok=True)
        self.state_store.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _emit_event(self, event: QueueEvent) -> None:
        self.events_out.parent.mkdir(parents=True, exist_ok=True)
        with self.events_out.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event)) + "\n")

    def _transition(
        self,
        job: JobRecord,
        worker_id: int,
        to_state: JobState,
        message: str,
        evidence: Optional[Dict[str, str]] = None,
    ) -> None:
        if not is_valid_transition(job.state, to_state):
            raise ValueError(f"Invalid transition {job.state} -> {to_state} for {job.key}")

        from_state = job.state
        job.state = to_state
        job.worker_id = worker_id
        job.last_message = message
        job.evidence = evidence

        self._emit_event(
            QueueEvent(
                ts=datetime.now(timezone.utc).isoformat(),
                worker_id=worker_id,
                job_idempotency_key=job.key,
                provider=job.provider,
                state_from=from_state,
                state_to=to_state,
                url=str(job.payload.get("apply_url") or job.payload.get("url") or ""),
                message=message,
                evidence=evidence,
            )
        )
        self._save_state()

    def _load_recovery_state(self) -> None:
        if not self.state_store.exists():
            return
        try:
            payload = json.loads(self.state_store.read_text(encoding="utf-8"))
        except Exception:
            return

        prior_jobs = payload.get("jobs", {})
        for key, data in prior_jobs.items():
            state = data.get("state")
            if state == "submitted":
                self.submitted_keys.add(key)

    def _bootstrap_jobs(self) -> None:
        self._load_recovery_state()
        for row in self.jobs_input:
            key = row["_idempotency_key"]
            if key in self.submitted_keys:
                continue
            payload = dict(row)
            payload["resume_path"] = (
                row.get("_resume_path")
                or row.get("resume_path")
                or self.resume_path
            )
            rec = JobRecord(
                key=key,
                provider=row.get("_provider", "generic"),
                payload=payload,
                state="queued",
            )
            self.jobs[key] = rec
            self.queue.put_nowait(key)
        self._save_state()

    def _record_terminal_result(
        self,
        *,
        job: JobRecord,
        worker_id: int,
        key: str,
        status: str,
        details: str,
        applied: bool,
        evidence: Optional[Dict[str, str]],
    ) -> str:
        if applied:
            final_state: JobState = "submitted"
            self._transition(job, worker_id, final_state, details, evidence)
            self.runtime.applied += 1
            self.submitted_keys.add(key)
        else:
            mapped = status if status in {"blocked_captcha", "blocked_login", "error"} else "failed_validation"
            final_state = mapped
            self._transition(job, worker_id, final_state, details, evidence)
            if final_state in {"blocked_captcha", "blocked_login"}:
                self.runtime.blocked += 1
            elif final_state == "error":
                self.runtime.errors += 1
            else:
                self.runtime.review_required += 1

        self.results.append(
            {
                "idempotency_key": key,
                "provider": job.provider,
                "status": final_state,
                "details": details,
                "applied": applied,
                "url": job.payload.get("apply_url") or job.payload.get("url"),
                "evidence": evidence,
            }
        )
        return final_state

    async def _worker_loop(self, worker_id: int, browser, max_applications: int) -> None:
        worker = self.workers_state[worker_id]
        while True:
            async with self._lock:
                if self.runtime.attempted >= max_applications:
                    return

            try:
                key = self.queue.get_nowait()
            except asyncio.QueueEmpty:
                return

            job = self.jobs[key]
            worker.state = "busy"
            worker.job_key = key
            async with self._lock:
                self.runtime.attempted += 1
                self._transition(job, worker_id, "loading", "Worker assigned")

            context = await browser.new_context(viewport={"width": 1280, "height": 900})
            page = await context.new_page()

            try:
                async with self._lock:
                    self._transition(job, worker_id, "filling", "Preparing form for manual submit")

                prep = await self.applier.prepare_until_submit_async(page, job.payload)
                watch_status = "failed_validation"
                watch_details = "review_required_timeout"
                watch_applied = False

                if prep.status in {"blocked_captcha", "blocked_login"} and self.blocked_flow_mode == "pause_for_manual_solve":
                    async with self._lock:
                        self._transition(job, worker_id, "paused_review", f"Blocked pre-submit ({prep.status}); awaiting manual solve")
                    if self.atlas_sync:
                        self.atlas_sync.sync_paused_job(
                            worker_id,
                            key,
                            str(job.payload.get("apply_url") or job.payload.get("url") or ""),
                            job.provider,
                        )

                    worker.state = "blocked"
                    watch = await self.applier.watch_manual_submit_async(
                        page,
                        timeout_s=self.submit_timeout_s,
                        allow_blocked_recovery=True,
                    )
                    watch_status = watch.status
                    watch_details = watch.details
                    watch_applied = watch.applied
                elif prep.status in {"blocked_captcha", "blocked_login", "failed_validation", "error"}:
                    watch_status = prep.status
                    watch_details = prep.details
                    watch_applied = False
                else:
                    async with self._lock:
                        pause_msg = "Prepared for auto submit" if self.submit_mode == "full_auto" else "Waiting for manual submit"
                        self._transition(job, worker_id, "paused_review", pause_msg)

                    if self.atlas_sync:
                        self.atlas_sync.sync_paused_job(
                            worker_id,
                            key,
                            str(job.payload.get("apply_url") or job.payload.get("url") or ""),
                            job.provider,
                        )

                    if self.submit_mode == "full_auto":
                        clicked = await self.applier.click_submit_async(page)
                        if not clicked:
                            watch_status = "failed_validation"
                            watch_details = "Unable to locate submit control for full_auto"
                            watch_applied = False
                        else:
                            watch_result = await self.applier.watch_manual_submit_async(
                                page,
                                timeout_s=min(90, self.submit_timeout_s),
                            )
                            watch_status = watch_result.status
                            watch_details = watch_result.details
                            watch_applied = watch_result.applied
                    elif self.submit_mode == "draft_only":
                        watch_status = "failed_validation"
                        watch_details = "Draft mode: prepared without submission"
                        watch_applied = False
                    else:
                        worker.state = "paused"
                        watch = await self.applier.watch_manual_submit_async(
                            page,
                            timeout_s=self.submit_timeout_s,
                            allow_blocked_recovery=(self.blocked_flow_mode == "pause_for_manual_solve"),
                        )
                        watch_status = watch.status
                        watch_details = watch.details
                        watch_applied = watch.applied
                evidence = None
                if not watch_applied:
                    evidence = await self.applier.capture_evidence_async(page, self.failures_dir, job.provider, watch_status)

                async with self._lock:
                    status = self._record_terminal_result(
                        job=job,
                        worker_id=worker_id,
                        key=key,
                        status=watch_status,
                        details=watch_details,
                        applied=watch_applied,
                        evidence=evidence,
                    )

                if self.atlas_sync:
                    self.atlas_sync.sync_completed_job(key, status)

            except Exception as exc:
                evidence = await self.applier.capture_evidence_async(page, self.failures_dir, job.provider, "error")
                async with self._lock:
                    self._transition(job, worker_id, "error", str(exc), evidence)
                    self.runtime.errors += 1
                    self.results.append(
                        {
                            "idempotency_key": key,
                            "provider": job.provider,
                            "status": "error",
                            "details": str(exc),
                            "applied": False,
                            "url": job.payload.get("apply_url") or job.payload.get("url"),
                            "evidence": evidence,
                        }
                    )
            finally:
                worker.state = "idle"
                worker.job_key = None
                await context.close()
                self.queue.task_done()
                self._save_state()

    async def run(self, max_applications: int) -> Dict[str, Any]:
        if async_playwright is None:
            raise RuntimeError("Playwright async API is not available")

        self._bootstrap_jobs()
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            try:
                tasks = [
                    asyncio.create_task(self._worker_loop(worker_id, browser, max_applications))
                    for worker_id in range(self.workers)
                ]
                await asyncio.gather(*tasks)
            finally:
                await browser.close()

        self._save_state()
        return {
            "attempted": self.runtime.attempted,
            "applied": self.runtime.applied,
            "blocked": self.runtime.blocked,
            "errors": self.runtime.errors,
            "review_required": self.runtime.review_required,
            "results": self.results,
        }
