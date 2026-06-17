<div align="center">
  <h1>InternMailer</h1>
  <p><strong>Autonomous Job Application System — Find, Tailor, Apply.</strong></p>

  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python"></a>
  <a href="https://flask.palletsprojects.com"><img src="https://img.shields.io/badge/Flask-2.3+-green.svg" alt="Flask"></a>
  <a href="docs/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License"></a>
  <a href="https://flamechargerr.github.io/InternMailer"><img src="https://img.shields.io/badge/docs-github.io-blueviolet" alt="Docs"></a>
  <a href="https://github.com/Flamechargerr/InternMailer/actions"><img src="https://github.com/Flamechargerr/InternMailer/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://github.com/Flamechargerr/InternMailer/pkgs/container/internmailer"><img src="https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker" alt="Docker"></a>

  <br><br>

  <a href="#features">Features</a> ·
  <a href="#quick-start">Quick Start</a> ·
  <a href="#architecture">Architecture</a> ·
  <a href="#configuration">Configuration</a> ·
  <a href="#deployment">Deployment</a> ·
  <a href="#api">API</a> ·
  <a href="https://flamechargerr.github.io/InternMailer">Docs</a>

  <hr>
</div>

InternMailer is an **AI-powered job application automation platform** that discovers internships and jobs across **20+ sources**, auto-tailors your resume and cover letter with **ATS-level keyword optimization**, and submits applications — all while respecting rate limits and staying under the radar.

## Features

| Feature | Description |
|---------|-------------|
| **Autonomous Job Discovery** | Scrapes LinkedIn, Indeed, Glassdoor, AngelList, Greenhouse, Lever, Ashby, Workday, Remotive, Builtin, ZipRecruiter, and more |
| **AI Resume & CV Tailoring** | Reads your resume PDF, generates job-specific versions with ATS keyword injection |
| **Mass Application Engine** | Intelligent rate limiting, human-like delays, stealth patterns, exponential backoff retry |
| **Autonomous Scheduler** | Full pipeline on cron: Discover → Tailor → Apply, with active-hours awareness |
| **Web Dashboard** | Real-time analytics, job queue management, application tracking, manual controls |
| **Email Campaign System** | AI-personalized recruiter outreach with reply classification and follow-up management |
| **Inbox Monitoring** | Auto-checks Gmail for replies, classifies intent, schedules follow-ups |
| **ATS Optimizer** | Scores and improves your resume against job descriptions for maximum ATS match |
| **Production Ready** | Docker support, health checks, metrics, Gunicorn, comprehensive logging |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Flamechargerr/InternMailer.git
cd InternMailer

# 2. Install
pip install -r requirements.txt
python -m playwright install chromium

# 3. Configure
cp config/.env.example .env
# Edit .env with your credentials:
#   GMAIL_USER, GMAIL_APP_PASSWORD, GROQ_API_KEY, RESUME_PATH

# 4. Run
python main.py
```

Open **http://localhost:5050** in your browser.

### Docker

```bash
docker run -p 5050:5050 \
  -v $(pwd)/.env:/app/.env \
  ghcr.io/flamechargerr/internmailer:latest
```

## Architecture

```
core/                          # Core engine modules
├── enhanced_job_discovery.py  # 20+ source job scraper
├── resume_tailor.py          # AI resume/CV tailor
├── mass_apply_orchestrator.py# Mass application engine
├── autonomous_scheduler.py   # Pipeline scheduler
├── job_apply.py              # Playwright auto-applier
├── job_discovery.py          # Legacy ATS discovery
├── email_system.py           # Email campaign engine
├── inbox_monitor.py          # Gmail reply monitoring
├── agents/                   # AI agent pipeline
└── ...
web/                           # Flask API + dashboard
utils/                         # Configuration & utilities
middleware/                    # Rate limiting, CSRF, health
data/                          # Databases & job sources
```

### Pipeline

```
DISCOVER ──▶ TAILOR ──▶ APPLY ──▶ TRACK
   20+ sources   AI resume    Rate-limited    SQLite DB
                    + cover letter
```

The autonomous scheduler runs this loop every 4–6 hours:
1. **Discover** — Scrape 20+ job sources for new postings
2. **Score** — Rank jobs by relevance to your profile (AI-powered)
3. **Tailor** — Generate job-specific resume + cover letter
4. **Apply** — Submit with human-like delays and stealth patterns
5. **Track** — Log everything in the dashboard database

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GMAIL_USER` | Yes | — | Your Gmail address |
| `GMAIL_APP_PASSWORD` | Yes | — | Gmail App Password (16 chars) |
| `GROQ_API_KEY` | Yes | — | Groq API key for AI features |
| `RESUME_PATH` | Yes | — | Path to your resume PDF |
| `JOB_ROLE_KEYWORDS` | No | `software engineering intern` | Job search keywords |
| `JOB_TARGET_LOCATIONS` | No | `remote` | Target locations |
| `JOB_SCORE_THRESHOLD` | No | `0.3` | Minimum match score (0.0–1.0) |
| `MAX_EMAILS_PER_DAY` | No | `100` | Daily email sending limit |
| `FLASK_PORT` | No | `5050` | Dashboard port |
| `ENVIRONMENT` | No | `development` | `development` / `production` |

## Deployment

### Docker

```bash
docker build -t internmailer .
docker run -p 5050:5050 --env-file .env internmailer
```

Or pull the pre-built image from GitHub Container Registry:
```bash
docker run -p 5050:5050 ghcr.io/flamechargerr/internmailer:latest
```

### Production

```bash
python main.py --production-check   # Verify setup
python main.py                      # Start with Gunicorn (auto-detected)
```

## API

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Service health check |
| `/api/stats` | GET | Dashboard statistics |
| `/api/jobs` | GET | List discovered jobs |
| `/api/jobs/discover` | POST | Trigger job discovery |
| `/api/jobs/apply` | POST | Trigger application queue |
| `/api/replies` | GET | List inbox replies |
| `/api/daemon/start` | POST | Start background daemon |

### Enhanced Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/enhanced/discover` | GET/POST | 20+ source discovery |
| `/api/enhanced/tailor` | POST | AI resume tailoring |
| `/api/enhanced/mass-apply` | POST | Mass application |
| `/api/enhanced/mass-apply/status` | GET | Apply analytics |
| `/api/enhanced/scheduler/analytics` | GET | Full scheduler stats |

## Project Structure

```
InternMailer/
├── core/                  # Engine modules (discovery, apply, tailor, scheduler)
├── web/                   # Flask API & dashboard
├── utils/                 # Configuration, bootstrap, helpers
├── frontend/              # React dashboard (Vite)
├── config/                # .env examples, Docker Compose, service configs
├── data/                  # Runtime databases, job sources, verification data
├── docs/                  # Documentation & GitHub Pages site
├── scripts/               # Utility scripts & verification tools
├── tests/                 # Test suite (pytest)
├── templates/             # Email & LaTeX templates
├── resume/                # Resume storage
├── middleware/            # Rate limiting, CSRF, health checks
├── campaign_results/      # Campaign output
├── optimized_documents/   # AI-generated tailored resumes
├── main.py                # Entry point
├── requirements.txt       # Dependencies
├── Dockerfile             # Docker image
└── README.md              # This file
```

## Guidelines

**Use responsibly.** Always review applications before submission. Some companies prohibit automated applications — use at your own discretion. This tool is designed to help job seekers apply more efficiently, not to spam.

## License

MIT License — see [LICENSE](docs/LICENSE).

---

<div align="center">
  Built with ❤️ by <a href="https://github.com/Flamechargerr">Anamay Tripathy</a>
  <br>
  <a href="https://flamechargerr.github.io/InternMailer">📖 Documentation</a>
  ·
  <a href="https://github.com/Flamechargerr/InternMailer/issues">🐛 Report Bug</a>
  ·
  <a href="https://github.com/Flamechargerr/InternMailer/discussions">💬 Discussions</a>
</div>
