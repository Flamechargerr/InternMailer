#!/usr/bin/env python3
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv()

def main():
    target_email = os.getenv('TEST_RECIPIENT_EMAIL', 'tripathy.anamay23@gmail.com')

    print("=== Running HR sample ===")
    try:
        from tools.send_hr_sample import main as hr_main
        hr_main()
    except Exception as e:
        print(f"HR sample failed: {e}")

    print("\n=== Running Professor sample ===")
    try:
        from production.ultra_system.send_html_template_emails_with_cv import (
            get_random_professor, create_academic_html_email, send_html_email_with_cv
        )
        prof = get_random_professor()
        subject, html = create_academic_html_email(prof)
        ok = send_html_email_with_cv(target_email, subject, html, 'Personalized Academic Professor')
        print(f"Professor sample sent: {ok}")
    except Exception as e:
        print(f"Professor sample failed: {e}")

if __name__ == '__main__':
    main()
