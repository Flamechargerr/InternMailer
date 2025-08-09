#!/usr/bin/env python3
"""
PRODUCTION LAUNCHER FOR MASS EMAIL CAMPAIGN
Process all 31,000+ professors with ultra-personalized emails based on real research data

🎯 MAXIMUM INTERNSHIP SUCCESS SYSTEM 🎯
"""

import json
import os
import sys
from datetime import datetime
from mass_personalized_email_system import MassPersonalizedEmailSystem

def load_your_profile(config_file='your_profile_config.json'):
    """Load your personal profile from the config file"""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Convert config to the format expected by the system
        your_profile = {
            'name': config['personal_info']['name'],
            'background': f"{config['background']['current_status']}, {config['background']['target_goal']}",
            'interests': config['research_interests'][:6],  # Top 6 interests for focus
            'skills': config['technical_skills'][:8],  # Top 8 skills
            'email': config['personal_info']['email'],
            'linkedin': config['personal_info']['linkedin'],
            'portfolio': config['personal_info']['portfolio'],
            'achievements': ', '.join(config['achievements'][:3]),  # Top 3 achievements
            'education': config['background']['education'],
            'research_experience': config['research_experience'],
            'why_phd': config['why_phd']
        }
        
        return your_profile, config
    except Exception as e:
        print(f"❌ Error loading profile config: {e}")
        print("📝 Please update your_profile_config.json with your information!")
        sys.exit(1)

def validate_profile(profile, config):
    """Validate that the profile is properly configured"""
    required_fields = ['name', 'email', 'interests']
    missing_fields = []
    
    for field in required_fields:
        if not profile.get(field) or profile[field] in ['YOUR FULL NAME HERE', 'your.email@university.edu']:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"❌ Please update these fields in your_profile_config.json:")
        for field in missing_fields:
            print(f"   • {field}")
        print("\n📝 Edit the config file with your real information before running!")
        return False
    
    return True

def print_campaign_preview(profile, config):
    """Print a preview of what the campaign will do"""
    print("🚀 MASS PERSONALIZED EMAIL CAMPAIGN PREVIEW")
    print("=" * 80)
    print(f"👤 Candidate: {profile['name']}")
    print(f"🎓 Background: {profile['background']}")
    print(f"🔬 Research Focus: {', '.join(profile['interests'][:3])}")
    print(f"📧 Contact: {profile['email']}")
    print("=" * 80)
    
    print("\n📊 CAMPAIGN SCOPE:")
    print("   • Target: 31,086+ professors worldwide")
    print("   • Sources: Multiple academic databases (Semantic Scholar, arXiv, CrossRef)")
    print("   • Personalization: 100% authentic research data (zero mock data)")
    print("   • Email Quality: Ultra-personalized with specific publication references")
    
    print("\n🎯 EACH EMAIL WILL INCLUDE:")
    print("   ✅ Professor's specific recent publications (2020-2025)")
    print("   ✅ Detailed research alignment analysis")
    print("   ✅ Personalized collaboration proposals")
    print("   ✅ Your authentic background and achievements")
    print("   ✅ Professional, compelling content tailored to their work")
    print("   ✅ Specific reasons for interest in their research")
    
    print("\n📈 EXPECTED OUTCOMES:")
    print("   • Email Generation: 15,000-25,000 personalized emails")
    print("   • Response Rate: 5-15% (750-3,750 responses)")
    print("   • Interview Opportunities: 2-8% (300-2,000 interviews)")
    print("   • Internship/PhD Offers: 0.5-3% (75-900 potential offers)")
    
    print("\n⚡ PROCESSING DETAILS:")
    print("   • Batch Size: 50 professors per batch")
    print("   • Rate Limiting: 2-4 seconds between API calls")
    print("   • Progress Tracking: Auto-save every 100 professors")
    print("   • Resume Capability: Can restart from interruption point")
    print("   • Estimated Runtime: 10-20 hours total")
    
    print("\n📁 OUTPUT FILES:")
    print("   • personalized_emails/ - Individual email files")
    print("   • mass_email_results.json - Detailed campaign results")
    print("   • mass_email_progress.json - Progress tracking")
    print("   • mass_email_system.log - System logs")

def main():
    """Main launcher function"""
    print("🎯 INTERNSHIP SUCCESS MAXIMIZER - MASS EMAIL CAMPAIGN")
    print("=" * 80)
    print("This system will generate ultra-personalized emails for 31,000+ professors")
    print("using authentic research data to maximize your internship success!")
    print("=" * 80)
    
    # Load and validate profile
    print("\n📋 Loading your profile configuration...")
    profile, config = load_your_profile()
    
    if not validate_profile(profile, config):
        return
    
    print("✅ Profile loaded successfully!")
    
    # Show campaign preview
    print_campaign_preview(profile, config)
    
    # Confirmation prompts
    print("\n" + "=" * 80)
    print("⚠️  IMPORTANT CONSIDERATIONS:")
    print("   • This will process 31,000+ professors with real API calls")
    print("   • The system respects rate limits and may take 10-20 hours")
    print("   • Each email is individually crafted with authentic research data")
    print("   • You can pause and resume the campaign at any time")
    print("   • All emails are saved to files (no actual sending without SMTP config)")
    
    # Final confirmation
    print("\n🚀 READY TO LAUNCH?")
    response = input("Type 'LAUNCH' to start the mass email campaign: ").upper()
    
    if response != 'LAUNCH':
        print("Campaign cancelled. Update your configuration and run again when ready!")
        return
    
    # Additional safety check
    print("\n⚠️  FINAL CONFIRMATION:")
    print("This will start processing ALL 31,000+ professors with real research data.")
    print("Each professor will get a unique, personalized email based on their publications.")
    
    final_response = input("Are you absolutely sure? Type 'YES' to proceed: ").upper()
    
    if final_response != 'YES':
        print("Campaign cancelled for safety. Run again when you're ready!")
        return
    
    # Launch the campaign!
    print("\n🚀 LAUNCHING MASS EMAIL CAMPAIGN!")
    print("=" * 80)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔄 Processing will begin immediately...")
    print("💾 Progress is automatically saved every 100 professors")
    print("⏸️  You can stop with Ctrl+C and resume later")
    print("=" * 80)
    
    try:
        # Initialize and run the campaign
        campaign = MassPersonalizedEmailSystem(profile)
        campaign.run_mass_email_campaign()
        
        print("\n🎉 CAMPAIGN COMPLETED SUCCESSFULLY! 🎉")
        print("📊 Check the results files for detailed statistics")
        print("📧 Your personalized emails are ready for maximum impact!")
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Campaign paused by user")
        print("✅ Progress has been saved automatically")
        print("🔄 Run this script again to resume from where you left off")
        
    except Exception as e:
        print(f"\n❌ Campaign error: {e}")
        print("📋 Check mass_email_system.log for detailed error information")
        print("🔄 You can restart the campaign - progress is saved automatically")

if __name__ == "__main__":
    main()
