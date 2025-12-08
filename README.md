# InternMailer - Automated Job Application System

🤖 **Fully automated job hunting agent** - send, track, and respond to job applications with **zero manual work**.

## Features

✅ **Email Campaign** - Send 500 personalized emails/day  
✅ **Inbox Monitor** - Auto-checks Gmail every hour  
✅ **Reply Classifier** - AI categorization (interested/not interested/etc)  
✅ **Auto-Actions** - Sends calendar links, archives rejections  
✅ **Follow-Ups** - Auto-sends after 7 days no reply  
✅ **Background Service** - Runs 24/7 unattended  

**Result:** 3.5 hours/day → **0 minutes/day** 🎯

---

## Quick Start

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Setup
```bash
python setup_automation.py
```

### 3. Configure Gmail
- Enable IMAP in Gmail settings
- Create App Password (Google Account → Security)
- Add to `.env` file

### 4. Test
```bash
python job_automation_daemon.py --test
```

### 5. Start
```bash
python job_automation_daemon.py --start
```

Done! System now runs 24/7 automatically.

---

## Usage

### Send Initial Campaign
```bash
# Send to 30 professors
python system.py --count 30 --template research

# Send to 30 companies
python system.py --count 30 --corporate
```

### Check Status
```bash
python job_automation_daemon.py --status
```

### View Logs
```bash
type campaign_results\automation_log.txt
```

---

## What Happens Automatically

**Every hour:**
- ✅ Checks Gmail inbox for replies
- ✅ Classifies each reply (interested/not/question/etc)
- ✅ Takes action:
  - Interested → Sends calendar link
  - Not interested → Archives
  - Question → Flags for review
  - Out of office → Schedules follow-up

**Every 6 hours:**
- ✅ Sends follow-ups to non-responders

**Daily:**
- ✅ Status report

---

## System Components

| Module | Purpose | Schedule |
|--------|---------|----------|
| `inbox_monitor.py` | Check Gmail via IMAP | Hourly |
| `auto_action_engine.py` | Take actions on replies | Immediate |
| `followup_scheduler.py` | Send follow-ups | Every 6h |
| `job_automation_daemon.py` | Background service | 24/7 |

---

## Configuration

Edit `config.yaml` to customize:
- Daily sending limit (default: 500)
- Follow-up delay (default: 7 days)
- Inbox check interval (default: 60 min)

---

## Safety Features

- ✅ Dry-run mode for testing
- ✅ Maximum follow-up limits (1 per contact)
- ✅ Blacklist to prevent spam
- ✅ Detailed logging
- ✅ Easy pause/resume

---

## Requirements

- Python 3.8+
- Gmail account with IMAP enabled
- Gmail App Password

---

## Support

Issues? Check:
1. `.env` file configured correctly
2. Gmail IMAP enabled
3. App password (not regular password)
4. Logs in `campaign_results/automation_log.txt`

---

## License

MIT