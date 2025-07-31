# InternMailer 🚀

**InternMailer** is a comprehensive, AI-powered academic outreach and job application automation platform designed to help students secure research internships and job opportunities through intelligent, personalized email campaigns.

## ✨ Key Features

### 🧠 Enhanced AI-Powered Resume Analysis
- **Advanced Resume Parser**: Dual-mode parsing with LLM + rule-based fallback for 100% extraction reliability
- **Comprehensive Data Extraction**: Skills (26+), projects (5+), experience (4+), courses (16+) with high accuracy
- **Smart Categorization**: Automatically groups and ranks skills by relevance and proficiency
- **Achievement Metrics**: Extracts quantifiable achievements and project outcomes

### 🎯 Intelligent Research Matching
- **Semantic Research Matcher**: Advanced sentence-transformers for precise profile-research alignment
- **Dynamic Skill Mapping**: Context-aware matching of skills to research areas
- **Project Relevance Engine**: Automatically selects most relevant projects per professor
- **Multi-dimensional Scoring**: Combines skills, experience, and research interests for optimal matches

### 📧 Advanced Email Personalization
- **Smart Email Generator**: Highly personalized emails with actual CV data integration
- **Research-Specific Templates**: Dynamic content adaptation based on professor's research area
- **Achievement Highlighting**: Incorporates specific metrics and accomplishments
- **Professional Formatting**: Clean, engaging structure with academic tone
- **Subject Line Optimization**: Dynamic subject generation for higher open rates

### 🔧 Production-Ready Infrastructure
- **Comprehensive Testing Suite**: 51 tests with 90%+ success rate and coverage monitoring
- **CI/CD Integration**: Automated testing, coverage validation, and deployment pipeline
- **Error Handling & Monitoring**: Sentry integration for exception tracking and debugging
- **Email Validation**: MX record validation and bounce handling
- **Rate Limiting & Retry Logic**: Robust email sending with failure recovery

### 🎨 Enhanced User Experience
- **Modern Streamlit Interface**: Professional UI with improved styling and navigation
- **Campaign Management**: Track outreach progress, analytics, and response rates
- **Template System**: Multiple email templates with preview and comparison features
- **Real-time Analytics**: Campaign performance metrics and insights

### 🏢 HR Mailing & Job Application Automation
- **Job Scraping**: Extract job postings from LinkedIn and other platforms automatically
- **HR Contact Discovery**: Use Hunter.io API integration to find HR contacts at target companies
- **Company Database**: Build and maintain a database of companies with HR contact information
- **Automated HR Outreach**: Send personalized emails to HR departments for job opportunities
- **CV Customization**: Automatically tailor resumes for each specific role and company
- **Application Tracking**: Monitor application status, responses, and follow-up requirements
- **Bulk HR Campaigns**: Launch large-scale campaigns to multiple companies simultaneously

### 📨 Advanced HR Email Features
- **Industry-Specific Templates**: Pre-built templates for different industries (tech, finance, healthcare)
- **Role-Based Personalization**: Customize content based on job requirements and company culture
- **HR Department Targeting**: Smart routing to appropriate HR contacts (recruiters, hiring managers)
- **Follow-up Automation**: Systematic follow-ups with customizable intervals and content
- **Response Tracking**: Monitor email open rates, click-through rates, and reply rates
- **Integration Capabilities**: Seamlessly integrate with existing email workflows and CRM systems

## Folder Structure
```
InternMailer/
├── data/
│   ├── professors_clean_final.csv    # Main professor database
│   └── sent_emails.json             # Duplicate prevention tracking
├── resumes/                         # Student CV/resume files
├── templates/                       # Email templates and assets
├── logs/                           # Campaign logs and analytics
├── auto_campaign.py                # Main campaign automation script
├── app.py                          # Streamlit web interface
├── .env                            # Environment variables and secrets
├── requirements.txt                # Python dependencies
└── README.md                       # This documentation
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Clone the repository
git clone https://github.com/Flamechargerr/InternMailer.git
cd InternMailer

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Application
```bash
# Create environment file
cp .env.example .env  # Copy example template
# Edit .env with your credentials (see Configuration section below)
```

### 3. Add Required Files
- **Resume**: Place your CV/resume PDF in `resumes/` folder
- **Professor Database**: Ensure `data/professors_clean_final.csv` exists with professor information

### 4. Launch Application
```bash
# Start the Streamlit interface
streamlit run app.py

# Or run command-line version
python auto_campaign.py
```

## ⚙️ Configuration

Create a `.env` file in the project root with the following variables:

```bash
# Gmail Configuration (Required)
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-character-app-password

# OpenAI API (Optional - enables enhanced AI email generation)
OPENAI_API_KEY=sk-your-openai-key-here

# Hunter.io Configuration (Required for HR email discovery)
HUNTER_API_KEY=your-hunter-api-key

# Azure AI Configuration (Optional - alternative AI provider)
AZURE_AI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_AI_KEY=your-azure-key

# Campaign Settings (Optional)
MAX_EMAILS_PER_DAY=50
MIN_DELAY_SECONDS=2
DRY_RUN_MODE=false

# Job Scraping Configuration (Optional)
LINKEDIN_EMAIL=your-linkedin-email
LINKEDIN_PASSWORD=your-linkedin-password
SCRAPE_DELAY_SECONDS=3
```

### Gmail App Password Setup
1. Enable 2-Factor Authentication on your Google Account
2. Go to [Google Account Settings](https://myaccount.google.com/security)
3. Navigate to **Security** → **2-Step Verification** → **App passwords**
4. Select **Mail** as the app and generate password
5. Copy the 16-character password to your `.env` file

### Professor Database Format
Your CSV file should contain columns:
- `Email`: Professor's email address
- `Name`: Full name
- `University`: Institution name  
- `Research Area`: Research interests/specialization

### Hunter.io API Setup (For HR Email Discovery)
1. Sign up for a free account at [Hunter.io](https://hunter.io)
2. Navigate to your dashboard and get your API key
3. Add the API key to your `.env` file as `HUNTER_API_KEY=your-key`
4. Free tier provides 25 requests/month, paid plans offer more

## 🏢 HR Mailing Workflow

### Step-by-Step HR Campaign Process

#### 1. Job Discovery & Scraping
```bash
# Navigate to Job Applications page in Streamlit UI
# Or use command line:
python job_harvester.py --keywords "software engineer intern" --location "remote"
```

#### 2. Company Database Building
- Jobs are parsed to extract company information
- Company database is built automatically in `data/scraped_companies.json`
- Duplicate companies are filtered out

#### 3. HR Contact Discovery
```bash
# Using the UI (recommended):
# 1. Go to Job Applications page
# 2. Enter Hunter.io API key in sidebar
# 3. Click "Find HR Emails"

# Command line alternative:
python hr_finder.py --api-key YOUR_HUNTER_KEY --companies-file data/scraped_companies.json
```

#### 4. Email Generation & Personalization
- System automatically generates personalized emails for each HR contact
- Templates are customized based on:
  - Job requirements
  - Company information
  - Your resume/skills
  - Industry context

#### 5. HR Email Campaign Execution
```bash
# Dry run first (recommended)
python integrated_job_hr_outreach.py --mode dry_run

# Live campaign
python integrated_job_hr_outreach.py --mode live
```

### HR Email Templates

The system includes industry-specific templates:

#### Technology Companies
```text
Subject: Software Engineering Intern Application - [Your Name]

Dear [HR Name],

I am writing to express my interest in the [Job Title] position at [Company]. 
With my experience in [Relevant Skills], I believe I would be a valuable 
addition to your team.

[Personalized content based on job requirements]

Best regards,
[Your Name]
```

#### Financial Services
```text
Subject: Internship Application - [Your Name] | [University]

Dear [HR Name],

I am currently pursuing [Degree] at [University] and am very interested 
in the [Job Title] opportunity at [Company]. My background in [Relevant Experience] 
aligns well with your requirements.

[Personalized content based on financial sector context]

Sincerely,
[Your Name]
```

### Advanced HR Features

#### Bulk HR Campaigns
```python
# Configure bulk campaign settings
campaign_settings = {
    'batch_size': 20,
    'delay_between_emails': 5,  # seconds
    'follow_up_enabled': True,
    'follow_up_delay_days': 7
}
```

#### Response Tracking
- All HR emails are logged with tracking IDs
- Response rates are calculated automatically
- Follow-up scheduling based on no-reply timeouts

#### Integration with Job Applications
- Seamlessly links HR contacts to specific job postings
- Tracks application status per company
- Manages multiple applications to the same company

### HR Campaign Analytics

Track your HR outreach performance:

```python
# View campaign statistics
from application_tracker import ApplicationTracker

tracker = ApplicationTracker()
stats = tracker.get_campaign_stats()

print(f"Total Applications: {stats['total_applications']}")
print(f"Response Rate: {stats['response_rate']}%")
print(f"Interview Requests: {stats['interviews']}")
```

## Security
- All secrets are read from `.env` and masked in logs.
- API calls are secured.
- Hunter.io API key is never logged or exposed.

## Testing
- Unit tests are included for core modules.
- HR workflow can be tested in dry-run mode.

## Bulk Send HOW-TO

### Required Environment Variables / Secrets

Before running bulk email campaigns, ensure the following environment variables are configured in your `.env` file:

```bash
# Required Gmail credentials
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-16-character-app-password

# Optional OpenAI API for enhanced email generation (falls back to Ollama/templates)
OPENAI_API_KEY=sk-your-openai-key-here
```

**Setting up Gmail App Password:**
1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Navigate to Security → 2-Step Verification → App passwords
3. Generate a new app password for "Mail"
4. Use the 16-character password (without spaces) in your `.env` file

**⚠️ Security Note:** Never commit your `.env` file to version control. All secrets are automatically masked in application logs.

### How to Switch from Dry-Run to Live Mode

#### Using the Streamlit Interface (Recommended)
1. Launch the application: `streamlit run app.py`
2. Complete steps 1-5 (upload resume, select preferences, preview emails)
3. In **Step 6: Outreach Mode**, select between:
   - **"Dry Run"**: Generates and displays emails without sending (safe for testing)
   - **"Live Send"**: Actually sends emails to professors
4. Click "Start Outreach" to begin

#### Using the Command Line Bulk Script
1. Review professors in `data/proffesor.csv`
2. Run: `python bulk_email_campaign.py`
3. Confirm at the prompt: "Proceed with bulk sending? (yes/no): **yes**"

**💡 Best Practice:** Always run a dry-run first to verify:
- Email personalization quality
- Professor targeting accuracy
- Template rendering correctness

### Recommended Send-Rate Throttling

The system includes built-in rate limiting to prevent account suspension and ensure deliverability:

#### Default Rate Limits
- **Minimum delay between emails**: 2 seconds (configurable in `GmailSender.min_delay`)
- **Bulk campaign delay**: 60-120 seconds random interval (prevents pattern detection)
- **Retry logic**: 3 attempts with exponential backoff (2^attempt seconds)

#### Recommended Production Settings
```python
# For high-volume campaigns (100+ emails)
min_delay = 5  # 5 seconds between emails
bulk_delay = 120-300  # 2-5 minutes between bulk sends

# For smaller campaigns (< 50 emails)
min_delay = 2  # 2 seconds between emails
bulk_delay = 60-120  # 1-2 minutes between bulk sends
```

#### Gmail Sending Limits
- **Daily limit**: 500 emails per day (Gmail free account)
- **Per hour**: ~100 emails recommended
- **Per minute**: 2-5 emails maximum to avoid temporary blocks

**⚠️ Important:** Exceeding these limits may result in temporary account suspension or reduced deliverability.

### Monitoring Sent-Mail Logs and Handling Bounces/Replies

#### Email Logs
All email activity is automatically logged to `email_log.csv` with the following structure:
```csv
Email,Subject,Status,Timestamp,Error
professor@university.edu,"Research Internship Inquiry",sent,2024-01-15 10:30:45,
test@invalid.com,"Test Subject",invalid_email,2024-01-15 10:31:02,Invalid email format
```

#### Log Status Types
- `sent`: Successfully delivered
- `invalid_email`: Email format validation failed
- `auth_error`: Gmail authentication issue
- `smtp_error`: SMTP server error (recipient refused, etc.)
- `failed`: General sending failure
- `config_error`: Missing credentials or configuration

#### Monitoring Commands
```bash
# View recent sending activity
tail -n 50 email_log.csv

# Count emails by status
cut -d',' -f3 email_log.csv | sort | uniq -c

# Find failed sends
grep "failed\|error" email_log.csv

# Daily sending volume
grep "$(date +%Y-%m-%d)" email_log.csv | wc -l
```

#### Handling Bounces and Replies

**Bounces (Automatic):**
- Hard bounces are logged as `smtp_error` status
- Invalid email addresses are caught during validation
- Soft bounces trigger automatic retry logic

**Manual Reply Monitoring:**
1. Monitor your Gmail inbox for professor responses
2. Use Gmail labels/filters to organize replies:
   - Create label: "InternMailer Responses"
   - Filter rule: Subject contains "Re: Research Internship"
3. Track response rates in the application analytics

**Follow-up Management:**
- The system includes automated follow-up scheduling
- Access via Streamlit interface → "Follow-up Scheduler" tab
- Configure delay periods and maximum follow-ups per campaign

### Roll-back or Pause Procedure

#### Emergency Stop During Campaign
1. **Streamlit Interface**: Close browser tab or press Ctrl+C in terminal
2. **Command Line**: Press Ctrl+C to interrupt the bulk script
3. **Process Kill**: `pkill -f "python.*bulk_email_campaign.py"`

#### Pausing an Active Campaign
```bash
# Create pause file to stop processing
touch PAUSE_CAMPAIGN

# Remove to resume
rm PAUSE_CAMPAIGN
```

#### Post-Send Damage Control

**If emails were sent with errors:**
1. **Review email_log.csv** to identify successfully sent emails
2. **Draft apology/correction email** if necessary
3. **Create exclusion list** from sent emails to avoid duplicates:
   ```bash
   grep "sent" email_log.csv | cut -d',' -f1 > sent_emails.txt
   ```

**If account is temporarily restricted:**
1. **Stop all sending activity** immediately
2. **Wait 24-48 hours** before resuming
3. **Reduce sending rate** by 50% when resuming
4. **Verify account status** in Gmail security settings

#### Follow-up Campaign Management

**Bulk Actions in Streamlit:**
- Navigate to "Follow-up Scheduler" → "Campaign Settings" tab
- Select problematic campaign
- Use bulk actions to:
  - Cancel all pending follow-ups
  - Reschedule entire campaign
  - Disable follow-ups for specific campaign

**Database Cleanup (Advanced):**
```bash
# Backup current state
cp scheduler/followup_data.db scheduler/followup_data.db.backup

# Cancel all pending follow-ups for emergency
# (Requires direct database access - use Streamlit interface instead)
```

#### Recovery Checklist
- [ ] Stop all active campaigns
- [ ] Review email_log.csv for sent count
- [ ] Check Gmail account status
- [ ] Update rate limiting settings if needed
- [ ] Create exclusion list from sent emails
- [ ] Plan revised sending schedule
- [ ] Test with small batch before resuming

**📞 Emergency Contacts:**
- Gmail Support: [Google Workspace Support](https://support.google.com/a/)
- University IT: Contact if academic account restrictions

## License
MIT 
