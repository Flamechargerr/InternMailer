from web.web_dashboard import app


def test_jobs_page_loads():
    client = app.test_client()
    resp = client.get("/jobs")
    assert resp.status_code == 200


def test_discover_jobs_endpoint():
    client = app.test_client()
    resp = client.post("/api/jobs/discover")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "status" in data
