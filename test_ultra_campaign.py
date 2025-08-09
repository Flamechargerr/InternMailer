#!/usr/bin/env python3
"""
Test Script for ULTRA HTML Bulk Campaign System
==============================================
This script sets up environment variables and runs a test campaign with 2 emails,
avoiding the ~681 professors we've already contacted.
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

# Set up test environment variables
def setup_test_environment():
    """Set up environment variables for testing."""
    
    # Essential email configuration - UPDATE THESE WITH YOUR CREDENTIALS
    os.environ['EMAIL_ADDRESS'] = 'YOUR_EMAIL@gmail.com'  # Replace with your email
    os.environ['EMAIL_PASSWORD'] = 'YOUR_APP_PASSWORD'    # Replace with your Gmail app password
    os.environ['SENDER_NAME'] = 'Anamay Tripathy'
    
    # Campaign configuration for testing
    os.environ['MAX_EMAILS_PER_SESSION'] = '2'  # Only send 2 emails for testing
    os.environ['CONCURRENT_WORKERS'] = '1'      # Use single worker for testing
    
    # Optional configuration
    os.environ['SMTP_SERVER'] = 'smtp.gmail.com'
    os.environ['SMTP_PORT'] = '587'
    os.environ['CV_PATH'] = 'Anamay_CV.pdf'  # Update this path if you have a CV
    os.environ['RESEARCH_KEYWORDS'] = 'machine learning,artificial intelligence,computer vision,deep learning,data science'
    
    print("✅ Environment variables configured for testing")
    print(f"📧 Email address: {os.environ['EMAIL_ADDRESS']}")
    print(f"📊 Max emails per session: {os.environ['MAX_EMAILS_PER_SESSION']}")
    print(f"🔧 Concurrent workers: {os.environ['CONCURRENT_WORKERS']}")

def load_existing_sent_emails():
    """Load the existing sent emails to show statistics."""
    sent_count = 0
    
    # Check email_log.csv
    email_log_path = Path("email_log.csv")
    if email_log_path.exists():
        try:
            df = pd.read_csv(email_log_path)
            sent_count = len(df) - 1  # Subtract header row
            print(f"📊 Found {sent_count} previously sent emails in email_log.csv")
        except Exception as e:
            print(f"⚠️  Could not read email_log.csv: {e}")
    
    return sent_count

def setup_database():
    """Setup the database file for the ULTRA system to use."""
    
    # Copy our data/list.csv to the main directory as professors_database.csv
    source_path = Path("data/list.csv")
    target_path = Path("professors_database.csv")
    
    if source_path.exists():
        try:
            df = pd.read_csv(source_path)
            
            # Clean and prepare the database
            print(f"📊 Loaded {len(df)} professors from data/list.csv")
            
            # Standardize column names for the ULTRA system
            df = df.rename(columns={
                'name': 'name',
                'email': 'email', 
                'university': 'university'
            })
            
            # Remove any that we've already contacted
            sent_emails = set()
            if Path("email_log.csv").exists():
                try:
                    log_df = pd.read_csv("email_log.csv")
                    sent_emails = set(log_df['email'].dropna().str.lower())
                    print(f"🔍 Found {len(sent_emails)} emails in sent log")
                except Exception as e:
                    print(f"⚠️  Could not read sent emails: {e}")
            
            # Filter out already sent emails
            df['email'] = df['email'].str.lower()
            original_count = len(df)
            df = df[~df['email'].isin(sent_emails)]
            remaining_count = len(df)
            
            print(f"📧 Filtered database: {original_count} → {remaining_count} professors (removed {original_count - remaining_count} already contacted)")
            
            if remaining_count == 0:
                print("❌ No new professors to contact! All have been contacted already.")
                return False
            
            # Save for ULTRA system to use
            df.to_csv(target_path, index=False)
            print(f"💾 Saved cleaned database to {target_path}")
            
            # Show first few for verification
            print("\n🎯 First few professors to be contacted:")
            print(df[['name', 'email', 'university']].head(5).to_string(index=False))
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up database: {e}")
            return False
    else:
        print(f"❌ Source database not found: {source_path}")
        return False

def main():
    """Main test execution."""
    print("🚀 ULTRA HTML Bulk Campaign - Test Mode")
    print("="*50)
    
    # Check credentials first
    email = input("📧 Enter your Gmail address: ").strip()
    password = input("🔑 Enter your Gmail App Password: ").strip()
    
    if not email or not password:
        print("❌ Email credentials required!")
        return
    
    # Update environment variables
    os.environ['EMAIL_ADDRESS'] = email
    os.environ['EMAIL_PASSWORD'] = password
    
    # Setup test environment
    setup_test_environment()
    
    # Load existing sent emails stats
    existing_sent = load_existing_sent_emails()
    
    # Setup database
    if not setup_database():
        print("❌ Database setup failed!")
        return
    
    print(f"\n🎯 TEST CONFIGURATION:")
    print(f"   • Previously sent emails: {existing_sent}")
    print(f"   • Test emails to send: 2")
    print(f"   • Total workers: 1")
    print(f"   • Database: professors_database.csv")
    
    # Ask for confirmation
    confirm = input(f"\n✅ Ready to send 2 test emails? (y/N): ").strip().lower()
    
    if confirm == 'y':
        print("🚀 Starting ULTRA campaign...")
        
        # Import and run the ULTRA system
        try:
            # Import the ULTRA system
            sys.path.append('.')
            from ULTRA_HTML_BULK_SYSTEM import UltraHTMLBulkCampaign
            
            # Create and run campaign
            campaign = UltraHTMLBulkCampaign()
            campaign.run_bulk_campaign()
            
            print("🎉 Test campaign completed!")
            
        except ImportError as e:
            print(f"❌ Could not import ULTRA system: {e}")
            print("💡 Make sure ULTRA_HTML_BULK_SYSTEM.py is in the current directory")
        except Exception as e:
            print(f"❌ Campaign failed: {e}")
    else:
        print("🛑 Test cancelled by user")

if __name__ == "__main__":
    main()
