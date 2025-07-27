# 🔒 InternMailer Security & Setup Guide

## 🚀 Quick Secure Start

To start the app with all security checks:

```bash
python start_secure.py
```

## 🔐 Security Features

### ✅ Implemented Security Measures

1. **Pinned Dependencies**: All packages use specific versions to prevent supply chain attacks
2. **Environment Variable Protection**: Sensitive data stored securely in `.env` files
3. **OAuth Authentication**: Secure Gmail integration using OAuth 2.0/App Passwords
4. **Comprehensive .gitignore**: Prevents accidental exposure of sensitive files
5. **File Permission Checks**: Validates sensitive file access
6. **Input Validation**: Upload size limits and file type restrictions
7. **Secure Startup**: Automated security validation before app start

### 🛡️ Security Checklist

Before running the application:

- [ ] `.env` file exists with valid credentials
- [ ] Gmail App Password generated (not regular password)
- [ ] Sensitive files excluded from version control
- [ ] Dependencies installed from requirements.txt
- [ ] No hardcoded credentials in source code

## 📋 Setup Instructions

### 1. Environment Setup

Create a `.env` file in the project root:

```env
# Gmail Configuration
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password-here

# Optional: Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:latest

# Optional: Rate limiting
EMAIL_RATE_LIMIT=50

# Optional: Testing mode
TEST_MODE=false
```

### 2. Generate Gmail App Password

1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Navigate to **Security** → **App passwords**
3. Generate a new app password for "Mail"
4. Use this password in your `.env` file (NOT your regular Gmail password)

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Validate Setup

Run security validation:

```bash
python setup_secure.py
```

### 5. Start Application

Use the secure startup script:

```bash
python start_secure.py
```

## 🔍 Security Validation

The security validation script checks for:

- **Environment Variables**: Validates Gmail credentials are set
- **File Permissions**: Checks sensitive file access
- **Directory Structure**: Ensures required directories exist
- **Data Files**: Validates professor CSV data availability
- **Dependencies**: Confirms all packages are installed
- **Cleanup**: Removes sensitive log files

## ⚠️ Security Warnings

### Critical Issues to Avoid

1. **Never commit `.env` files** to version control
2. **Don't use regular Gmail passwords** - always use App Passwords
3. **Avoid hardcoding credentials** in source code
4. **Don't share log files** - they may contain sensitive data
5. **Keep dependencies updated** - use pinned versions from requirements.txt

### Safe Usage Guidelines

- Always run `python setup_secure.py` before first use
- Use dry run mode for testing campaigns
- Regularly review and clean log files
- Monitor email sending rates to avoid being flagged as spam
- Keep resume files in the `resumes/` directory (git-ignored)

## 🚨 Incident Response

If you suspect a security issue:

1. **Stop the application** immediately
2. **Check logs** for suspicious activity
3. **Rotate credentials** (generate new Gmail App Password)
4. **Review `.env` file** for unauthorized changes
5. **Check git history** for accidentally committed secrets

## 📊 File Structure

```
internmailing/
├── .env                    # Sensitive credentials (git-ignored)
├── .gitignore             # Comprehensive exclusion rules
├── requirements.txt       # Pinned dependencies
├── setup_secure.py        # Security validation script
├── start_secure.py        # Secure startup script
├── data/                  # Application data
├── resumes/               # User resumes (git-ignored)
├── InternMailer/          # Main application
│   ├── app.py            # Main Streamlit app
│   ├── data/             # App-specific data
│   └── src/              # Source code
└── logs/                  # Application logs (git-ignored)
```

## 🔄 Regular Maintenance

### Weekly Tasks
- [ ] Review log files for errors
- [ ] Check for dependency updates
- [ ] Validate `.env` file integrity

### Monthly Tasks
- [ ] Rotate Gmail App Password
- [ ] Review git history for secrets
- [ ] Update dependencies if needed
- [ ] Clean old log files

## 📞 Support

If you encounter security issues or need help with setup:

1. Check this guide first
2. Run `python setup_secure.py` for automated validation
3. Review error messages carefully
4. Check the application logs for detailed error information

## 🏆 Best Practices Summary

1. **Use secure startup**: Always run `python start_secure.py`
2. **Validate regularly**: Run security checks before important campaigns
3. **Monitor logs**: Check for errors and suspicious activity
4. **Keep secrets secret**: Never share or commit credentials
5. **Test first**: Use dry run mode before sending real emails
6. **Stay updated**: Keep dependencies current with pinned versions

---

**Remember: Security is a continuous process, not a one-time setup!**
