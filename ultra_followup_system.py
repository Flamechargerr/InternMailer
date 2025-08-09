#!/usr/bin/env python3
"""
📧 ULTRA FOLLOW-UP SYSTEM
========================
Advanced follow-up email management for professor outreach campaigns

Features:
- Intelligent follow-up scheduling (2-3 weeks after initial email)
- Personalized follow-up templates based on research areas
- Response tracking and management
- Automated follow-up sequences
- Integration with main campaign system
- Professional follow-up timing
- Customizable templates
"""

import pandas as pd
import smtplib
import ssl
import json
import time
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Dict, List, Optional
import random
import os
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UltraFollowUpSystem:
    def __init__(self):
        """Initialize the follow-up system"""
        self.follow_up_templates = self.load_followup_templates()
        self.smtp_config = {}
        self.results_tracking = []
        
        # Follow-up timing configuration
        self.followup_timing = {
            'first_followup': 14,    # 2 weeks after initial
            'second_followup': 35,   # 5 weeks after initial  
            'final_followup': 60     # 8.5 weeks after initial
        }
        
        # Response detection patterns
        self.response_indicators = [
            'thank you for your email',
            'received your message',
            'interested in discussing',
            'would like to schedule',
            'unfortunately',
            'not accepting students',
            'no positions available'
        ]
    
    def load_followup_templates(self) -> Dict:
        """Load professional follow-up email templates"""
        return {
            'first_followup': {
                'subject': "Following up on Research Collaboration - {research_area}",
                'template': """Dear Professor {name},

I hope this email finds you well. I wanted to follow up on my previous email from {days_ago} days ago regarding research collaboration opportunities in {research_area}.

I understand that you receive many emails and wanted to reiterate my genuine interest in contributing to your research group at {affiliation}. Since my initial contact, I have been:

• Continuing to study your recent work, particularly in {specific_area}
• Developing relevant skills that align with your research methodologies
• Exploring potential research questions that could contribute to your ongoing projects

I would be grateful for the opportunity to discuss how I might contribute to your research initiatives, even if just for a brief conversation to learn more about your current projects.

Thank you for your time and consideration.

Best regards,
Anama Stylianou
Computer Science Student
Email: anamastylianouu@gmail.com
Phone: +357 99 123456

P.S. I am particularly drawn to the practical applications of {research_area} in solving real-world problems."""
            },
            
            'second_followup': {
                'subject': "Research Opportunity Inquiry - Final Follow-up",
                'template': """Dear Professor {name},

I hope you are having a productive semester. This is my final follow-up regarding potential research opportunities in {research_area} at {affiliation}.

I recognize that faculty receive numerous emails from prospective researchers, and I want to be respectful of your time. However, I remain genuinely interested in the innovative work being conducted in your research group.

Key points about my interest:
• Strong alignment with your research focus in {research_area}
• Commitment to making meaningful contributions to ongoing projects
• Flexibility in terms of research involvement and timeline
• Understanding that opportunities may be limited

If there might be any possibility for collaboration, mentorship, or even a brief informational discussion, I would be deeply grateful. If not, I completely understand and will not contact you further on this matter.

Thank you for your valuable contributions to the field and for considering my inquiry.

Respectfully,
Anama Stylianou
Computer Science Student
anamastylianouu@gmail.com"""
            },
            
            'research_specific': {
                'machine_learning': {
                    'subject': "ML Research Collaboration Follow-up - {specific_topic}",
                    'specific_area': "machine learning applications",
                    'details': "your work on neural networks and deep learning architectures"
                },
                'computer_systems': {
                    'subject': "Systems Research Follow-up - Distributed Computing",
                    'specific_area': "distributed systems",
                    'details': "your research on scalable computing infrastructure"
                },
                'security': {
                    'subject': "Cybersecurity Research Follow-up",
                    'specific_area': "cybersecurity",
                    'details': "your work on privacy-preserving technologies"
                },
                'algorithms': {
                    'subject': "Algorithms Research Follow-up",
                    'specific_area': "algorithmic optimization",
                    'details': "your research on computational efficiency"
                }
            }
        }
    
    def load_campaign_results(self) -> List[Dict]:
        """Load results from previous campaigns to identify follow-up candidates"""
        campaign_results = []
        
        # Look for campaign result files
        for file in os.listdir('.'):
            if file.startswith('ultra_campaign_results_v2_') and file.endswith('.csv'):
                try:
                    df = pd.read_csv(file)
                    
                    # Add metadata about the file
                    for _, row in df.iterrows():
                        result = row.to_dict()
                        result['campaign_file'] = file
                        result['original_timestamp'] = pd.to_datetime(row.get('timestamp'))
                        campaign_results.append(result)
                        
                    logger.info(f"📧 Loaded {len(df)} results from {file}")
                    
                except Exception as e:
                    logger.warning(f"Could not load {file}: {e}")
        
        return campaign_results
    
    def identify_followup_candidates(self) -> List[Dict]:
        """Identify professors who should receive follow-up emails"""
        campaign_results = self.load_campaign_results()
        
        if not campaign_results:
            logger.warning("No campaign results found for follow-up analysis")
            return []
        
        followup_candidates = []
        current_time = datetime.now()
        
        for result in campaign_results:
            # Only consider successfully sent emails
            if result.get('status') != 'success':
                continue
            
            original_time = result.get('original_timestamp')
            if not original_time:
                continue
            
            # Calculate days since original email
            days_since = (current_time - original_time).days
            
            # Determine follow-up type based on timing
            followup_type = None
            if days_since >= self.followup_timing['final_followup']:
                followup_type = 'final_followup'
            elif days_since >= self.followup_timing['second_followup']:
                followup_type = 'second_followup'  
            elif days_since >= self.followup_timing['first_followup']:
                followup_type = 'first_followup'
            
            if followup_type:
                candidate = {
                    'email': result.get('email'),
                    'name': result.get('name', 'Professor'),
                    'followup_type': followup_type,
                    'days_since_original': days_since,
                    'original_timestamp': original_time,
                    'research_found': result.get('research_found', False),
                    'research_areas': ['Computer Science'],  # Default
                    'affiliation': self.extract_affiliation_from_email(result.get('email', ''))
                }
                followup_candidates.append(candidate)
        
        # Remove duplicates (keep most recent)
        unique_candidates = {}
        for candidate in followup_candidates:
            email = candidate['email']
            if email not in unique_candidates or candidate['days_since_original'] > unique_candidates[email]['days_since_original']:
                unique_candidates[email] = candidate
        
        return list(unique_candidates.values())
    
    def extract_affiliation_from_email(self, email: str) -> str:
        """Extract university affiliation from email domain"""
        if not email or '@' not in email:
            return "University"
            
        domain = email.split('@')[1].lower()
        
        # Common university mappings
        university_map = {
            'mit.edu': 'MIT',
            'stanford.edu': 'Stanford University',
            'berkeley.edu': 'UC Berkeley',
            'harvard.edu': 'Harvard University',
            'cmu.edu': 'Carnegie Mellon University'
        }
        
        if domain in university_map:
            return university_map[domain]
        
        # Generic extraction
        if '.edu' in domain:
            name = domain.replace('.edu', '').replace('www.', '')
            return f"{name.capitalize()} University"
        
        return "University"
    
    def generate_followup_email(self, candidate: Dict) -> Dict[str, str]:
        """Generate personalized follow-up email"""
        followup_type = candidate['followup_type']
        template_data = self.follow_up_templates[followup_type]
        
        # Extract research area context
        research_area = 'Computer Science'
        specific_area = 'computational research'
        
        if candidate.get('research_found'):
            # Could be enhanced with actual research area detection
            research_areas = ['Machine Learning', 'Computer Systems', 'Security', 'Algorithms']
            research_area = random.choice(research_areas)
            specific_area = research_area.lower()
        
        # Generate subject
        subject = template_data['subject'].format(
            research_area=research_area,
            name=candidate['name']
        )
        
        # Generate body
        body = template_data['template'].format(
            name=candidate['name'].split()[0] if candidate['name'] != 'Professor' else 'Professor',
            days_ago=candidate['days_since_original'],
            research_area=research_area,
            specific_area=specific_area,
            affiliation=candidate['affiliation']
        )
        
        return {
            'subject': subject,
            'body': body,
            'template_type': followup_type
        }
    
    def send_followup_email(self, to_email: str, name: str, email_content: Dict, smtp_config: Dict) -> Dict:
        """Send a single follow-up email"""
        try:
            # Create message
            message = MIMEMultipart()
            message["From"] = formataddr(("Anama Stylianou", smtp_config['username']))
            message["To"] = to_email
            message["Subject"] = email_content['subject']
            message.attach(MIMEText(email_content['body'], "plain", "utf-8"))
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
                server.starttls(context=context)
                server.login(smtp_config['username'], smtp_config['password'])
                text = message.as_string()
                server.sendmail(smtp_config['username'], to_email, text)
            
            return {
                'email': to_email,
                'name': name,
                'status': 'success',
                'timestamp': datetime.now().isoformat(),
                'template_type': email_content['template_type']
            }
            
        except Exception as e:
            return {
                'email': to_email,
                'name': name,
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'template_type': email_content['template_type']
            }
    
    def run_followup_campaign(self, max_followups: int = 50) -> None:
        """Run a complete follow-up email campaign"""
        print("📧 ULTRA FOLLOW-UP SYSTEM")
        print("=" * 50)
        
        # Load email credentials (reuse from main system)
        try:
            with open('email_credentials.json', 'r') as f:
                creds = json.load(f)
                self.smtp_config = {
                    'server': 'smtp.gmail.com',
                    'port': 587,
                    'username': base64.b64decode(creds['username']).decode(),
                    'password': base64.b64decode(creds['password']).decode()
                }
            print("✅ Loaded saved email credentials")
        except:
            print("❌ Could not load email credentials. Please run main campaign first.")
            return
        
        # Identify candidates
        print("\n🔍 Identifying follow-up candidates...")
        candidates = self.identify_followup_candidates()
        
        if not candidates:
            print("📭 No follow-up candidates found.")
            print("💡 Make sure you have run email campaigns with successful sends.")
            return
        
        print(f"📊 Found {len(candidates)} follow-up candidates")
        
        # Group by follow-up type
        followup_stats = {}
        for candidate in candidates:
            ftype = candidate['followup_type']
            followup_stats[ftype] = followup_stats.get(ftype, 0) + 1
        
        print("\n📋 Follow-up Breakdown:")
        for ftype, count in followup_stats.items():
            days = {
                'first_followup': self.followup_timing['first_followup'],
                'second_followup': self.followup_timing['second_followup'], 
                'final_followup': self.followup_timing['final_followup']
            }[ftype]
            print(f"   • {ftype.replace('_', ' ').title()}: {count} ({days}+ days)")
        
        # Limit candidates
        if len(candidates) > max_followups:
            print(f"\n⚠️ Limiting to {max_followups} follow-ups (from {len(candidates)} candidates)")
            # Prioritize older candidates
            candidates = sorted(candidates, key=lambda x: x['days_since_original'], reverse=True)[:max_followups]
        
        # Confirm execution
        print(f"\n🚀 Ready to send {len(candidates)} follow-up emails")
        confirm = input("Continue with follow-up campaign? (y/n): ").strip().lower()
        
        if confirm not in ['y', 'yes']:
            print("❌ Follow-up campaign cancelled.")
            return
        
        # Send follow-ups
        print("\n📤 Sending follow-up emails...")
        results = []
        
        for i, candidate in enumerate(candidates, 1):
            try:
                # Generate email
                email_content = self.generate_followup_email(candidate)
                
                # Send email
                result = self.send_followup_email(
                    candidate['email'],
                    candidate['name'],
                    email_content,
                    self.smtp_config
                )
                
                results.append(result)
                
                # Progress indicator
                status_icon = "✅" if result['status'] == 'success' else "❌"
                print(f"   {status_icon} {i}/{len(candidates)}: {candidate['email']} ({candidate['followup_type']})")
                
                # Rate limiting
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.error(f"Error sending follow-up to {candidate['email']}: {e}")
                continue
        
        # Save results
        self.save_followup_results(results)
        self.display_followup_summary(results)
    
    def save_followup_results(self, results: List[Dict]) -> None:
        """Save follow-up campaign results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"followup_campaign_results_{timestamp}.csv"
        
        df_results = pd.DataFrame(results)
        df_results.to_csv(filename, index=False)
        
        print(f"\n💾 Follow-up results saved to: {filename}")
    
    def display_followup_summary(self, results: List[Dict]) -> None:
        """Display follow-up campaign summary"""
        total = len(results)
        successful = len([r for r in results if r['status'] == 'success'])
        failed = total - successful
        
        success_rate = (successful / total * 100) if total > 0 else 0
        
        print(f"\n🎉 FOLLOW-UP CAMPAIGN COMPLETED!")
        print("=" * 40)
        print(f"📊 RESULTS:")
        print(f"   • Total Follow-ups: {total}")
        print(f"   • Successful: {successful}")
        print(f"   • Failed: {failed}")
        print(f"   • Success Rate: {success_rate:.1f}%")
        
        # Breakdown by type
        type_stats = {}
        for result in results:
            ftype = result.get('template_type', 'unknown')
            if ftype not in type_stats:
                type_stats[ftype] = {'success': 0, 'failed': 0}
            
            type_stats[ftype][result['status']] += 1
        
        print(f"\n📋 BREAKDOWN BY TYPE:")
        for ftype, stats in type_stats.items():
            total_type = stats['success'] + stats['failed']
            success_rate_type = (stats['success'] / total_type * 100) if total_type > 0 else 0
            print(f"   • {ftype.replace('_', ' ').title()}: {stats['success']}/{total_type} ({success_rate_type:.1f}%)")

import base64

def main():
    """Main function to run follow-up system"""
    system = UltraFollowUpSystem()
    
    print("📧 ULTRA FOLLOW-UP SYSTEM")
    print("=" * 50)
    print("Professional follow-up email management for professor outreach")
    print()
    print("Features:")
    print("• Intelligent timing (2-8+ weeks after original)")
    print("• Personalized templates")
    print("• Professional tone and structure")
    print("• Automated candidate identification")
    print()
    
    # Check for campaign data
    results = system.load_campaign_results()
    if not results:
        print("❌ No campaign results found.")
        print("💡 Please run the main campaign system first to generate follow-up candidates.")
        return
    
    print(f"✅ Found {len(results)} previous campaign results")
    
    # Get follow-up configuration
    max_followups = input("Maximum follow-ups to send (default: 50): ").strip()
    try:
        max_followups = int(max_followups) if max_followups else 50
    except:
        max_followups = 50
    
    # Run follow-up campaign
    system.run_followup_campaign(max_followups)

if __name__ == "__main__":
    main()
