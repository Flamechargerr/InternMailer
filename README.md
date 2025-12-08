# InternMailer - Complete Email Campaign System

## 🚀 One Command - Everything Works

```bash
# That's it! All 10 features work automatically:
python system.py --count 50 --template research
```

## ✨ What Happens Automatically

When you run `python system.py`, **all 10 features are auto-enabled**:

1. ✅ **Email Validation** - DNS MX + regex checks (no bad emails!)
2. ✅ **SMTP Retry** - Auto-retry on disconnections (no lost emails!)
3. ✅ **Structured Logging** - JSON logs in `campaign_logs/` (easy debugging)
4. ✅ **DB Pooling** - Fast database access (30-40% speedup)
5. ✅ **Rate Limiting** - Adapts based on bounce rate (protects reputation)
6. ✅ **Reply Detection** - Categorizes responses (auto-actions ready)
7. ✅ **Configuration** - Centralized settings in `config.yaml`
8. ✅ **Unsubscribe Tracking** - Legal compliance (CAN-SPAM)
9. ✅ **A/B Testing** - Statistical analysis (optimize open rates)
10. ✅ **Monitoring** - Alert triggers (bounce/failure notifications)

**No separate servers needed!** Everything runs in one process.

## 📦 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Campaign
```bash
# Academic emails (professors)
python system.py --count 25 --template research

# Corporate emails (recruiters)  
python system.py --count 25 --corporate

# Mixed mode
python system.py --count 50 --template research
```

### 3. View Logs (Optional)
```bash
# See what happened
cat campaign_logs/application.log

# Run tests
pytest tests/ -v
```

## 🔧 Configuration (Optional)

Edit `config.yaml` to customize:
- Daily sending limit
- Turbo mode speed
- Personalization settings
- Email verification rules

**Default settings work great!** No need to change anything.

## 📊 Optional: Dashboards

If you want visual dashboards, run these in separate terminals:

```bash
# Terminal 1: Unsubscribe page
python unsubscribe_server.py  # http://localhost:5000

# Terminal 2: A/B testing metrics
python dashboard_ab_testing.py  # http://localhost:5001
```

**But they're totally optional!** The main system works perfectly without them.

## 🎯 How It Works

When you run `python system.py`:

1. **Auto-loads** all features from `integrated_system.py`
2. **Validates** each email before sending (DNS MX check)
3. **Retries** failed sends automatically (3 attempts)
4. **Logs** everything to JSON files
5. **Pools** database connections for speed
6. **Checks** daily rate limits based on reputation
7. **Uses** centralized config from `config.yaml`

## 🛡️ Safety Features (All Automatic)

- ✅ **Duplicate Prevention** - Never emails same person twice
- ✅ **Bounce Protection** - Blocks invalid emails before sending
- ✅ **Rate Limiting** - Adapts to your sender reputation
- ✅ **Error Recovery** - Auto-retries SMTP failures
- ✅ **Logging** - Full audit trail of all events

## 📁 Project Structure

```
InternMailer/
├── system.py                 # Main CLI (run this!)
├── integrated_system.py      # Auto-enables all 10 features
├── config.yaml              # Settings (optional to edit)
├── email_validator.py       # Free DNS MX validation
├── reply_classifier.py      # NLP categorization
├── monitoring_system.py     # Structured logging
├── db_pool.py              # Connection pooling
├── adaptive_rate_limiter.py # Smart daily limits
├── config_manager.py        # YAML loader
├── smtp_retry.py           # Exponential backoff
├── unsubscribe_server.py    # Optional: Web UI
├── dashboard_ab_testing.py  # Optional: Metrics UI
└── tests/                  # Pytest suite
```

## 🎓 Advanced Usage

### View Sender Reputation
```python
python -c "from integrated_system import get_integrated_system; get_integrated_system()"
```

### Check Email Validity
```python
python -c "from email_validator import get_email_validator; v = get_email_validator(); print(v.validate_email('test@mit.edu'))"
```

### Run Full Test Suite
```bash
pytest tests/ -v --cov
```

## ❓ Troubleshooting

**"Module not found" errors:**
```bash
pip install -r requirements.txt
```

**Syntax errors in system.py:**
```bash
# Revert to clean version
git checkout system.py
```

**Features not working:**
```bash
# Check what's enabled
python -c "from integrated_system import get_integrated_system; s = get_integrated_system()"
```

## 🎉 That's It!

Just run `python system.py --count 50` and everything works automatically.

No complex setup. No separate processes. One command. Done.