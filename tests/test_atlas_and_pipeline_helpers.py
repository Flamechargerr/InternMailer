import importlib.util
from pathlib import Path


def _load_module(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_atlas_canonicalize_and_duplicates():
    module = _load_module(
        "/Users/anamay/Desktop/Projects/internmailer_v3/scripts/atlas_tab_audit.py",
        "atlas_tab_audit",
    )

    canonical = module._canonicalize_url(
        "https://www.Example.com/jobs/?utm_source=x&gclid=abc&id=123&ref=foo"
    )
    assert canonical == "example.com/jobs?id=123"

    tabs = [
        {
            "title": "A",
            "url": "https://example.com/jobs?id=123&utm_source=mail",
            "window_id": 1,
            "tab_index": 1,
            "is_active": True,
        },
        {
            "title": "B",
            "url": "http://www.example.com/jobs/?id=123",
            "window_id": 1,
            "tab_index": 2,
            "is_active": False,
        },
    ]

    report = module._build_report(tabs)
    assert report["tab_count"] == 2
    assert len(report["duplicates"]["canonical_url"]) == 1
    assert report["duplicates"]["canonical_url"][0]["count"] == 2


def test_pipeline_helpers():
    module = _load_module(
        "/Users/anamay/Desktop/Projects/internmailer_v3/scripts/run_apply_pipeline.py",
        "run_apply_pipeline",
    )

    job = {
        "company": "Acme",
        "title": "SDE Intern",
        "location": "Bangalore, India",
        "apply_url": "https://jobs.lever.co/acme/123",
        "description": "Internship role in software engineering",
    }

    assert module.detect_provider(job["apply_url"]) == "lever"
    assert module.role_matches(job, ["sde", "data analyst"])
    assert module.location_matches(job, ["india"])

    key1 = module.idempotency_key(job)
    key2 = module.idempotency_key(dict(job))
    assert key1 == key2
    assert len(key1) == 64


def test_load_jobs_from_dict_shape(tmp_path: Path):
    module = _load_module(
        "/Users/anamay/Desktop/Projects/internmailer_v3/scripts/run_apply_pipeline.py",
        "run_apply_pipeline_2",
    )

    payload_path = tmp_path / "jobs.json"
    payload_path.write_text('{"jobs":[{"title":"SDE Intern","url":"https://example.com"}]}', encoding="utf-8")

    jobs = module.load_jobs(str(payload_path))
    assert len(jobs) == 1
    assert jobs[0]["title"] == "SDE Intern"
