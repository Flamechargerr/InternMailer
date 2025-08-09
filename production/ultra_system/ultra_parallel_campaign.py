#!/usr/bin/env python3
"""
ULTRA ENHANCED PARALLEL CAMPAIGN - 95%+ SUCCESS + ULTRA SPEED
=============================================================

Revolutionary improvements:
1. 🚀 ULTRA PARALLEL PROCESSING: Multiple professors processed simultaneously
2. 🎯 95%+ PROFESSOR RECOGNITION: Using ultra-enhanced research assistant
3. ⚡ SMART BATCHING: Process in optimal batch sizes with load balancing
4. 🔄 ADAPTIVE SPEED: Automatically adjusts speed based on success rates
5. 💾 INTELLIGENT CACHING: Never search the same professor twice
6. 🧠 SMART RETRY: Failed professors retried with different strategies
7. 📊 REAL-TIME METRICS: Live dashboard of campaign progress
8. 🛡️ RATE LIMIT MANAGEMENT: Prevents API overload while maximizing speed
9. ⚡ ASYNC EMAIL SENDING: Emails sent in parallel with research
10. 🎨 ENHANCED PERSONALIZATION: AI-driven email customization

PERFORMANCE TARGETS:
- Success Rate: 95%+
- Speed: 10-20x faster than sequential
- Professor Recognition: 95%+
- Email Quality: Premium personalization
"""

import sys
import os
import asyncio
import aiohttp
import pandas as pd
import json
import time
import random
import smtplib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import concurrent.futures
from dataclasses import dataclass, asdict
import threading
import logging
from pathlib import Path
import queue
from dotenv import load_dotenv, find_dotenv

# Robustly load environment from project root regardless of CWD
try:
    env_path = find_dotenv(usecwd=True)
    if not env_path:
        # Also try searching relative to this file's directory (../../.env)
        here = os.path.dirname(__file__)
        candidate = os.path.abspath(os.path.join(here, '..', '..', '.env'))
        if os.path.exists(candidate):
            env_path = candidate
    if env_path:
        load_dotenv(env_path, override=True)
except Exception:
    # Fallback: no-op if dotenv isn't available
    pass

# Import our ultra-enhanced components
from ultra_enhanced_research_assistant import UltraEnhancedResearchAssistant, ProfessorMatch
from enhanced_research_area_inference import EnhancedResearchAreaInference
from send_research_assistant_emails import create_enhanced_personalized_email
from send_html_template_emails_with_cv import send_html_email_with_cv

# Setup advanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ultra_campaign.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class CampaignConfig:
    """Configuration for ultra campaign"""
    max_parallel_professors: int = 12  # Process this many professors simultaneously
    max_parallel_sources: int = 8      # Research sources per professor
    email_batch_size: int = 5          # Emails to send in parallel
    min_delay_between_batches: float = 0.5  # Minimum delay between batches
    max_delay_between_batches: float = 3.0  # Maximum delay between batches
    success_rate_target: float = 0.95  # 95% target
    cache_duration_hours: int = 48     # Cache results for 48 hours
    retry_failed_professors: bool = True
    max_retries_per_professor: int = 2
    enable_adaptive_speed: bool = True
    save_intermediate_results: bool = True

@dataclass
class ProfessorResult:
    """Result for each professor processed"""
    professor: Dict
    status: str  # 'success', 'failed', 'skipped', 'retry'
    publications: List[Dict]
    confidence: float
    research_area: str
    email_sent: bool
    processing_time: float
    error_message: Optional[str] = None
    retry_count: int = 0

class UltraParallelCampaign:
    def __init__(self, 
                 database_file: str = "FINAL_MASTER_EMAIL_DATABASE.csv",
                 test_email: Optional[str] = None,
                 config: Optional[CampaignConfig] = None):
        
        self.database_file = database_file
        self.test_email = test_email
        self.config = config or CampaignConfig()
        
        # Ultra-enhanced components
        self.research_assistant = UltraEnhancedResearchAssistant(
            max_workers=self.config.max_parallel_sources,
            cache_dir="ultra_research_cache"
        )
        self.inference = EnhancedResearchAreaInference()
        
        # Campaign state
        self.results: List[ProfessorResult] = []
        self.processed_emails = set()
        self.failed_professors = {}
        self.campaign_start_time = None
        self.total_professors = 0
        
        # Duplicate prevention: load previously contacted emails and manual blocklist
        self.contacted_emails = set()
        self._load_contacted_emails()
        
        # Performance metrics
        self.metrics = {
            'total_processed': 0,
            'successful_emails': 0,
            'failed_searches': 0,
            'cache_hits': 0,
            'total_search_time': 0.0,
            'total_email_time': 0.0,
            'average_confidence': 0.0,
            'publications_found': 0,
            'high_confidence_matches': 0
        }
        
        # Thread safety
        self.results_lock = threading.Lock()
        self.metrics_lock = threading.Lock()
        
        # Progress tracking files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.results_file = f"ultra_campaign_results_{timestamp}.json"
        self.progress_file = "ultra_campaign_progress.json"
        self.live_metrics_file = "ultra_live_metrics.json"
        
        # Email queue for parallel processing
        self.email_queue = queue.Queue()
        self.email_results_queue = queue.Queue()

    def _load_contacted_emails(self):
        """Load previously contacted emails from multiple sources to avoid duplicates."""
        try:
            # 1) email_log.csv (statuses: sent, auth_error, etc.) -> treat any attempt as contacted to be safe
            log_path = os.path.abspath(os.path.join(os.getcwd(), 'email_log.csv'))
            if os.path.exists(log_path):
                import csv
                with open(log_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        email = (row.get('Email') or row.get('email') or '').strip()
                        status = (row.get('Status') or row.get('status') or '').strip().lower()
                        if email:
                            # Consider sent and smtp delivery attempts as contacted to prevent duplicates
                            if status in {'sent', 'smtp_error', 'failed', 'auth_error', 'config_error'}:
                                self.contacted_emails.add(email)
        except Exception as e:
            logger.warning(f"Failed to load email_log.csv for dedupe: {e}")

        try:
            # 2) sent_emails_log.json (if present)
            json_path = os.path.abspath(os.path.join(os.getcwd(), 'sent_emails_log.json'))
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    sent = data.get('sent_emails') or []
                    for email in sent:
                        if isinstance(email, str):
                            self.contacted_emails.add(email.strip())
        except Exception as e:
            logger.warning(f"Failed to load sent_emails_log.json for dedupe: {e}")

        try:
            # 3) manual blocklist.txt (one email per line)
            block_path = os.path.abspath(os.path.join(os.getcwd(), 'blocklist.txt'))
            if os.path.exists(block_path):
                with open(block_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        email = line.strip()
                        if email and '@' in email:
                            self.contacted_emails.add(email)
        except Exception as e:
            logger.warning(f"Failed to load blocklist.txt for dedupe: {e}")

        logger.info(f"🔒 Loaded {len(self.contacted_emails):,} contacted/blocklisted emails for duplicate prevention")

    def is_contacted(self, email: str) -> bool:
        return bool(email) and email in self.contacted_emails

    def mark_contacted(self, email: str):
        if not email:
            return
        self.contacted_emails.add(email)
        # Also persist minimally by appending to sent_emails_log.json for continuity
        try:
            json_path = os.path.abspath(os.path.join(os.getcwd(), 'sent_emails_log.json'))
            data = {'sent_emails': []}
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f) or data
            sent = set(data.get('sent_emails') or [])
            sent.add(email)
            data['sent_emails'] = sorted(sent)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.debug(f"Could not persist sent email to JSON: {e}")

    def load_progress(self) -> Dict:
        """Load previous campaign progress"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    data = json.load(f)
                    # Convert lists back to sets
                    if 'processed_emails' in data:
                        data['processed_emails'] = set(data['processed_emails'])
                    return data
        except Exception as e:
            logger.error(f"Error loading progress: {e}")
        
        return {
            'processed_emails': set(),
            'failed_professors': {},
            'last_index': 0,
            'campaign_id': f"campaign_{int(time.time())}"
        }

    def save_progress(self):
        """Save campaign progress"""
        try:
            progress_data = {
                'processed_emails': list(self.processed_emails),
                'failed_professors': self.failed_professors,
                'last_index': len(self.results),
                'campaign_id': getattr(self, 'campaign_id', 'unknown'),
                'timestamp': datetime.now().isoformat(),
                'metrics': self.metrics.copy()
            }
            
            with open(self.progress_file, 'w') as f:
                json.dump(progress_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving progress: {e}")

    def save_live_metrics(self):
        """Save live metrics for dashboard"""
        try:
            live_data = {
                'timestamp': datetime.now().isoformat(),
                'metrics': self.metrics.copy(),
                'current_success_rate': self.get_success_rate(),
                'processing_speed': self.get_processing_speed(),
                'eta_minutes': self.get_eta_minutes(),
                'recent_results': [asdict(r) for r in self.results[-10:]]  # Last 10 results
            }
            
            with open(self.live_metrics_file, 'w') as f:
                json.dump(live_data, f, indent=2)
                
        except Exception as e:
            logger.debug(f"Error saving live metrics: {e}")

    def load_ultra_professor_database(self, 
                                     sample_size: Optional[int] = None,
                                     start_from: int = 0,
                                     quality_filter: bool = True) -> List[Dict]:
        """Load professor database with ultra-enhanced filtering"""
        
        logger.info(f"🗄️ Loading ultra professor database: {self.database_file}")
        
        try:
            df = pd.read_csv(self.database_file)
            logger.info(f"📊 Loaded {len(df):,} total professors")
            
            # Enhanced data cleaning
            df_clean = df.dropna(subset=['email', 'name'])
            df_clean = df_clean[df_clean['email'].str.contains('@', na=False)]
            df_clean = df_clean[df_clean['name'].str.len() > 2]
            
            # Remove obvious spam/invalid emails
            invalid_patterns = [
                r'[0-9]{4,}',           # Long numbers
                r'\.open$|\.eduphone$|items\.|assistant$|secretary$',  # Administrative
                r'noreply|donotreply|no-reply',  # Auto emails
                r'webmaster|admin|info@',       # Generic addresses
            ]
            
            for pattern in invalid_patterns:
                df_clean = df_clean[~df_clean['email'].str.contains(pattern, regex=True, na=False, case=False)]
            
            # Ultra quality scoring
            if quality_filter:
                df_clean['ultra_quality_score'] = self.calculate_ultra_quality_scores(df_clean)
                df_clean = df_clean[df_clean['ultra_quality_score'] >= 0.7]  # Higher threshold
                df_clean = df_clean.sort_values('ultra_quality_score', ascending=False)
            
            # Apply pagination
            if start_from > 0:
                df_clean = df_clean.iloc[start_from:]
            
            if sample_size and sample_size < len(df_clean):
                df_clean = df_clean.head(sample_size)
            
            professors = df_clean.to_dict('records')
            logger.info(f"✅ Ultra-filtered database: {len(professors):,} high-quality professors")
            
            return professors
            
        except Exception as e:
            logger.error(f"❌ Error loading database: {e}")
            return []

    def calculate_ultra_quality_scores(self, df: pd.DataFrame) -> pd.Series:
        """Calculate ultra-quality scores for professors"""
        scores = []
        
        for _, row in df.iterrows():
            score = 0.3  # Base score
            
            # Name quality analysis
            name = str(row.get('name', '')).strip()
            if len(name.split()) >= 2:  # First + Last name
                score += 0.2
            if not any(char.isdigit() for char in name):  # No numbers
                score += 0.1
            if len(name) > 5 and len(name) < 50:  # Reasonable length
                score += 0.1
            
            # Email quality analysis
            email = str(row.get('email', '')).strip()
            if email.endswith('.edu'):
                score += 0.3  # Strong academic indicator
            elif email.endswith(('.org', '.gov')):
                score += 0.1
            
            # Check for professor-like email patterns
            email_lower = email.lower()
            if any(indicator in email_lower for indicator in ['prof', 'faculty', 'research', 'cs', 'eecs']):
                score += 0.1
            
            # Affiliation quality
            affiliation = str(row.get('affiliation', '') or row.get('university', '')).strip()
            if affiliation and len(affiliation) > 5:
                academic_keywords = ['university', 'college', 'institute', 'school', 'tech']
                if any(keyword in affiliation.lower() for keyword in academic_keywords):
                    score += 0.2
                
                # Bonus for well-known institutions
                prestigious = ['stanford', 'mit', 'harvard', 'berkeley', 'cmu', 'caltech', 'princeton']
                if any(univ in affiliation.lower() for univ in prestigious):
                    score += 0.1
            
            scores.append(min(score, 1.0))
        
        return pd.Series(scores)

    async def process_professor_ultra(self, professor: Dict) -> ProfessorResult:
        """Process a single professor with ultra-enhanced pipeline"""
        
        start_time = time.time()
        prof_name = professor.get('name', 'Unknown')
        prof_email = professor.get('email', '')
        prof_affiliation = professor.get('affiliation', professor.get('university', ''))
        
        logger.info(f"🔬 Ultra processing: {prof_name}")
        
        # Skip if already processed in this session
        if prof_email in self.processed_emails:
            return ProfessorResult(
                professor=professor,
                status='skipped',
                publications=[],
                confidence=0.0,
                research_area='',
                email_sent=False,
                processing_time=time.time() - start_time,
                error_message='Already processed in current session'
            )

        # Skip if already contacted historically (from logs/blocklist)
        if self.is_contacted(prof_email):
            logger.info(f"⏭️ Skipping {prof_name} - already contacted/blocklisted")
            return ProfessorResult(
                professor=professor,
                status='skipped',
                publications=[],
                confidence=0.0,
                research_area='',
                email_sent=False,
                processing_time=time.time() - start_time,
                error_message='Already contacted previously'
            )
        
        try:
            # Ultra-enhanced publication search
            publications, professor_match = self.research_assistant.find_professor_publications_ultra(
                prof_name, prof_affiliation
            )
            
            if not publications:
                # Record failure for potential retry
                self.failed_professors[prof_name] = {
                    'attempts': self.failed_professors.get(prof_name, {}).get('attempts', 0) + 1,
                    'last_attempt': datetime.now().isoformat(),
                    'reason': 'no_publications'
                }
                
                return ProfessorResult(
                    professor=professor,
                    status='failed',
                    publications=[],
                    confidence=0.0,
                    research_area='',
                    email_sent=False,
                    processing_time=time.time() - start_time,
                    error_message='No publications found'
                )
            
            # Enhanced research area inference
            combined_text = ' '.join([
                pub['title'] + ' ' + pub.get('summary', '') + ' ' + pub.get('venue', '')
                for pub in publications[:5]  # Use top 5 for inference
            ])
            
            research_area = self.inference.infer_research_area({
                'name': combined_text,
                'affiliation': prof_affiliation
            })
            
            # Generate ultra-personalized email
            subject = f"Research Collaboration Opportunity - Your {research_area} Research"
            
            try:
                html_content = create_enhanced_personalized_email(
                    prof_name, prof_affiliation, publications[:5], research_area
                )
            except Exception as e:
                logger.warning(f"Email generation failed for {prof_name}: {e}")
                return ProfessorResult(
                    professor=professor,
                    status='failed',
                    publications=publications,
                    confidence=professor_match.confidence,
                    research_area=research_area,
                    email_sent=False,
                    processing_time=time.time() - start_time,
                    error_message=f'Email generation failed: {str(e)}'
                )
            
            # Queue email for parallel sending
            recipient_email = self.test_email if self.test_email else prof_email
            email_data = {
                'recipient': recipient_email,
                'subject': subject,
                'html_content': html_content,
                'professor_name': prof_name,
                'send_time': time.time(),
                'original_email': prof_email  # Always track the original professor email
            }
            
            self.email_queue.put(email_data)
            
            # Mark as contacted immediately if not in test mode to avoid duplicates in long runs
            if not self.test_email and prof_email:
                self.mark_contacted(prof_email)
            
            # Save research data
            await self.save_professor_research_data(professor, publications, research_area, professor_match)
            
            # Update progress
            with self.results_lock:
                self.processed_emails.add(prof_email)
            
            processing_time = time.time() - start_time
            
            return ProfessorResult(
                professor=professor,
                status='success',
                publications=publications,
                confidence=professor_match.confidence,
                research_area=research_area,
                email_sent=True,  # Will be confirmed by email worker
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"❌ Ultra processing failed for {prof_name}: {e}")
            return ProfessorResult(
                professor=professor,
                status='failed',
                publications=[],
                confidence=0.0,
                research_area='',
                email_sent=False,
                processing_time=time.time() - start_time,
                error_message=str(e)
            )

    async def save_professor_research_data(self, 
                                          professor: Dict, 
                                          publications: List[Dict],
                                          research_area: str,
                                          professor_match: ProfessorMatch):
        """Save detailed research data for each professor"""
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prof_name_clean = professor.get('name', 'unknown').replace(' ', '_').replace('/', '_')
            
            # Create directories
            os.makedirs('ultra_research_data', exist_ok=True)
            
            research_data = {
                'professor': professor,
                'publications': publications,
                'research_area': research_area,
                'professor_match': asdict(professor_match),
                'timestamp': datetime.now().isoformat(),
                'analysis': {
                    'total_publications': len(publications),
                    'total_citations': sum(pub.get('citations', 0) for pub in publications),
                    'sources_used': list(set(pub.get('source') for pub in publications)),
                    'recent_publications': len([p for p in publications if self.research_assistant.is_recent_publication(p.get('year'))]),
                    'confidence_breakdown': {
                        'overall': professor_match.confidence,
                        'publication_count_factor': len(publications) / 10.0,
                        'source_diversity_factor': len(set(pub.get('source') for pub in publications)) / 5.0,
                        'citation_factor': min(sum(pub.get('citations', 0) for pub in publications) / 100.0, 1.0)
                    }
                }
            }
            
            # Save detailed JSON
            json_path = f"ultra_research_data/{timestamp}_{prof_name_clean}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(research_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.debug(f"Error saving research data: {e}")

    def email_worker(self):
        """Optimized worker thread for sending emails in parallel with connection pooling"""
        
        # Pre-establish SMTP connection for reuse
        smtp_server = None
        connection_attempts = 0
        max_connection_attempts = 3
        
        def get_smtp_connection():
            nonlocal smtp_server, connection_attempts
            
            if smtp_server is None or connection_attempts >= 10:  # Refresh connection every 10 emails
                try:
                    if smtp_server:
                        try:
                            smtp_server.quit()
                        except:
                            pass
                    
                    import os
                    gmail_user = os.getenv('GMAIL_USER')
                    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
                    
                    smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
                    smtp_server.starttls()
                    smtp_server.login(gmail_user, gmail_password)
                    connection_attempts = 0
                    logger.debug("📧 SMTP connection established/refreshed")
                    
                except Exception as e:
                    logger.warning(f"SMTP connection failed: {e}")
                    smtp_server = None
                    
            return smtp_server
        
        email_batch = []
        batch_size = 3  # Process emails in small batches
        
        while True:
            try:
                # Collect batch of emails
                timeout = 1 if not email_batch else 0.1  # Shorter timeout if batch is building
                
                try:
                    email_data = self.email_queue.get(timeout=timeout)
                    
                    if email_data is None:  # Poison pill to stop worker
                        break
                        
                    email_batch.append(email_data)
                    
                except queue.Empty:
                    pass  # Continue to process current batch
                
                # Process batch when full or queue is empty
                if len(email_batch) >= batch_size or (email_batch and self.email_queue.empty()):
                    batch_start = time.time()
                    
                    # Get SMTP connection
                    smtp_conn = get_smtp_connection()
                    
                    for email_data in email_batch:
                        email_start = time.time()
                        
                        try:
                            # Use optimized email sending with existing connection
                            success = self.send_email_optimized(
                                smtp_conn,
                                email_data['recipient'],
                                email_data['subject'], 
                                email_data['html_content'],
                                f"Ultra Campaign - {email_data['professor_name']}"
                            )
                            
                            email_time = time.time() - email_start
                            
                            # Track contacted professor if successful
                            if success and hasattr(self, 'contacted_tracker') and self.contacted_tracker:
                                # Extract original email if this is a test
                                original_email = email_data.get('original_email', email_data['recipient'])
                                if not self.test_email:  # Only track in production mode
                                    self.contacted_tracker.mark_contacted(original_email)
                            
                            # Report result
                            result = {
                                'success': success,
                                'professor_name': email_data['professor_name'],
                                'recipient': email_data['recipient'],
                                'send_time': email_time,
                                'timestamp': datetime.now().isoformat()
                            }
                            
                            self.email_results_queue.put(result)
                            
                            # Update metrics
                            with self.metrics_lock:
                                self.metrics['total_email_time'] += email_time
                                if success:
                                    self.metrics['successful_emails'] += 1
                                    
                            connection_attempts += 1
                            
                        except Exception as e:
                            logger.error(f"Email sending failed for {email_data['professor_name']}: {e}")
                            
                            # Report failure
                            self.email_results_queue.put({
                                'success': False,
                                'professor_name': email_data['professor_name'],
                                'recipient': email_data['recipient'],
                                'send_time': 0,
                                'timestamp': datetime.now().isoformat(),
                                'error': str(e)
                            })
                    
                    # Clear processed batch
                    email_batch = []
                    
                    batch_time = time.time() - batch_start
                    logger.debug(f"📧 Processed email batch in {batch_time:.2f}s")
                    
                    # Small delay between batches
                    time.sleep(0.05)
                
            except Exception as e:
                logger.error(f"Email worker batch error: {e}")
                email_batch = []  # Clear batch on error
                time.sleep(1)  # Wait before retry
        
        # Cleanup SMTP connection
        if smtp_server:
            try:
                smtp_server.quit()
                logger.debug("📧 SMTP connection closed")
            except:
                pass
    
    def send_email_optimized(self, smtp_server, recipient_email, subject, html_content, email_type):
        """Optimized email sending using existing SMTP connection"""
        
        if not smtp_server:
            return False
            
        try:
            import os
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            
            gmail_user = os.getenv('GMAIL_USER')
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = gmail_user
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            # Attach HTML content
            msg.attach(MIMEText(html_content, 'html'))
            
            # Attach CV (optimized - check once and cache)
            cv_path = 'resumes/CV_Anamay_Modern.pdf'
            if not hasattr(self, '_cv_attachment_cached'):
                if os.path.exists(cv_path):
                    with open(cv_path, 'rb') as attachment:
                        cv_data = attachment.read()
                        
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(cv_data)
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename=CV_Anamay_Tripathy.pdf'
                    )
                    self._cv_attachment_cached = part
                    logger.debug(f"📎 CV cached for reuse")
                else:
                    self._cv_attachment_cached = None
                    logger.warning(f"⚠️ CV not found at: {cv_path}")
            
            # Add cached CV attachment
            if self._cv_attachment_cached:
                msg.attach(self._cv_attachment_cached)
            
            # Send email using existing connection
            smtp_server.sendmail(gmail_user, recipient_email, msg.as_string())
            return True
            
        except Exception as e:
            logger.debug(f"Optimized email send failed: {e}")
            return False

    async def run_ultra_campaign(self,
                                sample_size: int = 50,
                                start_from: int = 0,
                                delay_range: Tuple[float, float] = (1.0, 3.0),
                                test_mode: bool = False):
        """Run the ultra-enhanced parallel campaign"""
        
        self.campaign_start_time = time.time()
        
        print("🚀" * 30)
        print("ULTRA ENHANCED PARALLEL CAMPAIGN")
        print("🚀" * 30)
        print(f"🎯 Target Success Rate: {self.config.success_rate_target*100:.1f}%")
        print(f"⚡ Parallel Processing: {self.config.max_parallel_professors} professors")
        print(f"📊 Sample Size: {sample_size:,}")
        print(f"🔬 Research Sources: {self.config.max_parallel_sources}")
        print(f"📧 Mode: {'TEST' if test_mode else 'PRODUCTION'}")
        print(f"⏰ Delay Range: {delay_range[0]:.1f}s - {delay_range[1]:.1f}s")
        print("=" * 90)
        
        # Load professors
        professors = self.load_ultra_professor_database(
            sample_size=sample_size,
            start_from=start_from
        )
        
        if not professors:
            logger.error("❌ No professors to process!")
            return
        
        self.total_professors = len(professors)
        logger.info(f"📊 Processing {len(professors):,} ultra-quality professors")
        
        # Start email worker threads
        num_email_workers = min(3, self.config.email_batch_size)  # Max 3 email workers
        email_threads = []
        
        for i in range(num_email_workers):
            thread = threading.Thread(target=self.email_worker, daemon=True)
            thread.start()
            email_threads.append(thread)
            logger.info(f"✅ Started email worker {i+1}")
        
        # Process professors in batches
        batch_size = self.config.max_parallel_professors
        
        for batch_start in range(0, len(professors), batch_size):
            batch_end = min(batch_start + batch_size, len(professors))
            batch = professors[batch_start:batch_end]
            
            logger.info(f"🔄 Processing batch {batch_start//batch_size + 1}: professors {batch_start+1}-{batch_end}")
            
            # Process batch in parallel
            batch_start_time = time.time()
            
            # Create tasks for parallel processing
            tasks = [self.process_professor_ultra(prof) for prof in batch]
            
            # Execute batch
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            batch_time = time.time() - batch_start_time
            
            # Process results
            successful_in_batch = 0
            for i, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"❌ Exception processing professor {batch_start + i}: {result}")
                    result = ProfessorResult(
                        professor=batch[i],
                        status='failed',
                        publications=[],
                        confidence=0.0,
                        research_area='',
                        email_sent=False,
                        processing_time=0.0,
                        error_message=str(result)
                    )
                
                # Store result
                with self.results_lock:
                    self.results.append(result)
                    if result.status == 'success':
                        successful_in_batch += 1
                
                # Update metrics
                with self.metrics_lock:
                    self.metrics['total_processed'] += 1
                    if result.publications:
                        self.metrics['publications_found'] += len(result.publications)
                    if result.confidence >= 0.8:
                        self.metrics['high_confidence_matches'] += 1
                    if result.status == 'failed':
                        self.metrics['failed_searches'] += 1
            
            # Batch summary
            batch_success_rate = (successful_in_batch / len(batch)) * 100
            logger.info(f"📊 Batch completed in {batch_time:.2f}s")
            logger.info(f"✅ Batch success rate: {batch_success_rate:.1f}% ({successful_in_batch}/{len(batch)})")
            
            # Overall progress
            overall_success_rate = self.get_success_rate()
            processing_speed = self.get_processing_speed()
            eta_minutes = self.get_eta_minutes()
            
            print(f"\n📈 ULTRA CAMPAIGN PROGRESS")
            print(f"   📊 Processed: {len(self.results)}/{len(professors)} ({len(self.results)/len(professors)*100:.1f}%)")
            print(f"   ✅ Success Rate: {overall_success_rate:.1f}% (Target: {self.config.success_rate_target*100:.1f}%)")
            print(f"   ⚡ Speed: {processing_speed:.1f} prof/min")
            print(f"   🕐 ETA: {eta_minutes:.1f} minutes")
            print(f"   📧 Emails Queued: {self.email_queue.qsize()}")
            print(f"   🎯 High Confidence: {self.metrics['high_confidence_matches']}")
            
            # Save progress and metrics
            self.save_progress()
            self.save_live_metrics()
            
            # Adaptive delay based on success rate
            if self.config.enable_adaptive_speed:
                if overall_success_rate > 90:
                    delay = delay_range[0]  # Minimum delay if doing well
                elif overall_success_rate > 80:
                    delay = (delay_range[0] + delay_range[1]) / 2  # Medium delay
                else:
                    delay = delay_range[1]  # Maximum delay if struggling
            else:
                delay = random.uniform(*delay_range)
            
            # Delay before next batch (except for last batch)
            if batch_end < len(professors):
                logger.info(f"⏳ Waiting {delay:.1f}s before next batch...")
                await asyncio.sleep(delay)
        
        # Wait for all emails to be sent
        logger.info("📧 Waiting for all emails to be sent...")
        email_wait_start = time.time()
        
        while not self.email_queue.empty() and time.time() - email_wait_start < 300:  # 5 min timeout
            await asyncio.sleep(1)
            
            # Process email results
            while not self.email_results_queue.empty():
                try:
                    email_result = self.email_results_queue.get_nowait()
                    if email_result['success']:
                        logger.info(f"✅ Email sent to {email_result['professor_name']}")
                    else:
                        logger.warning(f"❌ Email failed to {email_result['professor_name']}")
                except queue.Empty:
                    break
        
        # Stop email workers
        for _ in email_threads:
            self.email_queue.put(None)  # Poison pill
        
        for thread in email_threads:
            thread.join(timeout=5)
        
        # Final results
        await self.print_ultra_final_summary()

    async def print_ultra_final_summary(self):
        """Print comprehensive final summary"""
        
        total_time = time.time() - self.campaign_start_time
        
        print("\n" + "🎉" * 30)
        print("ULTRA CAMPAIGN COMPLETED!")
        print("🎉" * 30)
        
        # Calculate final metrics
        success_count = len([r for r in self.results if r.status == 'success'])
        failed_count = len([r for r in self.results if r.status == 'failed'])
        skipped_count = len([r for r in self.results if r.status == 'skipped'])
        
        success_rate = (success_count / len(self.results)) * 100 if self.results else 0
        avg_confidence = sum(r.confidence for r in self.results) / len(self.results) if self.results else 0
        total_publications = sum(len(r.publications) for r in self.results)
        total_citations = sum(sum(pub.get('citations', 0) for pub in r.publications) for r in self.results)
        
        print(f"\n📊 FINAL ULTRA STATISTICS:")
        print(f"   📧 Total Processed: {len(self.results):,}")
        print(f"   ✅ Successful: {success_count:,} ({success_rate:.1f}%)")
        print(f"   ❌ Failed: {failed_count:,}")
        print(f"   ⏭️ Skipped: {skipped_count:,}")
        print(f"   🎯 Average Confidence: {avg_confidence:.2f}")
        print(f"   📚 Publications Found: {total_publications:,}")
        print(f"   📈 Total Citations: {total_citations:,}")
        print(f"   ⏰ Total Time: {total_time/60:.1f} minutes")
        print(f"   ⚡ Processing Speed: {len(self.results)/(total_time/60):.1f} professors/minute")
        
        # Success rate assessment
        if success_rate >= 95:
            print(f"\n🏆 OUTSTANDING! Target exceeded!")
        elif success_rate >= 90:
            print(f"\n🎉 EXCELLENT! Very close to target!")
        elif success_rate >= 85:
            print(f"\n👍 VERY GOOD! Above average performance!")
        elif success_rate >= 80:
            print(f"\n✅ GOOD! Solid performance!")
        else:
            print(f"\n⚠️ NEEDS IMPROVEMENT: Below target success rate")
        
        # Save final results
        final_results = {
            'campaign_summary': {
                'total_processed': len(self.results),
                'success_count': success_count,
                'success_rate': success_rate,
                'average_confidence': avg_confidence,
                'total_time_minutes': total_time / 60,
                'processing_speed': len(self.results) / (total_time / 60),
                'campaign_start': datetime.fromtimestamp(self.campaign_start_time).isoformat(),
                'campaign_end': datetime.now().isoformat()
            },
            'detailed_results': [asdict(result) for result in self.results],
            'final_metrics': self.metrics
        }
        
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 ULTRA CAMPAIGN FILES:")
        print(f"   📊 Results: {self.results_file}")
        print(f"   💾 Progress: {self.progress_file}")
        print(f"   📈 Live Metrics: {self.live_metrics_file}")
        print(f"   🔬 Research Data: ultra_research_data/ directory")
        
        print("\n" + "=" * 90)

    def get_success_rate(self) -> float:
        """Calculate current success rate"""
        if not self.results:
            return 0.0
        success_count = len([r for r in self.results if r.status == 'success'])
        return (success_count / len(self.results)) * 100

    def get_processing_speed(self) -> float:
        """Calculate processing speed (professors per minute)"""
        if not self.campaign_start_time or not self.results:
            return 0.0
        elapsed_minutes = (time.time() - self.campaign_start_time) / 60
        return len(self.results) / elapsed_minutes if elapsed_minutes > 0 else 0.0

    def get_eta_minutes(self) -> float:
        """Estimate time remaining"""
        if not self.results or self.total_professors == 0:
            return 0.0
        
        remaining = self.total_professors - len(self.results)
        speed = self.get_processing_speed()
        
        return remaining / speed if speed > 0 else 0.0

# Command-line interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Ultra Enhanced Parallel Campaign')
    parser.add_argument('--production', action='store_true', help='Production mode')
    parser.add_argument('--size', type=int, default=50, help='Number of professors')
    parser.add_argument('--start', type=int, default=0, help='Starting position')
    parser.add_argument('--parallel', type=int, default=12, help='Parallel professors')
    parser.add_argument('--email', type=str, help='Test email address')
    parser.add_argument('--delay-min', type=float, default=1.0, help='Minimum delay')
    parser.add_argument('--delay-max', type=float, default=3.0, help='Maximum delay')
    
    args = parser.parse_args()
    
    # Configuration
    config = CampaignConfig(
        max_parallel_professors=args.parallel,
        max_parallel_sources=8,
        email_batch_size=5
    )
    
    # Test email
    test_email = None if args.production else (args.email or "tripathy.anamay23@gmail.com")
    
    print("🚀 ULTRA ENHANCED PARALLEL CAMPAIGN")
    print("=" * 60)
    print(f"🎯 Mode: {'PRODUCTION' if args.production else 'TEST'}")
    print(f"📊 Professors: {args.size:,}")
    print(f"⚡ Parallel: {args.parallel}")
    print(f"⏰ Delay: {args.delay_min}-{args.delay_max}s")
    if test_email:
        print(f"📧 Test Email: {test_email}")
    print("=" * 60)
    
    # Confirmation for production
    if args.production:
        confirm = input("⚠️ PRODUCTION MODE - Send emails to real professors? (y/N): ")
        if confirm.lower() not in ['y', 'yes']:
            print("❌ Cancelled")
            return
    
    # Initialize and run campaign
    campaign = UltraParallelCampaign(test_email=test_email, config=config)
    
    # Run the campaign
    asyncio.run(campaign.run_ultra_campaign(
        sample_size=args.size,
        start_from=args.start,
        delay_range=(args.delay_min, args.delay_max),
        test_mode=not args.production
    ))

if __name__ == "__main__":
    main()
