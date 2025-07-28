#!/usr/bin/env python3
"""
Fully Automated Email Campaign Runner
=====================================
One-command automation for professor outreach campaigns.
Handles everything: tracking sync, duplicate prevention, email sending, logging.

Usage: python auto_campaign.py [campaign_size]
Example: python auto_campaign.py 20
"""

import sys
import json
import csv
import smtplib
import random
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
import os
from enhanced_personalized_email import generate_deeply_personalized_email

# Configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "tripathy.anamay23@gmail.com"
EMAIL_PASSWORD = "qzxw bjqs wgqk wqtt"  # App password

CV_PATH = "../resumes/CV_Anamay_Modern.pdf"
PROFESSORS_DB = "data/proffesor_clean.csv"
EMAIL_LOG = "email_log.csv"
TRACKER_JSON = "data/emailed_professors.json"

# Email template - Professional style matching your actual emails
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
</head>
<body style="margin: 0; padding: 0; background-color: #f8f8f8;">
    <div style="max-width: 800px; margin: auto; background: #ffffff; padding: 30px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; line-height: 1.6; color: #333;">
      
      <p>Dear Prof. {professor_name},</p>

      <p>
        I am <strong>Anamay Tripathy</strong>, a third-year B.Tech Data Science student at MIT Manipal, India. I am writing to express my strong interest in a research internship with your esteemed group at <strong>{university}</strong>, particularly in the areas of <strong>{research_area}</strong> and <strong>Artificial Intelligence</strong>.
      </p>

      <p>
        Your pioneering work in <strong>{research_area}</strong> has been a significant inspiration for me, especially given {university}'s reputation for cutting-edge research in this domain. I am eager to contribute meaningfully to your ongoing projects and deepen my understanding under your expert guidance.
      </p>

      <h3 style="background-color: #f0f0f0; padding: 5px;">Academic Background</h3>
      <ul>
        <li><strong>Degree:</strong> B.Tech in Data Science Engineering (2023–2027)</li>
        <li><strong>Institution:</strong> MIT Manipal, India</li>
        <li><strong>CGPA:</strong> 7.6 / 10</li>
        <li><strong>Relevant Coursework:</strong> Data Structures & Algorithms, Machine Learning, DBMS, Computer Networks, Software Engineering</li>
      </ul>

      <h3 style="background-color: #f0f0f0; padding: 5px;">Professional Experience</h3>
      <ul>
        <li><strong>Technical Head</strong> – <a href="https://www.yaanbarpe.in/" target="_blank">YaanBarpe</a> (Current)</li>
        <li><strong>Data Analyst Intern</strong> – Intellect Design Arena (3 months)
          <ul>
            <li>Automated KPI dashboards using Python and SQL, saving 12+ hours/week</li>
            <li>Developed REST APIs that improved user engagement by 22%</li>
          </ul>
        </li>
      </ul>

      <h3 style="background-color: #f0f0f0; padding: 5px;">Selected Projects</h3>
      <ul>
        <li><strong><a href="https://crime-connect-fbi.lovable.app/login" target="_blank">CrimeConnect</a>:</strong> FBI-inspired case management dashboard (MERN + Supabase); 40% reduction in case processing time</li>
        <li><strong><a href="https://match-predictor-genie-66.lovable.app/" target="_blank">VARtificial Intelligence</a>:</strong> ML-based football match predictor (XGBoost, Pyodide); 89% accuracy</li>
        <li><strong><a href="https://flamechargerr.github.io/" target="_blank">HackOps</a>:</strong> Cybersecurity simulation & training platform with 25+ challenges; improved awareness by 35%</li>
        <li><strong><a href="https://github.com/Flamechargerr/flora-fight-frenzy" target="_blank">Flora Fight Frenzy</a>:</strong> Tower defense game inspired by Plant vs Zombies; original gameplay mechanics</li>
      </ul>

      <h3 style="background-color: #f0f0f0; padding: 5px;">Technical Skills</h3>
      <ul>
        <li><strong>Languages:</strong> Python, JavaScript, Java, C++, SQL</li>
        <li><strong>AI/ML:</strong> TensorFlow, PyTorch, Scikit-learn, XGBoost, OpenCV</li>
        <li><strong>Web:</strong> React, Node.js, MongoDB, Next.js</li>
        <li><strong>Tools:</strong> Git, Docker, AWS, GCP, Supabase, Firebase</li>
        <li><strong>Data Science:</strong> Statistical Analysis, Data Visualization, Predictive Modeling</li>
      </ul>

      <p>
        I am confident that my academic foundation in Data Science, hands-on experience with ML/AI projects, and enthusiasm for research in <strong>{research_area}</strong> align well with your group's research objectives. I believe my background in developing AI-powered systems and data analysis tools would allow me to make meaningful contributions to your ongoing work.
      </p>

      <p>
        I would be grateful for the opportunity to contribute as a research intern—remotely or on-site, funded or voluntary. I am particularly excited about the possibility of working on projects that combine my technical skills with your expertise in <strong>{research_area}</strong>.
      </p>

      <p>I would be happy to share my detailed CV and discuss how I can support your lab's work.</p>

      <h3 style="background-color: #f0f0f0; padding: 5px;">Contact</h3>
      <ul>
        <li><strong>CV:</strong> CV_Anamay_Modern (attached)</li>
        <li><strong>Email:</strong> <a href="mailto:tripathy.anamay23@gmail.com">tripathy.anamay23@gmail.com</a></li>
        <li><strong>Phone:</strong> <a href="tel:+919877454747">+91-9877454747</a></li>
        <li><strong>Portfolio:</strong> <a href="https://anamay.vercel.app/" target="_blank">anamay.vercel.app</a></li>
        <li><strong>LinkedIn:</strong> <a href="https://linkedin.com/in/anamay-tripathy" target="_blank">linkedin.com/in/anamay-tripathy</a></li>
        <li><strong>GitHub:</strong> <a href="https://github.com/Flamechargerr" target="_blank">github.com/Flamechargerr</a></li>
        <li><strong>GitHub Profile README:</strong> <a href="https://github.com/Flamechargerr/Flamechargerr/blob/main/README.md" target="_blank">Profile README</a></li>
      </ul>

      <p>Thank you for your time and consideration.</p>

      <p>Warm regards,<br />
      <strong>Anamay Tripathy</strong></p>

    </div>
</body>
</html>
"""

class AutoCampaignRunner:
    def __init__(self):
        self.professors_contacted = set()
        self.email_log_data = []
        self.tracker_data = {}
        
    def load_tracking_data(self):
        """Load and sync all tracking data"""
        print("📄 Loading and syncing tracking data...")
        
        # Load email log
        if os.path.exists(EMAIL_LOG):
            with open(EMAIL_LOG, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                self.email_log_data = list(reader)
                
            # Extract contacted emails
            for entry in self.email_log_data:
                if entry.get('status') in ['sent', 'success']:
                    self.professors_contacted.add(entry['email'].lower())
        
        # Load tracker JSON
        if os.path.exists(TRACKER_JSON):
            with open(TRACKER_JSON, 'r', encoding='utf-8') as file:
                self.tracker_data = json.load(file)
                
            # Add tracked emails to contacted set
            for email in self.tracker_data.get('emailed_professors', []):
                self.professors_contacted.add(email.lower())
        else:
            self.tracker_data = {'emailed_professors': []}
        
        print(f"✅ Loaded {len(self.professors_contacted)} already contacted professors")
        
    def get_available_professors(self, campaign_size):
        """Get list of available professors for campaign"""
        print("📋 Loading professor database...")
        
        if not os.path.exists(PROFESSORS_DB):
            print(f"❌ Professor database not found: {PROFESSORS_DB}")
            return []
            
        available_professors = []
        
        with open(PROFESSORS_DB, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                email = row.get('Email', '').lower()
                if email and email not in self.professors_contacted:
                    available_professors.append(row)
        
        print(f"📊 Found {len(available_professors)} available professors (not contacted)")
        
        if len(available_professors) < campaign_size:
            print(f"⚠️  Warning: Only {len(available_professors)} professors available, but {campaign_size} requested")
            campaign_size = len(available_professors)
        
        # Randomly select professors for campaign
        selected = random.sample(available_professors, min(campaign_size, len(available_professors)))
        print(f"🎯 Selected {len(selected)} professors for campaign")
        
        return selected
        
    def send_email(self, professor):
        """Send email to a single professor"""
        try:
            # Create email
            msg = MIMEMultipart()
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = professor['Email']
            msg['Subject'] = f"Research Internship Inquiry – Anamay Tripathy re: {professor.get('Research Area', 'AI Research')}"
            
# Generate personalized content
            html_body = generate_deeply_personalized_email(professor)
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attach CV
            if os.path.exists(CV_PATH):
                with open(CV_PATH, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(CV_PATH)}'
                    )
                    msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            text = msg.as_string()
            server.sendmail(EMAIL_ADDRESS, professor['Email'], text)
            server.quit()
            
            return True, "sent"
            
        except Exception as e:
            return False, str(e)
    
    def update_tracking(self, professor, status, error_msg=None):
        """Update tracking files with campaign results"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Update email log
        log_entry = {
            'timestamp': timestamp,
            'email': professor['Email'],
            'name': professor.get('Name', ''),
            'university': professor.get('University', ''),
            'status': status,
            'error': error_msg or ''
        }
        
        self.email_log_data.append(log_entry)
        
        # Update tracker JSON
        if status == 'sent':
            if 'emailed_professors' not in self.tracker_data:
                self.tracker_data['emailed_professors'] = []
            if professor['Email'].lower() not in [e.lower() for e in self.tracker_data['emailed_professors']]:
                self.tracker_data['emailed_professors'].append(professor['Email'])
    
    def save_tracking_data(self):
        """Save all tracking data to files"""
        print("💾 Saving tracking data...")
        
        # Save email log
        with open(EMAIL_LOG, 'w', newline='', encoding='utf-8') as file:
            if self.email_log_data:
                fieldnames = ['timestamp', 'email', 'name', 'university', 'status', 'error']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.email_log_data)
        
        # Save tracker JSON
        with open(TRACKER_JSON, 'w', encoding='utf-8') as file:
            json.dump(self.tracker_data, file, indent=2)
        
        print("✅ Tracking data saved successfully")
    
    def run_campaign(self, campaign_size):
        """Run the complete automated campaign"""
        print("🚀 Starting Automated Email Campaign")
        print("=" * 50)
        
        # Step 1: Load tracking data
        self.load_tracking_data()
        
        # Step 2: Get available professors
        professors = self.get_available_professors(campaign_size)
        
        if not professors:
            print("❌ No available professors for campaign")
            return
        
        # Step 3: Run campaign
        print(f"\n📤 Starting email campaign for {len(professors)} professors...")
        print("-" * 50)
        
        sent_count = 0
        failed_count = 0
        
        for i, professor in enumerate(professors, 1):
            print(f"[{i}/{len(professors)}] Emailing {professor.get('Name', 'Unknown')} ({professor['Email']})...", end=' ')
            
            success, result = self.send_email(professor)
            
            if success:
                print("✅ SENT")
                self.update_tracking(professor, 'sent')
                sent_count += 1
            else:
                print(f"❌ FAILED: {result}")
                self.update_tracking(professor, 'failed', result)
                failed_count += 1
            
            # Small delay between emails
            if i < len(professors):
                time.sleep(2)
        
        # Step 4: Save results
        self.save_tracking_data()
        
        # Step 5: Campaign summary
        print("\n" + "=" * 50)
        print("📊 CAMPAIGN SUMMARY")
        print("=" * 50)
        print(f"✅ Successfully sent: {sent_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📧 Total contacted (all time): {len(self.professors_contacted) + sent_count}")
        
        if sent_count > 0:
            print(f"\n🎉 Campaign completed! {sent_count} emails sent successfully.")
            print("📝 All tracking data updated automatically.")
            print("🔄 Run again anytime - duplicate prevention is active!")
        else:
            print("\n⚠️  No emails were sent successfully.")
        
def main():
    """Main entry point"""
    print("🤖 Automated Email Campaign Runner")
    print("=" * 40)
    
    # Get campaign size from command line or prompt
    campaign_size = 10  # default
    
    if len(sys.argv) > 1:
        try:
            campaign_size = int(sys.argv[1])
        except ValueError:
            print("❌ Invalid campaign size. Using default: 10")
    else:
        try:
            user_input = input(f"Enter campaign size (default: 10): ").strip()
            if user_input:
                campaign_size = int(user_input)
        except (ValueError, KeyboardInterrupt):
            print("Using default campaign size: 10")
    
    if campaign_size <= 0:
        print("❌ Campaign size must be positive")
        return
    
    print(f"🎯 Campaign size: {campaign_size}")
    print("-" * 40)
    
    # Run the campaign
    runner = AutoCampaignRunner()
    runner.run_campaign(campaign_size)

if __name__ == "__main__":
    main()
