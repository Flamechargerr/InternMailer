#!/usr/bin/env python3
"""
🚀 INTERNMAILING - CENTRALIZED CONFIGURATION
===========================================
Version: 2.1.0 | Enhanced Performance & Analytics
Centralized configuration management for academic and corporate outreach system
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()

class InternMailingConfig:
    """🔧 Centralized configuration for InternMailing system"""
    
    # 📁 Project Paths
    BASE_DIR = Path(__file__).parent.absolute()
    DATA_DIR = BASE_DIR / "data"
    TEMPLATES_DIR = BASE_DIR / "templates"
    LOGS_DIR = BASE_DIR / "logs"
    CACHE_DIR = BASE_DIR / "cache"
    
    # Ensure directories exist
    for directory in [DATA_DIR, TEMPLATES_DIR, LOGS_DIR, CACHE_DIR]:
        directory.mkdir(exist_ok=True)
    
    # 📧 Email Configuration
    class Email:
        # Gmail Configuration
        GMAIL_USER = os.getenv('GMAIL_USER', 'your.email@gmail.com')
        GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD', 'your_app_password')
        SENDER_EMAIL = os.getenv('SENDER_EMAIL', GMAIL_USER)
        SENDER_PASSWORD = os.getenv('SENDER_PASSWORD', GMAIL_APP_PASSWORD)
        
        # SMTP Configuration
        SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
        USE_TLS = os.getenv('USE_TLS', 'true').lower() == 'true'
        
        # Email Limits and Rate Limiting
        MAX_EMAILS_PER_DAY = int(os.getenv('MAX_EMAILS_PER_DAY', 500))
        MAX_CONCURRENT_EMAILS = int(os.getenv('MAX_CONCURRENT_EMAILS', 5))
        RATE_LIMIT_DELAY = int(os.getenv('RATE_LIMIT_DELAY', 2))
        BATCH_SIZE = int(os.getenv('BATCH_SIZE', 50))
        
        # Email Templates
        TEMPLATES = {
            'research': 'research_template.html',
            'internship': 'internship_template.html',
            'collaboration': 'collaboration_template.html',
            'job_referral': 'job_referral_template.html'  # Corporate expansion
        }
        
        # Email Quality Standards
        MIN_CONFIDENCE_SCORE = int(os.getenv('MIN_CONFIDENCE_SCORE', 95))
        REQUIRED_GRADE = os.getenv('REQUIRED_GRADE', 'A+')
        
    # 🤖 AI and Research Configuration
    class AI:
        # GitHub Models API
        GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
        GITHUB_API_BASE = os.getenv('GITHUB_API_BASE', 'https://models.inference.ai.azure.com')
        
        # Llama Configuration
        LLAMA_PROVIDER = os.getenv('LLAMA_PROVIDER', 'github')
        LLAMA_API_KEY = os.getenv('LLAMA_API_KEY', '')
        LLAMA_MODEL = os.getenv('LLAMA_MODEL', 'gpt-4o-mini')
        
        # OpenAI Configuration (optional)
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
        OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
        
        # AI Features
        ENABLE_AI_RESEARCH_MATCHING = True
        ENABLE_CONTENT_VARIATION = True
        ENABLE_RESPONSE_CLASSIFICATION = True
        
    # 📊 Database Configuration
    class Database:
        DATABASE_PATH = str(InternMailingConfig.DATA_DIR / 'verified_professors.db')
        TRACKING_DB_PATH = str(InternMailingConfig.DATA_DIR / 'email_tracking.db')
        CACHE_DB_PATH = str(InternMailingConfig.DATA_DIR / 'cache.db')
        
        # Database Settings
        CONNECTION_TIMEOUT = 30
        MAX_CONNECTIONS = 100
        ENABLE_WAL_MODE = True
        
    # ⚡ Performance Configuration
    class Performance:
        CACHE_TTL = int(os.getenv('CACHE_TTL', 3600))  # 1 hour
        MAX_WORKER_THREADS = int(os.getenv('MAX_WORKER_THREADS', 10))
        ENABLE_MULTIPROCESSING = True
        CHUNK_SIZE = 1000
        
        # Memory Management
        MAX_MEMORY_USAGE_MB = 1024  # 1GB
        GARBAGE_COLLECT_INTERVAL = 100
        
    # 🛡️ Security and Compliance
    class Security:
        ENABLE_BOUNCE_PROTECTION = os.getenv('ENABLE_BOUNCE_PROTECTION', 'true').lower() == 'true'
        ENABLE_SPAM_FILTERING = os.getenv('ENABLE_SPAM_FILTERING', 'true').lower() == 'true'
        RESPECT_UNSUBSCRIBE = os.getenv('RESPECT_UNSUBSCRIBE', 'true').lower() == 'true'
        GDPR_COMPLIANT = os.getenv('GDPR_COMPLIANT', 'true').lower() == 'true'
        
        # Data Retention
        EMAIL_LOG_RETENTION_DAYS = 365
        ANALYTICS_RETENTION_DAYS = 730
        
        # Encryption (if needed)
        EMAIL_ENCRYPTION_KEY = os.getenv('EMAIL_ENCRYPTION_KEY', '')
        DATABASE_ENCRYPTION_KEY = os.getenv('DATABASE_ENCRYPTION_KEY', '')
        
    # 📈 Analytics and Monitoring
    class Analytics:
        ENABLE_ANALYTICS = os.getenv('ENABLE_ANALYTICS', 'true').lower() == 'true'
        SAVE_EMAIL_LOGS = os.getenv('SAVE_EMAIL_LOGS', 'true').lower() == 'true'
        
        # Metrics Collection
        TRACK_OPEN_RATES = True
        TRACK_CLICK_RATES = True
        TRACK_RESPONSE_RATES = True
        
        # Real-time Monitoring
        ENABLE_REAL_TIME_MONITORING = True
        DASHBOARD_UPDATE_INTERVAL = 30  # seconds
        
    # 🌍 International Configuration
    class International:
        DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'en')
        SUPPORTED_LANGUAGES = os.getenv('SUPPORTED_LANGUAGES', 'en,es,fr,de,it,pt').split(',')
        TIMEZONE = os.getenv('TIMEZONE', 'UTC')
        
        # University Contamination Patterns
        UNIVERSITY_CONTAMINANTS = [
            # English
            'leuvenbelgium', 'kuleuvenbelgium', 'stanfordusa', 'mitusa', 'harvardusa',
            'oxforduk', 'cambridgeuk', 'ethzurich', 'tokyojapan', 'singaporesg',
            'berkeleyusa', 'yaleusa', 'princetonusa', 'cornellusa', 'cmuusa',
            'universityof', 'collegeof', 'institutefor', 'schoolof',
            # Spanish/Latin American
            'pregrado', 'posgrado', 'universidad', 'facultad', 'instituto',
            'colegio', 'escuela', 'centro', 'departamento',
            # French
            'universite', 'faculte', 'ecole', 'institut',
            # German
            'universitat', 'hochschule', 'technische', 'institut',
            # Italian
            'universita', 'facolta', 'dipartimento', 'istituto',
            # Portuguese
            'universidade', 'faculdade', 'instituto', 'escola',
            # Academic titles
            'professor', 'prof', 'doctor', 'dr', 'research', 'academic',
            'faculty', 'staff', 'admin', 'office'
        ]
        
    # 💼 Corporate Expansion Configuration (Future)
    class Corporate:
        ENABLE_CORPORATE_MODE = os.getenv('ENABLE_CORPORATE_MODE', 'false').lower() == 'true'
        
        # Corporate Data Sources
        LINKEDIN_API_KEY = os.getenv('LINKEDIN_API_KEY', '')
        APOLLO_API_KEY = os.getenv('APOLLO_API_KEY', '')
        ZOOMINFO_API_KEY = os.getenv('ZOOMINFO_API_KEY', '')
        
        # Company Research
        CRUNCHBASE_API_KEY = os.getenv('CRUNCHBASE_API_KEY', '')
        CLEARBIT_API_KEY = os.getenv('CLEARBIT_API_KEY', '')
        
        # Corporate Templates
        CORPORATE_TEMPLATES = {
            'job_application': 'corporate/job_application.html',
            'informational_interview': 'corporate/informational_interview.html',
            'referral_request': 'corporate/referral_request.html',
            'industry_insights': 'corporate/industry_insights.html'
        }
        
    # 📱 Multi-Channel Configuration (Future)
    class MultiChannel:
        # Social Media
        ENABLE_LINKEDIN_OUTREACH = False
        ENABLE_TWITTER_OUTREACH = False
        
        # Messaging Platforms
        DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK', '')
        SLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK', '')
        TEAMS_WEBHOOK = os.getenv('TEAMS_WEBHOOK', '')
        
        # Mobile
        TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
        TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
        
    # 🎪 Conference and Event Configuration (Future)
    class Events:
        EVENTBRITE_API_KEY = os.getenv('EVENTBRITE_API_KEY', '')
        CONFERENCE_ALERT_WEBHOOK = os.getenv('CONFERENCE_ALERT_WEBHOOK', '')
        
        # Event Tracking
        TRACK_CONFERENCE_PARTICIPATION = True
        TRACK_RESEARCH_EVENTS = True
        
    # 🔧 Development Configuration
    class Development:
        DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'
        DRY_RUN = os.getenv('DRY_RUN', 'false').lower() == 'true'
        
        LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        ENABLE_VERBOSE_LOGGING = DEBUG_MODE
        
        # Testing
        TEST_EMAIL_ADDRESS = 'test@example.com'
        MAX_TEST_EMAILS = 5
        
    # 📊 Content Quality Configuration (Memory-based)
    class ContentQuality:
        # Content variation settings
        ENABLE_CONTENT_VARIATION = True
        MAX_REPETITION_THRESHOLD = 3
        SYNONYM_VARIATION_ENABLED = True
        
        # Quality scoring thresholds
        MIN_PERSONALIZATION_SCORE = 0.7
        MAX_SPAM_LIKELIHOOD = 0.3
        MIN_ENGAGEMENT_POTENTIAL = 0.6
        MIN_TECHNICAL_ACCURACY = 0.8
        
        # Content improvement settings
        AUTO_IMPROVE_CONTENT = True
        LEARNING_RATE = 0.1
        
    @classmethod
    def get_config_summary(cls) -> Dict:
        """📊 Get configuration summary for validation"""
        return {
            'email_provider': cls.Email.SMTP_SERVER,
            'max_daily_emails': cls.Email.MAX_EMAILS_PER_DAY,
            'ai_enabled': bool(cls.AI.GITHUB_TOKEN),
            'international_support': len(cls.International.SUPPORTED_LANGUAGES),
            'corporate_mode': cls.Corporate.ENABLE_CORPORATE_MODE,
            'security_enabled': cls.Security.GDPR_COMPLIANT,
            'debug_mode': cls.Development.DEBUG_MODE
        }
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """🔍 Validate configuration and return any issues"""
        issues = []
        
        # Check essential credentials
        if not cls.Email.GMAIL_USER or cls.Email.GMAIL_USER == 'your.email@gmail.com':
            issues.append("Gmail user not configured")
        
        if not cls.Email.GMAIL_APP_PASSWORD or cls.Email.GMAIL_APP_PASSWORD == 'your_app_password':
            issues.append("Gmail app password not configured")
        
        # Check AI configuration
        if not cls.AI.GITHUB_TOKEN:
            issues.append("GitHub token not configured - AI features disabled")
        
        # Check directories
        for directory in [cls.DATA_DIR, cls.TEMPLATES_DIR]:
            if not directory.exists():
                issues.append(f"Directory missing: {directory}")
        
        return issues
    
    @classmethod
    def get_database_paths(cls) -> Dict[str, str]:
        """📊 Get all database file paths"""
        return {
            'main': cls.Database.DATABASE_PATH,
            'tracking': cls.Database.TRACKING_DB_PATH,
            'cache': cls.Database.CACHE_DB_PATH
        }

# 🚀 Export configuration instance
config = InternMailingConfig()

# 🧪 Configuration validation on import
if __name__ == "__main__":
    print("🚀 InternMailing Configuration Validation")
    print("=" * 50)
    
    # Print configuration summary
    summary = config.get_config_summary()
    for key, value in summary.items():
        print(f"✅ {key}: {value}")
    
    # Check for issues
    issues = config.validate_config()
    if issues:
        print("\n⚠️ Configuration Issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n🎉 Configuration is valid!")
    
    print(f"\n📁 Data Directory: {config.DATA_DIR}")
    print(f"📧 Email Provider: {config.Email.SMTP_SERVER}")
    print(f"🌍 Languages: {', '.join(config.International.SUPPORTED_LANGUAGES)}")
    print(f"🔧 Debug Mode: {config.Development.DEBUG_MODE}")