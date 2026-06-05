import re


def test_role_resolution_uses_job_title(monkeypatch, tmp_path):
    from core.email_system import EmailSystem
    from core.database_manager import get_job_discovery_db
    import importlib

    config_module = importlib.import_module("utils.config")
    monkeypatch.setenv("EMAIL_STRICT_TEMPLATE", "true")
    config_module.config.EMAIL_STRICT_TEMPLATE = True
    config_module.config.JOBS_DB_PATH = str(tmp_path / "jobs.db")
    config_module.config.DEFAULT_ROLE_TITLE = "Software Engineering Intern"

    db = get_job_discovery_db(config_module.config.JOBS_DB_PATH)
    db.insert(
        "jobs",
        {
            "source": "test",
            "source_id": "2",
            "company": "Nvidia",
            "title": "Software Engineering Intern",
            "location": "Remote",
            "location_type": "remote",
            "url": "https://nvidia.com/careers/123",
            "apply_url": "https://nvidia.com/careers/123",
            "description": "Work on Python and data pipelines.",
            "employment_type": "Internship",
            "posted_at": "2026-01-10",
            "season_match": 1,
            "visa_sponsorship": 0,
            "relocation_support": 0,
            "score": 0.8,
            "metadata": "{}",
        },
    )

    system = EmailSystem()
    subject, html, _ = system.generate_personalized_email(
        contact_name="Ava",
        email="ava@nvidia.com",
        company="nvidia.com",
        position="HR Business Partner",
        use_ai=False,
    )

    assert "software engineering intern" in subject.lower()
    assert "hr business partner" not in subject.lower()

    text = re.sub(r"<[^>]+>", "", html).lower()
    assert "software engineering intern" in text

    config_module.config.EMAIL_STRICT_TEMPLATE = False


def test_keyword_extraction_selects_expected():
    from core.email_system import EmailSystem

    system = EmailSystem()
    keywords = system._extract_job_keywords(
        "Looking for candidates with Python, SQL, and CI/CD experience."
    )
    assert "python" in keywords
    assert "sql" in keywords
