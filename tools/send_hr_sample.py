import os
import json
import csv
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from pathlib import Path

# Shared modules
try:
    from core.email.template_renderer import load_hr_template as shared_load_hr_template, render as shared_render
    from core.utils.email_validation import validate_recipient
except Exception:
    shared_load_hr_template = None
    shared_render = None
    def validate_recipient(e):
        return e

try:
    from dotenv import load_dotenv, find_dotenv
except Exception:
    load_dotenv = None
    find_dotenv = None

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Load environment variables robustly
if load_dotenv and find_dotenv:
    env_path = find_dotenv(usecwd=True)
    if env_path:
        load_dotenv(env_path)
    else:
        # Fallback to project root .env
        root_env = PROJECT_ROOT / '.env'
        if root_env.exists():
            load_dotenv(str(root_env))

TEST_RECIPIENT = os.getenv('TEST_RECIPIENT_EMAIL', 'tripathy.anamay23@gmail.com')

def load_smtp_from_env() -> dict:
    # Try multiple common env var names for compatibility
    host = os.getenv('SMTP_HOST') or os.getenv('EMAIL_HOST') or os.getenv('MAIL_HOST') or ''
    port = int(os.getenv('SMTP_PORT') or os.getenv('EMAIL_PORT') or os.getenv('MAIL_PORT') or '587')
    user = os.getenv('SMTP_USERNAME') or os.getenv('EMAIL_USER') or os.getenv('MAIL_USERNAME') or ''
    pwd = os.getenv('SMTP_PASSWORD') or os.getenv('EMAIL_PASSWORD') or os.getenv('MAIL_PASSWORD') or ''
    from_email = os.getenv('SMTP_FROM_EMAIL') or os.getenv('EMAIL_FROM') or user or 'noreply@example.com'
    from_name = os.getenv('SMTP_FROM_NAME') or os.getenv('EMAIL_FROM_NAME') or 'InternMailer'
    use_tls = (os.getenv('SMTP_USE_TLS') or os.getenv('EMAIL_USE_TLS') or 'true').lower() in ('1','true','yes','y')
    return {
        'host': host,
        'port': port,
        'username': user,
        'password': pwd,
        'from_email': from_email,
        'from_name': from_name,
        'use_tls': use_tls,
    }

def load_smtp_from_json() -> dict:
    cred_path = PROJECT_ROOT / 'email_credentials.json'
    if cred_path.exists():
        try:
            with cred_path.open('r', encoding='utf-8') as f:
                data = json.load(f) or {}
            return {
                'host': data.get('host') or data.get('SMTP_HOST') or '',
                'port': int(data.get('port') or data.get('SMTP_PORT') or 587),
                'username': data.get('username') or data.get('SMTP_USERNAME') or '',
                'password': data.get('password') or data.get('SMTP_PASSWORD') or '',
                'from_email': data.get('from_email') or data.get('SMTP_FROM_EMAIL') or data.get('username') or 'noreply@example.com',
                'from_name': data.get('from_name') or data.get('SMTP_FROM_NAME') or 'InternMailer',
                'use_tls': bool(data.get('use_tls', True)),
            }
        except Exception:
            pass
    return {}

def resolve_smtp_config() -> dict:
    cfg = load_smtp_from_env()
    if not cfg['host'] or not cfg['username'] or not cfg['password']:
        fallback = load_smtp_from_json()
        # Overlay fallbacks only for missing keys
        for k, v in fallback.items():
            if (k in ('host','username','password') and not cfg.get(k)) or k not in cfg or cfg.get(k) in (None, ''):
                cfg[k] = v
    # Gmail fallback mapping
    if (not cfg['host'] or not cfg['username'] or not cfg['password']):
        gmail_user = os.getenv('GMAIL_USER')
        gmail_app_pwd = os.getenv('GMAIL_APP_PASSWORD')
        if gmail_user and gmail_app_pwd:
            cfg.update({
                'host': 'smtp.gmail.com',
                'port': 587,
                'username': gmail_user,
                'password': gmail_app_pwd,
                'from_email': gmail_user,
                'from_name': cfg.get('from_name') or 'InternMailer',
                'use_tls': True,
            })
    return cfg

HR_DB_CANDIDATES = [
    PROJECT_ROOT / 'hr_contacts_cleaned.csv',
    PROJECT_ROOT / 'HR' / 'hr_contacts_cleaned.csv'
]
EMAIL_LOG = PROJECT_ROOT / 'email_log.csv'


def load_contacted_emails():
    contacted = set()
    if EMAIL_LOG.exists():
        try:
            with EMAIL_LOG.open('r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    email = (row.get('Email') or row.get('email') or '').strip()
                    status = (row.get('Status') or row.get('status') or '').strip().lower()
                    if email and status in {'sent', 'smtp_error', 'failed', 'auth_error', 'config_error'}:
                        contacted.add(email)
        except Exception:
            pass
    return contacted


def load_hr_template() -> str:
    """Return HTML template content for HR emails.
    Searches common locations and falls back to a minimal HTML if not found.
    """
    if shared_load_hr_template:
        try:
            return shared_load_hr_template()
        except Exception:
            pass
    candidates = [
        PROJECT_ROOT / 'templates' / 'enhanced_hr_template.html',
        PROJECT_ROOT / 'production' / 'ultra_system' / 'templates' / 'enhanced_hr_template.html',
    ]
    for p in candidates:
        if p.exists():
            try:
                return p.read_text(encoding='utf-8')
            except Exception:
                pass
    # Fallback minimal HTML (should rarely be used)
    return (
        """
        <html><body>
        <p>Dear <strong>{{ name }}</strong>,</p>
        <p>I hope this email finds you well. My name is <strong>Anamay Tripathy</strong>, and I'm reaching out regarding internship opportunities at <strong>{{ company_name }}</strong>.</p>
        <p>I've been following {{ company_name }}'s work in <em>{{ company_niche }}</em> and would love to contribute.</p>
        <p>Best regards,<br/>
        Anamay Tripathy<br/>
        <a href="https://www.linkedin.com/in/anamay-tripathy/">LinkedIn</a> ·
        <a href="https://github.com/Flamechargerr">GitHub</a>
        </p>
        </body></html>
        """
    )


def render_hr_template(html_tmpl: str, name: str, company_name: str, company_niche: str) -> str:
    """Render using shared renderer when available; fallback to simple replace."""
    if shared_render:
        try:
            return shared_render(html_tmpl, {
                'name': name,
                'company_name': company_name,
                'company_niche': company_niche,
            })
        except Exception:
            pass
    # Fallback minimal replace
    out = html_tmpl
    for k, v in {
        '{{ name }}': name,
        '{{ company_name }}': company_name,
        '{{ company_niche }}': company_niche,
    }.items():
        out = out.replace(k, v)
    return out


def pick_random_hr(contacted):
    for path in HR_DB_CANDIDATES:
        if path.exists():
            with path.open('r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = [r for r in reader if (r.get('email') or r.get('Email') or '').strip()]
            random.shuffle(rows)
            for r in rows:
                email = (r.get('email') or r.get('Email') or '').strip()
                if email and email not in contacted:
                    return r
            # Fallback: return any HR contact (we still send ONLY to TEST_RECIPIENT)
            if rows:
                return rows[0]
    return None


def build_email(hr_row, smtp_cfg):
    hr_name = (hr_row.get('name') or hr_row.get('Name') or 'Hiring Manager').strip()
    company = (hr_row.get('company') or hr_row.get('Company') or '').strip()
    niche = (hr_row.get('niche') or hr_row.get('industry') or hr_row.get('Company Niche') or '').strip()

    subject = f"Internship Opportunity - {company or 'Your Company'}"

    # Load and render HTML template
    tmpl = load_hr_template()
    html_body = render_hr_template(tmpl, name=hr_name, company_name=company or 'your organization', company_niche=niche or 'your domain')

    # Plain-text alternative (fallback)
    text_body = f"""
Dear {hr_name},

I hope this email finds you well. My name is Anamay Tripathy, and I'm reaching out regarding internship opportunities at {company or 'your organization'}.

I've been following {company or 'your organization'}'s work in {niche or 'your domain'} and would love to contribute.

Best regards,
Anamay Tripathy
LinkedIn: https://www.linkedin.com/in/anamay-tripathy/
GitHub: https://github.com/Flamechargerr
Email: {smtp_cfg['from_email']}
""".strip()

    # Build multipart/alternative message
    msg = MIMEMultipart('alternative')
    msg['From'] = formataddr((smtp_cfg['from_name'], smtp_cfg['from_email']))
    # Validate test recipient to avoid accidental invalid targets
    safe_to = validate_recipient(TEST_RECIPIENT) or TEST_RECIPIENT
    msg['To'] = safe_to
    msg['Subject'] = subject
    msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    return msg


def send_email(msg, smtp_cfg):
    if not smtp_cfg['host'] or not smtp_cfg['username'] or not smtp_cfg['password']:
        raise RuntimeError('Missing SMTP configuration (HOST/USERNAME/PASSWORD). Provide via .env or email_credentials.json')

    with smtplib.SMTP(smtp_cfg['host'], smtp_cfg['port'], timeout=30) as server:
        if smtp_cfg['use_tls']:
            server.starttls()
        server.login(smtp_cfg['username'], smtp_cfg['password'])
        to_addr = msg['To'] or TEST_RECIPIENT
        server.sendmail(smtp_cfg['from_email'], [to_addr], msg.as_string())


def main():
    smtp_cfg = resolve_smtp_config()
    contacted = load_contacted_emails()
    hr_row = pick_random_hr(contacted)
    if not hr_row:
        # Final fallback: create a dummy HR contact for composing email to TEST inbox only
        hr_row = {'name': 'Hiring Manager', 'company': 'Sample Company', 'email': 'hr@example.com'}

    msg = build_email(hr_row, smtp_cfg)
    send_email(msg, smtp_cfg)
    print(f"Sent HR sample to {TEST_RECIPIENT}")


if __name__ == '__main__':
    main()
