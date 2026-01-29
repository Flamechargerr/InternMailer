# 🤖 InternMailer - AI-Powered Job Application Automation

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Automate your entire job search** - Send personalized applications, optimize resumes for ATS, monitor replies, and manage follow-ups automatically.

## ✨ Features

- **📧 AI-Powered Email Sending** - Personalized emails with anti-templating technology
- **🎯 ATS Optimizer** - Auto-customize LaTeX resume & cover letter for each job (NEW!)
- **📥 Inbox Monitoring** - Auto-checks Gmail for replies via IMAP
- **🤖 Reply Classification** - AI categorizes replies (interested/not interested/question/OOO)
- **⚡ Auto-Actions** - Sends calendar links, archives rejections, flags questions
- **🔄 Follow-Up Management** - Auto-sends follow-ups after 7 days
- **🌐 Web Dashboard** - Visual interface to control everything
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

### 2. Launch Web Dashboard

```bash
python web_dashboard.py
```

Open http://localhost:5000 in your browser.

### 3. Or Use Command Line

```bash
# Interactive menu
python run.py

# Preview emails
python email_system.py --preview 5

# Send emails
python email_system.py --send 10

# Start full automation
python daemon.py --start --send 10
```

## 🎯 ATS Optimizer

Customize your resume and cover letter for each job application:

```bash
# Interactive mode
python ats_optimizer.py --interactive

# From file
python ats_optimizer.py --job-desc job.txt
```

The optimizer will:
1. Extract keywords from the job description using AI
2. Customize your LaTeX resume with relevant keywords
3. Generate a tailored cover letter
4. Calculate before/after ATS scores
5. Compile to PDF (if LaTeX is installed)

See [ATS Optimizer Guide](docs/ATS_OPTIMIZER_GUIDE.md) for details.

## 📁 Project Structure

```
internmailer/
├── web_dashboard.py           # 🌐 Web interface (NEW!)
├── ats_optimizer.py           # 🎯 Resume/cover letter optimizer
├── email_system.py            # 📧 Main email sending system
├── daemon.py                  # 🤖 Automation daemon
├── run.py                     # 🖥️ CLI menu
├── inbox_monitor.py           # 📥 Gmail IMAP monitoring
├── reply_classifier.py        # 🤖 AI reply classification
├── auto_action_engine.py      # ⚡ Auto-response actions
├── followup_scheduler.py      # 🔄 Follow-up management
├── unified_ai_provider.py     # 🤖 AI personalization
├── anti_templating_engine.py  # 📝 Email variation
├── config.py                  # ⚙️ Configuration
├── requirements.txt           # 📦 Dependencies
├── .env                       # 🔐 Environment variables
└── templates/                 # 📄 Email & LaTeX templates
```

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
from email_system import EmailSystem

system = EmailSystem()
system.send_campaign(count=50)  # Send 50 personalized emails
```

### Optimize Resume for a Job

```python
from ats_optimizer import ATSOptimizer

optimizer = ATSOptimizer()
job_description = """Data Science Intern position...
Requirements: Python, SQL, Machine Learning..."""

result = optimizer.optimize_for_job(job_description)
print(f"ATS Score: {result.ats_score_before} → {result.ats_score_after}")
```

### Monitor Inbox

```python
from inbox_monitor import get_inbox_monitor

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
