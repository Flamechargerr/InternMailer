"""
Enhanced Configuration System with Conflict Resolution
======================================================

This module integrates the enhanced configuration manager with the existing
configuration system for backward compatibility.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import the enhanced configuration manager
from .config_manager import get_configuration_manager, get_config as get_unified_config

# NOTE: dotenv loading is handled entirely by ConfigurationManager.
# Do NOT call load_dotenv() here to avoid double-loading.

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Environment:
    """Environment type constants"""
    DEVELOPMENT = 'development'
    STAGING = 'staging'
    PRODUCTION = 'production'
    TEST = 'test'


def _resolve_db_path(env_var: str, default_relative: str) -> str:
    """Resolve a database path, routing to /tmp/internmailer_db/ for TCC safety."""
    val = os.getenv(env_var, '')
    if val and os.path.isabs(val):
        # Already absolute (e.g. set explicitly to /tmp/...)
        os.makedirs(os.path.dirname(val), exist_ok=True)
        return val
    # Use /tmp/internmailer_db/ to avoid macOS TCC permission issues
    base = '/tmp/internmailer_db'
    os.makedirs(base, exist_ok=True)
    filename = os.path.basename(val or default_relative)
    return os.path.join(base, filename)



class Config:
    """
    Enhanced configuration class with conflict resolution
    
    This class provides backward compatibility while using the enhanced
    configuration manager under the hood.
    """
    
    def __init__(self):
        """Initialize configuration with enhanced manager"""
        # Get the unified configuration
        self._unified_config = get_unified_config()
        self._manager = get_configuration_manager()
        
        # Set up environment from unified config or fallback
        self.ENV = os.getenv('ENVIRONMENT', Environment.DEVELOPMENT)
        self.DEBUG = self.ENV in (Environment.DEVELOPMENT, Environment.TEST)
        
        # Flask configuration (keep existing)
        self.SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(32).hex())
        self.FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
        self.FLASK_PORT = int(os.getenv('FLASK_PORT', 5050))
        self.FLASK_APP = os.getenv('FLASK_APP', 'web.web_dashboard')
        
        # Email configuration from unified config
        self.SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
        self.SMTP_POOL_SIZE = int(os.getenv('SMTP_POOL_SIZE', 5))
        
        # Use resolved email credentials
        self.GMAIL_USER = self._unified_config.email_credentials.user
        self.GMAIL_APP_PASSWORD = self._unified_config.email_credentials.password
        
        # For backward compatibility
        self.EMAIL_ADDRESS = self.GMAIL_USER
        self.EMAIL_PASSWORD = self.GMAIL_APP_PASSWORD
        
        # Email limits from unified config
        self.MAX_EMAILS_PER_DAY = self._unified_config.max_emails_per_day
        self.MAX_CONCURRENT_EMAILS = self._unified_config.max_concurrent_emails
        self.RATE_LIMIT_DELAY = self._unified_config.rate_limit_delay
        
        # AI Configuration from unified config
        self.GROQ_API_KEY = self._unified_config.groq_api_key
        self.GROQ_MODEL = self._unified_config.groq_model
        self.OPENROUTER_API_KEY = self._unified_config.openrouter_api_key
        self.GITHUB_TOKEN = self._unified_config.github_token
        self.OPENAI_API_KEY = self._unified_config.openai_api_key
        self.HUNTER_API_KEY = self._unified_config.hunter_api_key
        self.APOLLO_API_KEY = self._unified_config.apollo_api_key
        self.FRONTEND_ORIGIN = os.getenv('FRONTEND_ORIGIN', 'http://localhost:5173')
        
        # Database Configuration — always use /tmp/ to bypass TCC
        self.DATABASE_PATH = _resolve_db_path('DATABASE_PATH', 'email_tracking.db')
        self.INBOX_DB_PATH = _resolve_db_path('INBOX_DB_PATH', 'inbox_monitor.db')
        self.DAEMON_DB_PATH = _resolve_db_path('DAEMON_DB_PATH', 'daemon_status.db')
        self.CONTACTS_DB_PATH = _resolve_db_path('CONTACTS_DB_PATH', 'contacts.db')
        self.JOBS_DB_PATH = _resolve_db_path('JOBS_DB_PATH', 'job_discovery.db')
        
        # Profile / Personalization from unified config
        self.PROFILE_PATH = os.getenv('PROFILE_PATH', '')
        self.RESUME_PATHS = str(self._unified_config.resume_path) if self._unified_config.resume_path else ''
        self.RESUME_PATH = self.RESUME_PATHS  # For backward compatibility
        self.RESUME_PDF_PATH = self.RESUME_PATHS  # For backward compatibility
        self.CALENDAR_LINK = os.getenv('CALENDAR_LINK', '')
        
        # Feature flags from unified config
        self.AUTO_APPROVE_SENDS = os.getenv('AUTO_APPROVE_SENDS', 'false').lower() == 'true'
        self.EMAIL_STRICT_TEMPLATE = self._unified_config.email_strict_template
        self.EMAIL_SKIP_ACADEMIC = self._unified_config.email_skip_academic
        self.CONTACT_DISCOVERY_ENABLED = self._unified_config.contact_discovery_enabled
        self.CONTACT_DISCOVERY_DAILY_CAP = self._unified_config.contact_discovery_daily_cap
        self.CONTACT_ROLE_KEYWORDS = ','.join(self._unified_config.job_role_keywords)
        self.COMPANY_CONTACTS_CSV = os.getenv('COMPANY_CONTACTS_CSV', '/tmp/internmailer_db/company_contacts.csv')
        self.CONTACT_DISCOVERY_STATE_PATH = os.getenv('CONTACT_DISCOVERY_STATE_PATH', '/tmp/internmailer_db/contact_discovery_state.json')
        self.CONTACT_DISCOVERY_OVERRIDES = os.getenv('CONTACT_DISCOVERY_OVERRIDES', '/tmp/internmailer_db/company_domain_overrides.json')
        self.CONTACT_DISCOVERY_PROVIDERS = os.getenv('CONTACT_DISCOVERY_PROVIDERS', 'hunter,apollo')
        self.DEFAULT_ROLE_TITLE = os.getenv('DEFAULT_ROLE_TITLE', 'Software Engineering Intern')
        self.STRICT_TEMPLATE_KEYWORDS_EXTRA = os.getenv('STRICT_TEMPLATE_KEYWORDS_EXTRA', '')
        
        # Job Discovery from unified config
        self.JOB_SOURCES_PATH = str(self._unified_config.job_sources_path)
        self.JOB_DISCOVERY_MAX_RESULTS = int(os.getenv('JOB_DISCOVERY_MAX_RESULTS', 500))
        self.JOB_DISCOVERY_DAILY_CAP = int(os.getenv('JOB_DISCOVERY_DAILY_CAP', 50))
        self.JOB_SCORE_THRESHOLD = self._unified_config.job_score_threshold
        self.JOB_SEASON_START = self._unified_config.job_season_start
        self.JOB_SEASON_END = self._unified_config.job_season_end
        self.JOB_ALLOW_LONG_TERM = os.getenv('JOB_ALLOW_LONG_TERM', 'true').lower() == 'true'
        self.JOB_TARGET_LOCATIONS = ','.join(self._unified_config.job_target_locations)
        self.JOB_ALLOW_USA_WITH_VISA = os.getenv('JOB_ALLOW_USA_WITH_VISA', 'true').lower() == 'true'
        self.JOB_ROLE_KEYWORDS = ','.join(self._unified_config.job_role_keywords)
        self.JOB_FORTUNE500_CSV = os.getenv('JOB_FORTUNE500_CSV', 'data/fortune500_2019.csv')
        
        # Backup Configuration (keep existing)
        self.BACKUP_DIR = os.getenv('BACKUP_DIR', 'backups')
        self.BACKUP_INTERVAL_HOURS = int(os.getenv('BACKUP_INTERVAL_HOURS', 24))
        self.BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', 30))
        self.BACKUP_COMPRESSION = os.getenv('BACKUP_COMPRESSION', 'true').lower() == 'true'
        
        # Rate Limiting (keep existing)
        self.RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 60))
        self.RATE_LIMIT_PER_HOUR = int(os.getenv('RATE_LIMIT_PER_HOUR', 1000))
        self.RATE_LIMIT_PER_DAY = int(os.getenv('RATE_LIMIT_PER_DAY', 10000))
        self.RATE_LIMIT_TYPE = os.getenv('RATE_LIMIT_TYPE', 'sliding')
        
        # Security (keep existing)
        self.CSRF_ENABLED = os.getenv('CSRF_ENABLED', 'true').lower() == 'true'
        self.SESSION_SECURE = os.getenv('SESSION_SECURE', 'true').lower() == 'true'
        self.SESSION_HTTPONLY = os.getenv('SESSION_HTTPONLY', 'true').lower() == 'true'
        self.SESSION_SAMESITE = os.getenv('SESSION_SAMESITE', 'Lax')
        
        # Logging (keep existing)
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_DIR = os.getenv('LOG_DIR', 'logs')
        self.LOG_MAX_SIZE_MB = int(os.getenv('LOG_MAX_SIZE_MB', 10))
        self.LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))
        
        # Paths
        self.BASE_DIR = Path(__file__).resolve().parent.parent
        self.DATA_DIR = self.BASE_DIR / 'data'
        self.TEMPLATES_DIR = self.BASE_DIR / 'templates'
        self.LOGS_DIR = self.BASE_DIR / self.LOG_DIR
        self.CACHE_DIR = self.BASE_DIR / 'cache'
        self.BACKUP_DIR_PATH = self.BASE_DIR / self.BACKUP_DIR
        self.CAMPAIGN_RESULTS_DIR = self.BASE_DIR / 'campaign_results'
        
        # Daemon Configuration (keep existing)
        self.DAEMON_INTERVAL_MINUTES = int(os.getenv('DAEMON_INTERVAL_MINUTES', 60))
        self.DAEMON_SEND_PER_CYCLE = int(os.getenv('DAEMON_SEND_PER_CYCLE', 0))
        self.FOLLOWUP_DELAY_DAYS = int(os.getenv('FOLLOWUP_DELAY_DAYS', 7))
        
        # Health Check Configuration (keep existing)
        self.HEALTH_CHECK_ENABLED = os.getenv('HEALTH_CHECK_ENABLED', 'true').lower() == 'true'
        self.HEALTH_CHECK_INTERVAL_SECONDS = int(os.getenv('HEALTH_CHECK_INTERVAL_SECONDS', 30))
        
        # Agent Configuration (keep existing)
        self.AGENTS_DB_PATH = _resolve_db_path('AGENTS_DB_PATH', 'agents.db')
        self.HEALTH_DB_PATH = _resolve_db_path('HEALTH_DB_PATH', 'health.db')
        self.AGENT_EMAILS_PER_CYCLE = int(os.getenv('AGENT_EMAILS_PER_CYCLE', 20))
        self.AGENT_JOBS_PER_CYCLE = int(os.getenv('AGENT_JOBS_PER_CYCLE', 50))
        
        # Lead Discovery Configuration (keep existing)
        self.LEAD_DISCOVERY_ENABLED = os.getenv('LEAD_DISCOVERY_ENABLED', 'true').lower() == 'true'
        self.LEAD_DISCOVERY_LINKEDIN_ENABLED = os.getenv('LEAD_DISCOVERY_LINKEDIN_ENABLED', 'false').lower() == 'true'
        self.LEAD_DISCOVERY_GLASSDOOR_ENABLED = os.getenv('LEAD_DISCOVERY_GLASSDOOR_ENABLED', 'false').lower() == 'true'
        self.LEAD_DISCOVERY_ENRICHMENT_ENABLED = os.getenv('LEAD_DISCOVERY_ENRICHMENT_ENABLED', 'true').lower() == 'true'
        self.LEAD_DISCOVERY_HIRING_MANAGER_TITLES = os.getenv('LEAD_DISCOVERY_HIRING_MANAGER_TITLES', 
            'engineering manager,tech lead,cto,vp engineering,director of engineering,head of engineering,team lead')
        
        # Gmail Agent Configuration (keep existing)
        self.GMAIL_AGENT_ENABLED = os.getenv('GMAIL_AGENT_ENABLED', 'true').lower() == 'true'
        self.GMAIL_AUTO_REPLY_ENABLED = os.getenv('GMAIL_AUTO_REPLY_ENABLED', 'true').lower() == 'true'
        self.GMAIL_PRIORITY_SENDERS = os.getenv('GMAIL_PRIORITY_SENDERS', '')
        self.GMAIL_ARCHIVE_AFTER_DAYS = int(os.getenv('GMAIL_ARCHIVE_AFTER_DAYS', 30))
        
        # Scheduler Configuration (keep existing)
        self.SCHEDULER_AUTO_SCHEDULE = os.getenv('SCHEDULER_AUTO_SCHEDULE', 'false').lower() == 'true'
        
        # Blacklist/Whitelist Configuration (keep existing)
        self.BLACKLIST_DOMAINS = os.getenv('BLACKLIST_DOMAINS', '')
        self.WHITELIST_DOMAINS = os.getenv('WHITELIST_DOMAINS', '')
        self.TARGET_COMPANIES_LIST = os.getenv('TARGET_COMPANIES_LIST', '')
        
        # Log configuration state
        self._log_configuration()
    
    def _log_configuration(self) -> None:
        """Log configuration state"""
        logger.info("Enhanced configuration loaded with conflict resolution")
        
        # Log resolved conflicts
        if self._unified_config.email_credentials.resolved_conflicts:
            logger.info(f"Resolved email credential conflicts: {self._unified_config.email_credentials.resolved_conflicts}")
        
        # Log validation issues
        if self._unified_config.validation_issues:
            error_count = sum(1 for issue in self._unified_config.validation_issues if issue.severity == "error")
            warning_count = sum(1 for issue in self._unified_config.validation_issues if issue.severity == "warning")
            
            if error_count > 0:
                logger.error(f"Configuration has {error_count} error(s)")
            if warning_count > 0:
                logger.warning(f"Configuration has {warning_count} warning(s)")
            
            for issue in self._unified_config.validation_issues:
                if issue.severity == "error":
                    logger.error(f"{issue.message}")
                    if issue.suggestion:
                        logger.error(f"  Suggestion: {issue.suggestion}")
                elif issue.severity == "warning":
                    logger.warning(f"{issue.message}")
                    if issue.suggestion:
                        logger.warning(f"  Suggestion: {issue.suggestion}")
        
        # Log key configuration values (without sensitive data)
        from utils.security import SecretMasker
        masked_email = SecretMasker.mask_string(self.GMAIL_USER) if self.GMAIL_USER else "not configured"
        logger.info(f"Email user: {masked_email}")
        logger.info(f"Resume path: {self.RESUME_PATH}")
        logger.info(f"Job sources: {self.JOB_SOURCES_PATH}")
        logger.info(f"Configuration valid: {self._unified_config.is_valid()}")
    
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENV == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENV == Environment.DEVELOPMENT
    
    def is_staging(self) -> bool:
        """Check if running in staging"""
        return self.ENV == Environment.STAGING
    
    def get_database_url(self) -> str:
        """Get database URL (for future SQLAlchemy integration)"""
        return f"sqlite:///{self.DATABASE_PATH}"
    
    def validate_config(self) -> list[str]:
        """
        Validate configuration and return list of issues
        
        Returns:
            List of validation errors
        """
        issues = []
        
        # Use enhanced validation from unified config
        for issue in self._unified_config.validation_issues:
            if issue.severity == "error":
                issues.append(f"{issue.message} (variable: {issue.variable})")
        
        # Additional backward compatibility checks
        if not self.GMAIL_USER:
            issues.append('GMAIL_USER not configured')
        
        if not self.GMAIL_APP_PASSWORD:
            issues.append('GMAIL_APP_PASSWORD not configured')
        
        # Check directories
        for dir_path in [self.DATA_DIR, self.LOGS_DIR, self.BACKUP_DIR_PATH]:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create directory {dir_path}: {e}")
        
        # Check numeric values
        if self.MAX_EMAILS_PER_DAY <= 0:
            issues.append('MAX_EMAILS_PER_DAY must be positive')
        
        if self.MAX_CONCURRENT_EMAILS <= 0:
            issues.append('MAX_CONCURRENT_EMAILS must be positive')
        
        if self.DAEMON_INTERVAL_MINUTES <= 0:
            issues.append('DAEMON_INTERVAL_MINUTES must be positive')
        
        return issues
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get configuration summary (without sensitive data)
        
        Returns:
            Dictionary of configuration settings
        """
        return {
            'environment': self.ENV,
            'debug': self.DEBUG,
            'flask': {
                'host': self.FLASK_HOST,
                'port': self.FLASK_PORT
            },
            'email': {
                'server': self.SMTP_SERVER,
                'port': self.SMTP_PORT,
                'max_per_day': self.MAX_EMAILS_PER_DAY,
                'max_concurrent': self.MAX_CONCURRENT_EMAILS,
                'user_configured': bool(self.GMAIL_USER),
                'password_configured': bool(self.GMAIL_APP_PASSWORD)
            },
            'ai': {
                'groq_configured': bool(self.GROQ_API_KEY),
                'openrouter_configured': bool(self.OPENROUTER_API_KEY),
                'github_configured': bool(self.GITHUB_TOKEN)
            },
            'rate_limiting': {
                'per_minute': self.RATE_LIMIT_PER_MINUTE,
                'per_hour': self.RATE_LIMIT_PER_HOUR,
                'per_day': self.RATE_LIMIT_PER_DAY
            },
            'security': {
                'csrf_enabled': self.CSRF_ENABLED,
                'session_secure': self.SESSION_SECURE,
                'session_httponly': self.SESSION_HTTPONLY
            },
            'backup': {
                'interval_hours': self.BACKUP_INTERVAL_HOURS,
                'retention_days': self.BACKUP_RETENTION_DAYS,
                'compression': self.BACKUP_COMPRESSION
            },
            'daemon': {
                'interval_minutes': self.DAEMON_INTERVAL_MINUTES,
                'send_per_cycle': self.DAEMON_SEND_PER_CYCLE
            },
            'jobs': {
                'sources_path': self.JOB_SOURCES_PATH,
                'max_results': self.JOB_DISCOVERY_MAX_RESULTS,
                'daily_cap': self.JOB_DISCOVERY_DAILY_CAP,
                'score_threshold': self.JOB_SCORE_THRESHOLD,
                'season_start': self.JOB_SEASON_START,
                'season_end': self.JOB_SEASON_END
            },
            'validation': {
                'is_valid': self._unified_config.is_valid(),
                'has_warnings': self._unified_config.has_warnings(),
                'issue_count': len(self._unified_config.validation_issues)
            }
        }
    
    def get_unified_config_summary(self) -> Dict[str, Any]:
        """Get the enhanced configuration manager summary"""
        return self._manager.get_configuration_summary()


# Create singleton instance
config = Config()


def get_config() -> Config:
    """Return the singleton Config instance (convenience re-export)."""
    return config