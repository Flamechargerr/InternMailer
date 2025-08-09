#!/usr/bin/env python3
"""
Ultra Improved Campaign System v2.0
Enhanced with better email error handling, SMTP management, and success rate optimization
"""

import asyncio
import time
import threading
import queue
import smtplib
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import logging

# Import the existing system components
from ultra_parallel_campaign import (
    UltraParallelCampaign, CampaignConfig, ProfessorResult, ProfessorMatch
)

load_dotenv()

# Enhanced logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class EmailResult:
    success: bool
    professor_name: str
    email: str
    error_message: Optional[str] = None
    retry_count: int = 0
    send_time: float = 0.0

class ImprovedEmailManager:
    """Enhanced email manager with robust SMTP connection handling"""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.smtp_pool = []
        self.pool_lock = threading.Lock()
        self.failed_emails = queue.Queue()
        self.email_stats = {
            'total_sent': 0,
            'total_failed': 0,
            'smtp_errors': 0,
            'auth_errors': 0,
            'network_errors': 0
        }
        
    def get_smtp_connection(self) -> Optional[smtplib.SMTP]:
        """Get a fresh SMTP connection with proper error handling"""
        try:
            gmail_user = os.getenv('GMAIL_USER')
            gmail_password = os.getenv('GMAIL_APP_PASSWORD')
            
            if not gmail_user or not gmail_password:
                logger.error("❌ Gmail credentials not found in environment")
                return None
            
            # Clean the password (remove spaces)
            gmail_password = gmail_password.replace(' ', '')
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.set_debuglevel(0)  # Disable debug output
            server.starttls()
            server.login(gmail_user, gmail_password)
            
            logger.debug("✅ SMTP connection established")
            return server
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP Authentication failed: {e}")
            self.email_stats['auth_errors'] += 1
            return None
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error: {e}")
            self.email_stats['smtp_errors'] += 1
            return None
        except Exception as e:
            logger.error(f"❌ Network/Connection error: {e}")
            self.email_stats['network_errors'] += 1
            return None
    
    def send_email_with_retry(self, recipient: str, subject: str, html_content: str, 
                             professor_name: str) -> EmailResult:
        """Send email with retry logic and comprehensive error handling"""
        
        for attempt in range(self.max_retries + 1):
            start_time = time.time()
            
            try:
                # Get fresh SMTP connection for each attempt
                server = self.get_smtp_connection()
                if not server:
                    if attempt == self.max_retries:
                        return EmailResult(
                            success=False,
                            professor_name=professor_name,
                            email=recipient,
                            error_message="SMTP connection failed after all retries",
                            retry_count=attempt
                        )
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                
                # Create email message
                msg = self.create_email_message(recipient, subject, html_content)
                if not msg:
                    if attempt == self.max_retries:
                        return EmailResult(
                            success=False,
                            professor_name=professor_name,
                            email=recipient,
                            error_message="Failed to create email message",
                            retry_count=attempt
                        )
                    continue
                
                # Send email
                gmail_user = os.getenv('GMAIL_USER')
                server.sendmail(gmail_user, recipient, msg.as_string())
                server.quit()
                
                send_time = time.time() - start_time
                self.email_stats['total_sent'] += 1
                
                logger.info(f"✅ Email sent to {professor_name} ({recipient}) in {send_time:.2f}s")
                return EmailResult(
                    success=True,
                    professor_name=professor_name,
                    email=recipient,
                    retry_count=attempt,
                    send_time=send_time
                )
                
            except smtplib.SMTPRecipientsRefused as e:
                logger.warning(f"❌ Recipient refused: {recipient} - {e}")
                return EmailResult(
                    success=False,
                    professor_name=professor_name,
                    email=recipient,
                    error_message=f"Recipient refused: {str(e)}",
                    retry_count=attempt
                )
                
            except smtplib.SMTPException as e:
                logger.warning(f"❌ SMTP error for {professor_name} (attempt {attempt+1}): {e}")
                if attempt == self.max_retries:
                    self.email_stats['total_failed'] += 1
                    return EmailResult(
                        success=False,
                        professor_name=professor_name,
                        email=recipient,
                        error_message=f"SMTP error: {str(e)}",
                        retry_count=attempt
                    )
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except Exception as e:
                logger.warning(f"❌ Unexpected error for {professor_name} (attempt {attempt+1}): {e}")
                if attempt == self.max_retries:
                    self.email_stats['total_failed'] += 1
                    return EmailResult(
                        success=False,
                        professor_name=professor_name,
                        email=recipient,
                        error_message=f"Unexpected error: {str(e)}",
                        retry_count=attempt
                    )
                time.sleep(2 ** attempt)
            
            finally:
                try:
                    if 'server' in locals() and server:
                        server.quit()
                except:
                    pass
        
        # This should never be reached, but just in case
        return EmailResult(
            success=False,
            professor_name=professor_name,
            email=recipient,
            error_message="Unexpected failure in retry loop",
            retry_count=self.max_retries
        )
    
    def create_email_message(self, recipient: str, subject: str, html_content: str) -> Optional[MIMEMultipart]:
        """Create email message with CV attachment"""
        try:
            gmail_user = os.getenv('GMAIL_USER')
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = gmail_user
            msg['To'] = recipient
            msg['Subject'] = subject
            
            # Attach HTML content
            msg.attach(MIMEText(html_content, 'html'))
            
            # Attach CV
            cv_path = 'resumes/CV_Anamay_Modern.pdf'
            if os.path.exists(cv_path):
                with open(cv_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    'attachment; filename=CV_Anamay_Tripathy.pdf'
                )
                msg.attach(part)
            else:
                logger.warning(f"⚠️ CV not found at: {cv_path}")
            
            return msg
            
        except Exception as e:
            logger.error(f"❌ Error creating email message: {e}")
            return None
    
    def get_stats(self) -> Dict:
        """Get email sending statistics"""
        total_attempts = self.email_stats['total_sent'] + self.email_stats['total_failed']
        success_rate = (self.email_stats['total_sent'] / total_attempts * 100) if total_attempts > 0 else 0
        
        return {
            **self.email_stats,
            'total_attempts': total_attempts,
            'success_rate': success_rate
        }

class UltraImprovedCampaign(UltraParallelCampaign):
    """Enhanced version of the ultra campaign with improved email handling"""
    
    def __init__(self, config: Optional[CampaignConfig] = None):
        super().__init__(config)
        self.email_manager = ImprovedEmailManager()
        self.real_time_stats = {
            'emails_sent': 0,
            'emails_failed': 0,
            'current_success_rate': 0.0,
            'avg_send_time': 0.0
        }
        # Initialize database file path - use the large 400k+ database
        self.database_file = "C:/Users/anama/OneDrive/Desktop/internmailing/enhanced_background_emails.csv"
        
    async def process_ultra_professor_improved(self, professor: Dict) -> ProfessorResult:
        """Enhanced professor processing with improved email handling"""
        
        start_time = time.time()
        prof_name = professor.get('name', 'Unknown')
        prof_email = professor.get('email', '')
        
        try:
            logger.info(f"🔬 Processing {prof_name}")
            
            # Enhanced research finding with fallback
            publications, professor_match = self.research_assistant.find_professor_publications_ultra(
                prof_name, professor.get('university', '')
            )
            
            # Infer research area using simple method
            research_area = self.infer_research_area_simple(publications, professor)
            if not research_area:
                research_area = 'computer science'  # Default fallback
            
            # Generate personalized email
            email_content = await self.generate_ultra_personalized_email(professor, publications, research_area)
            
            # Use test email if in test mode
            recipient_email = self.test_email if self.test_email else prof_email
            
            # Send email with improved error handling
            email_result = self.email_manager.send_email_with_retry(
                recipient=recipient_email,
                subject=email_content['subject'],
                html_content=email_content['html_content'],
                professor_name=prof_name
            )
            
            # Update real-time stats
            self.update_real_time_stats(email_result)
            
            # Track contacted professor if successful
            if email_result.success and hasattr(self, 'contacted_tracker') and self.contacted_tracker:
                if not self.test_email:  # Only track in production mode
                    self.contacted_tracker.mark_contacted(prof_email)
            
            # Save research data
            await self.save_professor_research_data(professor, publications, research_area, professor_match)
            
            processing_time = time.time() - start_time
            
            return ProfessorResult(
                professor=professor,
                status='success' if email_result.success else 'failed',
                publications=publications,
                confidence=professor_match.confidence,
                research_area=research_area,
                email_sent=email_result.success,
                processing_time=processing_time,
                error_message=email_result.error_message
            )
            
        except Exception as e:
            logger.error(f"❌ Enhanced processing failed for {prof_name}: {e}")
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
    
    def update_real_time_stats(self, email_result: EmailResult):
        """Update real-time statistics"""
        if email_result.success:
            self.real_time_stats['emails_sent'] += 1
        else:
            self.real_time_stats['emails_failed'] += 1
        
        total_emails = self.real_time_stats['emails_sent'] + self.real_time_stats['emails_failed']
        if total_emails > 0:
            self.real_time_stats['current_success_rate'] = (self.real_time_stats['emails_sent'] / total_emails) * 100
    
    async def generate_ultra_personalized_email(self, professor: Dict, publications: List[Dict], research_area: str) -> Dict:
        """Generate a personalized email for the professor"""
        prof_name = professor.get('name', 'Professor')
        affiliation = professor.get('university', professor.get('affiliation', ''))
        
        # Create subject based on research area
        subject = f"Research Collaboration Opportunity - {research_area.title()}"
        
        # Simple HTML email template
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <h2 style="color: #2c5aa0;">Dear {prof_name.split()[0] if prof_name.split() else 'Professor'},</h2>
            
            <p>I hope this email finds you well. My name is Anamay Tripathy, and I am a Data Science Engineering student at Manipal Institute of Technology.</p>
            
            <p>I am writing to express my keen interest in your research work in <strong>{research_area}</strong> at {affiliation}. I have been following your publications and am particularly impressed by your contributions to the field.</p>
            
            {self._generate_publication_highlights(publications)}
            
            <p>I would be honored to contribute to your research as an intern or research assistant. I have experience in:</p>
            <ul>
                <li>Machine Learning and Deep Learning</li>
                <li>Data Analysis and Visualization</li>
                <li>Python, R, and SQL programming</li>
                <li>Statistical Analysis and Modeling</li>
            </ul>
            
            <p>I have attached my CV for your review. I would greatly appreciate the opportunity to discuss how I might contribute to your research team.</p>
            
            <p>Thank you for your time and consideration. I look forward to hearing from you.</p>
            
            <p>Best regards,<br>
            <strong>Anamay Tripathy</strong><br>
            Data Science Engineering Student<br>
            Manipal Institute of Technology<br>
            Email: tripathy.anamay23@gmail.com</p>
        </body>
        </html>
        """
        
        return {
            'subject': subject,
            'html_content': html_content
        }
    
    def _generate_publication_highlights(self, publications: List[Dict]) -> str:
        """Generate highlights from recent publications"""
        if not publications:
            return "<p>Your research profile and academic contributions have caught my attention.</p>"
        
        # Take the most recent publications
        recent_pubs = publications[:3]
        highlights = "<p>Your recent work has particularly caught my attention:</p><ul>"
        
        for pub in recent_pubs:
            title = pub.get('title', 'Untitled')
            year = pub.get('year', 'Recent')
            highlights += f"<li><em>{title}</em> ({year})</li>"
        
        highlights += "</ul>"
        return highlights
    
    async def save_final_results(self, results: List[ProfessorResult]):
        """Save final campaign results"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"improved_campaign_results_{timestamp}.json"
            
            # Convert results to serializable format
            results_data = {
                'campaign_summary': {
                    'total_processed': len(results),
                    'successful': len([r for r in results if r.email_sent]),
                    'failed': len([r for r in results if not r.email_sent]),
                    'timestamp': datetime.now().isoformat(),
                    'email_stats': self.email_manager.get_stats()
                },
                'results': []
            }
            
            for result in results:
                results_data['results'].append({
                    'professor': result.professor,
                    'status': result.status,
                    'email_sent': result.email_sent,
                    'error_message': result.error_message,
                    'processing_time': result.processing_time,
                    'research_area': result.research_area,
                    'confidence': result.confidence,
                    'publications_count': len(result.publications)
                })
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Results saved to {filename}")
            
        except Exception as e:
            logger.error(f"❌ Error saving results: {e}")
    
    async def run_improved_campaign(self,
                                  sample_size: int = 200,
                                  start_from: int = 0,
                                  delay_range: Tuple[float, float] = (0.2, 0.8),
                                  test_mode: bool = False):
        """Run the improved campaign with enhanced error handling"""
        
        self.campaign_start_time = time.time()
        self.test_email = "tripathy.anamay23@gmail.com" if test_mode else None
        
        print("🚀" * 30)
        print("ULTRA IMPROVED CAMPAIGN SYSTEM V2.0")
        print("🚀" * 30)
        print(f"🎯 Enhanced Email Reliability")
        print(f"⚡ Parallel Processing: {self.config.max_parallel_professors} professors")
        print(f"📊 Sample Size: {sample_size:,}")
        print(f"📧 Mode: {'TEST' if test_mode else 'PRODUCTION'}")
        print(f"⏰ Delay Range: {delay_range[0]:.1f}s - {delay_range[1]:.1f}s")
        print("=" * 90)
        
        # Load professors with correct parameters
        professors = self.load_ultra_professor_database(
            sample_size,
            start_from
        )
        
        if not professors:
            logger.error("❌ No professors to process!")
            return
        
        self.total_professors = len(professors)
        logger.info(f"📊 Processing {len(professors):,} ultra-quality professors")
        
        # Process professors with enhanced handling
        results = []
        batch_size = self.config.max_parallel_professors
        
        for batch_start in range(0, len(professors), batch_size):
            batch_end = min(batch_start + batch_size, len(professors))
            batch_professors = professors[batch_start:batch_end]
            
            logger.info(f"🔄 Processing batch {batch_start//batch_size + 1} ({len(batch_professors)} professors)")
            
            # Process batch in parallel
            batch_tasks = [
                self.process_ultra_professor_improved(prof) for prof in batch_professors
            ]
            
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"❌ Batch processing error: {result}")
                else:
                    results.append(result)
            
            # Show progress
            processed = batch_end
            progress = (processed / len(professors)) * 100
            email_stats = self.email_manager.get_stats()
            
            print(f"\n📈 Progress: {processed}/{len(professors)} ({progress:.1f}%)")
            print(f"📧 Email Stats: {email_stats['total_sent']} sent, {email_stats['total_failed']} failed")
            print(f"✅ Current Success Rate: {email_stats['success_rate']:.1f}%")
            
            # Adaptive delay based on success rate
            if email_stats['success_rate'] < 70:
                delay = delay_range[1] * 2  # Slow down if success rate is low
                print(f"⚠️ Low success rate detected, increasing delay to {delay:.1f}s")
            else:
                delay = random.uniform(delay_range[0], delay_range[1])
            
            if batch_end < len(professors):  # Don't delay after last batch
                await asyncio.sleep(delay)
        
        # Save final results
        await self.save_final_results(results)
        
        # Show final statistics
        self.show_final_statistics(results)
        
        return results
    
    def show_final_statistics(self, results: List[ProfessorResult]):
        """Display comprehensive final statistics"""
        
        total_time = time.time() - self.campaign_start_time
        email_stats = self.email_manager.get_stats()
        
        successful_results = [r for r in results if r.status == 'success' and r.email_sent]
        failed_results = [r for r in results if r.status == 'failed' or not r.email_sent]
        
        print("\n🎉" * 30)
        print("ULTRA IMPROVED CAMPAIGN COMPLETED!")
        print("🎉" * 30)
        
        print(f"\n📊 FINAL STATISTICS:")
        print(f"   📧 Total Processed: {len(results)}")
        print(f"   ✅ Successful: {len(successful_results)} ({len(successful_results)/len(results)*100:.1f}%)")
        print(f"   ❌ Failed: {len(failed_results)} ({len(failed_results)/len(results)*100:.1f}%)")
        print(f"   ⏰ Total Time: {total_time/60:.1f} minutes")
        print(f"   ⚡ Processing Speed: {len(results)/(total_time/60):.1f} professors/minute")
        
        print(f"\n📧 EMAIL STATISTICS:")
        print(f"   📤 Emails Sent: {email_stats['total_sent']}")
        print(f"   ❌ Emails Failed: {email_stats['total_failed']}")
        print(f"   📈 Success Rate: {email_stats['success_rate']:.1f}%")
        print(f"   🔒 Auth Errors: {email_stats['auth_errors']}")
        print(f"   🌐 Network Errors: {email_stats['network_errors']}")
        print(f"   📡 SMTP Errors: {email_stats['smtp_errors']}")
        
        if email_stats['success_rate'] >= 90:
            print(f"\n🏆 EXCELLENT! Success rate above 90%!")
        elif email_stats['success_rate'] >= 80:
            print(f"\n✅ GOOD! Success rate above 80%!")
        else:
            print(f"\n⚠️ NEEDS IMPROVEMENT! Success rate below 80%")
        
        print("=" * 90)
    
    def infer_research_area_simple(self, publications: List[Dict], professor: Dict) -> str:
        """Simple research area inference from publications and professor data"""
        
        # Default research areas
        research_areas = {
            'machine learning': ['machine learning', 'ml', 'neural', 'deep learning', 'artificial intelligence', 'ai'],
            'computer vision': ['computer vision', 'image', 'visual', 'cv', 'vision'],
            'natural language processing': ['nlp', 'natural language', 'text', 'language', 'linguistic'],
            'data science': ['data science', 'analytics', 'big data', 'statistics', 'mining'],
            'robotics': ['robot', 'autonomous', 'control', 'robotic'],
            'cybersecurity': ['security', 'crypto', 'privacy', 'cyber'],
            'software engineering': ['software', 'programming', 'development', 'engineering'],
            'algorithms': ['algorithm', 'complexity', 'optimization', 'theoretical'],
            'databases': ['database', 'sql', 'nosql', 'data management'],
            'networks': ['network', 'distributed', 'internet', 'protocol'],
            'computer science': ['computer', 'computing', 'computational']
        }
        
        # Score each area based on publications
        area_scores = {area: 0 for area in research_areas}
        
        if publications:
            for pub in publications:
                title_text = (pub.get('title', '') + ' ' + pub.get('summary', '') + ' ' + pub.get('venue', '')).lower()
                categories = pub.get('categories', []) or pub.get('subjects', []) or []
                
                for area, keywords in research_areas.items():
                    for keyword in keywords:
                        if keyword in title_text:
                            area_scores[area] += 2
                        
                        # Check categories
                        for cat in categories:
                            if isinstance(cat, str) and keyword in cat.lower():
                                area_scores[area] += 1
        
        # Also check professor affiliation/name for clues
        prof_text = (professor.get('name', '') + ' ' + professor.get('affiliation', '')).lower()
        for area, keywords in research_areas.items():
            for keyword in keywords:
                if keyword in prof_text:
                    area_scores[area] += 1
        
        # Get the highest scoring area
        best_area = max(area_scores, key=area_scores.get)
        
        # Return the best area if it has a decent score, otherwise default
        return best_area if area_scores[best_area] > 0 else 'computer science'

async def main():
    """Main function to run the improved campaign"""
    
    # Create improved campaign
    campaign = UltraImprovedCampaign()
    
    # Run the campaign
    await campaign.run_improved_campaign(
        sample_size=200,
        start_from=0,
        delay_range=(0.2, 0.8),
        test_mode=False
    )

if __name__ == "__main__":
    import random
    asyncio.run(main())
