"""
Job Auto-Apply Engine (Playwright)
Automates job applications with sync and async workflows.
"""

from __future__ import annotations

import asyncio
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from utils.profile import Profile, get_profile

try:
    from playwright.async_api import Page as AsyncPage
    from playwright.async_api import TimeoutError as AsyncPlaywrightTimeoutError
except Exception:  # pragma: no cover - optional dependency
    AsyncPage = Any
    AsyncPlaywrightTimeoutError = Exception

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover - optional dependency
    sync_playwright = None
    PlaywrightTimeoutError = Exception

SubmitMode = Literal["human_verified", "full_auto", "draft_only"]


@dataclass
class ApplyResult:
    status: str
    details: str
    applied: bool
    provider: str = "generic"
    evidence: Optional[Dict[str, str]] = None


class JobAutoApplier:
    """Playwright-based job auto-apply engine."""

    VALID_STATUSES = {
        "applied",
        "review_required",
        "blocked_captcha",
        "blocked_login",
        "failed_validation",
        "error",
    }

    SUCCESS_PATTERNS = [
        "application submitted",
        "thank you for applying",
        "thanks for applying",
        "application received",
        "we've received your application",
    ]

    SUCCESS_URL_TOKENS = [
        "thank",
        "submitted",
        "application-confirmation",
        "confirmation",
        "success",
    ]

    def __init__(
        self,
        profile: Optional[Profile] = None,
        submit_mode: SubmitMode = "human_verified",
        max_steps_per_job: int = 6,
        required_confirmation_selector: Optional[str] = None,
    ):
        self.profile = profile or get_profile()
        self.user_data_dir = os.getenv("PLAYWRIGHT_USER_DATA_DIR", "output/playwright/profile")
        self.headless = os.getenv("PLAYWRIGHT_HEADLESS", "false").lower() == "true"
        self.resume_paths = [p for p in self.profile.resume_paths() if p]
        self.submit_mode = submit_mode
        self.max_steps_per_job = max_steps_per_job
        self.required_confirmation_selector = required_confirmation_selector

    def apply(
        self,
        job: Dict[str, Any],
        *,
        submit_mode: Optional[SubmitMode] = None,
        max_steps_per_job: Optional[int] = None,
        required_confirmation_selector: Optional[str] = None,
        artifacts_dir: str = "output/playwright/failures",
    ) -> ApplyResult:
        if sync_playwright is None:
            return ApplyResult(status="error", details="Playwright is not installed.", applied=False)

        mode = submit_mode or self.submit_mode
        max_steps = max_steps_per_job or self.max_steps_per_job
        confirm_selector = (
            required_confirmation_selector
            if required_confirmation_selector is not None
            else self.required_confirmation_selector
        )

        if mode not in {"human_verified", "full_auto", "draft_only"}:
            return ApplyResult(status="failed_validation", details=f"Invalid submit mode: {mode}", applied=False)

        apply_url = job.get("apply_url") or job.get("url")
        if not apply_url:
            return ApplyResult(status="failed_validation", details="Missing apply URL", applied=False)

        resume_override = job.get("resume_path")
        cover_letter_override = job.get("cover_letter_path")
        resolved_resume = self._resolve_resume_path(resume_override)
        if not resolved_resume:
            return ApplyResult(
                status="failed_validation",
                details="No valid resume path available for upload.",
                applied=False,
            )

        provider = self._detect_provider(apply_url)
        page = None
        context = None
        with sync_playwright() as p:
            try:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=self.user_data_dir,
                    headless=self.headless,
                    viewport={"width": 1280, "height": 900},
                )
                page = context.new_page()
                page.goto(apply_url, wait_until="domcontentloaded", timeout=60000)
                time.sleep(2)

                blocked = self._detect_blockers_text(page.content())
                if blocked:
                    evidence = self._capture_evidence(page, artifacts_dir, provider, blocked)
                    return ApplyResult(
                        status=blocked,
                        details="Blocked by login/captcha/verification challenge",
                        applied=False,
                        provider=provider,
                        evidence=evidence,
                    )

                self._fill_for_provider_sync(
                    page,
                    provider,
                    resume_override=resolved_resume,
                    cover_letter_override=cover_letter_override,
                )

                status, details, applied = self._attempt_submit(
                    page,
                    mode=mode,
                    max_steps=max_steps,
                    required_confirmation_selector=confirm_selector,
                )
                evidence = None
                if not applied:
                    evidence = self._capture_evidence(page, artifacts_dir, provider, status)
                return ApplyResult(
                    status=status,
                    details=details,
                    applied=applied,
                    provider=provider,
                    evidence=evidence,
                )

            except PlaywrightTimeoutError:
                evidence = self._capture_evidence(page, artifacts_dir, provider, "error") if page else None
                return ApplyResult(
                    status="review_required",
                    details="Page load timed out",
                    applied=False,
                    provider=provider,
                    evidence=evidence,
                )
            except Exception as e:
                evidence = self._capture_evidence(page, artifacts_dir, provider, "error") if page else None
                return ApplyResult(
                    status="error",
                    details=str(e),
                    applied=False,
                    provider=provider,
                    evidence=evidence,
                )
            finally:
                if context is not None:
                    context.close()

    def prepare_until_submit(
        self,
        job: Dict[str, Any],
        *,
        artifacts_dir: str = "output/playwright/failures",
    ) -> ApplyResult:
        """Prepare a single application up to final submit button (sync path)."""
        if sync_playwright is None:
            return ApplyResult(status="error", details="Playwright is not installed.", applied=False)

        apply_url = job.get("apply_url") or job.get("url")
        if not apply_url:
            return ApplyResult(status="failed_validation", details="Missing apply URL", applied=False)

        provider = self._detect_provider(apply_url)
        resume_override = job.get("resume_path")
        cover_letter_override = job.get("cover_letter_path")
        resolved_resume = self._resolve_resume_path(resume_override)
        if not resolved_resume:
            return ApplyResult(status="failed_validation", details="No valid resume path available.", applied=False)

        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.user_data_dir,
                headless=self.headless,
                viewport={"width": 1280, "height": 900},
            )
            page = context.new_page()
            try:
                page.goto(apply_url, wait_until="domcontentloaded", timeout=60000)
                time.sleep(2)
                blocked = self._detect_blockers_text(page.content())
                if blocked:
                    evidence = self._capture_evidence(page, artifacts_dir, provider, blocked)
                    return ApplyResult(blocked, "Blocked by login/captcha/verification challenge", False, provider, evidence)

                self._fill_for_provider_sync(
                    page,
                    provider,
                    resume_override=resolved_resume,
                    cover_letter_override=cover_letter_override,
                )

                submit_control = self._find_submit_button(page)
                if submit_control is None:
                    return ApplyResult("failed_validation", "Unable to locate submit control", False, provider)
                return ApplyResult("review_required", "Prepared and paused for manual submit", False, provider)
            except PlaywrightTimeoutError:
                evidence = self._capture_evidence(page, artifacts_dir, provider, "error")
                return ApplyResult("review_required", "Page load timed out", False, provider, evidence)
            except Exception as exc:
                evidence = self._capture_evidence(page, artifacts_dir, provider, "error")
                return ApplyResult("error", str(exc), False, provider, evidence)
            finally:
                context.close()

    def watch_manual_submit(
        self,
        page,
        timeout_s: int = 300,
        *,
        allow_blocked_recovery: bool = False,
    ) -> ApplyResult:
        """Sync watcher that detects manual submit and optional blocked-page recovery."""
        initial_url = ""
        try:
            initial_url = page.url
        except Exception:
            initial_url = ""

        end_at = time.time() + max(1, timeout_s)
        blocked_reason: Optional[str] = None
        while time.time() < end_at:
            try:
                if self._is_submission_success(page.url, page.content(), initial_url):
                    return ApplyResult("applied", "Manual submit detected", True)
                blocked = self._detect_blockers_text(page.content())
                if blocked:
                    if allow_blocked_recovery:
                        blocked_reason = blocked
                    else:
                        return ApplyResult(blocked, "Blocked during manual review", False)
            except Exception:
                pass
            time.sleep(2)

        if blocked_reason:
            return ApplyResult(blocked_reason, "manual_unblock_timeout", False)
        return ApplyResult("failed_validation", "review_required_timeout", False)

    async def prepare_until_submit_async(
        self,
        page: AsyncPage,
        job: Dict[str, Any],
    ) -> ApplyResult:
        """Prepare an async page up to final submit control for manual review."""
        apply_url = job.get("apply_url") or job.get("url")
        if not apply_url:
            return ApplyResult("failed_validation", "Missing apply URL", False)

        provider = self._detect_provider(apply_url)
        resume_override = job.get("resume_path")
        cover_letter_override = job.get("cover_letter_path")
        resolved_resume = self._resolve_resume_path(resume_override)
        if not resolved_resume:
            return ApplyResult("failed_validation", "No valid resume path available.", False, provider)

        try:
            await page.goto(apply_url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(1500)

            html = await page.content()
            blocked = self._detect_blockers_text(html)
            if blocked:
                return ApplyResult(blocked, "Blocked by login/captcha/verification challenge", False, provider)

            await self._fill_for_provider_async(
                page,
                provider,
                resume_override=resolved_resume,
                cover_letter_override=cover_letter_override,
            )

            submit_ready = await self._find_submit_button_async(page)
            if not submit_ready:
                return ApplyResult("failed_validation", "Unable to locate submit control", False, provider)
            return ApplyResult("review_required", "Prepared and paused for manual submit", False, provider)

        except AsyncPlaywrightTimeoutError:
            return ApplyResult("review_required", "Page load timed out", False, provider)
        except Exception as exc:
            return ApplyResult("error", str(exc), False, provider)

    async def watch_manual_submit_async(
        self,
        page: AsyncPage,
        timeout_s: int = 300,
        *,
        allow_blocked_recovery: bool = False,
    ) -> ApplyResult:
        """Async watcher for user submit completion with optional blocked-flow recovery."""
        try:
            initial_url = page.url
        except Exception:
            initial_url = ""

        end_at = time.time() + max(1, timeout_s)
        blocked_reason: Optional[str] = None
        while time.time() < end_at:
            try:
                current_url = page.url
                html = await page.content()
                if self._is_submission_success(current_url, html, initial_url):
                    return ApplyResult("applied", "Manual submit detected", True)
                blocked = self._detect_blockers_text(html)
                if blocked:
                    if allow_blocked_recovery:
                        blocked_reason = blocked
                    else:
                        return ApplyResult(blocked, "Blocked during manual review", False)
            except Exception:
                pass
            await asyncio.sleep(2)

        if blocked_reason:
            return ApplyResult(blocked_reason, "manual_unblock_timeout", False)
        return ApplyResult("failed_validation", "review_required_timeout", False)

    def _resolve_resume_path(self, resume_override: Optional[str]) -> Optional[str]:
        for path in [resume_override, *self.resume_paths]:
            if path and os.path.exists(path):
                return path
        return None

    def _detect_provider(self, url: str) -> str:
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
        return "generic"

    def _detect_blockers_text(self, text: str) -> Optional[str]:
        content = (text or "").lower()
        captcha_patterns = ["captcha", "hcaptcha", "recaptcha", "verify you are human"]
        login_patterns = [
            "sign in",
            "log in",
            "login",
            "two-factor",
            "2fa",
            "verification code",
            "one-time password",
            "authentication required",
            "verify your identity",
        ]

        if any(p in content for p in captcha_patterns):
            return "blocked_captcha"
        if any(p in content for p in login_patterns):
            return "blocked_login"
        return None

    def _detect_blockers(self, page) -> Optional[str]:
        """Backward-compatible wrapper used by older tests/callers."""
        try:
            return self._detect_blockers_text(page.content())
        except Exception:
            return None

    def _fill_for_provider_sync(
        self,
        page,
        provider: str,
        *,
        resume_override: Optional[str],
        cover_letter_override: Optional[str],
    ) -> None:
        self._fill_common_fields(page)

        if provider == "greenhouse":
            for selector, value in [
                ('input[name="first_name"]', self._profile_values().get("First Name", "")),
                ('input[name="last_name"]', self._profile_values().get("Last Name", "")),
                ('input[name="email"]', self._profile_values().get("Email", "")),
                ('input[name="phone"]', self._profile_values().get("Phone", "")),
            ]:
                self._fill_selector_sync(page, selector, value)
        elif provider == "lever":
            for selector, value in [
                ('input[name="name"]', self._profile_values().get("Full Name", "")),
                ('input[name="email"]', self._profile_values().get("Email", "")),
                ('input[name="phone"]', self._profile_values().get("Phone", "")),
            ]:
                self._fill_selector_sync(page, selector, value)
        elif provider == "ashby":
            for selector, value in [
                ('input[aria-label*="First"]', self._profile_values().get("First Name", "")),
                ('input[aria-label*="Last"]', self._profile_values().get("Last Name", "")),
                ('input[aria-label*="Email"]', self._profile_values().get("Email", "")),
                ('input[aria-label*="Phone"]', self._profile_values().get("Phone", "")),
            ]:
                self._fill_selector_sync(page, selector, value)
        elif provider == "linkedin":
            self._prepare_linkedin_easy_apply_sync(page)

        self._upload_resume(page, resume_override=resume_override, cover_letter_override=cover_letter_override)
        self._fill_cover_letter(page)

    async def _fill_for_provider_async(
        self,
        page: AsyncPage,
        provider: str,
        *,
        resume_override: Optional[str],
        cover_letter_override: Optional[str],
    ) -> None:
        await self._fill_common_fields_async(page)

        if provider == "greenhouse":
            for selector, value in [
                ('input[name="first_name"]', self._profile_values().get("First Name", "")),
                ('input[name="last_name"]', self._profile_values().get("Last Name", "")),
                ('input[name="email"]', self._profile_values().get("Email", "")),
                ('input[name="phone"]', self._profile_values().get("Phone", "")),
            ]:
                await self._fill_selector_async(page, selector, value)
        elif provider == "lever":
            for selector, value in [
                ('input[name="name"]', self._profile_values().get("Full Name", "")),
                ('input[name="email"]', self._profile_values().get("Email", "")),
                ('input[name="phone"]', self._profile_values().get("Phone", "")),
            ]:
                await self._fill_selector_async(page, selector, value)
        elif provider == "ashby":
            for selector, value in [
                ('input[aria-label*="First"]', self._profile_values().get("First Name", "")),
                ('input[aria-label*="Last"]', self._profile_values().get("Last Name", "")),
                ('input[aria-label*="Email"]', self._profile_values().get("Email", "")),
                ('input[aria-label*="Phone"]', self._profile_values().get("Phone", "")),
            ]:
                await self._fill_selector_async(page, selector, value)
        elif provider == "linkedin":
            await self._prepare_linkedin_easy_apply_async(page)

        await self._upload_resume_async(page, resume_override=resume_override, cover_letter_override=cover_letter_override)
        await self._fill_cover_letter_async(page)

    def _fill_selector_sync(self, page, selector: str, value: str) -> None:
        if not value:
            return
        try:
            page.locator(selector).first.fill(value)
        except Exception:
            pass

    async def _fill_selector_async(self, page: AsyncPage, selector: str, value: str) -> None:
        if not value:
            return
        try:
            locator = page.locator(selector).first
            await locator.fill(value)
        except Exception:
            pass

    def _prepare_linkedin_easy_apply_sync(self, page) -> None:
        try:
            btn = page.get_by_role("button", name="Easy Apply", exact=False)
            if btn.count() > 0:
                btn.first.click()
                time.sleep(1.5)
        except Exception:
            pass

    async def _prepare_linkedin_easy_apply_async(self, page: AsyncPage) -> None:
        try:
            btn = page.get_by_role("button", name="Easy Apply", exact=False)
            if await btn.count() > 0:
                await btn.first.click()
                await page.wait_for_timeout(1200)
        except Exception:
            pass

    def _fill_common_fields(self, page) -> None:
        values = self._profile_values()
        for label, value in values.items():
            if not value:
                continue
            try:
                page.get_by_label(label, exact=False).fill(value)
                continue
            except Exception:
                pass
            try:
                page.get_by_placeholder(label, exact=False).fill(value)
            except Exception:
                continue

    async def _fill_common_fields_async(self, page: AsyncPage) -> None:
        values = self._profile_values()
        for label, value in values.items():
            if not value:
                continue
            try:
                await page.get_by_label(label, exact=False).fill(value)
                continue
            except Exception:
                pass
            try:
                await page.get_by_placeholder(label, exact=False).fill(value)
            except Exception:
                continue

    def _upload_resume(self, page, resume_override: Optional[str] = None, cover_letter_override: Optional[str] = None) -> None:
        resume_path = self._resolve_resume_path(resume_override)
        file_inputs = page.locator('input[type="file"]')
        try:
            input_count = file_inputs.count()
        except Exception:
            return
        if input_count == 0:
            return
        if resume_path:
            try:
                file_inputs.first.set_input_files(resume_path)
            except Exception:
                pass
        if cover_letter_override and os.path.exists(cover_letter_override) and input_count > 1:
            try:
                file_inputs.nth(1).set_input_files(cover_letter_override)
            except Exception:
                pass

    async def _upload_resume_async(
        self,
        page: AsyncPage,
        resume_override: Optional[str] = None,
        cover_letter_override: Optional[str] = None,
    ) -> None:
        resume_path = self._resolve_resume_path(resume_override)
        file_inputs = page.locator('input[type="file"]')
        try:
            input_count = await file_inputs.count()
        except Exception:
            return
        if input_count == 0:
            return
        if resume_path:
            try:
                await file_inputs.first.set_input_files(resume_path)
            except Exception:
                pass
        if cover_letter_override and os.path.exists(cover_letter_override) and input_count > 1:
            try:
                await file_inputs.nth(1).set_input_files(cover_letter_override)
            except Exception:
                pass

    def _fill_cover_letter(self, page) -> None:
        cover_text = (
            "Hello,\n\n"
            "I am interested in this internship opportunity and believe my experience in software "
            "engineering and data systems would be a strong fit. I would welcome the chance to discuss "
            "how I can contribute to your team.\n\n"
            f"Best regards,\n{self.profile.get('name', '')}"
        )
        try:
            page.get_by_label("Cover Letter", exact=False).fill(cover_text)
        except Exception:
            pass
        try:
            page.get_by_placeholder("Cover Letter", exact=False).fill(cover_text)
        except Exception:
            pass

    async def _fill_cover_letter_async(self, page: AsyncPage) -> None:
        cover_text = (
            "Hello,\n\n"
            "I am interested in this internship opportunity and believe my experience in software "
            "engineering and data systems would be a strong fit. I would welcome the chance to discuss "
            "how I can contribute to your team.\n\n"
            f"Best regards,\n{self.profile.get('name', '')}"
        )
        try:
            await page.get_by_label("Cover Letter", exact=False).fill(cover_text)
        except Exception:
            pass
        try:
            await page.get_by_placeholder("Cover Letter", exact=False).fill(cover_text)
        except Exception:
            pass

    def _find_submit_button(self, page):
        button_texts = ["Submit", "Apply", "Send Application", "Send", "Finish", "Submit Application", "Submit application"]
        for text in button_texts:
            try:
                button = page.get_by_role("button", name=text, exact=False)
                if button.count() > 0:
                    return button.first
            except Exception:
                continue
        try:
            submit_input = page.locator('button[type="submit"], input[type="submit"]')
            if submit_input.count() > 0:
                return submit_input.first
        except Exception:
            pass
        return None

    async def _find_submit_button_async(self, page: AsyncPage) -> bool:
        button_texts = ["Submit", "Apply", "Send Application", "Send", "Finish", "Submit Application", "Submit application"]
        for text in button_texts:
            try:
                button = page.get_by_role("button", name=text, exact=False)
                if await button.count() > 0:
                    return True
            except Exception:
                continue
        try:
            submit_input = page.locator('button[type="submit"], input[type="submit"]')
            if await submit_input.count() > 0:
                return True
        except Exception:
            pass
        return False

    async def click_submit_async(self, page: AsyncPage) -> bool:
        button_texts = ["Submit", "Apply", "Send Application", "Send", "Finish", "Submit Application", "Submit application"]
        for text in button_texts:
            try:
                button = page.get_by_role("button", name=text, exact=False)
                if await button.count() > 0:
                    await button.first.click()
                    await page.wait_for_timeout(1200)
                    return True
            except Exception:
                continue
        try:
            submit_input = page.locator('button[type="submit"], input[type="submit"]')
            if await submit_input.count() > 0:
                await submit_input.first.click()
                await page.wait_for_timeout(1200)
                return True
        except Exception:
            pass
        return False

    def _find_next_button(self, page):
        for text in ["Next", "Continue"]:
            try:
                button = page.get_by_role("button", name=text, exact=False)
                if button.count() > 0:
                    return button.first
            except Exception:
                continue
        return None

    def _is_confirmation_satisfied(self, page, selector: Optional[str]) -> bool:
        if not selector:
            return False
        try:
            confirmation = page.locator(selector)
            if confirmation.count() == 0:
                return False
            element = confirmation.first
            if element.is_checked():
                return True
            if element.is_enabled() and element.is_visible():
                return True
        except Exception:
            return False
        return False

    def _attempt_submit(self, page, *, mode: SubmitMode, max_steps: int, required_confirmation_selector: Optional[str]) -> tuple[str, str, bool]:
        bounded_steps = max(1, max_steps)

        for step in range(bounded_steps):
            blocked = self._detect_blockers(page)
            if blocked:
                return blocked, "Blocked by login/captcha/verification challenge", False

            submit_control = self._find_submit_button(page)
            if submit_control is not None:
                if mode == "draft_only":
                    return "review_required", "Draft mode: form prepared without submission", False
                if mode == "human_verified":
                    if required_confirmation_selector:
                        if self._is_confirmation_satisfied(page, required_confirmation_selector):
                            submit_control.click()
                            time.sleep(2)
                            return "applied", "Submitted after confirmation selector check", True
                        return "review_required", f"Waiting for confirmation selector before submit: {required_confirmation_selector}", False
                    return "review_required", "Human-verified mode: review before final submit", False

                submit_control.click()
                time.sleep(2)
                return "applied", "Submitted via Playwright", True

            if mode == "draft_only":
                return "failed_validation", "Unable to locate submit control", False

            next_button = self._find_next_button(page)
            if next_button is None:
                return "failed_validation", "Unable to locate submit control", False

            try:
                next_button.click()
                time.sleep(2)
            except Exception:
                return "failed_validation", "Failed to advance multi-step form", False

            if step + 1 >= bounded_steps:
                return "failed_validation", "Exceeded max_steps_per_job before reaching submit", False

        return "failed_validation", "Unable to locate submit control", False

    def _is_submission_success(self, current_url: str, html: str, initial_url: str = "") -> bool:
        url = (current_url or "").lower()
        base_url_changed = bool(initial_url) and (url != (initial_url or "").lower())
        if any(token in url for token in self.SUCCESS_URL_TOKENS) and (base_url_changed or not initial_url):
            return True

        text = (html or "").lower()
        if any(pattern in text for pattern in self.SUCCESS_PATTERNS):
            return True

        return False

    def _capture_evidence(self, page, artifacts_dir: str, provider: str, status: str) -> Optional[Dict[str, str]]:
        if page is None:
            return None
        try:
            out_dir = Path(artifacts_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            safe_provider = re.sub(r"[^a-zA-Z0-9_-]", "_", provider)
            safe_status = re.sub(r"[^a-zA-Z0-9_-]", "_", status)
            base = f"{stamp}_{safe_provider}_{safe_status}"
            screenshot_path = out_dir / f"{base}.png"
            html_path = out_dir / f"{base}.html"
            page.screenshot(path=str(screenshot_path), full_page=True)
            html_path.write_text(page.content(), encoding="utf-8")
            return {"screenshot": str(screenshot_path), "html": str(html_path)}
        except Exception:
            return None

    async def capture_evidence_async(
        self,
        page: AsyncPage,
        artifacts_dir: str,
        provider: str,
        status: str,
    ) -> Optional[Dict[str, str]]:
        try:
            out_dir = Path(artifacts_dir)
            out_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            safe_provider = re.sub(r"[^a-zA-Z0-9_-]", "_", provider)
            safe_status = re.sub(r"[^a-zA-Z0-9_-]", "_", status)
            base = f"{stamp}_{safe_provider}_{safe_status}"
            screenshot_path = out_dir / f"{base}.png"
            html_path = out_dir / f"{base}.html"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            html = await page.content()
            html_path.write_text(html, encoding="utf-8")
            return {"screenshot": str(screenshot_path), "html": str(html_path)}
        except Exception:
            return None

    def _profile_values(self) -> Dict[str, str]:
        name = self.profile.get("name", "")
        first_name = name.split()[0] if name else ""
        last_name = name.split()[-1] if len(name.split()) > 1 else ""

        return {
            "First Name": first_name,
            "Last Name": last_name,
            "Full Name": name,
            "Name": name,
            "Email": self.profile.get("email", ""),
            "Phone": self.profile.get("phone", ""),
            "Location": self.profile.get("location", ""),
            "LinkedIn": self.profile.get("linkedin", ""),
            "GitHub": self.profile.get("github", ""),
            "Portfolio": self.profile.get("portfolio", ""),
            "Website": self.profile.get("portfolio", ""),
        }
