---
layout: default
title: InternMailer
---

# InternMailer

> **Autonomous Job Application System — Find, Tailor, Apply.**

InternMailer is an AI-powered job application automation platform that discovers internships and jobs across **20+ sources**, auto-tailors your resume and cover letter with **ATS optimization**, and applies on your behalf — all while respecting **rate limits** and staying **under the radar**.

[🚀 Get Started](#quick-start) · [📖 Docs](https://github.com/Flamechargerr/InternMailer#readme) · [🐳 Docker](https://github.com/Flamechargerr/InternMailer/pkgs/container/internmailer) · [⭐ GitHub](https://github.com/Flamechargerr/InternMailer)

---

## Features

| Feature | Description |
|---------|-------------|
| **20+ Job Sources** | LinkedIn, Indeed, Glassdoor, AngelList, Greenhouse, Lever, Ashby, Workday, Remotive, and more |
| **AI Resume Tailor** | Reads your PDF, generates job-specific resumes with ATS keyword optimization |
| **Mass Apply Engine** | Intelligent rate limiting, stealth patterns, human-like delays |
| **Autonomous Scheduler** | Runs discover → tailor → apply loop on schedule |
| **Web Dashboard** | Real-time analytics, job queue, application tracking |
| **Email Outreach** | AI-generated personalized recruiter emails |
| **Inbox Monitor** | Auto-reply detection, classification, follow-up management |

---

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  DISCOVER   │───▶│   TAILOR    │───▶│    APPLY    │
│ 20+ Sources │    │ AI Resume   │    │ Rate-Limited│
└─────────────┘    └─────────────┘    └─────────────┘
       │                                   │
       ▼                                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   TRACK     │◀───│  ANALYTICS  │◀───│   MONITOR   │
│  SQLite DB  │    │ Dashboard   │    │ Inbox/Email │
└─────────────┘    └─────────────┘    └─────────────┘
```

---

## Quick Start

```bash
# 1. Clone & Install
git clone https://github.com/Flamechargerr/InternMailer.git
cd InternMailer
pip install -r requirements.txt
playwright install chromium

# 2. Configure
cp config/.env.example .env
# Edit .env with your Gmail, Groq API key, resume path

# 3. Run
python main.py
# Open http://localhost:5050
```

Or with Docker:
```bash
docker run -p 5050:5050 ghcr.io/flamechargerr/internmailer:latest
```

---

## Tech Stack

- **Python 3.10+** — Core engine
- **Flask** — Web API & dashboard
- **Playwright** — Browser automation
- **Groq LLM** — AI resume tailoring & outreach
- **SQLite** — Embedded tracking database
- **React + Vite** — Frontend dashboard
- **Docker** — Container deployment

---

## API Endpoints

### Core
- `POST /api/jobs/discover` — Trigger job discovery
- `POST /api/jobs/apply` — Trigger application queue
- `GET /api/stats` — Dashboard statistics

### Enhanced
- `POST /api/enhanced/discover` — 20-source discovery
- `POST /api/enhanced/tailor` — AI resume tailoring
- `POST /api/enhanced/mass-apply` — Mass application
- `POST /api/enhanced/scheduler/start` — Start autonomous scheduler
- `GET /api/enhanced/scheduler/analytics` — Full analytics

---

## License

MIT License — see [LICENSE](https://github.com/Flamechargerr/InternMailer/blob/master/LICENSE)

---

Built with 💻 by [Anamay Tripathy](https://github.com/Flamechargerr)
