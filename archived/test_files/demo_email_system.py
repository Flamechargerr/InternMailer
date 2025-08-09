#!/usr/bin/env python3
"""
Demo Email System with Ultra-Accurate Research Finder
Sends personalized emails to the first 3 professors with real publication data
"""

import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
import json
import os
from typing import List, Dict
from ultra_accurate_research_finder import UltraAccurateResearchFinder, AuthorProfile, Publication

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('demo_email_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DemoEmailSystem:
    """
    Demo email system that sends personalized emails to professors using
    ultra-accurate research data
    """
    
    def __init__(self):
        self.research_finder = UltraAccurateResearchFinder()
        self.sent_emails = []
        
        # Email configuration (you'll need to set these)
        self.smtp_config = {
            'server': 'smtp.gmail.com',  # or your SMTP server
            'port': 587,
            'username': '',  # Your email
            'password': '',  # Your app password
            'use_tls': True
        }
        
        # Load email credentials from environment or config file
        self.load_email_config()
        
    def load_email_config(self):
        """Load email configuration from environment variables or config file"""
        # Try environment variables first
        if os.getenv('EMAIL_USERNAME'):
            self.smtp_config['username'] = os.getenv('EMAIL_USERNAME')
            self.smtp_config['password'] = os.getenv('EMAIL_PASSWORD')
            return
        
        # Try config file
        config_file = 'email_config.json'
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.smtp_config.update(config)
                logger.info("Email config loaded from file")
            except Exception as e:
                logger.error(f"Failed to load email config: {e}")
    
    def load_professors_database(self, csv_path: str = None) -> pd.DataFrame:
        """Load the professors database"""
        if csv_path is None:
            csv_path = "data/proffesor_clean.csv"
        
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df)} professors from database")
            return df
        except Exception as e:
            logger.error(f"Failed to load professors database: {e}")
            return pd.DataFrame()
    
    def generate_research_alignment_explanation(self, professor_profile: AuthorProfile, 
                                              your_research_interests: List[str]) -> str:
        """
        Generate personalized research alignment explanation based on professor's publications
        """
        # Default research interests if not provided
        if not your_research_interests:
            your_research_interests = [
                "machine learning", "artificial intelligence", "data mining", 
                "natural language processing", "computer vision"
            ]
        
        # Find overlapping research interests
        prof_interests = set(interest.lower() for interest in professor_profile.research_interests)
        your_interests = set(interest.lower() for interest in your_research_interests)
        overlap = prof_interests.intersection(your_interests)
        
        # Analyze recent publications for specific alignment
        publication_insights = []
        for pub in professor_profile.recent_publications[:3]:  # Top 3 publications
            if pub.abstract:
                # Simple keyword analysis for alignment
                abstract_lower = pub.abstract.lower()
                matching_interests = [
                    interest for interest in your_research_interests
                    if interest.lower() in abstract_lower
                ]
                
                if matching_interests:
                    publication_insights.append({
                        'title': pub.title,
                        'year': pub.year,
                        'venue': pub.venue,
                        'matching_interests': matching_interests,
                        'abstract_snippet': pub.abstract[:200] + "..."
                    })
        
        # Generate explanation text
        explanation_parts = []
        
        if overlap:
            explanation_parts.append(
                f"I noticed our research interests align particularly well in {', '.join(overlap)}."
            )
        
        if publication_insights:
            explanation_parts.append(
                f"Your recent work particularly caught my attention:"
            )
            
            for insight in publication_insights[:2]:  # Top 2 insights
                explanation_parts.append(
                    f"• Your {insight['year']} paper \"{insight['title']}\" "
                    f"published in {insight['venue']} aligns with my interests in "
                    f"{', '.join(insight['matching_interests'])}."
                )
        
        if not explanation_parts:
            # Fallback if no specific alignment found
            recent_work = professor_profile.recent_publications[0] if professor_profile.recent_publications else None
            if recent_work:
                explanation_parts.append(
                    f"I'm particularly interested in your recent work on \"{recent_work.title}\" "
                    f"({recent_work.year}), which relates to my research in {your_research_interests[0]}."
                )
            else:
                explanation_parts.append(
                    f"I'm very interested in your research in {', '.join(professor_profile.research_interests[:2])} "
                    f"and how it connects with my work in {your_research_interests[0]}."
                )
        
        return " ".join(explanation_parts)
    
    def create_personalized_email(self, professor_profile: AuthorProfile, 
                                 your_name: str = "Your Name",
                                 your_background: str = "research student",
                                 your_research_interests: List[str] = None) -> Dict[str, str]:
        """
        Create a personalized email based on professor's real publication data
        """
        if not your_research_interests:
            your_research_interests = ["machine learning", "artificial intelligence"]
        
        # Generate research alignment explanation
        research_alignment = self.generate_research_alignment_explanation(
            professor_profile, your_research_interests
        )
        
        # Create email subject
        subject = f"Research Collaboration Opportunity - {your_research_interests[0].title()} Alignment"
        
        # Create email body
        recent_pub = professor_profile.recent_publications[0] if professor_profile.recent_publications else None
        
        email_body = f"""Dear Professor {professor_profile.name.split()[-1]},

I hope this email finds you well. I am {your_name}, a {your_background} with a strong interest in {', '.join(your_research_interests[:2])}.

{research_alignment}

RECENT PUBLICATIONS ANALYSIS:
"""
        
        # Add detailed publication information
        if professor_profile.recent_publications:
            email_body += f"\nI've reviewed your recent publications and found several that align with my research:\n"
            
            for i, pub in enumerate(professor_profile.recent_publications[:3], 1):
                email_body += f"""
{i}. "{pub.title}" ({pub.year})
   Published in: {pub.venue}
   Citations: {pub.citations}
   Research Relevance: {pub.abstract[:150] if pub.abstract else 'Highly relevant to current research trends'}...
"""
        
        email_body += f"""

RESEARCH COLLABORATION POTENTIAL:
Based on your expertise in {', '.join(professor_profile.research_interests[:3])}, I believe there are several areas where our research could complement each other:

• Methodological approaches in {your_research_interests[0]}
• Collaborative publications in high-impact venues
• Joint research grant opportunities
• Cross-disciplinary innovation

I would be honored to discuss potential collaboration opportunities, whether through research projects, mentorship, or academic partnerships.

Would you be available for a brief call or meeting to explore how we might work together? I'm flexible with timing and can accommodate your schedule.

Thank you for your time and consideration. I look forward to the possibility of contributing to your research endeavors.

Best regards,
{your_name}

---
Research Interests: {', '.join(your_research_interests)}
Contact: [Your Email]
LinkedIn: [Your LinkedIn Profile]

P.S. This email was generated using advanced research analysis to ensure accurate representation of your current work and research focus.
"""
        
        return {
            'subject': subject,
            'body': email_body,
            'to_email': professor_profile.email,
            'to_name': professor_profile.name
        }
    
    def send_email(self, email_data: Dict[str, str]) -> bool:
        """Send email using SMTP"""
        try:
            if not self.smtp_config['username'] or not self.smtp_config['password']:
                logger.warning("Email credentials not configured - email will be saved to file instead")
                return self.save_email_to_file(email_data)
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['username']
            msg['To'] = email_data['to_email']
            msg['Subject'] = email_data['subject']
            
            # Add body
            msg.attach(MIMEText(email_data['body'], 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port']) as server:
                if self.smtp_config['use_tls']:
                    server.starttls()
                
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {email_data['to_name']} ({email_data['to_email']})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {email_data['to_email']}: {e}")
            # Save to file as fallback
            return self.save_email_to_file(email_data)
    
    def save_email_to_file(self, email_data: Dict[str, str]) -> bool:
        """Save email to file as fallback"""
        try:
            filename = f"demo_emails/email_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{email_data['to_name'].replace(' ', '_')}.txt"
            
            # Create directory if it doesn't exist
            os.makedirs('demo_emails', exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"TO: {email_data['to_name']} <{email_data['to_email']}>\n")
                f.write(f"SUBJECT: {email_data['subject']}\n")
                f.write("="*80 + "\n\n")
                f.write(email_data['body'])
            
            logger.info(f"Email saved to file: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save email to file: {e}")
            return False
    
    def run_demo(self, num_professors: int = 3):
        """
        Run the demo email system with ultra-accurate research data
        """
        print("🚀 STARTING DEMO EMAIL SYSTEM")
        print("=" * 80)
        
        # Load professors database
        professors_df = self.load_professors_database()
        
        if professors_df.empty:
            print("❌ Could not load professors database")
            return
        
        # Get first N professors for demo
        demo_professors = professors_df.head(num_professors)
        
        print(f"📊 Processing {len(demo_professors)} professors for demo")
        print("=" * 80)
        
        successful_emails = 0
        
        for idx, row in demo_professors.iterrows():
            print(f"\n🔍 Processing Professor {idx + 1}/{len(demo_professors)}")
            print(f"👤 Name: {row['Name']}")
            print(f"🏛️  University: {row['University']}")
            print(f"📧 Email: {row['Email']}")
            print("-" * 60)
            
            # Create author profile with ultra-accurate research data
            print("📚 Gathering research publications...")
            try:
                profile = self.research_finder.create_author_profile(
                    name=row['Name'],
                    affiliation=row['University'],
                    email=row['Email'],
                    homepage=row.get('Homepage', '')
                )
                
                print(f"✅ Found {len(profile.recent_publications)} recent publications")
                print(f"🔬 Research interests: {', '.join(profile.research_interests[:3])}")
                
                # Display publications found
                for i, pub in enumerate(profile.recent_publications, 1):
                    print(f"   {i}. \"{pub.title}\" ({pub.year}) - {pub.venue}")
                    print(f"      Citations: {pub.citations} | Confidence: {pub.confidence_score:.2f}")
                
                # Generate personalized email
                print("\n✉️  Generating personalized email...")
                email_data = self.create_personalized_email(
                    professor_profile=profile,
                    your_name="Alex Research Student",
                    your_background="PhD candidate in Computer Science",
                    your_research_interests=["machine learning", "artificial intelligence", "data mining"]
                )
                
                # Send or save email
                if self.send_email(email_data):
                    successful_emails += 1
                    self.sent_emails.append({
                        'professor': row['Name'],
                        'email': row['Email'],
                        'university': row['University'],
                        'publications_found': len(profile.recent_publications),
                        'research_interests': profile.research_interests,
                        'timestamp': datetime.now().isoformat(),
                        'success': True
                    })
                    print("✅ Email sent/saved successfully!")
                else:
                    print("❌ Failed to send/save email")
                
            except Exception as e:
                logger.error(f"Error processing {row['Name']}: {e}")
                print(f"❌ Error: {e}")
                continue
            
            print("=" * 80)
        
        # Summary
        print(f"\n📈 DEMO COMPLETED")
        print(f"✅ Successfully processed: {successful_emails}/{len(demo_professors)} professors")
        print(f"📁 Emails saved to: demo_emails/ directory")
        
        # Save summary report
        self.save_demo_report()
    
    def save_demo_report(self):
        """Save a summary report of the demo"""
        try:
            report = {
                'demo_timestamp': datetime.now().isoformat(),
                'total_processed': len(self.sent_emails),
                'success_rate': len([e for e in self.sent_emails if e['success']]) / len(self.sent_emails) if self.sent_emails else 0,
                'professors_data': self.sent_emails
            }
            
            with open('demo_email_report.json', 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"📊 Demo report saved to: demo_email_report.json")
            
        except Exception as e:
            logger.error(f"Failed to save demo report: {e}")

def main():
    """Main function to run the demo"""
    print("🎯 ULTRA-ACCURATE RESEARCH FINDER DEMO")
    print("This demo will:")
    print("1. Load the first 3 professors from your database")
    print("2. Find their real, recent publications using multiple sources")
    print("3. Generate personalized emails with research alignment")
    print("4. Save/send the emails with publication details")
    print("\n" + "="*80)
    
    # Initialize and run demo
    demo_system = DemoEmailSystem()
    demo_system.run_demo(num_professors=3)
    
    print("\n🎉 Demo completed!")
    print("📁 Check the 'demo_emails' folder for generated emails")
    print("📊 Check 'demo_email_report.json' for detailed statistics")
    print("\nIf the emails look good, we can scale to your full 40,000+ professor database!")

if __name__ == "__main__":
    main()
