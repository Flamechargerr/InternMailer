#!/usr/bin/env python3
"""
🚀 EMAIL SYSTEM v5.0 - Full Automation for Job Applications
===========================================================
Consolidated email system for sending personalized job application emails.

Features:
- AI-powered personalization
- Anti-templating for unique emails
- Rate limiting and safety
- Gmail SMTP integration
- SQLite tracking

Usage:
    from email_system import EmailSystem
    system = EmailSystem()
    system.send_campaign(count=50)
"""

import os
import sqlite3
import smtplib
import time
import random
import csv
import re
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from threading import Lock
from queue import Queue, Empty, Full
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager

# Config and profile
from utils.config import config
from utils.profile import get_profile
from utils.validators import EmailValidator
from core.database_manager import get_job_discovery_db

# Set up logging first
logger = logging.getLogger(__name__)

# Import AI components
try:
    from core.unified_ai_provider import get_unified_ai_provider, PersonalizationResult
    from core.anti_templating_engine import get_anti_templating_engine
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    logger.warning("AI components not available")


class RateLimiter:
    """Rate limiter for email sending with configurable limits"""
    
    def __init__(self, min_delay: float = 0.1, max_daily: int = 100):
        self.min_delay = min_delay  # Minimum seconds between emails
        self.max_daily = max_daily  # Maximum emails per day
        self.last_send_time = 0
        self.daily_sent = 0
        self.daily_reset_time = self._get_daily_reset_time()
        self.lock = Lock()
    
    def _get_daily_reset_time(self) -> float:
        """Get timestamp for next daily reset (midnight)"""
        now = datetime.now()
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return tomorrow.timestamp()
    
    def _check_daily_reset(self):
        """Check and reset daily counter if needed"""
        now = time.time()
        if now >= self.daily_reset_time:
            self.daily_sent = 0
            self.daily_reset_time = self._get_daily_reset_time()
    
    def can_send(self) -> Tuple[bool, str]:
        """Check if we can send an email now"""
        with self.lock:
            self._check_daily_reset()
            
            if self.daily_sent >= self.max_daily:
                return False, f"Daily limit reached ({self.daily_sent}/{self.max_daily})"
            
            return True, f"OK ({self.daily_sent}/{self.max_daily} today)"
    
    def wait_if_needed(self):
        """Wait if needed to maintain rate limit"""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_send_time
            
            if elapsed < self.min_delay:
                wait_time = self.min_delay - elapsed + random.uniform(0, 0.1)  # Add jitter
                time.sleep(wait_time)
            
            self.last_send_time = time.time()
    
    def record_sent(self):
        """Record that an email was sent"""
        with self.lock:
            self._check_daily_reset()
            self.daily_sent += 1
    
    def get_status(self) -> Dict[str, Any]:
        """Get current rate limiter status"""
        with self.lock:
            self._check_daily_reset()
            return {
                'daily_sent': self.daily_sent,
                'daily_limit': self.max_daily,
                'remaining_today': self.max_daily - self.daily_sent,
                'min_delay': self.min_delay,
                'next_reset': datetime.fromtimestamp(self.daily_reset_time).isoformat()
            }


class SMTPConnectionPool:
    """Connection pool for SMTP connections with proper error handling and connection reuse"""
    
    def __init__(self, email: str, password: str, pool_size: int = 5):
        self.email = email
        self.password = password
        self.pool_size = pool_size
        self.connections: Queue = Queue(maxsize=pool_size)
        self.lock = Lock()
        self.failed_connections = 0
        self.total_connections_created = 0
    
    def _initialize_pool(self):
        """Initialize connection pool with proper error tracking"""
        successful = 0
        for i in range(self.pool_size):
            try:
                connection = self._create_connection()
                self.connections.put(connection)
                successful += 1
            except Exception as e:
                logger.warning(f"Failed to create SMTP connection {i+1}/{self.pool_size}: {e}")
                self.failed_connections += 1
        
        if successful == 0:
            logger.warning("⚠️ Failed to pre-initialize any SMTP connections. Connections will be created lazily when sending.")
        elif successful < self.pool_size:
            logger.warning(f"Connection pool partially initialized: {successful}/{self.pool_size} connections created")
        else:
            logger.info(f"✅ Connection pool initialized with {successful} connections")
    
    def _create_connection(self) -> smtplib.SMTP:
        """
        Create a new SMTP connection with proper error handling.
        
        Raises:
            smtplib.SMTPAuthenticationError: If authentication fails
            smtplib.SMTPConnectError: If connection fails
            smtplib.SMTPException: For other SMTP errors
        """
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
            server.starttls()
            server.login(self.email, self.password)
            self.total_connections_created += 1
            logger.debug(f"Created new SMTP connection (total: {self.total_connections_created})")
            return server
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP authentication failed: {e}")
            raise
        except smtplib.SMTPConnectError as e:
            logger.error(f"❌ SMTP connection failed: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error creating SMTP connection: {e}")
            raise
    
    def _is_connection_alive(self, connection: smtplib.SMTP) -> bool:
        """
        Check if a connection is still alive and usable.
        
        Args:
            connection: SMTP connection to test
            
        Returns:
            True if connection is alive, False otherwise
        """
        try:
            status = connection.noop()
            return status[0] == 250
        except (smtplib.SMTPServerDisconnected, smtplib.SMTPException, OSError):
            return False
        except Exception as e:
            logger.debug(f"Unexpected error checking connection health: {e}")
            return False
    
    @contextmanager
    def get_connection(self):
        """
        Get a connection from the pool (context manager).
        
        This method:
        1. Tries to get a connection from the pool
        2. Validates the connection is still alive
        3. Creates a new connection if needed
        4. Returns the connection to the pool after use (if still valid)
        5. Handles all errors properly
        
        Yields:
            smtplib.SMTP: A valid SMTP connection
            
        Raises:
            smtplib.SMTPException: If unable to get a valid connection
        """
        connection = None
        connection_from_pool = False
        
        try:
            # Try to get from pool
            try:
                connection = self.connections.get_nowait()
                connection_from_pool = True
                logger.debug("Got connection from pool")
                
                # Validate connection is still alive
                if not self._is_connection_alive(connection):
                    logger.debug("Connection from pool is dead, creating new one")
                    try:
                        connection.quit()
                    except Exception:
                        pass  # Ignore errors closing dead connection
                    connection = self._create_connection()
                    connection_from_pool = False
                    
            except Empty:
                # Pool is empty, create new connection
                logger.debug("Pool empty, creating new connection")
                connection = self._create_connection()
                connection_from_pool = False
            
            # Yield the connection for use
            yield connection
            
            # After successful use, return connection to pool if still valid
            if connection:
                if self._is_connection_alive(connection):
                    try:
                        self.connections.put_nowait(connection)
                        logger.debug("Returned connection to pool")
                    except Full:
                        # Pool is full, close this connection
                        logger.debug("Pool full, closing connection")
                        try:
                            connection.quit()
                        except Exception:
                            pass
                else:
                    # Connection died during use, close it
                    logger.debug("Connection died during use, closing")
                    try:
                        connection.quit()
                    except Exception:
                        pass
                    
                    # Try to create a replacement connection for the pool
                    try:
                        new_connection = self._create_connection()
                        try:
                            self.connections.put_nowait(new_connection)
                            logger.debug("Created replacement connection for pool")
                        except Full:
                            new_connection.quit()
                    except Exception as e:
                        logger.warning(f"Failed to create replacement connection: {e}")
                        
        except Exception as e:
            # Error occurred, clean up connection
            if connection:
                try:
                    connection.quit()
                except Exception:
                    pass  # Ignore errors closing connection
            raise e
    
    def close_all(self):
        """Close all connections in the pool"""
        closed = 0
        errors = 0
        
        while not self.connections.empty():
            try:
                connection = self.connections.get_nowait()
                connection.quit()
                closed += 1
            except Empty:
                break
            except Exception as e:
                logger.debug(f"Error closing connection: {e}")
                errors += 1
        
        logger.info(f"Closed {closed} connections ({errors} errors)")
    
    def get_stats(self) -> Dict[str, int]:
        """Get connection pool statistics"""
        return {
            'pool_size': self.pool_size,
            'available_connections': self.connections.qsize(),
            'total_created': self.total_connections_created,
            'failed_connections': self.failed_connections
        }


class EmailSystem:
    """
    Unified email system for job application campaigns with enhanced reliability.
    """
    
    def __init__(self):
        # Load profile and credentials
        self.profile = get_profile()
        self.email = config.EMAIL_ADDRESS or self.profile.get('email')
        self.password = config.EMAIL_PASSWORD
        
        if not self.email or not self.password:
            error_msg = """
❌ Email credentials not found!

Required environment variables:
  - GMAIL_USER or EMAIL_ADDRESS: Your Gmail address
  - GMAIL_APP_PASSWORD or EMAIL_PASSWORD: Your Gmail app password

Setup instructions:
  1. Enable 2-Step Verification in your Google account
  2. Generate an App Password at: https://myaccount.google.com/apppasswords
  3. Add to .env file:
     GMAIL_USER=your.email@gmail.com
     GMAIL_APP_PASSWORD=your_16_char_app_password
            """
            logger.error(error_msg)
            raise ValueError("Email credentials not configured. See error message above for setup instructions.")
        
        # Gmail credentials validation is handled lazily during actual email sending
        self.credentials_valid = True
        
        # Database paths
        self.contacts_db = config.CONTACTS_DB_PATH
        self.tracking_db = config.DATABASE_PATH
        
        # Initialize AI components
        self.ai_provider = None
        self.anti_template = None
        if AI_AVAILABLE:
            try:
                self.ai_provider = get_unified_ai_provider()
                self.anti_template = get_anti_templating_engine()
            except Exception as e:
                logger.warning(f"AI initialization failed: {e}")
        
        # Thread safety and connection pooling
        self.send_lock = Lock()
        self.connection_pool = SMTPConnectionPool(
            email=self.email,
            password=self.password,
            pool_size=min(config.MAX_CONCURRENT_EMAILS, 10)
        )
        
        # Rate limiting
        self.rate_limiter = RateLimiter(
            min_delay=float(config.RATE_LIMIT_DELAY),
            max_daily=int(config.MAX_EMAILS_PER_DAY)
        )
        
        # Store max daily emails for easy access
        self.max_daily_emails = int(config.MAX_EMAILS_PER_DAY)
        
        # Statistics
        self.stats = {
            'sent': 0,
            'failed': 0,
            'skipped': 0,
            'ai_generated': 0,
            'fallback_used': 0,
            'auth_errors': 0,
            'connection_errors': 0,
            'rate_limit_hits': 0,
            'daily_limit_exceeded': 0
        }
        
        self.auto_approve = bool(config.AUTO_APPROVE_SENDS)
        
        # Ensure directories exist
        os.makedirs(Path(self.tracking_db).parent, exist_ok=True)
        os.makedirs(Path(self.contacts_db).parent, exist_ok=True)
        
        # Initialize tracking DB
        self._init_tracking_db()
        
        logger.info("🚀 Email System initialized")
        logger.info(f"   Email: {self.email}")
        logger.info(f"   Daily Limit: {self.max_daily_emails}")
        logger.info(f"   Connection Pool Size: {self.connection_pool.pool_size}")
    
    def _validate_credentials(self) -> bool:
        """
        Validate Gmail credentials before using them.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        logger.info("Validating Gmail credentials...")
        
        try:
            # Test SMTP connection and authentication
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
                server.starttls()
                
                try:
                    server.login(self.email, self.password)
                except smtplib.SMTPAuthenticationError as auth_error:
                    logger.error(f"❌ Gmail authentication failed: {auth_error}")
                    logger.error("""
Common Gmail authentication issues:
1. Ensure 2-Step Verification is enabled in your Google account
2. Generate an App Password at: https://myaccount.google.com/apppasswords
3. Use the 16-character app password (not your regular password)
4. Make sure the app password is copied correctly (no spaces)
5. Check that your Google account is not locked or suspended

Troubleshooting steps:
- Visit https://myaccount.google.com/security
- Verify 2-Step Verification is ON
- Go to App Passwords and create a new one for "Mail"
- Copy the 16-character password exactly
- Update GMAIL_APP_PASSWORD in your .env file
                    """)
                    return False
                
                # Send a test NOOP command to verify connection
                response = server.noop()
                if response[0] == 250:
                    logger.info("✅ Gmail credentials validated successfully")
                    return True
                else:
                    logger.error(f"❌ Gmail validation failed with response: {response}")
                    return False
                    
        except smtplib.SMTPAuthenticationError as e:
            # Already handled above, but catch again for safety
            logger.error(f"❌ Gmail authentication failed: {e}")
            return False
            
        except smtplib.SMTPConnectError as e:
            logger.error(f"❌ SMTP connection error: {e}")
            logger.error("Check your network connection and firewall settings")
            logger.error("Gmail SMTP server: smtp.gmail.com:587")
            return False
            
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error: {e}")
            logger.error("This may be a temporary Gmail service issue. Try again in a few minutes.")
            return False
            
        except Exception as e:
            logger.error(f"❌ Unexpected error during credential validation: {e}")
            logger.error("Check your system configuration and network connectivity")
            return False
    
    def _init_tracking_db(self):
        """Initialize tracking database with enhanced schema"""
        with sqlite3.connect(self.tracking_db) as conn:
            # Create main tracking table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sent_emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT,
                    name TEXT,
                    company TEXT,
                    position TEXT,
                    subject TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    provider_used TEXT,
                    ai_confidence REAL,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    followup_sent BOOLEAN DEFAULT 0,
                    replied BOOLEAN DEFAULT 0,
                    retry_count INTEGER DEFAULT 0,
                    last_retry_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(email, sent_at)  -- Allow same email on different days
                )
            ''')
            
            # Create rate limiting tracking table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS rate_limit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    action TEXT,
                    daily_sent INTEGER,
                    daily_limit INTEGER,
                    min_delay REAL,
                    was_allowed BOOLEAN,
                    reason TEXT
                )
            ''')
            
            # Create campaign statistics table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS campaign_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_date DATE DEFAULT CURRENT_DATE,
                    total_sent INTEGER DEFAULT 0,
                    total_failed INTEGER DEFAULT 0,
                    total_skipped INTEGER DEFAULT 0,
                    ai_generated INTEGER DEFAULT 0,
                    fallback_used INTEGER DEFAULT 0,
                    auth_errors INTEGER DEFAULT 0,
                    connection_errors INTEGER DEFAULT 0,
                    rate_limit_hits INTEGER DEFAULT 0,
                    daily_limit_exceeded INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(campaign_date)
                )
            ''')
            
            # Migrations for legacy schemas
            existing_cols = [row[1] for row in conn.execute("PRAGMA table_info(sent_emails)")]
            
            # Add missing columns - SQLite doesn't allow DEFAULT with functions in ALTER TABLE
            # So we add columns without defaults and then update them
            columns_to_add = [
                ('error_message', 'TEXT'),
                ('retry_count', 'INTEGER'),
                ('last_retry_at', 'TIMESTAMP'),
                ('created_at', 'TIMESTAMP'),
                ('updated_at', 'TIMESTAMP'),
                ('status', 'TEXT')
            ]
            
            for col_name, col_type in columns_to_add:
                if col_name not in existing_cols:
                    try:
                        conn.execute(f"ALTER TABLE sent_emails ADD COLUMN {col_name} {col_type}")
                        
                        # Set default values after adding column
                        if col_name == 'retry_count':
                            conn.execute(f"UPDATE sent_emails SET {col_name} = 0 WHERE {col_name} IS NULL")
                        elif col_name == 'status':
                            conn.execute(f"UPDATE sent_emails SET {col_name} = 'pending' WHERE {col_name} IS NULL")
                        elif col_name in ('created_at', 'updated_at'):
                            conn.execute(f"UPDATE sent_emails SET {col_name} = CURRENT_TIMESTAMP WHERE {col_name} IS NULL")
                    except Exception as e:
                        logger.warning(f"Could not add column {col_name}: {e}")
            
            # Backfill legacy columns if present
            if 'university' in existing_cols and 'company' in existing_cols:
                conn.execute(
                    "UPDATE sent_emails SET company = COALESCE(company, university)"
                )
            if 'research_area' in existing_cols and 'position' in existing_cols:
                conn.execute(
                    "UPDATE sent_emails SET position = COALESCE(position, research_area)"
                )
            
            # Update status for existing records
            conn.execute("UPDATE sent_emails SET status = 'sent' WHERE status IS NULL OR status = ''")
            
            conn.commit()
            
            logger.info(f"Tracking database initialized: {self.tracking_db}")
    
    def get_daily_sent_count(self) -> int:
        """Get number of emails sent today from database"""
        today = datetime.now().strftime('%Y-%m-%d')
        try:
            with sqlite3.connect(self.tracking_db) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM sent_emails WHERE DATE(sent_at) = ? AND status = 'sent'",
                    (today,)
                )
                return cursor.fetchone()[0]
        except:
            return 0
    
    def can_send_today(self) -> Tuple[bool, int]:
        """Check if we can send more emails today using rate limiter"""
        can_send, message = self.rate_limiter.can_send()
        status = self.rate_limiter.get_status()
        remaining = status['remaining_today']
        return can_send, remaining
    
    def get_fresh_contacts(self, count: int = 50) -> List[Tuple]:
        """
        Get contacts that haven't been emailed yet.
        Looks for company contacts CSV first, then falls back to data/ CSVs.
        """
        # Get already sent emails
        sent_emails = set()
        try:
            with sqlite3.connect(self.tracking_db) as conn:
                cursor = conn.execute("SELECT email FROM sent_emails")
                sent_emails = {row[0].lower() for row in cursor.fetchall()}
        except:
            pass
        
        contacts = []
        
        csv_files: List[Path] = []
        company_csv = Path(config.COMPANY_CONTACTS_CSV)
        if company_csv.exists():
            csv_files = [company_csv]
        else:
            if config.EMAIL_SKIP_ACADEMIC:
                logger.warning(f"⚠️  Company contacts CSV missing at {company_csv.absolute()}")
                logger.warning("   Academic fallback disabled. No contacts available.")
                logger.warning(f"   Please create {company_csv} with contact data or set EMAIL_SKIP_ACADEMIC=false")
                return contacts
            # Fallback to any CSVs in data directory (legacy)
            data_dir = Path(self.contacts_db).parent
            csv_files = list(data_dir.glob('*.csv'))
        
        if not csv_files:
            logger.error(f"❌ No CSV files found for contacts")
            logger.error(f"   Expected: {company_csv.absolute()}")
            logger.error(f"   Searched: {data_dir.absolute()}")
            logger.error("   Please add contact CSV files to enable email campaigns")
            return contacts
        
        for csv_path in csv_files:
            try:
                with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    random.shuffle(rows)
                    
                    for row in rows:
                        # Try common column names
                        name = (row.get('Name') or row.get('name') or 
                                row.get('Full Name') or row.get('full_name') or '').strip()
                        email = (row.get('Email') or row.get('email') or 
                                 row.get('E-mail') or row.get('e-mail') or '').strip()
                        company = (row.get('Company') or row.get('company') or 
                                   row.get('University') or row.get('university') or 
                                   row.get('Organization') or '').strip()
                        position = (row.get('Position') or row.get('position') or 
                                    row.get('Title') or row.get('title') or 
                                    row.get('Research Interest') or '').strip()
                        job_url = (row.get('job_url') or row.get('Job URL') or row.get('url')
                                   or row.get('apply_url') or row.get('posting_url') or '').strip()
                        company = self._normalize_company_name(company)
                        
                        if email and email.lower() not in sent_emails:
                            email = EmailValidator.sanitize_email(email)
                            if not EmailValidator.is_valid_email(email):
                                continue
                            if config.EMAIL_SKIP_ACADEMIC and self._is_academic_contact(company, email):
                                continue
                            contacts.append((name, email, company, position, job_url))
                            if len(contacts) >= count:
                                break
                    if len(contacts) >= count:
                        break
            except Exception as e:
                logger.warning(f"Error reading {csv_path}: {e}")
                continue
        
        return contacts

    def _is_academic_contact(self, company: str, email: str) -> bool:
        """Return True if contact is academic (.edu or university keywords)."""
        domain = (email.split("@")[-1] if email else "").lower()
        if domain.endswith(".edu") or ".edu." in domain:
            return True
        if domain.endswith(".ac.uk") or domain.endswith(".ac.in") or ".ac." in domain:
            return True
        company_lower = (company or "").lower()
        academic_keywords = [
            "university",
            "college",
            "institute",
            "school",
            "department",
            "dept",
            "faculty",
            "laboratory",
            "lab",
            "academy",
            "research",
        ]
        return any(keyword in company_lower for keyword in academic_keywords)

    def _normalize_company_name(self, company: str) -> str:
        if not company:
            return ""
        value = company.strip()
        # If it's a domain, strip TLD and title-case
        if "." in value and " " not in value:
            value = value.split("@")[-1]
            value = value.split(":")[-1]
            if value.count(".") >= 1:
                base = value.split(".")[0]
                if base:
                    return base.replace("-", " ").title()
        return value

    def _resolve_job_context(self, company: str, email: str, job_url: str = "") -> Dict[str, str]:
        """Resolve job title, url, and description from the jobs DB."""
        default_role = config.DEFAULT_ROLE_TITLE or "Software Engineering Intern"
        company_name = self._normalize_company_name(company or "")
        email_domain = ""
        if email and "@" in email:
            email_domain = email.split("@")[-1].lower()

        def _select_row(rows: List[sqlite3.Row]) -> Optional[sqlite3.Row]:
            return rows[0] if rows else None

        try:
            db = get_job_discovery_db(config.JOBS_DB_PATH)
        except Exception:
            db = None

        row = None
        if db and job_url:
            try:
                row = _select_row(
                    db.fetch_all(
                        """
                        SELECT title, url, apply_url, description, score, posted_at, updated_at, created_at
                        FROM jobs
                        WHERE url = ? OR apply_url = ?
                        ORDER BY score DESC, posted_at DESC, updated_at DESC, created_at DESC, id DESC
                        LIMIT 1
                        """,
                        (job_url, job_url),
                    )
                )
            except Exception:
                row = None

        if db and not row and email_domain:
            like = f"%{email_domain}%"
            try:
                row = _select_row(
                    db.fetch_all(
                        """
                        SELECT title, url, apply_url, description, score, posted_at, updated_at, created_at
                        FROM jobs
                        WHERE url LIKE ? OR apply_url LIKE ?
                        ORDER BY score DESC, posted_at DESC, updated_at DESC, created_at DESC, id DESC
                        LIMIT 1
                        """,
                        (like, like),
                    )
                )
            except Exception:
                row = None

        if db and not row and company_name:
            try:
                row = _select_row(
                    db.fetch_all(
                        """
                        SELECT title, url, apply_url, description, score, posted_at, updated_at, created_at
                        FROM jobs
                        WHERE lower(company) = ?
                        ORDER BY score DESC, posted_at DESC, updated_at DESC, created_at DESC, id DESC
                        LIMIT 1
                        """,
                        (company_name.lower(),),
                    )
                )
                if not row:
                    row = _select_row(
                        db.fetch_all(
                            """
                            SELECT title, url, apply_url, description, score, posted_at, updated_at, created_at
                            FROM jobs
                            WHERE lower(company) LIKE ?
                            ORDER BY score DESC, posted_at DESC, updated_at DESC, created_at DESC, id DESC
                            LIMIT 1
                            """,
                            (f"%{company_name.lower()}%",),
                        )
                    )
            except Exception:
                row = None

        resolved_title = default_role
        resolved_url = job_url or ""
        resolved_description = ""

        if row:
            resolved_title = row["title"] or default_role
            resolved_url = row["apply_url"] or row["url"] or resolved_url
            resolved_description = row["description"] or ""

        return {
            "job_title": resolved_title,
            "job_url": resolved_url,
            "job_description": resolved_description,
        }

    def _strict_keyword_whitelist(self) -> List[str]:
        curated = [
            "python",
            "sql",
            "java",
            "javascript",
            "react",
            "node",
            "node.js",
            "flask",
            "express",
            "etl",
            "data pipeline",
            "data pipelines",
            "data modeling",
            "dashboard",
            "analytics",
            "ml",
            "ai",
            "machine learning",
            "ci/cd",
            "testing",
            "automation",
            "api",
            "backend",
            "frontend",
            "full stack",
            "postgresql",
            "mongodb",
        ]
        skills = self.profile.get("skills") or []
        if isinstance(skills, dict):
            flat = []
            for values in skills.values():
                if isinstance(values, list):
                    flat.extend(values)
            skills = flat
        skills = [s.strip().lower() for s in skills if isinstance(s, str)]
        extra = []
        if config.STRICT_TEMPLATE_KEYWORDS_EXTRA:
            extra = [k.strip().lower() for k in config.STRICT_TEMPLATE_KEYWORDS_EXTRA.split(",") if k.strip()]
        seen = set()
        whitelist = []
        for item in curated + skills + extra:
            if item and item not in seen:
                whitelist.append(item)
                seen.add(item)
        return whitelist

    def _extract_job_keywords(self, description: str, limit: int = 3) -> List[str]:
        if not description:
            return []
        text = description.lower()
        keywords = []
        for keyword in self._strict_keyword_whitelist():
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, text):
                keywords.append(keyword)
                if len(keywords) >= limit:
                    break
        return keywords

    def _summarize_highlight(self, highlight: str) -> str:
        if not highlight:
            return "building reliable systems"
        summary = highlight.split(",")[0].strip()
        summary = summary.rstrip(".")
        return summary or "building reliable systems"
    
    def generate_personalized_email(
        self,
        contact_name: str,
        email: str,
        company: str,
        position: str,
        use_ai: bool = True,
        job_url: str = ""
    ) -> Tuple[str, str, Dict]:
        """
        Generate personalized email for a contact with robust fallback handling.
        
        Ensures unique content for each recipient through:
        1. AI personalization with uniqueness seed
        2. Anti-templating engine with variation
        3. Fallback templates with deterministic variation
        
        Returns:
            Tuple of (subject, html_body, metadata)
        """
        # Create uniqueness seed from all contact information
        # This ensures each recipient gets unique content
        uniqueness_seed = f"{contact_name}_{email}_{company}_{position}_{job_url}"
        
        metadata = {
            'ai_used': False,
            'provider': 'none',
            'confidence': 0.0,
            'generation_time_ms': 0,
            'fallback_used': False,
            'uniqueness_seed': uniqueness_seed
        }
        
        ai_personalization = None
        
        # Check if strict template mode is enabled
        if config.EMAIL_STRICT_TEMPLATE:
            use_ai = False
            logger.debug("Using strict template mode (AI disabled)")

        # Handle strict template mode
        if config.EMAIL_STRICT_TEMPLATE:
            try:
                context = self._resolve_job_context(company=company, email=email, job_url=job_url)
                role = context.get("job_title") or config.DEFAULT_ROLE_TITLE or "Software Engineering Intern"
                resolved_job_url = context.get("job_url") or job_url
                job_description = context.get("job_description") or ""
                subject, html_body = self._generate_strict_email(
                    contact_name=contact_name,
                    company=company,
                    position=role,
                    job_url=resolved_job_url,
                    job_description=job_description,
                )
                metadata['provider'] = 'strict_template'
                return subject, html_body, metadata
            except Exception as e:
                logger.warning(f"Strict template generation failed: {e}, falling back to regular template")
                metadata['fallback_used'] = True

        # Attempt AI personalization if enabled and available
        if use_ai and self.ai_provider:
            try:
                # Build candidate context for role-based personalization
                experience = self.profile.get("experience_highlights") or []
                projects = self.profile.get("project_highlights") or []
                skills = self.profile.get("skills") or []
                
                # Flatten skills if it's a dictionary
                if isinstance(skills, dict):
                    flat = []
                    for values in skills.values():
                        if isinstance(values, list):
                            flat.extend(values)
                    skills = flat
                
                skills = [s for s in skills if isinstance(s, str)]
                candidate_background = "; ".join(
                    [*experience[:2], *projects[:1], f"Skills: {', '.join(skills[:6])}"]
                ).strip("; ")

                # Generate AI personalization with uniqueness seed
                # The seed ensures different content for each recipient
                ai_result = self.ai_provider.generate_role_personalization(
                    contact_name=contact_name or "Hiring Manager",
                    company=company or "your organization",
                    role=position or "Software Engineering",
                    candidate_background=candidate_background,
                    uniqueness_seed=uniqueness_seed
                )
                
                metadata['ai_used'] = True
                metadata['provider'] = ai_result.provider_used
                metadata['confidence'] = ai_result.confidence
                metadata['generation_time_ms'] = ai_result.generation_time_ms
                
                ai_personalization = {
                    'opening_hook': ai_result.opening_hook,
                    'connection_paragraph': ai_result.connection_paragraph,
                    'research_mention': ai_result.research_mention,
                    'why_fit': ai_result.why_fit
                }
                
                logger.debug(f"AI personalization generated for {email}: {metadata['provider']} (confidence: {metadata['confidence']:.2f})")
                
            except Exception as e:
                logger.warning(f"AI generation failed for {email}: {e}, falling back to templates")
                metadata['fallback_used'] = True
                # Continue to fallback templates
        
        # Generate email with appropriate template engine
        try:
            if self.anti_template:
                # Use anti-templating engine for uniqueness
                # Pass the uniqueness seed to ensure variation
                subject, html_body = self.anti_template.generate_html_email(
                    contact_name=contact_name,
                    company=company or "your organization",
                    focus_area=position or "the role",
                    ai_personalization=ai_personalization,
                    seed=uniqueness_seed,
                    profile=self.profile
                )
                metadata['provider'] = 'anti_template' if metadata['provider'] == 'none' else metadata['provider']
                logger.debug(f"Anti-template email generated for {email}")
            else:
                # Fallback to basic template with uniqueness seed
                subject = f"Application for {position or 'open roles'} at {company or 'your organization'}"
                html_body = self._generate_fallback_email(
                    contact_name, 
                    company, 
                    position, 
                    uniqueness_seed=uniqueness_seed
                )
                metadata['provider'] = 'fallback_template'
                metadata['fallback_used'] = True
                logger.debug(f"Fallback template used for {email}")
                
        except Exception as e:
            logger.error(f"Template generation failed for {email}: {e}, using minimal fallback")
            # Ultimate fallback with uniqueness seed
            subject = f"Interest in {position or 'opportunities'} at {company or 'your organization'}"
            html_body = self._generate_minimal_fallback_email(
                contact_name, 
                company, 
                position,
                uniqueness_seed=uniqueness_seed
            )
            metadata['provider'] = 'minimal_fallback'
            metadata['fallback_used'] = True
        
        return subject, html_body, metadata

    def _generate_strict_email(
        self,
        contact_name: str,
        company: str,
        position: str,
        job_url: str = "",
        job_description: str = "",
    ) -> Tuple[str, str]:
        role = position or config.DEFAULT_ROLE_TITLE or "Software Engineering Intern"
        company_name = self._normalize_company_name(company or "your company")
        role_lower = role.lower()
        if "intern" in role_lower:
            subject = f"Interest in {role} at {company_name}"
        else:
            subject = f"Interest in {role} internship at {company_name}"

        posting_line = f"I’m reaching out about the {role} opportunity at {company_name}."
        if job_url:
            posting_line = (
                f"I’m reaching out about the {role} posting at {company_name}: "
                f"<a href=\"{job_url}\">{job_url}</a>."
            )

        skills = self.profile.get("skills") or []
        if isinstance(skills, dict):
            flat = []
            for values in skills.values():
                if isinstance(values, list):
                    flat.extend(values)
            skills = flat
        skills = [s for s in skills if isinstance(s, str)]
        skills_line = ", ".join(skills[:6])

        signature = self.profile.signature_html()
        why_me_sentence, why_me_bullets = self._select_why_me_highlights(role)
        job_keywords = self._extract_job_keywords(job_description)
        fit_highlights = [self._summarize_highlight(item) for item in why_me_bullets]
        if len(fit_highlights) < 2:
            fit_highlights = (fit_highlights + ["automation and testing", "building reliable systems"])[:2]

        body_lines = [
            posting_line,
            f"I’m especially interested in contributing to {company_name}’s engineering team and learning from the work you do.",
            "I’ve built data systems and automation tools using Python and SQL, and shipped production features with testing and CI.",
        ]

        if job_keywords:
            keyword_phrase = ", ".join(job_keywords)
            body_lines.append(f"Noticed the posting emphasizes {keyword_phrase}.")
            body_lines.append(
                f"My experience in {fit_highlights[0]} and {fit_highlights[1]} maps to that."
            )

        body_lines.append("Resume attached; happy to discuss if there’s a fit.")

        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <p>Dear {contact_name or 'Hiring Manager'},</p>
    <p>{body_lines[0]}</p>
    <p>{body_lines[1]}</p>
    <p>{body_lines[2]}</p>
    {"".join([f"<p>{line}</p>" for line in body_lines[3:-1]])}
    <p><strong>{why_me_sentence}</strong></p>
    <ul>
        {''.join([f'<li>{item}</li>' for item in why_me_bullets])}
    </ul>
    <p>{body_lines[-1]}</p>
    <p><strong>Core Skills:</strong> {skills_line}</p>
    <p>
        Best regards,<br><br>
        {signature}
    </p>
</body>
</html>"""

        return subject, html_body

    def _select_why_me_highlights(self, role: str) -> Tuple[str, List[str]]:
        role_lower = (role or "").lower()
        highlights = self.profile.get("experience_highlights") or []
        projects = self.profile.get("project_highlights") or []
        pool = [h for h in highlights if isinstance(h, str)] + [p for p in projects if isinstance(p, str)]

        data_keywords = ["data", "analytics", "ml", "ai", "machine learning"]
        software_keywords = ["software", "sde", "backend", "full stack", "frontend", "engineer"]

        preferred = []
        if any(k in role_lower for k in data_keywords):
            preferred = [h for h in pool if any(k in h.lower() for k in ["etl", "accuracy", "data", "model", "analytics"])]
        elif any(k in role_lower for k in software_keywords):
            preferred = [h for h in pool if any(k in h.lower() for k in ["platform", "ci/cd", "uptime", "production", "automation", "tests"])]

        if not preferred:
            preferred = pool

        bullets = []
        seen = set()
        for item in preferred:
            if item.lower() in seen:
                continue
            bullets.append(item)
            seen.add(item.lower())
            if len(bullets) == 2:
                break

        if len(bullets) < 2:
            for item in pool:
                if item.lower() in seen:
                    continue
                bullets.append(item)
                seen.add(item.lower())
                if len(bullets) == 2:
                    break

        sentence = "Why me for this role:"
        return sentence, bullets[:2]
    
    def _generate_fallback_email(self, name: str, company: str, position: str, uniqueness_seed: str = "") -> str:
        """
        Generate a fallback email with variation based on uniqueness seed.
        Ensures each recipient gets unique content even without AI.
        """
        sender_name = self.profile.get('name', 'Your Name')
        sender_title = self.profile.get('title', '')
        sender_company = self.profile.get('location', '')
        signature = self.profile.signature_html()
        
        # Use uniqueness seed to deterministically select variations
        seed_hash = hash(uniqueness_seed) if uniqueness_seed else hash(f"{name}{company}{position}")
        variation_index = abs(seed_hash) % 4
        
        # Opening variations
        openings = [
            f"I hope this email finds you well. I am writing to express my interest in the {position or 'open positions'} at {company or 'your organization'}.",
            f"I'm reaching out regarding opportunities at {company or 'your organization'}, particularly in {position or 'software engineering'}.",
            f"I came across {company or 'your organization'} and was impressed by your work. I'm interested in the {position or 'available roles'}.",
            f"I'm writing to express my strong interest in joining {company or 'your organization'} as a {position or 'team member'}."
        ]
        
        # Body variations
        bodies = [
            "With a background in building reliable systems and data-driven solutions, I believe I can contribute meaningfully to your team.",
            "My experience includes developing scalable applications, working with modern tech stacks, and delivering production-ready solutions.",
            "I have hands-on experience with software development, data systems, and automation that aligns well with your team's needs.",
            "My technical background in Python, SQL, and cloud technologies would enable me to make immediate contributions to your projects."
        ]
        
        # Closing variations
        closings = [
            "I have attached my resume for your review. I would welcome the opportunity to discuss how my skills align with your needs.",
            "Please find my resume attached. I'm excited about the possibility of contributing to your team and would love to discuss further.",
            "I've attached my resume and would be happy to provide additional information or discuss potential opportunities.",
            "My resume is attached for your consideration. I look forward to the possibility of discussing how I can contribute to your team."
        ]
        
        opening = openings[variation_index]
        body = bodies[(variation_index + 1) % len(bodies)]
        closing = closings[(variation_index + 2) % len(closings)]
        
        return f"""
        <html>
        <body>
        <p>Dear {name or 'Hiring Manager'},</p>
        
        <p>{opening}</p>
        
        <p>{body}</p>
        
        <p>{closing}</p>
        
        <p>Best regards,<br>
        {signature}</p>
        </body>
        </html>
        """
    
    def _generate_minimal_fallback_email(self, name: str, company: str, position: str, uniqueness_seed: str = "") -> str:
        """
        Generate a minimal fallback email with variation when all other methods fail.
        Uses uniqueness seed to ensure different content for each recipient.
        """
        sender_name = self.profile.get('name', 'Your Name')
        signature = self.profile.signature_html()
        
        # Use uniqueness seed for deterministic variation
        seed_hash = hash(uniqueness_seed) if uniqueness_seed else hash(f"{name}{company}{position}")
        variation_index = abs(seed_hash) % 3
        
        opening_phrases = [
            "I hope this email finds you well.",
            "I'm writing to express my interest in opportunities at your organization.",
            "I came across your organization and was impressed by your work."
        ]
        
        body_phrases = [
            "With experience in software engineering and data systems, I believe I can contribute to your team.",
            "My background includes building scalable systems and working with modern technologies.",
            "I have experience with Python, SQL, and cloud technologies that could benefit your projects."
        ]
        
        closing_phrases = [
            "I've attached my resume and would welcome the chance to discuss potential opportunities.",
            "Please find my resume attached, and I'm available to discuss how I might contribute.",
            "My resume is attached for your review, and I'm open to discussing next steps."
        ]
        
        opening = opening_phrases[variation_index]
        body = body_phrases[(variation_index + 1) % len(body_phrases)]
        closing = closing_phrases[(variation_index + 2) % len(closing_phrases)]
        
        return f"""
        <html>
        <body>
        <p>Dear {name or 'Hiring Manager'},</p>
        
        <p>{opening}</p>
        
        <p>{body}</p>
        
        <p>{closing}</p>
        
        <p>Best regards,<br>
        {signature}</p>
        </body>
        </html>
        """
    
    def send_single_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        contact_name: str = "",
        metadata: Optional[Dict] = None,
        attachments: Optional[List[str]] = None,
        max_retries: int = 3
    ) -> bool:
        """
        Send a single email with rate limiting, connection pooling, and retry logic.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            contact_name: Recipient name
            metadata: Additional metadata
            attachments: List of attachment paths
            max_retries: Maximum number of retry attempts for transient failures
        
        Returns:
            True if sent successfully, False otherwise
        """
        # Check credentials validation status
        if not getattr(self, 'credentials_valid', True):
            logger.error("❌ Cannot send email: Gmail credentials failed validation during startup.")
            self.stats['failed'] += 1
            self.stats['auth_errors'] += 1
            return False

        # Check rate limits
        can_send, message = self.rate_limiter.can_send()
        if not can_send:
            logger.error(f"❌ Rate limit exceeded: {message}")
            self.stats['daily_limit_exceeded'] += 1
            self.log_rate_limit("send_email", False, message)
            return False
        
        # Log successful rate limit check
        self.log_rate_limit("send_email", True, message)
        
        # Wait if needed to maintain rate limit
        self.rate_limiter.wait_if_needed()
        
        # Prepare email message (outside retry loop since it doesn't change)
        msg = MIMEMultipart('alternative')
        msg['From'] = self.email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Attach HTML
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))
        
        # Attach resume/other files
        attachment_paths = attachments or self.profile.resume_paths()
        attach_path = None
        for path in attachment_paths:
            if path and Path(path).exists():
                attach_path = path
                break
        if attach_path:
            cv_path = Path(attach_path)
            with open(cv_path, 'rb') as f:
                attachment = MIMEBase('application', 'octet-stream')
                attachment.set_payload(f.read())
                encoders.encode_base64(attachment)
                attachment.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{cv_path.name}"'
                )
                msg.attach(attachment)
        
        # Retry loop for transient failures
        last_error = None
        for attempt in range(max_retries):
            try:
                with self.send_lock:
                    # Send using connection pool
                    try:
                        with self.connection_pool.get_connection() as server:
                            server.send_message(msg)
                        
                        self.stats['sent'] += 1
                        self.rate_limiter.record_sent()
                        
                        logger.debug(f"✅ Sent email to {to_email}")
                        return True
                        
                    except (smtplib.SMTPAuthenticationError, smtplib.SMTPConnectError) as pool_error:
                        # Re-raise these to be handled by outer exception handlers
                        raise pool_error
                    except Exception as pool_error:
                        # Connection pool error - log and re-raise
                        logger.error(f"Connection pool error: {pool_error}")
                        raise pool_error
                    
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"❌ Authentication error sending to {to_email}: {e}")
                logger.error("   Check Gmail app password and 2FA settings")
                self.stats['failed'] += 1
                self.stats['auth_errors'] += 1
                # Authentication errors are not retryable
                return False
                
            except smtplib.SMTPServerDisconnected as e:
                last_error = e
                logger.warning(f"⚠️ Server disconnected (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    # Wait with exponential backoff before retry
                    backoff = 2 ** attempt + random.uniform(0, 1)
                    logger.info(f"   Retrying in {backoff:.2f} seconds...")
                    time.sleep(backoff)
                    continue
                else:
                    logger.error(f"❌ Max retries exceeded for {to_email}: {last_error}")
                    self.stats['failed'] += 1
                    self.stats['connection_errors'] += 1
                    return False
                    
            except smtplib.SMTPConnectError as e:
                last_error = e
                logger.warning(f"⚠️ Connection error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    backoff = 2 ** attempt + random.uniform(0, 1)
                    logger.info(f"   Retrying in {backoff:.2f} seconds...")
                    time.sleep(backoff)
                    continue
                else:
                    logger.error(f"❌ Max retries exceeded for {to_email}: {last_error}")
                    self.stats['failed'] += 1
                    self.stats['connection_errors'] += 1
                    return False
                    
            except smtplib.SMTPDataError as e:
                last_error = e
                # Data errors (like rate limiting) might be retryable
                error_code = getattr(e, 'smtp_code', 0)
                if error_code == 421:  # Service not available, try later
                    logger.warning(f"⚠️ Gmail rate limited (attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        backoff = 30 * (attempt + 1) + random.uniform(0, 10)  # Longer backoff for rate limits
                        logger.info(f"   Rate limited by Gmail, waiting {backoff:.2f} seconds...")
                        time.sleep(backoff)
                        continue
                
                logger.error(f"❌ Data error sending to {to_email}: {e}")
                logger.error(f"   SMTP error code: {error_code}")
                self.stats['failed'] += 1
                return False
                
            except smtplib.SMTPRecipientsRefused as e:
                logger.error(f"❌ Recipient refused for {to_email}: {e}")
                logger.error("   Email address may be invalid or blocked")
                self.stats['failed'] += 1
                # Recipient errors are not retryable
                return False
                
            except smtplib.SMTPSenderRefused as e:
                logger.error(f"❌ Sender refused: {e}")
                logger.error("   Your Gmail account may be blocked or restricted")
                self.stats['failed'] += 1
                self.stats['auth_errors'] += 1
                # Sender errors are not retryable
                return False
                
            except smtplib.SMTPException as e:
                last_error = e
                logger.warning(f"⚠️ SMTP error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    backoff = 2 ** attempt + random.uniform(0, 1)
                    logger.info(f"   Retrying in {backoff:.2f} seconds...")
                    time.sleep(backoff)
                    continue
                else:
                    logger.error(f"❌ Max retries exceeded for {to_email}: {last_error}")
                    self.stats['failed'] += 1
                    self.stats['connection_errors'] += 1
                    return False
                
            except OSError as e:
                last_error = e
                logger.warning(f"⚠️ Network error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    backoff = 2 ** attempt + random.uniform(0, 1)
                    logger.info(f"   Retrying in {backoff:.2f} seconds...")
                    time.sleep(backoff)
                    continue
                else:
                    logger.error(f"❌ Max retries exceeded for {to_email}: {last_error}")
                    self.stats['failed'] += 1
                    self.stats['connection_errors'] += 1
                    return False
                
            except Exception as e:
                logger.error(f"❌ Unexpected error sending to {to_email}: {e}")
                logger.error(f"   Error type: {type(e).__name__}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")
                self.stats['failed'] += 1
                return False
        
        return False
    
    def track_email(
        self,
        email: str,
        name: str,
        company: str,
        position: str,
        metadata: Dict,
        subject: str,
        status: str = 'sent',
        error_message: Optional[str] = None,
        retry_count: int = 0
    ):
        """Track email in database with status and error details"""
        try:
            with sqlite3.connect(self.tracking_db) as conn:
                now = datetime.now().isoformat()
                
                # Check if email already exists (same day)
                today = datetime.now().strftime('%Y-%m-%d')
                cursor = conn.execute(
                    "SELECT id, retry_count FROM sent_emails WHERE email = ? AND DATE(sent_at) = ?",
                    (email, today)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing record
                    conn.execute('''
                        UPDATE sent_emails 
                        SET name = ?, company = ?, position = ?, subject = ?,
                            provider_used = ?, ai_confidence = ?, status = ?, error_message = ?,
                            retry_count = ?, last_retry_at = ?, updated_at = ?
                        WHERE id = ?
                    ''', (
                        name, company, position, subject,
                        metadata.get('provider', 'unknown'),
                        metadata.get('confidence', 0.0),
                        status,
                        error_message,
                        retry_count,
                        now if retry_count > 0 else None,
                        now,
                        existing[0]
                    ))
                else:
                    # Insert new record
                    conn.execute('''
                        INSERT INTO sent_emails
                        (email, name, company, position, subject, provider_used, ai_confidence, 
                         status, error_message, retry_count, sent_at, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        email, name, company, position,
                        subject,
                        metadata.get('provider', 'unknown'),
                        metadata.get('confidence', 0.0),
                        status,
                        error_message,
                        retry_count,
                        now,
                        now,
                        now
                    ))
                
                conn.commit()
                logger.debug(f"Tracked email: {email} ({status}, retry={retry_count})")
                
        except Exception as e:
            logger.warning(f"Failed to track email: {e}")
    
    def log_rate_limit(self, action: str, was_allowed: bool, reason: str = ""):
        """Log rate limiting decision"""
        try:
            status = self.rate_limiter.get_status()
            with sqlite3.connect(self.tracking_db) as conn:
                conn.execute('''
                    INSERT INTO rate_limit_log
                    (action, daily_sent, daily_limit, min_delay, was_allowed, reason)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    action,
                    status['daily_sent'],
                    status['daily_limit'],
                    status['min_delay'],
                    was_allowed,
                    reason
                ))
                conn.commit()
        except Exception as e:
            logger.warning(f"Failed to log rate limit: {e}")
    
    def update_campaign_stats(self):
        """Update campaign statistics for today"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            with sqlite3.connect(self.tracking_db) as conn:
                # Check if stats exist for today
                cursor = conn.execute(
                    "SELECT id FROM campaign_stats WHERE campaign_date = ?",
                    (today,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing stats
                    conn.execute('''
                        UPDATE campaign_stats 
                        SET total_sent = ?, total_failed = ?, total_skipped = ?,
                            ai_generated = ?, fallback_used = ?, auth_errors = ?,
                            connection_errors = ?, rate_limit_hits = ?, daily_limit_exceeded = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE campaign_date = ?
                    ''', (
                        self.stats['sent'],
                        self.stats['failed'],
                        self.stats['skipped'],
                        self.stats['ai_generated'],
                        self.stats['fallback_used'],
                        self.stats['auth_errors'],
                        self.stats['connection_errors'],
                        self.stats['rate_limit_hits'],
                        self.stats['daily_limit_exceeded'],
                        today
                    ))
                else:
                    # Insert new stats
                    conn.execute('''
                        INSERT INTO campaign_stats
                        (campaign_date, total_sent, total_failed, total_skipped,
                         ai_generated, fallback_used, auth_errors, connection_errors,
                         rate_limit_hits, daily_limit_exceeded)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        today,
                        self.stats['sent'],
                        self.stats['failed'],
                        self.stats['skipped'],
                        self.stats['ai_generated'],
                        self.stats['fallback_used'],
                        self.stats['auth_errors'],
                        self.stats['connection_errors'],
                        self.stats['rate_limit_hits'],
                        self.stats['daily_limit_exceeded']
                    ))
                
                conn.commit()
                logger.debug("Updated campaign statistics")
                
        except Exception as e:
            logger.warning(f"Failed to update campaign stats: {e}")
    
    def test_email_sending(self, test_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Test email sending functionality with detailed diagnostics.
        
        Args:
            test_email: Optional test recipient email (defaults to sender)
        
        Returns:
            Dictionary with test results and diagnostics
        """
        test_email = test_email or self.email
        logger.info(f"Testing email sending to {test_email}...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'test_email': test_email,
            'sender_email': self.email,
            'credential_validation': self.validate_credentials(),
            'connection_pool_status': {
                'pool_size': self.connection_pool.pool_size,
                'queue_size': self.connection_pool.connections.qsize()
            },
            'steps': {}
        }
        
        # Step 1: Credential validation
        logger.info("Step 1: Validating credentials...")
        cred_validation = self.validate_credentials()
        results['steps']['credential_validation'] = {
            'status': 'passed' if cred_validation.get('valid') else 'failed',
            'details': cred_validation
        }
        
        if not cred_validation.get('valid'):
            logger.error("❌ Credential validation failed")
            results['overall_status'] = 'failed'
            return results
        
        # Step 2: Test connection
        logger.info("Step 2: Testing SMTP connection...")
        try:
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
                server.starttls()
                server.login(self.email, self.password)
                response = server.noop()
                
                results['steps']['smtp_connection'] = {
                    'status': 'passed',
                    'response_code': response[0],
                    'response_message': response[1].decode() if isinstance(response[1], bytes) else response[1]
                }
                logger.info("✅ SMTP connection successful")
        except Exception as e:
            results['steps']['smtp_connection'] = {
                'status': 'failed',
                'error': str(e)
            }
            logger.error(f"❌ SMTP connection failed: {e}")
            results['overall_status'] = 'failed'
            return results
        
        # Step 3: Test email sending
        logger.info("Step 3: Testing email sending...")
        test_subject = f"InternMailer Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        test_body = """
        <html>
        <body>
        <h2>InternMailer System Test</h2>
        <p>This is a test email sent by the InternMailer system.</p>
        <p>If you received this email, the system is working correctly.</p>
        <p>Timestamp: {timestamp}</p>
        </body>
        </html>
        """.format(timestamp=datetime.now().isoformat())
        
        try:
            success = self.send_single_email(
                to_email=test_email,
                subject=test_subject,
                html_body=test_body,
                max_retries=1  # Don't retry for test
            )
            
            results['steps']['email_sending'] = {
                'status': 'passed' if success else 'failed',
                'success': success,
                'subject': test_subject
            }
            
            if success:
                logger.info("✅ Test email sent successfully")
                results['overall_status'] = 'passed'
            else:
                logger.error("❌ Test email sending failed")
                results['overall_status'] = 'failed'
                
        except Exception as e:
            results['steps']['email_sending'] = {
                'status': 'failed',
                'error': str(e)
            }
            logger.error(f"❌ Test email sending failed: {e}")
            results['overall_status'] = 'failed'
        
        # Step 4: System status
        logger.info("Step 4: Checking system status...")
        results['steps']['system_status'] = {
            'daily_sent': self.get_daily_sent_count(),
            'daily_limit': self.max_daily_emails,
            'can_send_today': self.can_send_today()[0],
            'tracking_db_exists': Path(self.tracking_db).exists()
        }
        
        logger.info(f"Test complete: {results['overall_status']}")
        return results
    
    def send_campaign(
        self,
        count: int = 50,
        use_ai: bool = True,
        dry_run: bool = False
    ) -> Dict:
        """
        Send a campaign of personalized emails with enhanced error handling.
        
        Args:
            count: Number of emails to send
            use_ai: Whether to use AI for personalization
            dry_run: If True, don't actually send emails
        
        Returns:
            Statistics dict
        """
        # Check daily limit
        can_send, remaining = self.can_send_today()
        if not can_send:
            logger.error("❌ Daily email limit reached!")
            return self.stats

        # Validate credentials lazily before starting actual sending
        if not dry_run:
            logger.info("Validating Gmail credentials for campaign...")
            validation_result = self._validate_credentials()
            self.credentials_valid = validation_result
            if not validation_result:
                logger.error("❌ Gmail authentication failed. Check credentials and 2FA settings.")
                self.stats['failed'] += count
                self.stats['auth_errors'] += 1
                return self.stats
        
        actual_count = min(count, remaining)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🚀 STARTING EMAIL CAMPAIGN")
        logger.info(f"{'='*60}")
        logger.info(f"Target: {actual_count} emails (daily remaining: {remaining})")
        logger.info(f"AI Personalization: {'✅' if use_ai else '❌'}")
        logger.info(f"Dry Run: {'✅' if dry_run else '❌'}")
        logger.info(f"{'='*60}\n")
        
        # Get contacts
        contacts = self.get_fresh_contacts(actual_count)
        logger.info(f"📋 Found {len(contacts)} fresh contacts")
        
        if len(contacts) == 0:
            logger.error("❌ No fresh contacts available!")
            return self.stats
        
        # Process each contact with error isolation
        for i, contact in enumerate(contacts, 1):
            job_url = ""
            if isinstance(contact, dict):
                name = contact.get("name", "")
                email = contact.get("email", "")
                company = contact.get("company", "")
                position = contact.get("position", "")
                job_url = contact.get("job_url", "") or contact.get("url", "")
            else:
                name = contact[0] if len(contact) > 0 else ""
                email = contact[1] if len(contact) > 1 else ""
                company = contact[2] if len(contact) > 2 else ""
                position = contact[3] if len(contact) > 3 else ""
                job_url = contact[4] if len(contact) > 4 else ""
            
            logger.info(f"\n[{i}/{len(contacts)}] {name} @ {company}")
            
            # Skip if missing critical data
            if not email:
                logger.warning("   ⚠️ Skipping - missing email")
                self.stats['skipped'] += 1
                continue
            if not name:
                name = "Hiring Manager"
            
            # Generate personalized email with error isolation
            try:
                subject, html_body, metadata = self.generate_personalized_email(
                    contact_name=name,
                    email=email,
                    company=company or "your company",
                    position=position or "Software Engineering",
                    use_ai=use_ai,
                    job_url=job_url,
                )
                
                provider = metadata.get('provider', 'none')
                confidence = metadata.get('confidence', 0)
                
                if metadata['ai_used']:
                    self.stats['ai_generated'] += 1
                    if provider == 'fallback':
                        self.stats['fallback_used'] += 1
                
                logger.info(f"   ✓ Generated ({provider}, conf={confidence:.2f})")
                
                # Preview first email
                if i == 1 and not dry_run and not self.auto_approve:
                    logger.info(f"\n{'='*60}")
                    logger.info("PREVIEW (first email):")
                    logger.info(f"{'='*60}")
                    logger.info(f"To: {email}")
                    logger.info(f"Subject: {subject}")
                    logger.info(f"Body preview: {html_body[:300]}...")
                    logger.info(f"{'='*60}\n")
                    
                    confirm = input("Proceed with sending? (y/n): ").strip().lower()
                    if confirm != 'y':
                        logger.info("Cancelled by user")
                        return self.stats
                
                # Send or dry run
                if dry_run:
                    logger.info(f"   📝 Dry run - would send to {email}")
                else:
                    success = self.send_single_email(
                        to_email=email,
                        subject=subject,
                        html_body=html_body,
                        contact_name=name,
                        metadata=metadata
                    )
                    
                    if success:
                        self.track_email(
                            email=email,
                            name=name,
                            company=company,
                            position=position,
                            metadata=metadata,
                            subject=subject,
                            status='sent'
                        )
                        logger.info(f"   ✅ Sent")
                    else:
                        logger.error(f"   ❌ Failed")
                        # Track failed email with error status
                        self.track_email(
                            email=email,
                            name=name,
                            company=company,
                            position=position,
                            metadata=metadata,
                            subject=subject,
                            status='failed',
                            error_message='Send failed after retries'
                        )
                        # Check if we should stop due to authentication errors
                        if self.stats['auth_errors'] >= 3:
                            logger.error("⚠️ Too many authentication errors, stopping campaign")
                            break
                
            except Exception as e:
                logger.error(f"   ❌ Error processing contact: {e}")
                self.stats['failed'] += 1
                # Log full error with context for debugging
                logger.error(f"   Error context: name={name}, email={email}, company={company}")
        
        # Update campaign statistics
        self.update_campaign_stats()
        
        # Print summary
        rate_limit_status = self.rate_limiter.get_status()
        logger.info(f"\n{'='*60}")
        logger.info("CAMPAIGN SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Sent: {self.stats['sent']}")
        logger.info(f"Failed: {self.stats['failed']}")
        logger.info(f"Skipped: {self.stats['skipped']}")
        logger.info(f"AI Generated: {self.stats['ai_generated']}")
        logger.info(f"Auth Errors: {self.stats['auth_errors']}")
        logger.info(f"Connection Errors: {self.stats['connection_errors']}")
        logger.info(f"Rate Limit Hits: {self.stats['rate_limit_hits']}")
        logger.info(f"Daily Limit Exceeded: {self.stats['daily_limit_exceeded']}")
        logger.info(f"Daily: {rate_limit_status['daily_sent']}/{rate_limit_status['daily_limit']}")
        logger.info(f"Remaining Today: {rate_limit_status['remaining_today']}")
        logger.info(f"Next Reset: {rate_limit_status['next_reset']}")
        logger.info(f"{'='*60}\n")
        
        return self.stats
    
    def preview(self, count: int = 3) -> List[Dict]:
        """Preview emails without sending"""
        contacts = self.get_fresh_contacts(count)
        previews = []
        
        for contact in contacts:
            name, email, company, position = contact[0], contact[1], contact[2], contact[3]
            
            subject, html_body, metadata = self.generate_personalized_email(
                contact_name=name,
                email=email,
                company=company or "your company",
                position=position or "Software Engineering",
                use_ai=True
            )
            
            previews.append({
                'name': name,
                'email': email,
                'company': company,
                'position': position,
                'subject': subject,
                'body': html_body,
                'metadata': metadata
            })
        
        return previews
    
    def validate_credentials(self) -> Dict[str, Any]:
        """
        Validate Gmail credentials and return detailed status.
        
        Returns:
            Dictionary with validation results
        """
        try:
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=10) as server:
                server.starttls()
                server.login(self.email, self.password)
                response = server.noop()
                
                return {
                    'valid': response[0] == 250,
                    'response_code': response[0],
                    'response_message': response[1].decode() if isinstance(response[1], bytes) else response[1],
                    'email': self.email,
                    'timestamp': datetime.now().isoformat()
                }
                
        except smtplib.SMTPAuthenticationError as e:
            return {
                'valid': False,
                'error_type': 'authentication',
                'error_message': str(e),
                'email': self.email,
                'timestamp': datetime.now().isoformat(),
                'suggestion': 'Check 2FA settings and app password at https://myaccount.google.com/apppasswords'
            }
            
        except smtplib.SMTPException as e:
            return {
                'valid': False,
                'error_type': 'smtp',
                'error_message': str(e),
                'email': self.email,
                'timestamp': datetime.now().isoformat(),
                'suggestion': 'Check network connection and SMTP settings'
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error_type': 'unexpected',
                'error_message': str(e),
                'email': self.email,
                'timestamp': datetime.now().isoformat(),
                'suggestion': 'Check system configuration and logs'
            }
    
    def get_stats(self) -> Dict:
        """Get comprehensive campaign statistics"""
        try:
            with sqlite3.connect(self.tracking_db) as conn:
                # Basic email statistics
                cursor = conn.execute("SELECT COUNT(*) FROM sent_emails")
                total_sent = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM sent_emails WHERE replied = 1")
                total_replied = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM sent_emails WHERE followup_sent = 1")
                total_followups = cursor.fetchone()[0]
                
                # Status breakdown
                cursor = conn.execute("SELECT status, COUNT(*) FROM sent_emails GROUP BY status")
                status_breakdown = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Today's campaign stats
                today = datetime.now().strftime('%Y-%m-%d')
                cursor = conn.execute(
                    "SELECT * FROM campaign_stats WHERE campaign_date = ?",
                    (today,)
                )
                today_stats_row = cursor.fetchone()
                today_stats = {}
                if today_stats_row:
                    columns = [desc[0] for desc in cursor.description]
                    today_stats = dict(zip(columns, today_stats_row))
                
                # Rate limit logs from last hour
                hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
                cursor = conn.execute(
                    "SELECT action, was_allowed, COUNT(*) FROM rate_limit_log WHERE timestamp > ? GROUP BY action, was_allowed",
                    (hour_ago,)
                )
                rate_limit_stats = cursor.fetchall()
                
                # Get rate limiter status
                rate_limit_status = self.rate_limiter.get_status()
                
                return {
                    'total_sent': total_sent,
                    'total_replied': total_replied,
                    'total_followups': total_followups,
                    'status_breakdown': status_breakdown,
                    'current_session': self.stats,
                    'daily_sent': self.get_daily_sent_count(),
                    'daily_limit': rate_limit_status['daily_limit'],
                    'rate_limit_status': rate_limit_status,
                    'today_campaign_stats': today_stats,
                    'recent_rate_limits': rate_limit_stats,
                    'connection_pool_size': self.connection_pool.pool_size,
                    'credential_status': self.validate_credentials()
                }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                'current_session': self.stats,
                'rate_limit_status': self.rate_limiter.get_status(),
                'error': str(e)
            }
    
    def cleanup(self):
        """Clean up resources (connection pool, etc.)"""
        logger.info("Cleaning up email system resources...")
        self.connection_pool.close_all()
        logger.info("Email system cleanup complete")


# Global instance
_email_system = None

def get_email_system() -> EmailSystem:
    """Get singleton instance"""
    global _email_system
    if _email_system is None:
        _email_system = EmailSystem()
    return _email_system


if __name__ == "__main__":
    import sys
    
    system = get_email_system()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--preview':
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 3
            logger.info(f"\nGenerating {count} previews...\n")
            
            previews = system.preview(count)
            
            for i, p in enumerate(previews, 1):
                logger.info(f"\n{'='*70}")
                logger.info(f"PREVIEW {i}/{count}")
                logger.info(f"{'='*70}")
                logger.info(f"To: {p['name']} <{p['email']}>")
                logger.info(f"Company: {p['company']}")
                logger.info(f"Subject: {p['subject']}")
                logger.info(f"AI: {p['metadata'].get('provider', 'none')}")
                logger.info(f"\nBody:\n{p['body'][:800]}...")
                logger.info(f"{'='*70}\n")
        
        elif sys.argv[1] == '--send':
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            dry_run = '--dry-run' in sys.argv
            no_ai = '--no-ai' in sys.argv
            
            system.send_campaign(
                count=count,
                use_ai=not no_ai,
                dry_run=dry_run
            )
        
        elif sys.argv[1] == '--stats':
            stats = system.get_stats()
            logger.info("\n📊 Campaign Statistics")
            logger.info(f"Total Sent: {stats.get('total_sent', 0)}")
            logger.info(f"Total Replied: {stats.get('total_replied', 0)}")
            logger.info(f"Daily Sent: {stats.get('daily_sent', 0)}/{stats.get('daily_limit', 100)}")
            logger.info(f"Credential Status: {'✅ Valid' if stats.get('credential_status', {}).get('valid') else '❌ Invalid'}")
        
        elif sys.argv[1] == '--test':
            test_email = sys.argv[2] if len(sys.argv) > 2 else None
            results = system.test_email_sending(test_email)
            
            logger.info("\n🧪 Email System Test Results")
            logger.info(f"{'='*60}")
            logger.info(f"Overall Status: {results.get('overall_status', 'unknown').upper()}")
            logger.info(f"Test Email: {results.get('test_email')}")
            logger.info(f"Sender Email: {results.get('sender_email')}")
            logger.info(f"Timestamp: {results.get('timestamp')}")
            logger.info(f"{'='*60}")
            
            for step_name, step_result in results.get('steps', {}).items():
                status = step_result.get('status', 'unknown')
                status_icon = '✅' if status == 'passed' else '❌' if status == 'failed' else '⚠️'
                logger.info(f"{step_name.replace('_', ' ').title()}: {status_icon} {status}")
                if 'error' in step_result:
                    logger.info(f"  Error: {step_result['error']}")
                if 'suggestion' in step_result:
                    logger.info(f"  Suggestion: {step_result['suggestion']}")
        
        else:
            logger.info("""
Usage:
    python email_system.py --preview [count]     # Preview emails
    python email_system.py --send [count]        # Send emails
    python email_system.py --send 10 --dry-run   # Dry run
    python email_system.py --stats               # Show statistics
    python email_system.py --test [email]        # Test email sending
            """)
    else:
        logger.info("""
🚀 Email System

Usage:
    python email_system.py --preview [count]     # Preview emails
    python email_system.py --send [count]        # Send emails
    python email_system.py --send 10 --dry-run   # Dry run
    python email_system.py --stats               # Show statistics
    python email_system.py --test [email]        # Test email sending
        """)
