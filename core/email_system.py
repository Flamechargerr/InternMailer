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
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from threading import Lock

logger = logging.getLogger(__name__)

# Import AI components
try:
    from core.unified_ai_provider import get_unified_ai_provider, PersonalizationResult
    from core.anti_templating_engine import get_anti_templating_engine
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    logger.warning("AI components not available")


class EmailSystem:
    """
    Unified email system for job application campaigns.
    """
    
    def __init__(self):
        # Load credentials
        self.email = os.getenv('GMAIL_USER') or os.getenv('EMAIL_ADDRESS')
        self.password = os.getenv('GMAIL_APP_PASSWORD') or os.getenv('EMAIL_PASSWORD')
        
        if not self.email or not self.password:
            raise ValueError("Email credentials not found. Set GMAIL_USER and GMAIL_APP_PASSWORD in .env")
        
        # Database paths
        self.contacts_db = 'data/contacts.db'
        self.tracking_db = 'campaign_results/email_tracking.db'
        
        # Initialize AI components
        self.ai_provider = None
        self.anti_template = None
        if AI_AVAILABLE:
            try:
                self.ai_provider = get_unified_ai_provider()
                self.anti_template = get_anti_templating_engine()
            except Exception as e:
                logger.warning("AI initialization failed: %s", e)
        
        # Thread safety
        self.send_lock = Lock()
        self.stats = {
            'sent': 0,
            'failed': 0,
            'skipped': 0,
            'ai_generated': 0,
            'fallback_used': 0
        }
        
        # Rate limiting
        self.min_delay = 3  # seconds between emails
        self.last_send_time = 0
        self.max_daily_emails = int(os.getenv('MAX_EMAILS_PER_DAY', '100'))
        
        # Ensure directories exist
        os.makedirs('campaign_results', exist_ok=True)
        os.makedirs('data', exist_ok=True)
        
        # Initialize tracking DB
        self._init_tracking_db()
        
        logger.info("Email System initialized")
        logger.info("Email: %s", self.email)
        logger.info("Daily limit: %s", self.max_daily_emails)
    
    def _init_tracking_db(self):
        """Initialize tracking database"""
        with sqlite3.connect(self.tracking_db) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sent_emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    name TEXT,
                    company TEXT,
                    position TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    provider_used TEXT,
                    ai_confidence REAL,
                    status TEXT DEFAULT 'sent',
                    followup_sent BOOLEAN DEFAULT 0,
                    replied BOOLEAN DEFAULT 0
                )
            ''')
            conn.commit()
    
    def get_daily_sent_count(self) -> int:
        """Get number of emails sent today"""
        today = datetime.now().strftime('%Y-%m-%d')
        try:
            with sqlite3.connect(self.tracking_db) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM sent_emails WHERE DATE(sent_at) = ?",
                    (today,)
                )
                return cursor.fetchone()[0]
        except:
            return 0
    
    def can_send_today(self) -> Tuple[bool, int]:
        """Check if we can send more emails today"""
        sent_today = self.get_daily_sent_count()
        remaining = self.max_daily_emails - sent_today
        return remaining > 0, remaining
    
    def get_fresh_contacts(self, count: int = 50) -> List[Tuple]:
        """
        Get contacts that haven't been emailed yet.
        Looks for CSV files in data/ directory.
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
        
        # Try to find CSV files
        data_dir = Path('data')
        csv_files = list(data_dir.glob('*.csv'))
        
        if not csv_files:
            logger.warning("No CSV files found in data/ directory")
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
                        
                        if email and email.lower() not in sent_emails:
                            contacts.append((name, email, company, position))
                            if len(contacts) >= count:
                                break
            except Exception as e:
                logger.warning("Error reading %s: %s", csv_path, e)
                continue
        
        return contacts
    
    def generate_personalized_email(
        self,
        contact_name: str,
        email: str,
        company: str,
        position: str,
        use_ai: bool = True
    ) -> Tuple[str, str, Dict]:
        """
        Generate personalized email for a contact.
        
        Returns:
            Tuple of (subject, html_body, metadata)
        """
        metadata = {
            'ai_used': False,
            'provider': 'none',
            'confidence': 0.0,
            'generation_time_ms': 0
        }
        
        ai_personalization = None
        
        if use_ai and self.ai_provider:
            try:
                # Generate AI personalization
                ai_result = self.ai_provider.generate_professor_personalization(
                    professor_name=contact_name,
                    university=company,
                    research_area=position or "Software Engineering"
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
            except Exception as e:
                logger.warning("AI generation failed for %s: %s", contact_name, e)
        
        # Generate email with anti-templating
        if self.anti_template:
            seed = f"{contact_name}_{email}_{position}"
            subject, html_body = self.anti_template.generate_html_email(
                professor_name=contact_name,
                university=company or "your organization",
                research_area=position or "Software Engineering",
                ai_personalization=ai_personalization,
                seed=seed
            )
        else:
            # Fallback template
            subject = f"Application for opportunities at {company or 'your organization'}"
            html_body = self._generate_fallback_email(contact_name, company, position)
        
        return subject, html_body, metadata
    
    def _generate_fallback_email(self, name: str, company: str, position: str) -> str:
        """Generate a simple fallback email if AI is unavailable"""
        return f"""
        <html>
        <body>
        <p>Dear {name or 'Hiring Manager'},</p>
        
        <p>I hope this email finds you well. I am writing to express my interest in opportunities 
        at {company or 'your organization'}.</p>
        
        <p>With a background in software engineering and machine learning, I believe I can 
        contribute meaningfully to your team.</p>
        
        <p>I have attached my resume for your review. I would welcome the opportunity to 
        discuss how my skills align with your needs.</p>
        
        <p>Best regards,<br>
        Anamay</p>
        </body>
        </html>
        """
    
    def send_single_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        contact_name: str = "",
        metadata: Optional[Dict] = None
    ) -> bool:
        """Send a single email with rate limiting"""
        # Rate limiting
        elapsed = time.time() - self.last_send_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        
        try:
            with self.send_lock:
                msg = MIMEMultipart('alternative')
                msg['From'] = self.email
                msg['To'] = to_email
                msg['Subject'] = subject
                
                # Attach HTML
                msg.attach(MIMEText(html_body, 'html', 'utf-8'))
                
                # Attach CV if exists
                cv_paths = [
                    Path('resumes/CV_Anamay_Modern.pdf'),
                    Path('CV_Anamay_Modern.pdf'),
                    Path('resume.pdf'),
                ]
                for cv_path in cv_paths:
                    if cv_path.exists():
                        with open(cv_path, 'rb') as f:
                            attachment = MIMEBase('application', 'pdf')
                            attachment.set_payload(f.read())
                            encoders.encode_base64(attachment)
                            attachment.add_header(
                                'Content-Disposition',
                                f'attachment; filename="{cv_path.name}"'
                            )
                            msg.attach(attachment)
                        break
                
                # Send via Gmail SMTP
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    server.login(self.email, self.password)
                    server.send_message(msg)
                
                self.last_send_time = time.time()
                self.stats['sent'] += 1
                
                return True
                
        except Exception as e:
            logger.exception("Failed to send to %s", to_email)
            self.stats['failed'] += 1
            return False
    
    def track_email(
        self,
        email: str,
        name: str,
        company: str,
        position: str,
        metadata: Dict
    ):
        """Track sent email in database"""
        try:
            with sqlite3.connect(self.tracking_db) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO sent_emails
                    (email, name, company, position, provider_used, ai_confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    email, name, company, position,
                    metadata.get('provider', 'unknown'),
                    metadata.get('confidence', 0.0)
                ))
                conn.commit()
        except Exception as e:
            logger.warning("Failed to track email %s: %s", email, e)
    
    def send_campaign(
        self,
        count: int = 50,
        use_ai: bool = True,
        dry_run: bool = False
    ) -> Dict:
        """
        Send a campaign of personalized emails.
        
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
            logger.warning("Daily email limit reached")
            return self.stats
        
        actual_count = min(count, remaining)
        
        logger.info("%s", '=' * 60)
        logger.info("STARTING EMAIL CAMPAIGN")
        logger.info("%s", '=' * 60)
        logger.info("Target: %s emails (daily remaining: %s)", actual_count, remaining)
        logger.info("AI Personalization: %s", use_ai)
        logger.info("Dry Run: %s", dry_run)
        logger.info("%s", '=' * 60)
        
        # Get contacts
        contacts = self.get_fresh_contacts(actual_count)
        logger.info("Found %s fresh contacts", len(contacts))
        
        if len(contacts) == 0:
            logger.warning("No fresh contacts available")
            return self.stats
        
        # Process each contact
        for i, contact in enumerate(contacts, 1):
            name, email, company, position = contact[0], contact[1], contact[2], contact[3]
            
            logger.info("[%s/%s] %s @ %s", i, len(contacts), name, company)
            
            # Skip if missing critical data
            if not email or not name:
                logger.warning("Skipping contact with missing email or name")
                self.stats['skipped'] += 1
                continue
            
            # Generate personalized email
            try:
                subject, html_body, metadata = self.generate_personalized_email(
                    contact_name=name,
                    email=email,
                    company=company or "your company",
                    position=position or "Software Engineering",
                    use_ai=use_ai
                )
                
                provider = metadata.get('provider', 'none')
                confidence = metadata.get('confidence', 0)
                
                if metadata['ai_used']:
                    self.stats['ai_generated'] += 1
                    if provider == 'fallback':
                        self.stats['fallback_used'] += 1
                
                logger.info("Generated email (provider=%s, confidence=%.2f)", provider, confidence)
                
                # Preview first email
                if i == 1 and not dry_run:
                    logger.info("%s", '=' * 60)
                    logger.info("PREVIEW (first email)")
                    logger.info("%s", '=' * 60)
                    logger.info("To: %s", email)
                    logger.info("Subject: %s", subject)
                    logger.info("Body preview: %s...", html_body[:300])
                    logger.info("%s", '=' * 60)
                    
                    confirm = input("Proceed with sending? (y/n): ").strip().lower()
                    if confirm != 'y':
                        logger.info("Cancelled by user")
                        return self.stats
                
                # Send or dry run
                if dry_run:
                    logger.info("[DRY RUN] Would send to %s", email)
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
                            metadata=metadata
                        )
                        logger.info("Sent to %s", email)
                    else:
                        logger.error("Failed to send to %s", email)
                
            except Exception as e:
                logger.exception("Unexpected error during campaign loop")
                self.stats['failed'] += 1
        
        # Print summary
        logger.info("%s", '=' * 60)
        logger.info("CAMPAIGN SUMMARY")
        logger.info("%s", '=' * 60)
        logger.info("Sent: %s", self.stats['sent'])
        logger.info("Failed: %s", self.stats['failed'])
        logger.info("Skipped: %s", self.stats['skipped'])
        logger.info("AI Generated: %s", self.stats['ai_generated'])
        logger.info("Remaining Today: %s", self.max_daily_emails - self.get_daily_sent_count())
        logger.info("%s", '=' * 60)
        
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
    
    def get_stats(self) -> Dict:
        """Get campaign statistics"""
        try:
            with sqlite3.connect(self.tracking_db) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM sent_emails")
                total_sent = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM sent_emails WHERE replied = 1")
                total_replied = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM sent_emails WHERE followup_sent = 1")
                total_followups = cursor.fetchone()[0]
                
                return {
                    'total_sent': total_sent,
                    'total_replied': total_replied,
                    'total_followups': total_followups,
                    'current_session': self.stats,
                    'daily_sent': self.get_daily_sent_count(),
                    'daily_limit': self.max_daily_emails
                }
        except Exception as e:
            logger.warning("Error getting stats: %s", e)
            return self.stats


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
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
    
    system = get_email_system()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--preview':
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 3
            logger.info("Generating %s previews", count)
            
            previews = system.preview(count)
            
            for i, p in enumerate(previews, 1):
                logger.info("%s", '=' * 70)
                logger.info("PREVIEW %s/%s", i, count)
                logger.info("%s", '=' * 70)
                logger.info("To: %s <%s>", p['name'], p['email'])
                logger.info("Company: %s", p['company'])
                logger.info("Subject: %s", p['subject'])
                logger.info("AI: %s", p['metadata'].get('provider', 'none'))
                logger.info("Body: %s...", p['body'][:800])
                logger.info("%s", '=' * 70)
        
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
            logger.info("Campaign Statistics")
            logger.info("Total Sent: %s", stats.get('total_sent', 0))
            logger.info("Total Replied: %s", stats.get('total_replied', 0))
            logger.info("Daily Sent: %s/%s", stats.get('daily_sent', 0), stats.get('daily_limit', 100))
        
        else:
            logger.info("""
Usage:
    python email_system.py --preview [count]     # Preview emails
    python email_system.py --send [count]        # Send emails
    python email_system.py --send 10 --dry-run   # Dry run
    python email_system.py --stats               # Show statistics
            """)
    else:
        logger.info("""
🚀 Email System

Usage:
    python email_system.py --preview [count]     # Preview emails
    python email_system.py --send [count]        # Send emails
    python email_system.py --send 10 --dry-run   # Dry run
    python email_system.py --stats               # Show statistics
        """)
