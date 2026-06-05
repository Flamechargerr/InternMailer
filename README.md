# 🤖 InternMailer - AI-Powered Job Application Automation

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Automate your entire job search** - Send personalized applications, optimize resumes for ATS, monitor replies, and manage follow-ups automatically.

## ✨ Features

- **🌐 Web Dashboard** - Visual interface to control everything
- **🎯 ATS Optimizer** - Auto-customize LaTeX resume & cover letter for each job
- **📧 AI-Powered Email Sending** - Personalized emails with anti-templating
- **📥 Inbox Monitoring** - Auto-checks Gmail for replies via IMAP
- **🤖 Reply Classification** - AI categorizes replies (interested/not interested/question/OOO)
- **⚡ Auto-Actions** - Sends calendar links, archives rejections, flags questions
- **🔄 Follow-Up Management** - Auto-sends follow-ups after 7 days
- **📊 Campaign Tracking** - SQLite database tracks all activity

## 🚀 Quick Start

### 1. Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/internmailer.git
cd internmailer

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials (Gmail + Groq API key)
```

### 2. Launch

```bash
# Start web dashboard (default)
python3 main.py

# Or use CLI menu
python3 main.py --cli
```

Open http://localhost:5050 in your browser.

## 📁 Project Structure

```
internmailer/
├── main.py                  # 🚀 Entry point (web dashboard)
├── core/                    # 📦 Core modules
│   ├── email_system.py      # 📧 Email sending
│   ├── enhanced_daemon.py   # 🤖 Automation daemon
│   ├── inbox_monitor.py     # 📥 Gmail monitoring
│   ├── reply_classifier.py  # 🤖 AI classification
│   ├── auto_action_engine.py# ⚡ Auto-actions
│   ├── followup_scheduler.py# 🔄 Follow-ups
│   ├── unified_ai_provider.py# 🤖 AI provider
│   ├── anti_templating_engine.py
│   └── config.py
├── web/                     # 🌐 Web interface
│   ├── web_dashboard.py     # Flask app
│   └── ats_optimizer.py     # Resume optimizer
├── utils/                   # 🛠️ Utilities
│   └── run.py               # CLI menu
├── templates/               # 📄 Email & LaTeX templates
├── docs/                    # 📚 Documentation
├── .env                     # 🔐 Configuration
└── requirements.txt         # 📦 Dependencies
```

## 🎯 ATS Optimizer

Customize your resume and cover letter for each job application:

### Via Web Dashboard
1. Open http://localhost:5050
2. Click "ATS Optimizer" tab
3. Paste job description
4. Download optimized PDFs

### Via CLI
```bash
python web/ats_optimizer.py --interactive
```

The optimizer will:
1. Extract keywords from the job description using AI
2. Customize your LaTeX resume with relevant keywords
3. Generate a tailored cover letter
4. Calculate before/after ATS scores
5. Compile to PDF (if LaTeX is installed)

See [ATS Optimizer Guide](docs/ATS_OPTIMIZER_GUIDE.md) for details.

## 🔧 Configuration

Create `.env` file:

```bash
# Gmail (required)
GMAIL_USER=your.email@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password

# AI APIs (recommended for best results)
GROQ_API_KEY=your_groq_key

# Settings
MAX_EMAILS_PER_DAY=100
FOLLOWUP_DAYS=7
```

**Get Gmail App Password:**
1. Go to [Google Account Settings](https://myaccount.google.com)
2. Security → 2-Step Verification → App passwords
3. Generate app password for "Mail"

**Get Groq API Key (Free):**
1. Go to [console.groq.com](https://console.groq.com)
2. Create an account
3. Generate an API key

## 🌐 Web Dashboard Features

The web dashboard provides a visual interface for:

- **📊 Real-time Statistics** - Emails sent, replies received, contacts reached
- **📧 Send Emails** - Send campaigns with one click
- **🎯 ATS Optimizer** - Paste job descriptions and get optimized documents
- **📇 Contacts Management** - View and manage your contact list
- **📬 Replies Monitoring** - Track and classify replies
- **⚙️ Settings** - View configuration and system status
- **🤖 Daemon Control** - Start/stop automation daemon

## 📖 Usage Examples

### Send Personalized Emails

```python
from core.email_system import EmailSystem

system = EmailSystem()
system.send_campaign(count=50)  # Send 50 personalized emails
```

### Optimize Resume for a Job

```python
from web.ats_optimizer import ATSOptimizer

optimizer = ATSOptimizer()
job_description = """Data Science Intern position...
Requirements: Python, SQL, Machine Learning..."""

result = optimizer.optimize_for_job(job_description)
print(f"ATS Score: {result.ats_score_before} → {result.ats_score_after}")
```

### Monitor Inbox

```python
from core.inbox_monitor import get_inbox_monitor

monitor = get_inbox_monitor()
replies = monitor.check_inbox()
for reply in replies:
    print(f"From: {reply['sender']}, Category: {reply['category']}")
```

## 🔄 Automation Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   SEND      │────▶│   MONITOR   │────▶│   CLASSIFY  │
│   EMAILS    │     │   INBOX     │     │   REPLIES   │
└─────────────┘     └─────────────┘     └──────┬──────┘
       │                                       │
       ▼                                       ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  FOLLOW-UP  │◀────│   TAKE      │◀────│   AUTO-     │
│  SCHEDULER  │     │   ACTION    │     │   RESPOND   │
└─────────────┘     └─────────────┘     └─────────────┘
```

## 🛠️ Requirements

- Python 3.8+
- Gmail account with App Password
- Groq API key (free tier available)
- LaTeX distribution (optional, for PDF compilation)
  - macOS: `brew install --cask mactex`
  - Ubuntu: `sudo apt-get install texlive-full`

## 📝 License

MIT License - see [LICENSE](LICENSE) file

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 🙏 Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com)
- AI powered by [Groq](https://groq.com)
- Email handling via Python's `smtplib` and `imaplib`
