# 📅 Follow-up Scheduler System

The InternMailer Follow-up Scheduler is a comprehensive automated system for managing email follow-ups with advanced scheduling capabilities, per-campaign configurations, and an intuitive UI.

## ✨ Features

### Core Functionality
- **🎯 Per-Campaign Intervals**: Configure different follow-up delays for each campaign (7-14 days or custom)
- **🎨 Dynamic Template Selection**: Use different templates for different follow-up sequences
- **📊 Real-time Dashboard**: Monitor follow-up status, analytics, and performance
- **🔧 Campaign Management**: Enable/disable, reschedule, or cancel follow-ups per campaign
- **⚡ Overdue Processing**: Automatically handle overdue follow-ups

### Advanced Features
- **📈 Analytics & Reporting**: Track success rates, response patterns, and campaign performance
- **🔄 Bulk Operations**: Reschedule or cancel multiple follow-ups at once
- **⏰ Smart Scheduling**: Business hours, weekday-only, and holiday exclusion support
- **🚦 Rate Limiting**: Configurable hourly and daily sending limits
- **📱 Mobile-Friendly UI**: Responsive design for managing follow-ups on any device

## 🏗️ Architecture

### Components

1. **Streamlit UI** (`InternMailer/app.py`)
   - Integrated tabs for dashboard, follow-ups, settings, and analytics
   - Real-time updates and interactive management

2. **Scheduler API** (`src/scheduler/streamlit_api.py`)
   - SQLite-based storage for campaigns and follow-ups
   - Campaign management and follow-up scheduling logic

3. **Celery Integration** (`src/scheduler/celery_app.py`, `followup_tasks.py`)
   - Background task processing (optional for production)
   - Distributed follow-up sending and processing

4. **Advanced Scheduler** (`src/scheduler/followup_scheduler.py`)
   - Per-campaign configuration support
   - Conditional follow-up logic
   - Template management integration

### Database Schema

```sql
-- Campaigns table
CREATE TABLE campaigns (
    id TEXT PRIMARY KEY,
    name TEXT,
    description TEXT,
    user_id TEXT,
    status TEXT DEFAULT 'active',
    followup_enabled INTEGER DEFAULT 1,
    followup_delay_days INTEGER DEFAULT 7,
    max_followups INTEGER DEFAULT 2,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Follow-ups table
CREATE TABLE followups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id TEXT,
    original_email TEXT,
    contact_name TEXT,
    contact_email TEXT,
    sequence_number INTEGER,
    scheduled_at TEXT,
    sent_at TEXT,
    status TEXT DEFAULT 'scheduled',
    template_id TEXT,
    subject_override TEXT,
    conditions TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## 🚀 Quick Start

### 1. Basic Setup (Streamlit Only)

```bash
# Install dependencies
pip install -r requirements.txt

# Start the application
python start_app.py
```

The basic scheduler works out-of-the-box with SQLite storage and integrated UI.

### 2. Advanced Setup (With Celery)

For production environments with distributed task processing:

```bash
# 1. Install and start Redis
redis-server

# 2. Start Celery worker (new terminal)
celery -A src.scheduler.celery_app worker --loglevel=info

# 3. Start Celery beat scheduler (new terminal)
celery -A src.scheduler.celery_app beat --loglevel=info

# 4. Start the Streamlit app
streamlit run InternMailer/app.py
```

## 📖 Usage Guide

### Creating Campaigns

1. **Run Email Outreach**: Use the main InternMailer interface
2. **Automatic Campaign Creation**: Campaigns are created automatically when you send emails
3. **Follow-up Scheduling**: Follow-ups are scheduled based on campaign settings

### Managing Follow-ups

#### Dashboard Tab 📊
- View overall follow-up statistics
- Process overdue follow-ups with one click
- See campaign breakdown charts

#### All Follow-ups Tab 📋
- View all scheduled, sent, and cancelled follow-ups
- Filter by status
- Reschedule individual follow-ups by selecting new date/time
- Cancel specific follow-ups

#### Campaign Settings Tab ⚙️
- Select campaign to configure
- Enable/disable follow-ups per campaign
- Set follow-up delay (1-30 days)
- Configure maximum number of follow-ups (1-5)
- View campaign-specific statistics

#### Analytics Tab 📈
- Success rate tracking
- Status distribution charts
- Performance metrics
- Recent activity feed

### Advanced Configuration

#### Per-Campaign Follow-up Rules

```python
from scheduler.followup_scheduler import FollowUpRule, CampaignFollowUpConfig

# Create custom follow-up rules
rules = [
    FollowUpRule(
        sequence_number=1,
        delay_days=7,
        condition=FollowUpCondition.IF_NOT_REPLIED,
        template_id="follow_up_template_1"
    ),
    FollowUpRule(
        sequence_number=2, 
        delay_days=14,
        condition=FollowUpCondition.IF_NOT_OPENED,
        subject_override="Final follow-up: Research opportunity"
    )
]

# Configure campaign
config = CampaignFollowUpConfig(
    campaign_id="your_campaign_id",
    enabled=True,
    rules=rules,
    business_hours_only=True,
    weekdays_only=True,
    rate_limit_per_day=50
)
```

#### Business Hours & Rate Limiting

- **Business Hours**: Automatically reschedule follow-ups outside 9 AM - 5 PM
- **Weekdays Only**: Skip weekends for professional communications
- **Rate Limiting**: Configurable hourly and daily sending limits
- **Holiday Exclusions**: Skip specific dates (e.g., holidays, conferences)

## 🎛️ Configuration Options

### Campaign-Level Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `followup_enabled` | Enable follow-ups for campaign | `True` |
| `followup_delay_days` | Days between email and first follow-up | `7` |
| `max_followups` | Maximum follow-ups per contact | `2` |
| `business_hours_only` | Only send during business hours | `False` |
| `weekdays_only` | Only send on weekdays | `False` |
| `rate_limit_per_hour` | Maximum emails per hour | `100` |
| `rate_limit_per_day` | Maximum emails per day | `1000` |

### Follow-up Conditions

- **Always**: Send follow-up regardless of engagement
- **If Not Opened**: Only if original email wasn't opened
- **If Not Clicked**: Only if original email wasn't clicked  
- **If Not Replied**: Only if recipient didn't reply
- **If No Engagement**: No opens, clicks, or replies
- **Custom**: Custom condition logic

## 🔧 API Reference

### Core Methods

```python
from scheduler.streamlit_api import get_followup_manager

manager = get_followup_manager()

# Create campaign
campaign_id = manager.create_campaign("My Campaign", "Description")

# Log email sent (triggers follow-up scheduling)
manager.log_email_sent(campaign_id, "prof@university.edu", "Research Inquiry")

# Reschedule follow-up
manager.reschedule_followup(followup_id, new_datetime)

# Cancel follow-up  
manager.cancel_followup(followup_id, "Reason")

# Get analytics
analytics = manager.get_analytics()
```

### Celery Tasks

```python
from scheduler.followup_tasks import send_followup_email

# Schedule follow-up email
send_followup_email.apply_async(
    args=[followup_id],
    eta=scheduled_datetime
)
```

## 📊 Monitoring & Analytics

### Key Metrics Tracked

- **Total Follow-ups**: Overall count of scheduled follow-ups
- **Success Rate**: Percentage of follow-ups successfully sent
- **Overdue Rate**: Percentage of follow-ups past their scheduled time
- **Campaign Performance**: Follow-up counts and success rates per campaign
- **Response Tracking**: Integration with email engagement metrics

### Real-time Dashboard

The Streamlit interface provides:
- Live metrics updates
- Interactive charts and graphs
- Campaign comparison tools
- Recent activity feeds
- Performance trend analysis

## 🚨 Troubleshooting

### Common Issues

#### Follow-ups Not Scheduling
- Check campaign `followup_enabled` setting
- Verify `max_followups` hasn't been reached
- Ensure email was logged with `log_email_sent()`

#### Database Errors
- Check SQLite database permissions
- Verify database file path is writable
- Look for database corruption (recreate if needed)

#### Celery Issues
- Ensure Redis server is running
- Check Celery worker and beat processes are active
- Verify task routing configuration

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging for scheduler
logger = logging.getLogger('scheduler')
logger.setLevel(logging.DEBUG)
```

## 🔮 Future Enhancements

### Planned Features

- **A/B Testing**: Test different follow-up strategies
- **Machine Learning**: Optimize send times based on recipient behavior  
- **Email Templates**: Visual template editor for follow-ups
- **Integration Hub**: Connect with CRM systems and email providers
- **Mobile App**: Native mobile app for follow-up management
- **Team Collaboration**: Multi-user campaign management

### Contributing

We welcome contributions! Areas for improvement:

1. **Template System**: Enhanced template management
2. **Analytics**: Advanced reporting and insights
3. **Integrations**: Third-party service connections
4. **UI/UX**: Interface improvements and mobile optimization
5. **Performance**: Database optimization and caching

## 📄 License

This follow-up scheduler system is part of InternMailer and follows the same licensing terms.

---

**Need Help?** 
- Check the troubleshooting section above
- Review the configuration options
- Look at the usage examples
- Open an issue for bug reports or feature requests
