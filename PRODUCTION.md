# Production Deployment Guide

## Pre-Deployment Checklist

### 1. Security Configuration

```bash
# Run production readiness check
python3 main.py --production-check

# Run setup validation
python3 main.py --validate
```

### 2. Environment Variables

**Required:**
- `ENVIRONMENT=production`
- `DEBUG=false`
- `SECRET_KEY=<strong-random-secret>`
- `GMAIL_USER=<your-email>`
- `GMAIL_APP_PASSWORD=<app-password>`

**Recommended:**
- `GROQ_API_KEY=<your-key>` (for AI features)
- `SESSION_SECURE=true` (if using HTTPS)

### 3. Security Hardening

✅ **SQL Injection Prevention**
- All database queries use parameterized statements
- Table/column names are validated

✅ **Input Validation**
- All API endpoints validate and sanitize input
- String length limits enforced
- Email/URL format validation

✅ **Rate Limiting**
- API endpoints have rate limits
- Email sending has strict limits
- Configurable per-endpoint

✅ **Secret Masking**
- Credentials masked in logs
- No secrets in error messages
- Secure configuration loading

### 4. Performance Optimization

**Database:**
- Use `/tmp/` for SQLite databases (faster I/O)
- Connection pooling enabled
- Query timeouts configured

**SMTP:**
- Connection pool size: 5-10 (configurable)
- Retry logic with exponential backoff
- Connection health checks

**Rate Limits:**
- Default: 60/min, 1000/hour, 10000/day
- Email sending: 2/min, 10/hour
- AI endpoints: 10/min, 100/hour

### 5. Monitoring & Logging

**Health Checks:**
- `/health` - System health status
- `/metrics` - Application metrics

**Logging:**
- Structured logging with levels
- Sensitive data automatically masked
- Log rotation configured

### 6. Deployment Steps

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   python3 -m playwright install chromium
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

3. **Validate Setup**
   ```bash
   python3 main.py --validate
   python3 main.py --production-check
   ```

4. **Start Application**

   **Development:**
   ```bash
   python3 main.py
   ```

   **Production:**
   ```bash
   ENVIRONMENT=production python3 main.py
   ```

   The launcher uses Gunicorn automatically when it is installed and falls back to the Flask server if needed.

### 7. Production Configuration

**Recommended Settings:**

```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<generate-strong-secret>

# Flask
FLASK_HOST=0.0.0.0
FLASK_PORT=5050

# Security
SESSION_SECURE=true
SESSION_HTTPONLY=true
SESSION_SAMESITE=Lax
CSRF_ENABLED=true

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
RATE_LIMIT_PER_DAY=10000

# Email Limits
MAX_EMAILS_PER_DAY=100
MAX_CONCURRENT_EMAILS=5
SMTP_POOL_SIZE=5

# Database (use /tmp/ for better performance)
DATABASE_PATH=/tmp/internmailer_db/email_tracking.db
JOBS_DB_PATH=/tmp/internmailer_db/job_discovery.db
INBOX_DB_PATH=/tmp/internmailer_db/inbox_monitor.db
```

### 8. Security Best Practices

1. **Never commit `.env` file** - Already in `.gitignore`
2. **Use strong SECRET_KEY** - Generate with: `python3 -c "import secrets; print(secrets.token_hex(32))"`
3. **Enable HTTPS** - Use reverse proxy (nginx/traefik) with SSL
4. **Set SESSION_SECURE=true** - Only over HTTPS
5. **Limit CORS origins** - Set a specific allowed origin for any external client
6. **Monitor logs** - Check for suspicious activity
7. **Regular backups** - Backup databases regularly
8. **Update dependencies** - Keep requirements.txt updated

### 9. Troubleshooting

**Common Issues:**

1. **Database permission errors**
   - Use `/tmp/internmailer_db/` for databases
   - Ensure directory exists and is writable

2. **Email sending fails**
   - Verify Gmail app password
   - Check 2FA is enabled
   - Review SMTP connection pool logs

3. **Rate limit errors**
   - Check rate limit configuration
   - Review rate limit headers in responses
   - Adjust limits if needed

4. **Import errors**
   - Run: `pip install -r requirements.txt`
   - Check Python version (3.9+)

### 10. Monitoring

**Health Check Endpoint:**
```bash
curl http://localhost:5050/health
```

**Metrics Endpoint:**
```bash
curl http://localhost:5050/metrics
```

**Check Logs:**
```bash
tail -f logs/internmailer.log
```

## Production Checklist Summary

- [ ] Environment variables configured
- [ ] `ENVIRONMENT=production` set
- [ ] `DEBUG=false` set
- [ ] Strong `SECRET_KEY` generated
- [ ] Email credentials configured
- [ ] Production check passed (`--production-check`)
- [ ] Setup validation passed (`--validate`)
- [ ] HTTPS enabled (if exposing publicly)
- [ ] CORS configured correctly
- [ ] Rate limits configured
- [ ] Monitoring/logging set up
- [ ] Backups configured
- [ ] Dependencies up to date
