import os

from core.lead_discovery import EnhancedLeadDiscovery, EnrichedContact
from utils.config import config


def test_lead_discovery_daily_cap(tmp_path, monkeypatch):
    output_csv = tmp_path / "company_contacts.csv"
    state_path = tmp_path / "state.json"

    original_enabled = config.LEAD_DISCOVERY_ENABLED
    original_cap = config.CONTACT_DISCOVERY_DAILY_CAP
    original_keywords = config.CONTACT_ROLE_KEYWORDS
    original_csv = config.COMPANY_CONTACTS_CSV
    original_state = config.CONTACT_DISCOVERY_STATE_PATH
    original_hunter = config.HUNTER_API_KEY

    config.LEAD_DISCOVERY_ENABLED = True
    config.CONTACT_DISCOVERY_DAILY_CAP = 1
    config.CONTACT_ROLE_KEYWORDS = "recruiter"
    config.COMPANY_CONTACTS_CSV = str(output_csv)
    config.CONTACT_DISCOVERY_STATE_PATH = str(state_path)
    config.HUNTER_API_KEY = "test"

    discovery = EnhancedLeadDiscovery(
        output_csv=str(output_csv),
        state_path=str(state_path),
    )

    def fake_hunter(domain, limit=10):
        return [
            EnrichedContact(
                name="Recruiter One",
                email="recruiter@example.com",
                company="Example Co",
                domain=domain,
                role="Recruiter",
                seniority="",
                department="",
                linkedin_url="",
                phone="",
                source="hunter",
                confidence=0.95,
                enrichment_data={},
                discovered_at="2024-01-01T00:00:00",
            ),
            EnrichedContact(
                name="Engineer Two",
                email="engineer@example.com",
                company="Example Co",
                domain=domain,
                role="Engineer",
                seniority="",
                department="",
                linkedin_url="",
                phone="",
                source="hunter",
                confidence=0.90,
                enrichment_data={},
                discovered_at="2024-01-01T00:00:00",
            ),
        ][:limit]

    discovery._search_hunter = fake_hunter

    result = discovery.discover(domains=["example.com"], daily_cap=1)

    assert result["contacts_saved"] == 1
    assert output_csv.exists()

    config.LEAD_DISCOVERY_ENABLED = original_enabled
    config.CONTACT_DISCOVERY_DAILY_CAP = original_cap
    config.CONTACT_ROLE_KEYWORDS = original_keywords
    config.COMPANY_CONTACTS_CSV = original_csv
    config.CONTACT_DISCOVERY_STATE_PATH = original_state
    config.HUNTER_API_KEY = original_hunter
