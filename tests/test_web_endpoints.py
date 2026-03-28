import types

import web.web_dashboard as web_dashboard


class DummyEmailSystem:
    def send_campaign(self, count=10):
        return {"sent": count, "failed": 0}

    def preview(self, count=3):
        return ["preview"] * count


class DummyATS:
    def optimize_for_job(self, job_description):
        return types.SimpleNamespace(
            company_name="Example",
            ats_score_before=50,
            ats_score_after=80,
            keywords_found=["python"],
            resume_path="optimized_documents/resume_example.tex",
            cover_letter_path="optimized_documents/cover_example.tex",
            pdf_resume_path=None,
            pdf_cover_letter_path=None,
        )


class DummyDiscovery:
    def run(self):
        return {"total_found": 0, "total_saved": 0}


class DummyPipeline:
    def apply_pending(self, limit=50):
        return {"attempted": 0, "results": []}


class DummyMarketSentiment:
    def _topic_snapshot(self, topic):
        return {
            "topic": topic,
            "score": 0.42,
            "positive": 2,
            "negative": 1,
            "neutral": 1,
            "item_count": 2,
            "window_hours": 24,
            "computed_at": "2026-03-28T10:00:00+00:00",
            "data": {},
            "items": [
                {
                    "topic": topic,
                    "source": "Reuters",
                    "title": f"{topic} stock rallies on strong guidance",
                    "summary": "Positive news flow.",
                    "url": "https://example.com/1",
                    "published_at": "2026-03-28T10:00:00+00:00",
                    "sentiment_score": 0.75,
                    "confidence": 0.8,
                    "raw": {},
                }
            ],
        }

    def get_snapshot(self, topics=None):
        topics = topics or ["SPY", "NASDAQ"]
        return {topic: self._topic_snapshot(topic) for topic in topics}

    def refresh(self, watchlist=None, limit_per_entity=6):
        return self.get_snapshot(watchlist)

    def get_history(self, limit=8):
        return [
            {
                "id": 1,
                "topic": "SPY",
                "created_at": "2026-03-28T10:00:00+00:00",
                "score": 0.42,
                "label": "Bullish",
                "overall_label": "Bullish",
                "positive": 2,
                "negative": 1,
                "neutral": 1,
                "item_count": 2,
                "window_hours": 24,
                "data": {},
            }
        ]


def test_web_endpoints(monkeypatch):
    web_dashboard.app.config["TESTING"] = True

    monkeypatch.setattr(web_dashboard, "EmailSystem", DummyEmailSystem)
    monkeypatch.setattr(web_dashboard, "JobDiscovery", DummyDiscovery)
    monkeypatch.setattr(web_dashboard, "JobPipeline", DummyPipeline)
    monkeypatch.setattr(web_dashboard, "get_market_sentiment_engine", lambda: DummyMarketSentiment())

    client = web_dashboard.app.test_client()
    csrf_token = "test-token"
    with client.session_transaction() as sess:
        sess["csrf_token"] = csrf_token

    assert client.get("/").status_code == 200
    assert client.get("/api/stats").status_code == 200
    assert client.get("/contacts").status_code == 200
    assert client.get("/replies").status_code == 200
    assert client.get("/settings").status_code == 200
    assert client.get("/jobs").status_code == 200
    assert client.get("/sentiment").status_code == 200
    assert client.get("/api/sentiment/snapshot").status_code == 200

    resp = client.post(
        "/send-emails",
        json={"count": 1},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert resp.status_code == 200

    resp = client.get("/preview-emails?count=1")
    assert resp.status_code == 200

    resp = client.post(
        "/ats-optimizer",
        data={"job_description": "Intern role", "csrf_token": csrf_token},
    )
    assert resp.status_code in (200, 302)

    resp = client.post("/api/jobs/discover")
    assert resp.status_code == 200

    resp = client.post("/api/jobs/apply", json={"limit": 1})
    assert resp.status_code == 200

    resp = client.post("/api/sentiment/refresh", json={"limit": 1})
    assert resp.status_code == 200
