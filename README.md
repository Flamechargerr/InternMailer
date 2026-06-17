# InternMailer

> **Autonomous Job Application System — Find, Tailor, Apply.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)]()

**InternMailer** is an autonomous job application system that discovers internships and jobs across 20+ sources, auto-tailors your resume and cover letter with AI, and applies on your behalf — all while respecting rate limits and staying under the radar.

---

## Features

- **Autonomous Job Discovery** — Scrapes 20+ sources (LinkedIn, Indeed, Glassdoor, AngelList, Greenhouse, Lever, Ashby, Workday, Remotive, Builtin, ZipRecruiter, and more)
- **AI Resume & CV Tailoring** — Reads your resume PDF and generates job-specific versions with ATS keyword optimization
- **Mass Application Engine** — Intelligent rate limiting, human-like delays, stealth patterns, and retry logic
- **Autonomous Scheduler** — Runs the full pipeline on schedule: discover → tailor → apply, with active-hours awareness
- **Web Dashboard** — Real-time analytics, job queue management, application tracking, and manual controls
- **Email Campaign System** — Personalized outreach to recruiters with AI-generated messages
- **Inbox Monitoring** — Auto-checks Gmail for replies, classifies responses, and manages follow-ups
- **Production Ready** — Docker support, health checks, metrics endpoint, and comprehensive logging

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/Flamechargerr/InternMailer.git
cd InternMailer
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your credentials (Gmail, Groq API key, resume path)
```

Required:
- `GMAIL_USER` — Your Gmail address
- `GMAIL_APP_PASSWORD` — Gmail App Password (not your regular password)
- `GROQ_API_KEY` — Free API key from [console.groq.com](https://console.groq.com)
- `RESUME_PATH` — Path to your resume PDF

### 3. Run

```bash
# Start the web dashboard
python main.py

# Or run the CLI
python main.py --cli

# Or run the autonomous scheduler directly
python core/autonomous_scheduler.py --daemon
```

Open `http://localhost:5050` in your browser.

---

## Architecture

```
internmailer/
├── core/                          # Core engine modules
│   ├── enhanced_job_discovery.py  # 20+ source job scraper
│   ├── resume_tailor.py           # AI resume/CV tailor
│   ├── mass_apply_orchestrator.py # Mass application engine
│   ├── autonomous_scheduler.py    # Autonomous pipeline scheduler
│   ├── job_apply.py               # Playwright auto-applier
│   ├── job_discovery.py           # Legacy ATS discovery
│   ├── email_system.py            # Email campaign engine
│   ├── inbox_monitor.py           # Gmail reply monitoring
│   ├── reply_classifier.py        # AI reply classification
│   ├── followup_scheduler.py      # Follow-up management
│   └── unified_ai_provider.py   # LLM abstraction layer
├── web/                           # Web interface
│   ├── web_dashboard.py           # Flask API + React host
│   └── ats_optimizer.py           # ATS optimization tools
├── frontend/                      # React dashboard (Vite)
├── utils/                         # Utilities & configuration
├── scripts/                       # Helper scripts
├── tests/                         # Test suite
├── docs/                          # Documentation
├── templates/                     # Email & LaTeX templates
├── data/                          # Data files & databases
├── resume/                        # Resume storage
├── services/                      # System service configs
├── main.py                        # Entry point
├── requirements.txt               # Dependencies
├── Dockerfile                     # Docker image
└── docker-compose.yml             # Docker Compose setup
```

---

## API Endpoints

### Dashboard
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Service health check |
| `/api/stats` | GET | Dashboard statistics |
| `/api/jobs` | GET | List discovered jobs |
| `/api/jobs/discover` | POST | Trigger job discovery |
| `/api/jobs/apply` | POST | Trigger application queue |
| `/api/replies` | GET | List inbox replies |
| `/api/settings` | GET | Configuration overview |
| `/api/daemon/start` | POST | Start background daemon |
| `/api/daemon/stop` | POST | Stop background daemon |

### Enhanced APIs
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/enhanced/discover` | GET/POST | Enhanced discovery (20+ sources) |
| `/api/enhanced/tailor` | POST | AI tailor resume for a job |
| `/api/enhanced/batch-tailor` | POST | Batch tailor multiple resumes |
| `/api/enhanced/mass-apply` | POST | Mass application with rate limiting |
| `/api/enhanced/mass-apply/status` | GET | Mass apply analytics |
| `/api/enhanced/jobs/high-match` | GET | High-match jobs (score ≥ 0.7) |
| `/api/enhanced/jobs/sources` | GET | Job source breakdown |
| `/api/enhanced/jobs/batch-apply` | POST | Apply to specific job IDs |
| `/api/enhanced/scheduler/start` | POST | Start autonomous scheduler |
| `/api/enhanced/scheduler/stop` | POST | Stop autonomous scheduler |
| `/api/enhanced/scheduler/status` | GET | Scheduler status |
| `/api/enhanced/scheduler/analytics` | GET | Scheduler analytics |
| `/api/enhanced/scheduler/run-now` | POST | Manual scheduler run |

---

## Autonomous Pipeline

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   DISCOVER      │────▶│     TAILOR       │────▶│     APPLY       │
│  (20+ sources)  │     │  (AI resume/CV)  │     │  (Rate-limited) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                                               │
         ▼                                               ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   TRACK         │◀────│    ANALYTICS     │◀────│    MONITOR      │
│   (SQLite DB)   │     │   (Dashboard)    │     │  (Inbox/Email)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

The autonomous scheduler runs this loop every 4-6 hours:
1. **Discover** — Scrape 20+ job sources for new postings
2. **Score** — Rank jobs by relevance to your profile
3. **Tailor** — Generate job-specific resume + cover letter
4. **Apply** — Submit applications with human-like delays
5. **Track** — Log everything in the dashboard database

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GMAIL_USER` | Yes | Your Gmail address |
| `GMAIL_APP_PASSWORD` | Yes | Gmail App Password (16 chars) |
| `GROQ_API_KEY` | Yes | Groq API key for AI features |
| `RESUME_PATH` | Yes | Path to your resume PDF |
| `PROFILE_PATH` | No | Path to candidate profile markdown |
| `JOB_ROLE_KEYWORDS` | No | Comma-separated job keywords |
| `JOB_TARGET_LOCATIONS` | No | Comma-separated target locations |
| `JOB_SCORE_THRESHOLD` | No | Minimum job score (0.0-1.0, default 0.3) |
| `MAX_EMAILS_PER_DAY` | No | Daily email limit (default 100) |
| `FOLLOWUP_DELAY_DAYS` | No | Follow-up delay (default 7) |
| `FLASK_PORT` | No | Dashboard port (default 5050) |

### Scheduler Settings

```python
# In core/autonomous_scheduler.py or via API
SchedulerConfig(
    discover_interval_hours=6.0,    # How often to discover jobs
    apply_interval_hours=4.0,       # How often to apply
    max_jobs_per_apply=25,          # Max jobs per apply batch
    max_applications_per_hour=8,    # Rate limit: per hour
    max_applications_per_day=40,   # Rate limit: per day
    active_hours_start=9,           # 9 AM
    active_hours_end=22,            # 10 PM
    skip_weekends=True,             # Skip weekends
    submit_mode="human_verified",   # or "full_auto" or "draft_only"
)
```

---

## Docker

```bash
# Build and run
docker-compose up -d

# Or run directly
docker build -t internmailer .
docker run -p 5050:5050 -v $(pwd)/.env:/app/.env internmailer
```

---

## Production Deployment

```bash
# Run production checks
python main.py --production-check

# Start with Gunicorn
python main.py --web

# Or run the scheduler as a system service
# See services/internmailer.service for systemd config
```

---

## License

MIT License — see [LICENSE](LICENSE) file.

---

## Built With

- [Flask](https://flask.palletsprojects.com) — Web framework
- [Playwright](https://playwright.dev) — Browser automation
- [Groq](https://groq.com) — LLM inference
- [SQLite](https://sqlite.org) — Embedded database
- [React](https://react.dev) — Dashboard frontend

---

> **Note:** This tool is designed to help job seekers apply more efficiently. Use responsibly and always review applications before submission. Some companies may have terms of service that prohibit automated applications — use at your own discretion.
