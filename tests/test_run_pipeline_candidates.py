import importlib.util


def _load_module(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_build_candidates_includes_linkedin_and_filters():
    module = _load_module(
        "/Users/anamay/Desktop/Projects/internmailer_v3/scripts/run_apply_pipeline.py",
        "run_apply_pipeline_candidates",
    )
    jobs = [
        {
            "company": "Acme",
            "title": "SDE Intern",
            "location": "India",
            "apply_url": "https://jobs.lever.co/acme/1",
            "description": "software intern",
        },
        {
            "company": "InCo",
            "title": "Data Analyst Intern",
            "location": "Remote",
            "apply_url": "https://www.linkedin.com/jobs/view/123",
            "description": "analyst intern",
        },
        {
            "company": "Nope",
            "title": "Designer",
            "location": "India",
            "apply_url": "https://example.com/jobs/1",
            "description": "design",
        },
    ]

    role_keywords = ["sde", "data analyst", "intern"]
    locations = ["india", "remote"]
    candidates = module.build_candidates(jobs, role_keywords, locations, set(), set(), [])
    providers = {c["_provider"] for c in candidates}
    assert "lever" in providers
    assert "linkedin" in providers
    assert len(candidates) == 2


def test_idempotency_skips_existing():
    module = _load_module(
        "/Users/anamay/Desktop/Projects/internmailer_v3/scripts/run_apply_pipeline.py",
        "run_apply_pipeline_candidates_2",
    )
    job = {
        "company": "Acme",
        "title": "SDE Intern",
        "location": "India",
        "apply_url": "https://jobs.lever.co/acme/1",
        "description": "software intern",
    }
    key = module.idempotency_key(job)
    candidates = module.build_candidates([job], ["sde", "intern"], ["india"], set(), {key}, [])
    assert candidates == []


def test_provider_detects_hosted_greenhouse():
    module = _load_module(
        "/Users/anamay/Desktop/Projects/internmailer_v3/scripts/run_apply_pipeline.py",
        "run_apply_pipeline_candidates_3",
    )
    assert module.detect_provider("https://stripe.com/jobs/search?gh_jid=12345") == "greenhouse"


def test_non_usa_filter_and_resume_routing(tmp_path):
    module = _load_module(
        "/Users/anamay/Desktop/Projects/internmailer_v3/scripts/run_apply_pipeline.py",
        "run_apply_pipeline_candidates_4",
    )
    sde_resume = tmp_path / "sde.pdf"
    business_resume = tmp_path / "business.pdf"
    default_resume = tmp_path / "default.pdf"
    sde_resume.write_text("x", encoding="utf-8")
    business_resume.write_text("x", encoding="utf-8")
    default_resume.write_text("x", encoding="utf-8")

    usa_job = {
        "company": "Acme",
        "title": "SDE Intern",
        "location": "New York, United States",
        "apply_url": "https://jobs.lever.co/acme/2",
        "description": "software intern",
    }
    india_job = {
        "company": "Beta",
        "title": "Business Analyst Intern",
        "location": "Bangalore, India",
        "apply_url": "https://jobs.lever.co/beta/2",
        "description": "analyst intern",
    }

    candidates = module.build_candidates(
        [usa_job, india_job],
        ["intern", "analyst", "sde"],
        ["india", "remote", "united states"],
        set(),
        set(),
        [],
        non_usa_only=True,
        default_resume=str(default_resume),
        sde_resume=str(sde_resume),
        business_resume=str(business_resume),
    )

    assert len(candidates) == 1
    assert candidates[0]["company"] == "Beta"
    assert candidates[0]["_resume_path"] == str(business_resume)
