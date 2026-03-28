import pytest

import web.web_dashboard as web_dashboard
from web.web_dashboard import app as minimal_app


class DummyMarketSentiment:
    def get_snapshot(self, topics=None):
        topics = topics or ["SPY"]
        return {
            topic: {
                "topic": topic,
                "score": 0.25,
                "positive": 2,
                "negative": 0,
                "neutral": 1,
                "item_count": 3,
                "window_hours": 24,
                "computed_at": "2026-03-28T10:00:00+00:00",
                "data": {},
                "items": [
                    {
                        "topic": topic,
                        "source": "Reuters",
                        "title": f"{topic} higher on strong earnings",
                        "summary": "Positive signal.",
                        "url": "https://example.com/1",
                        "published_at": "2026-03-28T10:00:00+00:00",
                        "sentiment_score": 0.5,
                        "confidence": 0.8,
                        "raw": {},
                    }
                ],
            }
            for topic in topics
        }

    def refresh(self, *args, **kwargs):
        return self.get_snapshot(kwargs.get("topics"))

    def get_history(self, limit=12):
        return [
            {
                "id": 1,
                "topic": "SPY",
                "score": 0.25,
                "label": "Bullish",
                "overall_label": "Bullish",
                "positive": 2,
                "negative": 0,
                "neutral": 1,
                "item_count": 3,
                "window_hours": 24,
                "computed_at": "2026-03-28T10:00:00+00:00",
                "data": {},
            }
        ]


class DummyEmailSystem:
    def send_campaign(self, count=10):
        return {"sent": count, "failed": 0}

    def preview(self, count=3):
        return ["preview"] * count


class DummyATS:
    def optimize_for_job(self, job_description):
        return type("Result", (), {
            "company_name": "Example",
            "ats_score_before": 50,
            "ats_score_after": 80,
            "keywords_found": ["python"],
            "resume_path": "optimized_documents/resume_example.tex",
            "cover_letter_path": "optimized_documents/cover_example.tex",
            "pdf_resume_path": None,
            "pdf_cover_letter_path": None,
        })()


class DummyDiscovery:
    def run(self):
        return {"total_found": 0, "total_saved": 0}


class DummyPipeline:
    def apply_pending(self, limit=50):
        return {"attempted": 0, "results": []}


@pytest.fixture(autouse=True)
def stub_dashboard_services(monkeypatch):
    monkeypatch.setattr(web_dashboard, "EmailSystem", DummyEmailSystem)
    monkeypatch.setattr(web_dashboard, "ATSOptimizer", DummyATS, raising=False)
    monkeypatch.setattr(web_dashboard, "JobDiscovery", DummyDiscovery)
    monkeypatch.setattr(web_dashboard, "JobPipeline", DummyPipeline)
    monkeypatch.setattr(web_dashboard, "get_market_sentiment_engine", lambda: DummyMarketSentiment())


@pytest.fixture
def client():
    with minimal_app.test_client() as client:
        yield client


def test_dashboard_home_renders(client):
    rv = client.get('/')
    assert rv.status_code == 200


def test_api_stats_returns_json(client):
    rv = client.get('/api/stats')
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'emails_sent' in data


def test_send_emails_updates_count(client):
    rv = client.post('/send-emails', json={'count': 5})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['status'] == 'started'


def test_preview_emails_endpoint(client):
    rv = client.get('/preview-emails?count=2')
    assert rv.status_code == 200
    data = rv.get_json()
    assert isinstance(data.get('previews'), list)


def test_daemon_endpoints(client):
    rv = client.post('/api/daemon/start')
    assert rv.status_code == 200
    rv = client.get('/api/daemon/status')
    assert rv.status_code == 200
    rv = client.post('/api/daemon/stop')
    assert rv.status_code == 200


def test_sentiment_endpoints(client, monkeypatch):
    monkeypatch.setattr("web.web_dashboard.get_market_sentiment_engine", lambda: DummyMarketSentiment())

    rv = client.get('/sentiment')
    assert rv.status_code == 200

    rv = client.get('/api/sentiment/snapshot')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data.get("status") in ("success", "unavailable", "error")

    rv = client.post('/api/sentiment/refresh', json={})
    assert rv.status_code == 200
    data = rv.get_json()
    assert data.get("status") == "started"

    rv = client.get('/api/sentiment/history?limit=2')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data.get("status") == "success"
