# 🤖 InternMailer - End-to-End Job Application Automation

**Automate the full pipeline** from job discovery to ATS-optimized resumes, auto-apply, email follow-ups, and reply handling through the Flask web dashboard and CLI.

## ✨ Features

- **🧭 Job Discovery + Scoring** - Scrape curated sources and score roles with season/location/visa filters
- **🎯 ATS Auto-Customization** - Tailor resume + cover letter per job and generate PDFs
- **⚡ Auto-Apply (Playwright)** - Apply on common ATS platforms with a persistent browser profile (uploads resume + cover letter when possible)
- **📧 Personalized Outreach** - AI-written cold emails and tailored follow-ups
- **📥 Inbox Monitoring** - Classify replies and trigger next actions automatically
- **🔄 Follow-Up Scheduler** - Send follow-ups after configured delays
- **📈 Market Sentiment Engine** - Pull public news, score market mood, and persist sentiment snapshots
- **🌐 Web Dashboard** - Control everything from a single UI
- **📊 Observability** - Health checks, metrics, and campaign tracking

## 🚀 Quick Start

### 1) Install

```bash
pip install -r requirements.txt
python3 -m playwright install chromium
```

### 2) Configure

```bash
cp .env.example .env
# Edit .env with Gmail + AI keys
```

Minimum required for email automation:

```
GMAIL_USER=your.email@gmail.com
GMAIL_APP_PASSWORD=your_app_password
```

Optional but recommended for AI/ATS:

```
GROQ_API_KEY=your_groq_key
```

### 3) Load Your Profile + Resume Data

Your canonical profile lives in `data/profile.yaml`. If you have PDFs, ingest them:

```bash
python3 utils/resume_ingest.py --dir /Users/anamay/Desktop/cv --profile data/profile.yaml
```

You can also point to a single resume:

```bash
python3 utils/resume_ingest.py --pdf /path/to/resume.pdf --profile data/profile.yaml
```

### 4) Validate Setup (Recommended)

Before starting, validate your configuration:

```bash
python3 -m utils.validate_setup
# or
python3 main.py --validate
```

This will check:
- Email credentials are configured
- Job sources file exists
- Contact CSV files are present
- Required directories exist

### 5) Start the App

```bash
python3 main.py
```

Open http://localhost:5050

**Note:** If you see warnings about missing data sources, the system will still start but won't be able to discover jobs or send emails until you add the required files.

## 🧭 Job Discovery + Auto-Apply

- Job sources are in `data/job_sources.yaml`
- Scoring uses `JOB_ROLE_KEYWORDS`, `JOB_TARGET_LOCATIONS`, `JOB_SEASON_START/END`, and `JOB_SCORE_THRESHOLD`
- Fortune 500 boost uses `data/fortune500_2019.csv`
- Some sources (LinkedIn, Indeed) require login; use the persistent Playwright profile to stay signed in

## 📇 Company Contact Discovery (Hunter/Apollo)

If you don’t have a contacts CSV, the system can auto-discover recruiter/HR emails via Hunter.io (and optionally Apollo).

How it works:
1. Collects company domains from job sources + job discovery DB
2. Queries Hunter (and Apollo if configured)
3. Filters roles using `CONTACT_ROLE_KEYWORDS`
4. Saves contacts to `data/company_contacts.csv`
5. Enforces a daily cap

Optional overrides:
- `data/company_domain_overrides.json` can map company names to domains for better coverage (especially Fortune 500).

Key settings:
```
CONTACT_DISCOVERY_ENABLED=true
CONTACT_DISCOVERY_DAILY_CAP=100
CONTACT_ROLE_KEYWORDS="recruiter,talent,people,hr,hiring"
COMPANY_CONTACTS_CSV="data/company_contacts.csv"
CONTACT_DISCOVERY_PROVIDERS="hunter,apollo"
HUNTER_API_KEY="..."
APOLLO_API_KEY=""
EMAIL_SKIP_ACADEMIC=true
```

Optional: refresh Fortune 500 list

```bash
python3 scripts/download_fortune500.py
```

Optional: map ATS providers (slow; uses cached results)

```bash
python3 scripts/map_ats_sources.py --limit 50
```

## 🎯 ATS Optimizer

The ATS engine uses `data/profile.yaml` and the job description to generate a tailored resume:

- `web/ats_optimizer.py` produces LaTeX + PDF
- `core/job_pipeline.py` uses the optimizer during auto-apply
- `optimized_documents/` stores outputs

## 📈 Market Sentiment Engine

The market sentiment MVP turns public news into a lightweight, dashboard-friendly signal:

- `core/market_sentiment.py` fetches Google News RSS results and scores them with a lexicon-based model
- `core/sentiment_store.py` persists topic snapshots, scored items, and run history in SQLite
- `core/agents/market_sentiment.py` exposes the engine through the existing agent framework
- `web/web_dashboard.py` adds:
  - `GET /sentiment`
  - `GET /api/sentiment/snapshot`
  - `POST /api/sentiment/refresh`
  - `GET /api/sentiment/history`
- `templates/web/sentiment.html` shows the combined market pulse, topic breakdowns, and recent headlines

Defaults:

```
MARKET_SENTIMENT_DB_PATH=/tmp/internmailer_db/market_sentiment.db
MARKET_SENTIMENT_TOPICS=SPY,NASDAQ,NIFTY,BTC
```

## 🌐 Web Dashboard Endpoints

- `GET /` Dashboard
- `GET /jobs` Job discovery page
- `GET /sentiment` Market sentiment dashboard
- `POST /api/jobs/discover` Run job discovery
- `POST /api/jobs/apply` Auto-apply to queued jobs
- `GET /api/sentiment/snapshot` Latest sentiment snapshot
- `POST /api/sentiment/refresh` Refresh market sentiment in the background
- `GET /api/sentiment/history` Recent sentiment history
- `POST /send-emails` Send a campaign
- `GET /preview-emails` Preview upcoming emails
- `GET /health` Health check
- `GET /metrics` Metrics
- `POST /api/daemon/start` Start automation daemon
- `POST /api/daemon/stop` Stop daemon
- `GET /api/daemon/status` Daemon status

## ⚙️ Configuration Highlights

Key `.env` variables:

```
PROFILE_PATH=data/profile.yaml
RESUME_PDF_PATH=/Users/anamay/Desktop/cv
RESUME_PATHS=path/to/your_resume.pdf
CALENDAR_LINK=your_calendar_link

JOB_DISCOVERY_DAILY_CAP=50
JOB_SCORE_THRESHOLD=0.6
JOB_TARGET_LOCATIONS=India
JOB_ALLOW_USA_WITH_VISA=true
JOB_SEASON_START=2026-05-01
JOB_SEASON_END=2026-07-31

MARKET_SENTIMENT_TOPICS=SPY,NASDAQ,NIFTY,BTC
MARKET_SENTIMENT_DB_PATH=/tmp/internmailer_db/market_sentiment.db

PLAYWRIGHT_USER_DATA_DIR=output/playwright/profile
EMAIL_SKIP_ACADEMIC=true
CONTACT_DISCOVERY_ENABLED=true
CONTACT_DISCOVERY_DAILY_CAP=100
CONTACT_ROLE_KEYWORDS="recruiter,talent,people,hr,hiring"
COMPANY_CONTACTS_CSV="data/company_contacts.csv"
DEFAULT_ROLE_TITLE="Software Engineering Intern"
STRICT_TEMPLATE_KEYWORDS_EXTRA=""
```

## 🧪 Tests

```bash
pytest
```

## 📁 Project Structure

```
internmailer/
├── core/                   # Automation engine
├── web/                    # Flask dashboard + ATS optimizer
├── utils/                  # Config, profile, resume ingest
├── templates/              # HTML + LaTeX templates
├── data/                   # Profile + job sources + ATS mapping
├── scripts/                # Fortune 500 + ATS mapping
├── market sentiment/       # Market sentiment workspace additions
└── tests/                  # Test suite
```

## 📝 License

MIT
