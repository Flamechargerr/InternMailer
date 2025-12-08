# InternMailer - Automated Internship Outreach System

A powerful, production-ready email automation system for internship and research position outreach.

## 🚀 Features

### Email Campaigns
- **Academic Mode**: Personalized emails to professors with research-specific content
- **Corporate Mode**: Professional outreach to HR/recruiters with company-specific context
- **Smart Research**: Auto-fetches professor research areas from Semantic Scholar & DBLP
- **HTML Formatting**: Clean, professional email templates
- **Resume Attachment**: Automatically attaches PDF resume

### Database Management
- **1,900+ Recruiters**: From top companies (Google, Meta, Amazon, Citadel, etc.)
- **700+ Professors**: From MIT, Stanford, CMU, and other top universities
- **Email Tracking**: Full history of sent emails to prevent duplicates

### Safety Features
- **Duplicate Prevention**: Never emails the same person twice
- **Email Validation**: Filters invalid/corrupted emails
- **Rate Limiting**: Respects email sending limits
- **SMTP Connection Pool**: Fast, reliable sending

---

## 📦 Quick Start

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure email credentials in .env
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your_app_password
```

### 2. Run Campaigns

**Send to 10 Professors:**
```bash
python system.py --count 10
```

**Send to 10 Recruiters:**
```bash
python system.py --hr --count 10
```

**View Dashboard:**
```bash
streamlit run dashboard.py
```

---

## 📊 Usage Commands

| Command | Description |
|---------|-------------|
| `python system.py --count N` | Send to N professors |
| `python system.py --hr --count N` | Send to N recruiters |
| `python system.py --status` | View campaign status |
| `streamlit run dashboard.py` | Open visual dashboard |

---

## 📁 Project Structure

```
InternMailer/
├── system.py              # Main email system
├── smart_research_system.py # Professor research lookup
├── recruiter_finder.py    # Recruiter database management
├── dashboard.py           # Streamlit dashboard
├── data/
│   ├── recruiters.db      # Recruiter contacts database
│   ├── clean_40k_professors.db # Professor contacts
│   ├── Anamay_Tripathy_Resume.pdf # Resume attachment
│   └── *.csv              # Import files
├── campaign_results/
│   └── email_tracking.db  # Sent email history
└── .env                   # Email credentials
```

---

## 🎯 Email Templates

### Academic (Professors)
- Research-specific opening with professor's work
- Relevant experience highlights
- Technical skills aligned with research area
- Clear call-to-action for internship

### Corporate (Recruiters)
- Company-specific context (auto-generated for 15+ top companies)
- Impact-focused experience bullets
- Tech stack alignment
- Professional sign-off

---

## 📈 Stats

- **Total Contacts**: 2,600+ (professors + recruiters)
- **Companies Covered**: Google, Meta, Amazon, Apple, Microsoft, Citadel, etc.
- **Universities**: MIT, Stanford, CMU, Berkeley, etc.
- **Delivery Rate**: 98%+

---

## ⚙️ Configuration

### .env File
```
EMAIL_ADDRESS=your.email@gmail.com
EMAIL_PASSWORD=your_gmail_app_password
```

### Getting Gmail App Password
1. Go to Google Account → Security
2. Enable 2-Step Verification
3. Go to App Passwords
4. Generate password for "Mail"

---

## 🔧 Maintenance

### Import New Recruiters
```bash
python recruiter_finder.py
```

### Check System Health
```bash
python -c "import system; vs = system.VerifiedEmailSystem(); vs.show_status()"
```

---

## 📝 License

MIT License - Use responsibly for legitimate internship outreach only.