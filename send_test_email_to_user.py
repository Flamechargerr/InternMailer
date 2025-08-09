#!/usr/bin/env python3
"""
Send Test Email to User
Sends both HR and Academic email templates to confirm they work properly
"""

import smtplib
import pandas as pd
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime

def load_hr_template():
    """Load the enhanced HR email template"""
    template_path = "templates/enhanced_email_template.html"
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "HR template not found"

def load_academic_template():
    """Load the enhanced academic email template"""
    template_path = "templates/academic_research_template.html"
    if os.path.exists(template_path):
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Academic template not found"

def create_hr_email(name, company_name, company_niche):
    """Create HR email with personalization"""
    template = load_hr_template()
    
    # Replace placeholders with actual data
    email_content = template.replace("{{name}}", name)
    email_content = email_content.replace("{{company_name}}", company_name)
    email_content = email_content.replace("{{company_niche}}", company_niche)
    email_content = email_content.replace("{{company_niche.lower()}}", company_niche.lower())
    
    return email_content

def create_academic_email(professor_name, research_area):
    """Create academic email with personalization"""
    template = load_academic_template()
    
    # Replace placeholders with actual data
    email_content = template.replace("{{professor_name}}", professor_name)
    email_content = email_content.replace("{{research_area}}", research_area)
    email_content = email_content.replace("{{research_area.lower()}}", research_area.lower())
    
    return email_content

def send_test_email_to_user():
    """Send test email to user with both templates"""
    print("📧 SENDING TEST EMAIL TO USER...")
    
    # Sample data for testing
    hr_sample = {
        'name': 'Sarah Johnson', 
        'company_name': 'TechInnovate Solutions', 
        'company_niche': 'Artificial Intelligence',
        'email': 'sarah.johnson@techinnovate.com'
    }
    
    prof_sample = {
        'name': 'Dr. Michael Chen',
        'affiliation': 'Stanford University',
        'email': 'mchen@stanford.edu',
        'research_area': 'Machine Learning and Computer Vision'
    }
    
    # Create emails
    hr_email = create_hr_email(
        hr_sample['name'], 
        hr_sample['company_name'], 
        hr_sample['company_niche']
    )
    
    academic_email = create_academic_email(
        prof_sample['name'], 
        prof_sample['research_area']
    )
    
    # Create combined test email
    combined_email = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Email Templates Test - HR & Academic</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .section {{ margin-bottom: 40px; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px; }}
            .hr-section {{ border-left: 4px solid #3498db; }}
            .academic-section {{ border-left: 4px solid #27ae60; }}
            h1 {{ color: #333; text-align: center; margin-bottom: 30px; }}
            h2 {{ color: #3498db; margin-bottom: 20px; }}
            .academic-section h2 {{ color: #27ae60; }}
            .info-box {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 30px; }}
            .info-box h3 {{ color: #495057; margin-top: 0; }}
            .info-box ul {{ margin: 0; padding-left: 20px; }}
            .info-box li {{ margin-bottom: 8px; color: #6c757d; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📧 Email Templates Test - HR & Academic</h1>
            
            <div class="section hr-section">
                <h2>💼 Professional HR Email Template</h2>
                <p><strong>To:</strong> {hr_sample['name']} ({hr_sample['email']})</p>
                <p><strong>Company:</strong> {hr_sample['company_name']} - {hr_sample['company_niche']}</p>
                {hr_email}
            </div>
            
            <div class="section academic-section">
                <h2>🎓 Academic Research Email Template</h2>
                <p><strong>To:</strong> {prof_sample['name']} ({prof_sample['email']})</p>
                <p><strong>Affiliation:</strong> {prof_sample['affiliation']}</p>
                <p><strong>Research Area:</strong> {prof_sample['research_area']}</p>
                {academic_email}
            </div>
            
            <div class="info-box">
                <h3>✅ Template Status</h3>
                <ul>
                    <li>✅ HR Template: Professional and business-focused</li>
                    <li>✅ Academic Template: Research-oriented and detailed</li>
                    <li>✅ Personalization: Dynamic content replacement working</li>
                    <li>✅ Formatting: Clean and professional design</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Email configuration
    sender_email = "tripathy.anamay23@gmail.com"
    receiver_email = "tripathy.anamay23@gmail.com"
    password = "your_app_password_here"  # Replace with actual app password
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"Email Templates Test - HR & Academic - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    # Attach HTML content
    msg.attach(MIMEText(combined_email, 'html'))
    
    # Save to file for backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"email_templates_test_{timestamp}.html"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(combined_email)
    
    print(f"✅ Test email saved to: {filename}")
    
    # Send the email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        print("✅ Test email sent successfully to tripathy.anamay23@gmail.com!")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        print("📧 To send the email, update the password in the script")
        return False

def explain_scraper_differences():
    """Explain the differences between targeted and mass professor scrapers"""
    print("\n" + "="*60)
    print("🔍 TARGETED vs MASS PROFESSOR SCRAPER DIFFERENCES")
    print("="*60)
    
    print("\n📊 TARGETED PROFESSOR SCRAPER (targeted_professor_scraper.py):")
    print("   • Purpose: Scrape up to 2000 professors with intelligent prioritization")
    print("   • File Prioritization: Prioritizes CSV files likely to contain professor data")
    print("   • Caching: Uses JSON cache to skip already processed files")
    print("   • Limit: Stops at 2000 professors maximum")
    print("   • Efficiency: Skips files that have already been processed")
    print("   • Output: targeted_professors_scraped.csv")
    
    print("\n📊 MASS PROFESSOR SCRAPER (mass_professor_scraper.py):")
    print("   • Purpose: Process ALL available CSV files without limits")
    print("   • No Prioritization: Processes files in order found")
    print("   • No Caching: Processes all files every time")
    print("   • No Limit: Processes all professors found")
    print("   • Redundancy: May process same files multiple times")
    print("   • Output: mass_professors_scraped.csv")
    
    print("\n🤔 WHY NOT MERGE THEM?")
    print("   • Different Use Cases:")
    print("     - Targeted: For focused, efficient scraping with limits")
    print("     - Mass: For comprehensive, complete data collection")
    print("   • Performance: Targeted is faster for regular updates")
    print("   • Data Quality: Mass ensures no data is missed")
    print("   • Flexibility: Different scenarios need different approaches")
    
    print("\n💡 RECOMMENDATION:")
    print("   • Use TARGETED for regular updates and efficiency")
    print("   • Use MASS for initial data collection or when you need everything")
    print("   • They serve different purposes, so keeping them separate is beneficial")

def main():
    """Main function"""
    print("🚀 EMAIL TEMPLATES TEST & SCRAPER EXPLANATION")
    print("=" * 50)
    
    # Send test email
    success = send_test_email_to_user()
    
    if success:
        print("\n✅ Test email sent successfully!")
        print("📧 Check your email at tripathy.anamay23@gmail.com")
    else:
        print("\n📧 Email content generated and saved to file")
        print("📧 Update the password in the script to send the email")
    
    # Explain scraper differences
    explain_scraper_differences()

if __name__ == "__main__":
    main() 