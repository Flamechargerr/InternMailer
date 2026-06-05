import json

from core.job_discovery import JobDiscovery, JobPosting


def test_score_job_internship_summer_and_location():
    discovery = JobDiscovery()
    job = JobPosting(
        source="test",
        source_id="1",
        company="Example",
        title="Software Engineer Intern",
        location="Bangalore, India",
        location_type="onsite",
        url="https://example.com/job/1",
        apply_url="https://example.com/job/1",
        description="Summer 2026 internship with visa sponsorship mentioned for US roles.",
        employment_type="internship",
    )

    score = discovery._score_job(job)
    assert score >= 0.6
    assert job.season_match is True


def test_score_job_us_without_visa_penalty():
    discovery = JobDiscovery()
    job = JobPosting(
        source="test",
        source_id="2",
        company="Example",
        title="Data Analyst Intern",
        location="New York, United States",
        location_type="onsite",
        url="https://example.com/job/2",
        apply_url="https://example.com/job/2",
        description="Internship role without any visa sponsorship mention.",
        employment_type="internship",
    )

    score = discovery._score_job(job)
    assert score < 0.6

