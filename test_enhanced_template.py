#!/usr/bin/env python3
"""
Test the enhanced email template with improved professional formatting.
This demonstrates the new refined template that will be used for all professor outreach.
"""

import os
import sys
from dotenv import load_dotenv

# Add src directory to path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gmail_sender import GmailSender
from email_generator import EmailGenerator

def test_enhanced_template():
    """Test the enhanced email template with a sample professor."""
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    
    if not gmail_user or not gmail_password:
        print("Error: Gmail credentials not found in .env file")
        return False
    
    # Sample student info (this would normally come from resume parser)
    student_info = {
        'name': 'Anamay Tripathy',
        'email': 'tripathy.anamay23@gmail.com',
        'university': 'MIT Manipal',
        'cgpa': '7.6',
        'skills': ['Python', 'TensorFlow', 'PyTorch', 'JavaScript', 'React', 'Node.js', 'AWS', 'Docker'],
        'projects': ['CrimeConnect', 'VARtificial Intelligence', 'HackOps', 'Flora Fight Frenzy'],
        'experience': ['Technical Head at YaanBarpe', 'Data Analyst Intern at Intellect Design Arena']
    }
    
    # Sample professor data
    sample_professor = {
        'Name': 'Dr. Barbara Liskov',
        'Research Area': 'Distributed systems (AI)',
        'University': 'MIT',
        'email': 'liskov@mit.edu'
    }
    
    # Initialize email generator and sender
    email_gen = EmailGenerator(student_info)
    sender = GmailSender(gmail_user, gmail_password)
    
    # Generate subject and body using enhanced template
    subject = email_gen.generate_subject(sample_professor)
    body = email_gen.generate_body(sample_professor)
    
    # Test email details
    to_email = "tripathy.anamay23@gmail.com"
    
    print("🎨 Testing Enhanced Email Template")
    print("=" * 60)
    print(f"📧 To: {to_email}")
    print(f"📝 Subject: {subject}")
    print("🎯 Using: Enhanced HTML template with professional styling")
    print("⏳ Sending enhanced template email...")
    
    # Send the enhanced template email
    success = sender.send_email(to_email, subject, body, is_html=True)
    
    if success:
        print("✅ SUCCESS: Enhanced template email sent!")
        print("\n🎨 The enhanced template includes:")
        print("   • Modern gradient header design")
        print("   • Color-coded section headers with emojis")
        print("   • Professional card-style layout with shadows")
        print("   • Improved typography and spacing")
        print("   • Enhanced contact information section")
        print("   • Mobile-responsive design")
        print("   • Professional color scheme throughout")
        print("   • Better visual hierarchy and readability")
        print("\n📨 Check your inbox to see the stunning new design!")
        print("💡 This template will now be used for ALL professor outreach emails!")
    else:
        print("❌ FAILED: Could not send enhanced template email.")
        print("🔧 Please check your email configuration.")
    
    return success

if __name__ == "__main__":
    print("🚀 Enhanced Email Template Test")
    print("=" * 60)
    print("Testing the new refined template with professional styling")
    print("=" * 60)
    test_enhanced_template()
