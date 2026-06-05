import re

from core.anti_templating_engine import AntiTemplatingEngine


def test_email_sanitization_removes_academic_phrasing():
    engine = AntiTemplatingEngine()
    subject, html = engine.generate_html_email(
        contact_name="Alex",
        company="Example Corp",
        focus_area="Software Engineering",
        ai_personalization={
            "opening_hook": "I'm The Software Engineering opportunity at Example Corp is compelling.",
            "connection_paragraph": "Professor Smith's lab work inspires me.",
            "research_mention": "Professor Smith's lab research is impressive.",
            "why_fit": "My lab experience is relevant.",
        },
        seed="sanitize_test",
    )

    text = re.sub(r"<[^>]+>", "", html).lower()
    # Check for academic phrasing as whole words, not substrings
    assert not re.search(r"\bprofessor\b", text), "Found 'professor' in text"
    assert not re.search(r"\blab\b", text), "Found 'lab' as standalone word in text"
    assert "i'm the" not in text


def test_strict_template_content(monkeypatch, tmp_path):
    from core.email_system import EmailSystem
    from core.database_manager import get_job_discovery_db
    import importlib
    config_module = importlib.import_module("utils.config")

    # Force strict template mode
    monkeypatch.setenv("EMAIL_STRICT_TEMPLATE", "true")
    config_module.config.EMAIL_STRICT_TEMPLATE = True
    config_module.config.JOBS_DB_PATH = str(tmp_path / "jobs.db")
    config_module.config.DEFAULT_ROLE_TITLE = "Software Engineering Intern"

    db = get_job_discovery_db(config_module.config.JOBS_DB_PATH)
    db.insert(
        "jobs",
        {
            "source": "test",
            "source_id": "1",
            "company": "Acme",
            "title": "Software Engineering Intern",
            "location": "Remote",
            "location_type": "remote",
            "url": "https://careers.acme.com/jobs/123",
            "apply_url": "https://careers.acme.com/jobs/123",
            "description": "Looking for interns with Python and SQL experience plus CI/CD.",
            "employment_type": "Internship",
            "posted_at": "2026-01-01",
            "season_match": 1,
            "visa_sponsorship": 0,
            "relocation_support": 0,
            "score": 0.9,
            "metadata": "{}",
        },
    )

    system = EmailSystem()
    subject, html, _ = system.generate_personalized_email(
        contact_name="Alex",
        email="alex@acme.com",
        company="acme.com",
        position="Software Engineering",
        use_ai=True,
    )

    text = re.sub(r"<[^>]+>", "", html).lower()
    # Check for academic phrasing as whole words
    assert not re.search(r"\bprofessor\b", text), "Found 'professor' in text"
    assert not re.search(r"\bresearch\b", text), "Found 'research' as standalone word in text"
    assert not re.search(r"\blab\b", text), "Found 'lab' as standalone word in text"
    assert "i'm the" not in text
    assert "why me for this role" in text
    assert "noticed the posting emphasizes python" in text
    assert "sql" in text
    # Ensure bullet list exists in HTML
    assert "<ul>" in html and "</ul>" in html
    assert "software engineering intern" in subject.lower()

    # Reset for other tests
    config_module.config.EMAIL_STRICT_TEMPLATE = False
