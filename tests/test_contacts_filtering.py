import csv

from utils.config import config
from core.email_system import EmailSystem


def test_company_only_filtering(tmp_path):
    csv_path = tmp_path / "company_contacts.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "email", "company", "role"])
        writer.writeheader()
        writer.writerow(
            {
                "name": "Jane Recruiter",
                "email": "jane@acme.com",
                "company": "Acme Inc",
                "role": "Recruiter",
            }
        )
        writer.writerow(
            {
                "name": "Prof X",
                "email": "prof@harvard.edu",
                "company": "Harvard University",
                "role": "Professor",
            }
        )

    original_csv = config.COMPANY_CONTACTS_CSV
    original_skip = config.EMAIL_SKIP_ACADEMIC
    original_db = config.DATABASE_PATH
    original_contacts_db = config.CONTACTS_DB_PATH
    original_strict = config.EMAIL_STRICT_TEMPLATE

    config.COMPANY_CONTACTS_CSV = str(csv_path)
    config.EMAIL_SKIP_ACADEMIC = True
    config.EMAIL_STRICT_TEMPLATE = True
    config.DATABASE_PATH = str(tmp_path / "email_tracking.db")
    config.CONTACTS_DB_PATH = str(tmp_path / "contacts.db")

    system = EmailSystem()
    contacts = system.get_fresh_contacts(count=10)

    # With academic blocking + strict company-only, only non-academic remains
    assert len(contacts) == 1
    assert contacts[0][1] == "jane@acme.com"

    config.COMPANY_CONTACTS_CSV = original_csv
    config.EMAIL_SKIP_ACADEMIC = original_skip
    config.DATABASE_PATH = original_db
    config.CONTACTS_DB_PATH = original_contacts_db
    config.EMAIL_STRICT_TEMPLATE = original_strict
