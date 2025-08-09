#!/usr/bin/env python3
"""
SIMPLE ENHANCED CAMPAIGN RUNNER - COMMAND LINE INTERFACE
========================================================

Easy-to-use command line interface for running enhanced email campaigns.

Usage Examples:
    # Test mode - 5 professors
    python run_enhanced_campaign.py

    # Test mode - 20 professors
    python run_enhanced_campaign.py --size 20

    # Production mode - 50 professors
    python run_enhanced_campaign.py --production --size 50

    # Resume from specific position
    python run_enhanced_campaign.py --production --size 100 --start 250

    # Fast campaign (1 second delay)
    python run_enhanced_campaign.py --production --size 30 --delay 1
"""

import argparse
import sys
import os
from enhanced_bulk_campaign import EnhancedBulkCampaign

def main():
    print("🚀 Enhanced Bulk Email Campaign - Simple Runner")
    print("="*60)
    
    # Command line arguments
    parser = argparse.ArgumentParser(
        description='Enhanced Bulk Email Campaign with 80%+ Success Rate',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Test 5 professors (default)
    python run_enhanced_campaign.py
    
    # Test 20 professors
    python run_enhanced_campaign.py --size 20
    
    # Production - 50 professors
    python run_enhanced_campaign.py --production --size 50
    
    # Resume from position 100
    python run_enhanced_campaign.py --production --start 100 --size 50
        """
    )
    
    parser.add_argument(
        '--production', 
        action='store_true', 
        help='Send emails to real professors (default: test mode)'
    )
    
    parser.add_argument(
        '--size', 
        type=int, 
        default=5, 
        help='Number of professors to process (default: 5)'
    )
    
    parser.add_argument(
        '--delay', 
        type=int, 
        default=2, 
        help='Delay between emails in seconds (default: 2)'
    )
    
    parser.add_argument(
        '--start', 
        type=int, 
        default=0, 
        help='Starting position in database (default: 0)'
    )
    
    parser.add_argument(
        '--email', 
        type=str, 
        default='tripathy.anamay23@gmail.com',
        help='Test email address (for test mode)'
    )
    
    parser.add_argument(
        '--database', 
        type=str, 
        default='FINAL_MASTER_EMAIL_DATABASE.csv',
        help='Professor database file'
    )
    
    args = parser.parse_args()
    
    # Display configuration
    mode = "PRODUCTION" if args.production else "TEST"
    print(f"🎯 Mode: {mode}")
    print(f"📊 Professors: {args.size}")
    print(f"⏰ Delay: {args.delay}s")
    print(f"🔢 Start from: {args.start}")
    print(f"📧 Database: {args.database}")
    
    if not args.production:
        print(f"✉️ Test email: {args.email}")
    
    print("="*60)
    
    # Confirmation for production
    if args.production:
        print("⚠️  PRODUCTION MODE - Emails will be sent to REAL professors!")
        confirm = input("Continue? (y/N): ").lower()
        if confirm not in ['y', 'yes']:
            print("❌ Cancelled.")
            return
    
    # Check if database exists
    if not os.path.exists(args.database):
        print(f"❌ Database file not found: {args.database}")
        print("Available CSV files:")
        for file in os.listdir('.'):
            if file.endswith('.csv'):
                print(f"   - {file}")
        return
    
    try:
        # Initialize campaign
        test_email = None if args.production else args.email
        campaign = EnhancedBulkCampaign(
            database_file=args.database,
            test_email=test_email
        )
        
        # Run campaign
        print("\n🚀 Starting enhanced campaign...")
        campaign.run_enhanced_campaign(
            sample_size=args.size,
            delay_seconds=args.delay,
            start_from=args.start,
            test_mode=not args.production
        )
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Campaign stopped by user.")
        print("Progress has been saved. You can resume with --start parameter.")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please check your configuration and try again.")

if __name__ == "__main__":
    main()
