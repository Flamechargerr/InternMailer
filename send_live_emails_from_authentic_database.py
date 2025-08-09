#!/usr/bin/env python3
"""
Live Email Campaign - Using AUTHENTIC 40K Professor Database
InternMailing System with Enhanced Academic Templates and Research Area Analysis
"""

import os
import smtplib
import json
import pandas as pd
import random
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
from jinja2 import Template

load_dotenv()

class AuthenticProfessorEmailSystem:
    def __init__(self):
        self.databases = {
            'final_master': 'production/databases/FINAL_MASTER_EMAIL_DATABASE.csv',
            'enhanced_emails': 'enhanced_background_emails.csv',
            'cleaned_database': 'cleaned_professor_database_20250807_181910.csv'
        }
        
    def load_contacted_emails(self):
        """Load all previously contacted email addresses"""
        contacted = set()
        contacted_names = set()
        
        # PRIORITY 1: Load from email_log.csv (main source of contacted emails)
        try:
            df = pd.read_csv('email_log.csv')
            if 'email' in df.columns:
                csv_emails = set(df['email'].dropna().str.lower().str.strip())
                contacted.update(csv_emails)
                print(f"📊 Loaded {len(csv_emails)} emails from email_log.csv")
            
            # Also get names if available
            if 'name' in df.columns:
                csv_names = set(df['name'].dropna().str.lower().str.strip())
                contacted_names.update(csv_names)
                print(f"📊 Loaded {len(csv_names)} names from email_log.csv")
        except FileNotFoundError:
            print("⚠️ email_log.csv not found - continuing with other sources")
        except Exception as e:
            print(f"⚠️ Error loading email_log.csv: {e}")
        
        # PRIORITY 2: Load from emailed_professors.json
        try:
            with open('data/emailed_professors.json', 'r') as f:
                emailed = json.load(f)
                for prof in emailed:
                    email = prof.get('recipient_email', '').strip().lower()
                    if email:
                        contacted.add(email)
                    name = prof.get('recipient_name', '').strip().lower()
                    if name:
                        contacted_names.add(name)
                print(f"📊 Added {len(emailed)} from emailed_professors.json")
        except FileNotFoundError:
            print("⚠️ data/emailed_professors.json not found")
        except Exception as e:
            print(f"⚠️ Error loading emailed_professors.json: {e}")
            
        # PRIORITY 3: Load from sent_emails_log.json (from ULTRA system)
        try:
            with open('sent_emails_log.json', 'r') as f:
                data = json.load(f)
                sent_emails = data.get('sent_emails', [])
                contacted.update([email.lower().strip() for email in sent_emails])
                print(f"📊 Added {len(sent_emails)} from sent_emails_log.json")
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"⚠️ Error loading sent_emails_log.json: {e}")
            
        # PRIORITY 4: From campaign results
        import glob
        campaign_count = 0
        for file_path in glob.glob('campaign_results/email_*.txt'):
            try:
                with open(file_path, 'r') as f:
                    first_line = f.readline()
                    if 'TO:' in first_line and '<' in first_line and '>' in first_line:
                        email = first_line.split('<')[1].split('>')[0].strip().lower()
                        contacted.add(email)
                        campaign_count += 1
            except:
                continue
        if campaign_count > 0:
            print(f"📊 Added {campaign_count} from campaign_results")
                
        # PRIORITY 5: From personalized emails folder
        personalized_count = 0
        for file_path in glob.glob('personalized_emails/email_*.txt'):
            filename = os.path.basename(file_path)
            if 'email_' in filename:
                name_part = filename.split('_', 3)[-1].replace('.txt', '').replace('_', ' ')
                contacted_names.add(name_part.lower().strip())
                personalized_count += 1
        if personalized_count > 0:
            print(f"📊 Added {personalized_count} names from personalized_emails")
        
        print(f"\n🔍 TOTAL DUPLICATE DETECTION SUMMARY:")
        print(f"📧 Total contacted emails: {len(contacted)}")
        print(f"👤 Total contacted names: {len(contacted_names)}")
        print(f"🛡️ Duplicate detection active for {len(contacted) + len(contacted_names)} entries")
        
        return contacted, contacted_names
    
    def validate_email(self, email):
        """Validate email address"""
        if not email or not isinstance(email, str):
            return False
        
        email = email.strip()
        
        # Basic format check
        if '@' not in email or '.' not in email:
            return False
            
        # Remove common contaminations from scraping
        contaminations = [
            'Office', 'Faculty', 'Phone', 'Fax', 'Room', 'Building',
            'http://', 'https://', 'www.', '.html', '.php', '.aspx',
            'Professor', 'Dr.', 'PhD', 'Address'
        ]
        
        for contamination in contaminations:
            if contamination in email:
                return False
        
        # Check for valid academic domains
        valid_domains = [
            '.edu', '.ac.uk', '.ac.in', '.ac.jp', '.ac.kr', '.ac.cn',
            '.edu.au', '.edu.sg', '.edu.hk', '.uni-', '.univ-'
        ]
        
        if not any(domain in email.lower() for domain in valid_domains):
            return False
            
        # Check for common invalid patterns
        invalid_patterns = ['.open', '.pdf', '.doc', '.txt', '.jpg']
        if any(pattern in email.lower() for pattern in invalid_patterns):
            return False
            
        return True
    
    def infer_research_area_from_email_and_name(self, email, name, affiliation=""):
        """Infer research area from available data"""
        if not email or not name:
            return 'Computer Science'
            
        combined_text = f"{email} {name} {affiliation}".lower()
        
        # AI/ML researchers
        if any(keyword in combined_text for keyword in [
            'ai', 'ml', 'machine learning', 'artificial intelligence', 
            'neural', 'deep learning', 'nlp', 'computer vision', 'cv'
        ]):
            if any(keyword in combined_text for keyword in ['vision', 'image', 'graphics', 'cv']):
                return 'Computer Vision'
            else:
                return 'Machine Learning'
        
        # Security researchers
        if any(keyword in combined_text for keyword in [
            'security', 'crypto', 'cryptography', 'cyber', 'privacy',
            'secure', 'auth', 'authentication'
        ]):
            return 'Cybersecurity'
        
        # Systems researchers
        if any(keyword in combined_text for keyword in [
            'systems', 'distributed', 'parallel', 'cloud', 'hpc',
            'performance', 'network', 'os', 'operating'
        ]):
            return 'Distributed Systems'
        
        # Data science researchers
        if any(keyword in combined_text for keyword in [
            'data', 'analytics', 'statistics', 'database', 'mining',
            'big data', 'visualization'
        ]):
            return 'Data Science'
        
        # Web/Software engineering
        if any(keyword in combined_text for keyword in [
            'web', 'software engineering', 'programming', 'development',
            'frontend', 'backend'
        ]):
            return 'Web Technologies'
            
        return 'Computer Science'
    
    def is_professor_already_contacted(self, name, affiliation, email, contacted_names, contacted_emails):
        """Advanced duplicate detection by name, university, and email patterns"""
        if not name:
            return True
            
        # Check exact email match
        if email in contacted_emails:
            return True
            
        # Extract name components
        name_parts = name.lower().strip().split()
        if len(name_parts) < 2:
            return False
            
        first_name = name_parts[0]
        last_name = name_parts[-1]
        
        # Check for name variations in contacted list
        for contacted_name in contacted_names:
            contacted_parts = contacted_name.split()
            if len(contacted_parts) >= 2:
                contacted_first = contacted_parts[0]
                contacted_last = contacted_parts[-1]
                
                # Check if both first and last name match
                if (first_name == contacted_first and last_name == contacted_last) or \
                   (first_name in contacted_name or contacted_first in name.lower()) and \
                   (last_name in contacted_name or contacted_last in name.lower()):
                    print(f"📋 Duplicate detected: {name} matches contacted {contacted_name}")
                    return True
        
        # Check university + name combination
        if affiliation:
            affiliation_lower = affiliation.lower()
            # Extract university domain from email if possible
            email_domain = email.split('@')[1] if '@' in email else ""
            
            # Look for similar names at same university
            for contacted_name in contacted_names:
                if len(name_parts) >= 2 and len(contacted_name.split()) >= 2:
                    # If last name matches and university domain matches
                    if last_name in contacted_name.lower():
                        # This might be the same person
                        print(f"📋 Potential duplicate: {name} at {affiliation} (similar to {contacted_name})")
                        return True
        
        return False
    
    def load_authentic_professors(self, limit=50):
        """Load professors from authentic databases with quality filtering"""
        print("🔍 Loading from AUTHENTIC 40K Professor Database...")
        
        contacted_emails, contacted_names = self.load_contacted_emails()
        fresh_professors = []
        
        # Try to load from the best available database
        for db_name, db_path in self.databases.items():
            if os.path.exists(db_path):
                print(f"📂 Loading from {db_name}: {db_path}")
                
                try:
                    df = pd.read_csv(db_path)
                    print(f"📊 Found {len(df)} records in {db_name}")
                    
                    processed = 0
                    for _, row in df.iterrows():
                        if len(fresh_professors) >= limit:
                            break
                            
                        processed += 1
                        if processed > 1000:  # Limit processing for performance
                            break
                        
                        # Extract data with multiple fallbacks
                        email = ""
                        name = ""
                        affiliation = ""
                        
                        # Try different column names
                        for email_col in ['email', 'Email', 'EMAIL']:
                            if email_col in row and pd.notna(row[email_col]):
                                email = str(row[email_col]).strip()
                                break
                        
                        for name_col in ['name', 'Name', 'NAME']:
                            if name_col in row and pd.notna(row[name_col]):
                                name = str(row[name_col]).strip()
                                break
                        
                        for affil_col in ['affiliation', 'university', 'University', 'Affiliation']:
                            if affil_col in row and pd.notna(row[affil_col]):
                                affiliation = str(row[affil_col]).strip()
                                break
                        
                        # Quality checks
                        if not self.validate_email(email):
                            continue
                            
                        if email in contacted_emails:
                            continue
                            
                        if not name or len(name) < 2:
                            continue
                            
                        # Advanced duplicate detection by name and university
                        if self.is_professor_already_contacted(name, affiliation, email, contacted_names, contacted_emails):
                            continue
                        
                        # Extract research area
                        research_area = self.infer_research_area_from_email_and_name(email, name, affiliation)
                        
                        # Parse name
                        name_parts = name.split()
                        first_name = name_parts[0] if name_parts else 'Professor'
                        last_name = name_parts[-1] if len(name_parts) > 1 else 'Professor'
                        
                        professor_data = {
                            'first_name': first_name,
                            'last_name': last_name,
                            'email': email,
                            'university': affiliation if affiliation else 'University',
                            'research_area': research_area,
                            'full_name': name,
                            'source_database': db_name,
                            'quality_score': self.calculate_quality_score(email, name, affiliation)
                        }
                        
                        fresh_professors.append(professor_data)
                        
                        if len(fresh_professors) % 10 == 0:
                            print(f"   ✅ Found {len(fresh_professors)} quality professors...")
                
                except Exception as e:
                    print(f"⚠️ Error reading {db_path}: {e}")
                    continue
                
                if fresh_professors:
                    break
        
        # Sort by quality score and return best ones
        fresh_professors.sort(key=lambda x: x['quality_score'], reverse=True)
        
        print(f"🎯 Found {len(fresh_professors)} high-quality fresh professors")
        return fresh_professors[:limit]
    
    def calculate_quality_score(self, email, name, affiliation):
        """Calculate quality score for professor data"""
        score = 0
        
        # Email quality
        if self.validate_email(email):
            score += 5
            
        # Name quality
        if name and len(name.split()) >= 2:
            score += 3
            
        # University quality
        if affiliation and len(affiliation) > 5:
            score += 2
            
        # Top university bonus
        top_unis = ['MIT', 'Stanford', 'Harvard', 'Berkeley', 'CMU', 'Caltech']
        if any(uni.lower() in affiliation.lower() for uni in top_unis):
            score += 5
            
        return score
    
    def save_emailed_professor(self, professor_data, success):
        """Save professor to emailed list"""
        try:
            with open('data/emailed_professors.json', 'r') as f:
                emailed_professors = json.load(f)
        except FileNotFoundError:
            emailed_professors = []
        
        emailed_professors.append({
            "timestamp": datetime.now().isoformat(),
            "email_type": "Professor",
            "recipient_email": professor_data['email'],
            "recipient_name": professor_data['first_name'],
            "company": "",
            "university": professor_data['university'],
            "research_area": professor_data['research_area'],
            "source_database": professor_data.get('source_database', 'authentic_db'),
            "quality_score": professor_data.get('quality_score', 0),
            "success": success
        })
        
        with open('data/emailed_professors.json', 'w') as f:
            json.dump(emailed_professors, f, indent=4)
    
    def create_personalized_email(self, professor_data):
        """Create personalized email using enhanced template"""
        try:
            with open('templates/enhanced_academic_research_template.html', 'r', encoding='utf-8') as f:
                template_content = f.read()
        except FileNotFoundError:
            print("❌ Enhanced template not found, using basic template")
            return None, None
        
        research_area = professor_data['research_area']
        
        # Research area specific personalization
        if research_area == 'Machine Learning':
            highlighted_projects = ['VARtificial Intelligence - Machine Learning Sports Prediction System']
            relevant_coursework = ['Machine Learning', 'Deep Learning', 'Statistical Analysis', 'Neural Networks']
            skills_emphasis = ['TensorFlow', 'PyTorch', 'Scikit-learn', 'XGBoost']
            research_alignment = f"My expertise in machine learning algorithms, deep learning frameworks, and AI applications directly aligns with your research in {research_area}. My projects demonstrate practical implementation of ML models achieving 89% prediction accuracy."
        elif research_area == 'Computer Vision':
            highlighted_projects = ['Computer Vision and Image Analysis Systems']
            relevant_coursework = ['Computer Vision', 'Image Processing', 'OpenCV', 'Digital Signal Processing']
            skills_emphasis = ['OpenCV', 'Computer Vision', 'Image Processing', 'Pattern Recognition']
            research_alignment = f"My experience with computer vision algorithms, image processing techniques, and pattern recognition systems directly relates to your research in {research_area}. I have hands-on experience with OpenCV and advanced image analysis."
        elif research_area == 'Cybersecurity':
            highlighted_projects = ['HackOps - Cybersecurity Simulation and Training Platform']
            relevant_coursework = ['Network Security', 'Cryptography', 'Ethical Hacking', 'Information Security']
            skills_emphasis = ['Security Frameworks', 'Penetration Testing', 'Network Security']
            research_alignment = f"My cybersecurity training platform with 25+ security challenges and penetration testing experience directly relates to your research in {research_area}. I've implemented comprehensive security frameworks improving user awareness by 35%."
        elif research_area == 'Data Science':
            highlighted_projects = ['CrimeConnect - FBI-Inspired Case Management Dashboard']
            relevant_coursework = ['Data Science', 'Statistical Analysis', 'Data Visualization', 'Predictive Modeling']
            skills_emphasis = ['Statistical Analysis', 'Data Visualization', 'Predictive Modeling']
            research_alignment = f"My background in statistical analysis, predictive modeling, and data visualization aligns perfectly with your research in {research_area}. I've achieved 22% improvement in user engagement through data-driven insights."
        elif research_area == 'Distributed Systems':
            highlighted_projects = ['Scalable System Architectures and Cloud Platforms']
            relevant_coursework = ['Distributed Systems', 'Cloud Computing', 'System Architecture', 'Performance Optimization']
            skills_emphasis = ['AWS', 'GCP', 'Docker', 'System Design']
            research_alignment = f"My experience with scalable system architectures, cloud computing, and distributed algorithm optimization directly complements your research in {research_area}. I have practical experience with AWS, GCP, and high-performance computing systems."
        else:  # Default including Web Technologies and Computer Science
            highlighted_projects = ['VARtificial Intelligence', 'CrimeConnect', 'HackOps']
            relevant_coursework = ['Data Structures & Algorithms', 'Machine Learning', 'Database Management', 'Software Engineering']
            skills_emphasis = ['Python', 'Machine Learning', 'System Design', 'Full Stack Development']
            research_alignment = f"My diverse technical background and experience across multiple domains of computer science positions me well to contribute to your research in {research_area}."
        
        context = {
            'professor': {
                'last_name': professor_data['last_name'],
                'research_area': research_area,
                'research_title': research_area,
                'research_alignment': research_alignment,
                'highlighted_projects': highlighted_projects,
                'relevant_coursework': relevant_coursework,
                'skills_emphasis': skills_emphasis,
                'recent_publications_html': None
            }
        }
        
        html_content = Template(template_content).render(**context)
        subject = f"Research Internship Inquiry - {research_area}"
        
        return subject, html_content
    
    def send_html_email_with_cv(self, recipient_email, subject, html_content, professor_name):
        """Send HTML email with CV attachment"""
        gmail_user = os.getenv('GMAIL_USER')
        gmail_password = os.getenv('GMAIL_APP_PASSWORD')
        
        if not gmail_user or not gmail_password:
            print("❌ Gmail credentials not found in environment variables")
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = gmail_user
        msg['To'] = recipient_email
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
                f'attachment; filename=CV_Anamay_Tripathy.pdf'
            )
            msg.attach(part)
            print(f"📎 CV attached: {cv_path}")
        else:
            print(f"⚠️ CV not found at: {cv_path}")
        
        # Send email
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, recipient_email, msg.as_string())
            server.quit()
            print(f"✅ Email sent successfully to {professor_name} ({recipient_email})")
            return True
        except Exception as e:
            print(f"❌ Failed to send email to {professor_name}: {e}")
            return False

def main():
    """Main function for authentic professor email campaign"""
    print("🚀 LIVE EMAIL CAMPAIGN - AUTHENTIC 40K PROFESSOR DATABASE")
    print("=" * 80)
    print("📧 Using Enhanced Academic Research Template with Research Area Analysis")
    print("📊 Quality-filtered professors from authentic database")
    print("📎 CV attachments included automatically")
    print("🎯 Advanced research area inference and personalization")
    print("=" * 80)
    print()
    
    system = AuthenticProfessorEmailSystem()
    
    # Load fresh professors from authentic database
    print("🔍 Loading high-quality professors from authentic database...")
    fresh_professors = system.load_authentic_professors(limit=10)
    
    if not fresh_professors:
        print("❌ No fresh professors found in authentic database!")
        return
    
    # Select top 3 by quality score
    top_professors = fresh_professors[:3]
    
    print(f"✅ Found {len(top_professors)} top-quality fresh professors to contact:")
    for i, prof in enumerate(top_professors, 1):
        print(f"   {i}. {prof['full_name']} - {prof['university']}")
        print(f"      📧 {prof['email']} | 🎯 {prof['research_area']}")
        print(f"      🏆 Quality Score: {prof['quality_score']} | 📂 Source: {prof['source_database']}")
    print()
    
    # Confirm before sending
    user_input = input("🤔 Ready to send live emails to these HIGH-QUALITY professors? (y/n): ")
    if user_input.lower() != 'y':
        print("❌ Email campaign cancelled by user.")
        return
    
    print()
    print("📤 STARTING LIVE EMAIL CAMPAIGN WITH AUTHENTIC DATA...")
    print("=" * 80)
    
    successful_sends = 0
    
    for i, professor in enumerate(top_professors, 1):
        print(f"\n📧 EMAIL {i}/{len(top_professors)}: {professor['full_name']}")
        print(f"🏫 University: {professor['university']}")
        print(f"🎯 Research Area: {professor['research_area']}")
        print(f"📩 Email: {professor['email']}")
        print(f"🏆 Quality Score: {professor['quality_score']}")
        
        # Create personalized email
        subject, html_content = system.create_personalized_email(professor)
        if not subject:
            print(f"❌ Failed to create email for {professor['full_name']}")
            continue
            
        print(f"📋 Subject: {subject}")
        
        # Send email
        success = system.send_html_email_with_cv(
            professor['email'], 
            subject, 
            html_content, 
            professor['full_name']
        )
        
        # Save to emailed list
        system.save_emailed_professor(professor, success)
        
        if success:
            successful_sends += 1
            print(f"✅ Email {i} sent successfully!")
        else:
            print(f"❌ Email {i} failed to send.")
        
        # Add delay between emails
        if i < len(top_professors):
            print("⏳ Waiting 5 seconds before next email...")
            time.sleep(5)
    
    print("\n" + "=" * 80)
    print("📊 AUTHENTIC DATABASE LIVE EMAIL CAMPAIGN RESULTS")
    print("=" * 80)
    print(f"📤 Total emails attempted: {len(top_professors)}")
    print(f"✅ Successfully sent: {successful_sends}")
    print(f"❌ Failed to send: {len(top_professors) - successful_sends}")
    print(f"📈 Success rate: {(successful_sends/len(top_professors)*100):.1f}%")
    
    if successful_sends > 0:
        print("\n🎉 AUTHENTIC DATABASE FEATURES DEPLOYED:")
        print("✅ 40K+ Professor Database with Quality Filtering")
        print("✅ Research Area Analysis and Inference")
        print("✅ Enhanced Academic Research Template")
        print("✅ Research area-specific personalization")
        print("✅ CV attachments included")
        print("✅ Professional HTML styling")
        print("✅ Quality score-based professor ranking")
        print("✅ Advanced duplicate detection")
        
        print("\n📧 High-quality professors contacted with personalized emails:")
        for prof in top_professors:
            print(f"   • {prof['full_name']} ({prof['research_area']}) - Quality: {prof['quality_score']}")
    
    print("\n" + "=" * 80)
    print("🚀 AUTHENTIC DATABASE LIVE EMAIL CAMPAIGN COMPLETED!")
    print("📊 Using your premium 40K professor database with quality filtering")
    print("=" * 80)

if __name__ == "__main__":
    main()
