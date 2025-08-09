#!/usr/bin/env python3
"""
Ultra HTML Bulk Campaign System v5.0
=====================================
Final production-ready system combining:
- Large database processing with proper email validation
- Semantic Scholar research integration
- Sophisticated HTML email templates with research content
- CV attachments and professional formatting
- High-performance bulk mailing with concurrency
- Comprehensive duplicate tracking and analytics
"""

import pandas as pd
import numpy as np
import smtplib
import ssl
import re
import os
import json
import time
import logging
import hashlib
import requests
import asyncio
import aiosmtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, RLock
from jinja2 import Template
from typing import Dict, List, Tuple, Optional
import concurrent.futures
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ultra_campaign.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltraHTMLBulkCampaign:
    """Ultra sophisticated HTML bulk email campaign system."""
    
    def __init__(self):
        self.config = self.load_config()
        self.sent_emails = set()
        self.sent_emails_file = 'sent_emails_log.json'
        self.campaign_stats = {
            'total_processed': 0,
            'emails_sent': 0,
            'emails_failed': 0,
            'duplicates_skipped': 0,
            'invalid_emails': 0,
            'research_papers_found': 0,
            'start_time': None,
            'end_time': None
        }
        self.lock = RLock()
        self.load_sent_emails_log()
        
        # Semantic Scholar API settings
        self.api_base_url = "https://api.semanticscholar.org/graph/v1"
        self.api_delay = 0.1  # Rate limiting
        
        # Email templates
        self.setup_html_templates()
        
    def load_config(self) -> Dict:
        """Load configuration from environment or defaults."""
        config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'email_address': os.getenv('EMAIL_ADDRESS', ''),
            'email_password': os.getenv('EMAIL_PASSWORD', ''),
            'sender_name': os.getenv('SENDER_NAME', 'Anam Ahmed'),
            'cv_attachment_path': os.getenv('CV_PATH', 'Anam_Ahmed_CV.pdf'),
            'max_emails_per_session': int(os.getenv('MAX_EMAILS_PER_SESSION', '100')),
            'concurrent_workers': int(os.getenv('CONCURRENT_WORKERS', '5')),
            'research_keywords': os.getenv('RESEARCH_KEYWORDS', 'machine learning,artificial intelligence,computer vision,natural language processing').split(',')
        }
        
        if not config['email_address'] or not config['email_password']:
            logger.error("Email credentials not found in environment variables!")
            raise ValueError("Please set EMAIL_ADDRESS and EMAIL_PASSWORD environment variables")
            
        return config
    
    def setup_html_templates(self):
        """Setup sophisticated HTML email templates."""
        self.email_template = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Collaboration Opportunity</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px 10px 0 0;
            text-align: center;
        }
        .content {
            background: white;
            padding: 30px;
            border-radius: 0 0 10px 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .research-highlight {
            background: #f0f8ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .publication-list {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }
        .cta-button {
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 25px;
            text-decoration: none;
            border-radius: 25px;
            font-weight: bold;
            margin: 20px 0;
        }
        .signature {
            margin-top: 30px;
            border-top: 2px solid #eee;
            padding-top: 20px;
        }
        .skills-tags {
            margin: 15px 0;
        }
        .skill-tag {
            display: inline-block;
            background: #e9ecef;
            color: #495057;
            padding: 5px 12px;
            margin: 3px;
            border-radius: 15px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎓 Research Collaboration Opportunity</h1>
        <p>Connecting Innovation with Excellence</p>
    </div>
    
    <div class="content">
        <p>Dear Professor {{ professor_name }},</p>
        
        <p>I hope this email finds you well. My name is <strong>{{ sender_name }}</strong>, and I am writing to explore potential research collaboration opportunities with your esteemed team at <strong>{{ university }}</strong>.</p>
        
        {% if research_alignment %}
        <div class="research-highlight">
            <h3>🔬 Research Alignment</h3>
            <p>{{ research_alignment }}</p>
        </div>
        {% endif %}
        
        {% if recent_publications %}
        <div class="publication-list">
            <h3>📚 Your Recent Publications That Caught My Attention</h3>
            <ul>
            {% for pub in recent_publications %}
                <li><strong>{{ pub.title }}</strong> ({{ pub.year }})
                    {% if pub.venue %} - <em>{{ pub.venue }}</em>{% endif %}
                    {% if pub.citations %} - {{ pub.citations }} citations{% endif %}
                </li>
            {% endfor %}
            </ul>
        </div>
        {% endif %}
        
        <h3>🚀 About My Research Background</h3>
        <p>I am a passionate researcher specializing in:</p>
        <div class="skills-tags">
            {% for skill in research_skills %}
            <span class="skill-tag">{{ skill }}</span>
            {% endfor %}
        </div>
        
        <p>My current research focuses on developing innovative solutions in {{ primary_research_area }}, with particular emphasis on practical applications and real-world impact.</p>
        
        <div class="research-highlight">
            <h3>💡 Collaboration Proposal</h3>
            <p>I would be honored to contribute to your research initiatives through:</p>
            <ul>
                <li><strong>Technical Expertise:</strong> {{ technical_skills }}</li>
                <li><strong>Research Contribution:</strong> {{ research_contribution }}</li>
                <li><strong>Innovation Focus:</strong> {{ innovation_focus }}</li>
            </ul>
        </div>
        
        <p>I have attached my CV for your review, which provides comprehensive details about my academic background, research experience, and technical competencies.</p>
        
        <p>I would be delighted to discuss potential collaboration opportunities at your convenience. Would you be available for a brief call or meeting to explore how we might work together?</p>
        
        <a href="mailto:{{ sender_email }}?subject=Re: Research Collaboration Opportunity" class="cta-button">
            📧 Let's Connect
        </a>
        
        <div class="signature">
            <p>Thank you for considering this opportunity. I look forward to your response.</p>
            
            <p><strong>Best regards,</strong><br>
            {{ sender_name }}<br>
            📧 {{ sender_email }}<br>
            🔗 Available for immediate collaboration<br>
            📋 CV attached for detailed review</p>
        </div>
    </div>
</body>
</html>
        """)
        
        # Plain text fallback
        self.plain_text_template = Template("""
Dear Professor {{ professor_name }},

I hope this email finds you well. My name is {{ sender_name }}, and I am writing to explore potential research collaboration opportunities with your esteemed team at {{ university }}.

{% if research_alignment %}
RESEARCH ALIGNMENT:
{{ research_alignment }}
{% endif %}

{% if recent_publications %}
YOUR RECENT PUBLICATIONS THAT CAUGHT MY ATTENTION:
{% for pub in recent_publications %}
- {{ pub.title }} ({{ pub.year }}){% if pub.venue %} - {{ pub.venue }}{% endif %}
{% endfor %}
{% endif %}

ABOUT MY RESEARCH BACKGROUND:
I am a passionate researcher specializing in: {{ research_skills | join(', ') }}

My current research focuses on developing innovative solutions in {{ primary_research_area }}, with particular emphasis on practical applications and real-world impact.

COLLABORATION PROPOSAL:
I would be honored to contribute to your research initiatives through:
- Technical Expertise: {{ technical_skills }}
- Research Contribution: {{ research_contribution }}
- Innovation Focus: {{ innovation_focus }}

I have attached my CV for your review, which provides comprehensive details about my academic background, research experience, and technical competencies.

I would be delighted to discuss potential collaboration opportunities at your convenience. Would you be available for a brief call or meeting to explore how we might work together?

Thank you for considering this opportunity. I look forward to your response.

Best regards,
{{ sender_name }}
{{ sender_email }}
CV attached for detailed review
        """)
    
    def load_sent_emails_log(self):
        """Load previously sent emails to avoid duplicates."""
        try:
            # First try the JSON log
            if os.path.exists(self.sent_emails_file):
                with open(self.sent_emails_file, 'r') as f:
                    data = json.load(f)
                    self.sent_emails = set(data.get('sent_emails', []))
                logger.info(f"Loaded {len(self.sent_emails)} previously sent emails from JSON log")
            
            # Also load from email_log.csv if it exists
            if os.path.exists('email_log.csv'):
                try:
                    import pandas as pd
                    df = pd.read_csv('email_log.csv')
                    if 'email' in df.columns:
                        csv_emails = set(df['email'].dropna().str.lower())
                        original_count = len(self.sent_emails)
                        self.sent_emails.update(csv_emails)
                        new_count = len(self.sent_emails) - original_count
                        logger.info(f"Added {new_count} additional sent emails from email_log.csv")
                        logger.info(f"Total sent emails loaded: {len(self.sent_emails)}")
                except Exception as e:
                    logger.warning(f"Could not load email_log.csv: {e}")
            
        except Exception as e:
            logger.error(f"Error loading sent emails log: {e}")
            self.sent_emails = set()
    
    def save_sent_emails_log(self):
        """Save sent emails log to prevent duplicates."""
        try:
            with open(self.sent_emails_file, 'w') as f:
                json.dump({
                    'sent_emails': list(self.sent_emails),
                    'last_updated': datetime.now().isoformat(),
                    'total_sent': len(self.sent_emails)
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving sent emails log: {e}")
    
    def load_professor_database(self) -> pd.DataFrame:
        """Load and clean the professor database."""
        logger.info("Loading professor database...")
        
        # Try to load the main database file
        database_files = [
            'professors_database.csv',
            'enhanced_background_emails.csv',
            'enhanced_background_emails_part1.csv',
            'data/list.csv',
            'data/proffesor_clean.csv'
        ]
        
        df = None
        for file_path in database_files:
            if os.path.exists(file_path):
                try:
                    logger.info(f"Loading database from {file_path}")
                    df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)
                    break
                except Exception as e:
                    logger.warning(f"Failed to load {file_path}: {e}")
                    continue
        
        if df is None:
            raise FileNotFoundError("No valid professor database file found!")
        
        logger.info(f"Loaded {len(df)} total records")
        
        # Clean and validate the data
        df = self.clean_database(df)
        
        return df
    
    def clean_database(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate professor database."""
        logger.info("Cleaning professor database...")
        
        original_count = len(df)
        
        # Handle different possible column names
        email_columns = ['email', 'Email', 'email_address', 'Email Address']
        name_columns = ['name', 'Name', 'professor_name', 'Professor Name', 'full_name']
        university_columns = ['university', 'University', 'institution', 'Institution', 'affiliation']
        
        # Find the correct column names
        email_col = next((col for col in email_columns if col in df.columns), None)
        name_col = next((col for col in name_columns if col in df.columns), None)
        university_col = next((col for col in university_columns if col in df.columns), None)
        
        if not email_col:
            raise ValueError(f"No email column found. Available columns: {list(df.columns)}")
        
        # Standardize column names
        df = df.rename(columns={
            email_col: 'email',
            name_col: 'name' if name_col else 'name',
            university_col: 'university' if university_col else 'university'
        })
        
        # Ensure required columns exist
        if 'name' not in df.columns:
            df['name'] = ''
        if 'university' not in df.columns:
            df['university'] = ''
        
        # Clean email addresses
        df['email'] = df['email'].astype(str)
        df['email'] = df['email'].str.strip().str.lower()
        
        # Remove invalid emails
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        valid_email_mask = df['email'].str.match(email_pattern, na=False)
        df = df[valid_email_mask]
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['email'])
        
        # Clean names - extract from email if name is missing
        df['name'] = df['name'].astype(str)
        missing_name_mask = (df['name'].isna()) | (df['name'] == '') | (df['name'] == 'nan')
        
        def extract_name_from_email(email):
            try:
                local_part = email.split('@')[0]
                # Remove common prefixes and suffixes
                local_part = re.sub(r'^(prof|dr|professor)\.?', '', local_part, flags=re.IGNORECASE)
                local_part = re.sub(r'\.(prof|dr|professor)$', '', local_part, flags=re.IGNORECASE)
                
                # Split by common separators and title case
                parts = re.split(r'[._-]', local_part)
                name_parts = [part.title() for part in parts if part.isalpha() and len(part) > 1]
                return ' '.join(name_parts) if name_parts else local_part.title()
            except:
                return "Professor"
        
        df.loc[missing_name_mask, 'name'] = df.loc[missing_name_mask, 'email'].apply(extract_name_from_email)
        
        # Clean university names
        df['university'] = df['university'].astype(str)
        df.loc[df['university'].isna() | (df['university'] == 'nan'), 'university'] = 'University'
        
        # Remove emails that have already been contacted
        df = df[~df['email'].isin(self.sent_emails)]
        
        final_count = len(df)
        removed_count = original_count - final_count
        
        logger.info(f"Database cleaned: {removed_count} records removed, {final_count} valid records remaining")
        
        return df
    
    def fetch_research_papers(self, professor_name: str, university: str) -> List[Dict]:
        """Fetch research papers from Semantic Scholar API."""
        try:
            # Search for the professor
            search_query = f"{professor_name} {university}"
            url = f"{self.api_base_url}/author/search"
            
            params = {
                'query': search_query,
                'limit': 5
            }
            
            response = requests.get(url, params=params, timeout=10)
            time.sleep(self.api_delay)  # Rate limiting
            
            if response.status_code != 200:
                return []
            
            authors_data = response.json()
            
            if not authors_data.get('data'):
                return []
            
            # Get the first author (most likely match)
            author = authors_data['data'][0]
            author_id = author.get('authorId')
            
            if not author_id:
                return []
            
            # Fetch papers for this author
            papers_url = f"{self.api_base_url}/author/{author_id}/papers"
            papers_params = {
                'fields': 'title,year,venue,citationCount,publicationDate',
                'limit': 5
            }
            
            papers_response = requests.get(papers_url, params=papers_params, timeout=10)
            time.sleep(self.api_delay)  # Rate limiting
            
            if papers_response.status_code != 200:
                return []
            
            papers_data = papers_response.json()
            papers = papers_data.get('data', [])
            
            # Process and return recent papers
            processed_papers = []
            for paper in papers:
                processed_papers.append({
                    'title': paper.get('title', 'Unknown Title'),
                    'year': paper.get('year', 'Unknown Year'),
                    'venue': paper.get('venue', ''),
                    'citations': paper.get('citationCount', 0)
                })
            
            # Sort by year (most recent first)
            processed_papers.sort(key=lambda x: x['year'] if isinstance(x['year'], int) else 0, reverse=True)
            
            self.campaign_stats['research_papers_found'] += len(processed_papers)
            
            return processed_papers[:3]  # Return top 3 most recent papers
            
        except Exception as e:
            logger.debug(f"Error fetching papers for {professor_name}: {e}")
            return []
    
    def generate_personalized_content(self, professor_name: str, university: str, papers: List[Dict]) -> Dict:
        """Generate personalized email content."""
        
        # Research alignment based on papers
        research_alignment = ""
        if papers:
            research_areas = []
            for paper in papers:
                title = paper.get('title', '').lower()
                for keyword in self.config['research_keywords']:
                    if keyword.lower() in title:
                        research_areas.append(keyword)
            
            if research_areas:
                unique_areas = list(set(research_areas))
                research_alignment = f"I am particularly interested in your work in {', '.join(unique_areas[:3])}, which aligns perfectly with my research interests and expertise."
        
        if not research_alignment:
            research_alignment = "Your research profile and academic contributions align well with my interests in cutting-edge technological innovation and practical applications."
        
        # Generate content
        content = {
            'professor_name': professor_name,
            'university': university,
            'sender_name': self.config['sender_name'],
            'sender_email': self.config['email_address'],
            'research_alignment': research_alignment,
            'recent_publications': papers,
            'research_skills': [
                'Machine Learning & Deep Learning',
                'Computer Vision & Image Processing',
                'Natural Language Processing',
                'Data Science & Analytics',
                'Artificial Intelligence Applications',
                'Software Engineering & Development'
            ],
            'primary_research_area': 'artificial intelligence and machine learning',
            'technical_skills': 'Advanced programming in Python, TensorFlow, PyTorch, and modern ML frameworks',
            'research_contribution': 'Innovative algorithmic approaches and practical implementation of AI solutions',
            'innovation_focus': 'Bridging the gap between theoretical research and real-world applications'
        }
        
        return content
    
    def create_email_message(self, recipient_email: str, content: Dict) -> MIMEMultipart:
        """Create sophisticated HTML email message with CV attachment."""
        
        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr((self.config['sender_name'], self.config['email_address']))
        msg['To'] = recipient_email
        msg['Subject'] = f"Research Collaboration Opportunity - {self.config['sender_name']}"
        
        # Generate HTML and plain text versions
        html_content = self.email_template.render(**content)
        text_content = self.plain_text_template.render(**content)
        
        # Attach both versions
        text_part = MIMEText(text_content, 'plain')
        html_part = MIMEText(html_content, 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Attach CV if available
        cv_path = self.config['cv_attachment_path']
        if os.path.exists(cv_path):
            try:
                with open(cv_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(cv_path)}'
                    )
                    msg.attach(part)
            except Exception as e:
                logger.warning(f"Could not attach CV: {e}")
        
        return msg
    
    def send_single_email(self, recipient_email: str, professor_name: str, university: str) -> bool:
        """Send a single email with full personalization."""
        
        try:
            # Check if already sent
            if recipient_email in self.sent_emails:
                with self.lock:
                    self.campaign_stats['duplicates_skipped'] += 1
                return False
            
            # Fetch research papers
            papers = self.fetch_research_papers(professor_name, university)
            
            # Generate personalized content
            content = self.generate_personalized_content(professor_name, university, papers)
            
            # Create email message
            msg = self.create_email_message(recipient_email, content)
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                server.starttls(context=context)
                server.login(self.config['email_address'], self.config['email_password'])
                server.send_message(msg)
            
            # Mark as sent
            with self.lock:
                self.sent_emails.add(recipient_email)
                self.campaign_stats['emails_sent'] += 1
                
                # Save email content for records
                email_record = {
                    'timestamp': datetime.now().isoformat(),
                    'recipient': recipient_email,
                    'professor_name': professor_name,
                    'university': university,
                    'papers_found': len(papers),
                    'subject': msg['Subject']
                }
                
                # Save to individual file
                safe_email = re.sub(r'[^\w\-_.]', '_', recipient_email)
                with open(f'sent_emails/{safe_email}.json', 'w') as f:
                    json.dump(email_record, f, indent=2)
            
            logger.info(f"✅ Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            with self.lock:
                self.campaign_stats['emails_failed'] += 1
            logger.error(f"❌ Failed to send email to {recipient_email}: {e}")
            return False
    
    def run_bulk_campaign(self):
        """Run the complete bulk email campaign."""
        
        logger.info("🚀 Starting Ultra HTML Bulk Campaign System v5.0")
        self.campaign_stats['start_time'] = datetime.now()
        
        # Create directories
        os.makedirs('sent_emails', exist_ok=True)
        
        # Load professor database
        try:
            df = self.load_professor_database()
        except Exception as e:
            logger.error(f"Failed to load database: {e}")
            return
        
        # Limit emails for this session
        max_emails = min(len(df), self.config['max_emails_per_session'])
        df_session = df.head(max_emails)
        
        logger.info(f"📧 Processing {len(df_session)} professors in this session")
        logger.info(f"🔄 Using {self.config['concurrent_workers']} concurrent workers")
        
        # Process emails with threading
        with ThreadPoolExecutor(max_workers=self.config['concurrent_workers']) as executor:
            
            # Submit all email tasks
            future_to_email = {}
            for idx, row in df_session.iterrows():
                email = row['email']
                name = row['name']
                university = row['university']
                
                future = executor.submit(self.send_single_email, email, name, university)
                future_to_email[future] = email
                
                self.campaign_stats['total_processed'] += 1
            
            # Process completed tasks
            completed_count = 0
            for future in as_completed(future_to_email):
                completed_count += 1
                
                # Progress update
                if completed_count % 10 == 0:
                    progress = (completed_count / len(df_session)) * 100
                    logger.info(f"📈 Progress: {completed_count}/{len(df_session)} ({progress:.1f}%)")
                
                # Save progress periodically
                if completed_count % 25 == 0:
                    self.save_sent_emails_log()
        
        # Final save and statistics
        self.save_sent_emails_log()
        self.campaign_stats['end_time'] = datetime.now()
        self.print_campaign_summary()
    
    def print_campaign_summary(self):
        """Print comprehensive campaign statistics."""
        
        duration = (self.campaign_stats['end_time'] - self.campaign_stats['start_time']).total_seconds()
        
        logger.info("\n" + "="*60)
        logger.info("📊 ULTRA CAMPAIGN SUMMARY")
        logger.info("="*60)
        logger.info(f"⏱️  Campaign Duration: {duration:.2f} seconds")
        logger.info(f"📧 Total Processed: {self.campaign_stats['total_processed']}")
        logger.info(f"✅ Emails Sent: {self.campaign_stats['emails_sent']}")
        logger.info(f"❌ Failed: {self.campaign_stats['emails_failed']}")
        logger.info(f"🔄 Duplicates Skipped: {self.campaign_stats['duplicates_skipped']}")
        logger.info(f"🔬 Research Papers Found: {self.campaign_stats['research_papers_found']}")
        
        if self.campaign_stats['emails_sent'] > 0:
            success_rate = (self.campaign_stats['emails_sent'] / self.campaign_stats['total_processed']) * 100
            emails_per_minute = (self.campaign_stats['emails_sent'] / duration) * 60
            logger.info(f"📈 Success Rate: {success_rate:.1f}%")
            logger.info(f"⚡ Speed: {emails_per_minute:.1f} emails/minute")
        
        logger.info(f"📁 Email records saved in: sent_emails/ directory")
        logger.info(f"📋 Sent emails log: {self.sent_emails_file}")
        logger.info("="*60)

def main():
    """Main execution function."""
    try:
        # Initialize and run campaign
        campaign = UltraHTMLBulkCampaign()
        campaign.run_bulk_campaign()
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Campaign interrupted by user")
    except Exception as e:
        logger.error(f"💥 Critical error: {e}")
        raise

if __name__ == "__main__":
    main()
