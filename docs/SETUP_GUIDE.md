# 📋 InternMailer Setup Guide

Complete step-by-step setup guide for the InternMailer system.

## 🎯 Prerequisites

- **Python 3.8+** installed on your system
- **Git** for version control
- **Gmail account** with app-specific password for email notifications
- **OpenAI API key** (optional, for enhanced AI matching)

## 📦 Installation Steps

### Step 1: Clone and Setup Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/InternMailer.git
cd InternMailer

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Create Directory Structure

```bash
# Create necessary directories
mkdir data logs reports

# Verify structure
ls -la
# Should show: src/, config/, data/, logs/, reports/, tests/
```

### Step 3: Configure Environment Variables

```bash
# Copy environment template
copy config\.env.example .env

# Edit .env file with your credentials
notepad .env
```

Add your credentials to `.env`:

```env
# Email Configuration
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-specific-password
RECIPIENT_EMAIL=tripathy.anamay23@gmail.com

# API Keys (Optional)
OPENAI_API_KEY=your-openai-api-key

# Database
DATABASE_PATH=data/internmailer.db

# Logging
LOG_LEVEL=INFO
```

### Step 4: Configure User Profile

Edit `config/config.yaml`:

```yaml
user_profile:
  name: "Your Full Name"
  email: "your.email@example.com"
  degree: "BTech"
  branch: "Data Science"
  semester: 5
  level: "Undergraduate"
  target_term: "Summer 2026"
  
  # Your skills (customize based on your profile)
  skills:
    languages: ["Python", "R", "SQL", "Java"]
    ml_ai: ["Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Scikit-learn"]
    data_science: ["Data Analysis", "Statistics", "Pandas", "NumPy", "Matplotlib"]
    frameworks: ["Flask", "Django", "React", "Node.js"]
    cloud: ["AWS", "Google Cloud", "Azure"]
    tools: ["Git", "Docker", "Jupyter", "VS Code"]

target_roles:
  - "Machine Learning Intern"
  - "AI Intern"
  - "Data Science Intern"
  - "Research Intern"
  - "Software Engineering Intern"

target_domains:
  - "Machine Learning"
  - "Artificial Intelligence"
  - "Data Science & Analytics"
  - "Software Development"

preferred_locations:
  primary: ["India", "Remote"]
  secondary: ["USA", "UK", "Europe", "Canada", "Singapore"]

preferences:
  min_match_score: 0.65
  min_prestige_tier: "Tier 3"
  max_applications_per_day: 10

email:
  recipient: "tripathy.anamay23@gmail.com"
  daily_report: true
  follow_up_reminders: true

schedule:
  daily_run_time: "09:00"
  timezone: "Asia/Kolkata"
```

### Step 5: Initialize Database

```bash
# Initialize the database
python src/database_manager.py

# Verify database creation
dir data
# Should show: internmailer.db
```

### Step 6: Test Email Configuration

```bash
# Test email sending
python -c "
from src.email_notifier import EmailNotifier
notifier = EmailNotifier()
success = notifier.send_test_email()
print(f'Test email sent: {success}')
"
```

### Step 7: Run System Tests

```bash
# Run all tests
python tests/run_all_tests.py

# Expected output:
# ✅ ALL TESTS PASSED!
# Coverage: X/Y modules (Z%)
```

### Step 8: Test Individual Components

```bash
# Test prestige scorer
python src/prestige_scorer.py

# Test application tracker
python src/application_tracker.py

# Test error handler
python src/error_handler.py
```

## 🚀 First Run

### Manual Test Run

```bash
# Run the system once manually
python src/scheduler.py

# Check logs
type logs\internmailer.log
```

### Start Automated Scheduler

```bash
# Start the automated daily scheduler
python -c "
from src.scheduler import InternMailerScheduler
import time

scheduler = InternMailerScheduler()
scheduler.start_scheduler()
print('InternMailer started! Daily runs at 09:00 AM.')
print('Press Ctrl+C to stop.')

try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    scheduler.stop_scheduler()
    print('InternMailer stopped.')
"
```

## 🔧 Configuration Options

### Resume Configuration

Place your base resume in `data/base_resume.pdf` or configure path:

```yaml
resume:
  base_file: "data/my_resume.pdf"
  format: "pdf"  # or "docx"
  
  # Section headers in your resume
  sections:
    skills: "Technical Skills"
    projects: "Projects"
    experience: "Experience"
    education: "Education"
```

### Job Sources Configuration

Configure additional job sources in `src/job_scraper.py`:

```python
CUSTOM_SOURCES = {
    'company_portal': {
        'name': 'Custom Company Portal',
        'url': 'https://company.com/api/jobs',
        'enabled': True,
        'rate_limit': 1.0  # seconds between requests
    }
}
```

### Email Templates

Customize email templates by editing `src/email_notifier.py` or creating template files in `config/email_templates/`.

## 📊 Monitoring Setup

### Log Monitoring

```bash
# Monitor main logs
Get-Content logs\internmailer.log -Wait

# Monitor errors only
Get-Content logs\errors.log -Wait

# Monitor performance
Get-Content logs\performance.log -Wait
```

### Database Monitoring

```bash
# Check application count
python -c "
from src.application_tracker import ApplicationTracker
tracker = ApplicationTracker()
metrics = tracker.get_application_metrics()
print(f'Total applications: {metrics[\"totals\"][\"total_applications\"]}')
"
```

### Generate Reports

```bash
# Generate comprehensive report
python -c "
from src.reporting_dashboard import ReportingDashboard
dashboard = ReportingDashboard()
report_path = dashboard.generate_comprehensive_report()
print(f'Report saved to: {report_path}')
"

# Generate analytics dashboard
python -c "
from src.reporting_dashboard import ReportingDashboard
dashboard = ReportingDashboard()
chart_path = dashboard.generate_analytics_dashboard()
print(f'Charts saved to: {chart_path}')
"
```

## 🔒 Security Setup

### Gmail App Password Setup

1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Navigate to Security → 2-Step Verification
3. Generate App Password for "Mail"
4. Use this password in your `.env` file

### API Key Security

- Never commit `.env` file to version control
- Use environment variables in production
- Rotate API keys regularly

### Data Privacy

- All data stored locally in SQLite database
- No cloud storage by default
- Contact information cached locally only

## 🚨 Troubleshooting

### Common Issues and Solutions

#### 1. Import Errors

```bash
# If you get import errors, ensure virtual environment is activated
venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. Database Errors

```bash
# Reset database if corrupted
del data\internmailer.db
python src\database_manager.py
```

#### 3. Email Not Sending

```bash
# Check email configuration
python -c "
import os
print(f'Sender email: {os.getenv(\"SENDER_EMAIL\")}')
print(f'Password set: {bool(os.getenv(\"SENDER_PASSWORD\"))}')
"

# Test SMTP connection
python -c "
import smtplib
try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    print('SMTP connection successful')
    server.quit()
except Exception as e:
    print(f'SMTP error: {e}')
"
```

#### 4. Scraping Issues

```bash
# Check for rate limiting or blocked requests
findstr "ERROR" logs\job_scraper.log

# Test individual scrapers
python -c "
from src.job_scraper import JobScraper
scraper = JobScraper()
# Test with a small sample
jobs = scraper.scrape_linkedin_jobs(limit=5)
print(f'Found {len(jobs)} jobs')
"
```

#### 5. Low Match Scores

```bash
# Update your skills in config.yaml
# Test AI matcher
python src\ai_matcher.py

# Check resume content
python -c "
from src.resume_tailor import ResumeTailor
tailor = ResumeTailor()
# Check if base resume is loaded correctly
"
```

## 📈 Performance Optimization

### Database Optimization

```bash
# Vacuum database periodically
python -c "
import sqlite3
conn = sqlite3.connect('data/internmailer.db')
conn.execute('VACUUM')
conn.close()
print('Database optimized')
"
```

### Log Rotation

```bash
# Archive old logs (run weekly)
python -c "
import os
from datetime import datetime
timestamp = datetime.now().strftime('%Y%m%d')
os.rename('logs/internmailer.log', f'logs/internmailer_{timestamp}.log')
print('Logs rotated')
"
```

## 🔄 Maintenance

### Daily Checks

1. Check email reports received
2. Monitor error logs
3. Verify application count growth

### Weekly Maintenance

1. Review application metrics
2. Update configuration if needed
3. Check for system updates
4. Archive old logs

### Monthly Reviews

1. Analyze success rates
2. Update resume and skills
3. Review and update target companies
4. Performance optimization

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review logs in `logs/` directory
3. Run the test suite: `python tests/run_all_tests.py`
4. Email support: tripathy.anamay23@gmail.com

## ✅ Verification Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed successfully
- [ ] Directory structure created
- [ ] Environment variables configured
- [ ] User profile configured in config.yaml
- [ ] Database initialized
- [ ] Email configuration tested
- [ ] All tests passing
- [ ] Manual test run successful
- [ ] Automated scheduler started
- [ ] Logs being generated
- [ ] Email reports being received

Once all items are checked, your InternMailer system is ready for production use!

---

**🎯 Your elite internship automation system is now ready to discover Summer 2026 opportunities!**