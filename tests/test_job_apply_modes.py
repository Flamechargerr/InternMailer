from core.job_apply import JobAutoApplier


class _FakeControl:
    def __init__(self):
        self.clicked = 0

    def click(self):
        self.clicked += 1


class _FakeWatchPage:
    def __init__(self, html_steps, url="https://jobs.example.com/form"):
        self._steps = list(html_steps)
        self.url = url
        self._idx = 0

    def content(self):
        idx = min(self._idx, len(self._steps) - 1)
        html = self._steps[idx]
        self._idx += 1
        return html


def test_provider_detection():
    applier = JobAutoApplier()
    assert applier._detect_provider("https://boards.greenhouse.io/acme/jobs/1") == "greenhouse"
    assert applier._detect_provider("https://jobs.lever.co/acme/123") == "lever"
    assert applier._detect_provider("https://jobs.ashbyhq.com/acme/123") == "ashby"
    assert applier._detect_provider("https://www.example.com/jobs/123") == "generic"


def test_submit_mode_draft_only_never_submits(monkeypatch):
    applier = JobAutoApplier()
    control = _FakeControl()

    monkeypatch.setattr(applier, "_detect_blockers", lambda page: None)
    monkeypatch.setattr(applier, "_find_submit_button", lambda page: control)

    status, details, applied = applier._attempt_submit(
        page=object(),
        mode="draft_only",
        max_steps=3,
        required_confirmation_selector=None,
    )

    assert status == "review_required"
    assert not applied
    assert control.clicked == 0
    assert "Draft mode" in details


def test_submit_mode_human_verified_requires_confirmation(monkeypatch):
    applier = JobAutoApplier()
    control = _FakeControl()

    monkeypatch.setattr(applier, "_detect_blockers", lambda page: None)
    monkeypatch.setattr(applier, "_find_submit_button", lambda page: control)
    monkeypatch.setattr(applier, "_is_confirmation_satisfied", lambda page, selector: False)

    status, details, applied = applier._attempt_submit(
        page=object(),
        mode="human_verified",
        max_steps=3,
        required_confirmation_selector="#confirm-submit",
    )

    assert status == "review_required"
    assert not applied
    assert control.clicked == 0
    assert "confirmation selector" in details


def test_submit_mode_full_auto_clicks_submit(monkeypatch):
    applier = JobAutoApplier()
    control = _FakeControl()

    monkeypatch.setattr(applier, "_detect_blockers", lambda page: None)
    monkeypatch.setattr(applier, "_find_submit_button", lambda page: control)

    status, details, applied = applier._attempt_submit(
        page=object(),
        mode="full_auto",
        max_steps=3,
        required_confirmation_selector=None,
    )

    assert status == "applied"
    assert applied
    assert control.clicked == 1
    assert "Submitted" in details


def test_submit_mode_fails_when_no_submit_and_no_next(monkeypatch):
    applier = JobAutoApplier()

    monkeypatch.setattr(applier, "_detect_blockers", lambda page: None)
    monkeypatch.setattr(applier, "_find_submit_button", lambda page: None)
    monkeypatch.setattr(applier, "_find_next_button", lambda page: None)

    status, details, applied = applier._attempt_submit(
        page=object(),
        mode="full_auto",
        max_steps=2,
        required_confirmation_selector=None,
    )

    assert status == "failed_validation"
    assert not applied
    assert "submit control" in details


def test_submission_success_heuristics():
    applier = JobAutoApplier()
    assert applier._is_submission_success(
        "https://jobs.example.com/application/thank-you",
        "<html></html>",
        "https://jobs.example.com/application/form",
    )
    assert applier._is_submission_success(
        "https://jobs.example.com/application/form",
        "<html>Thank you for applying</html>",
        "https://jobs.example.com/application/form",
    )


def test_watch_manual_submit_allows_blocked_recovery(monkeypatch):
    applier = JobAutoApplier()
    page = _FakeWatchPage(
        [
            "<html>please complete captcha</html>",
            "<html>thank you for applying</html>",
        ]
    )

    ticks = iter([0.0, 0.1, 0.2, 0.3, 0.4])
    monkeypatch.setattr("core.job_apply.time.time", lambda: next(ticks, 10.0))
    monkeypatch.setattr("core.job_apply.time.sleep", lambda _seconds: None)

    result = applier.watch_manual_submit(page, timeout_s=5, allow_blocked_recovery=True)
    assert result.status == "applied"
    assert result.applied is True
