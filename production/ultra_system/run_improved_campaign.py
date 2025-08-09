#!/usr/bin/env python3
"""
Command-line runner for the Ultra Improved Campaign System v2.0
"""

import argparse
import asyncio
import sys
import os
from ultra_improved_campaign import UltraImprovedCampaign
from ultra_parallel_campaign import CampaignConfig

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Ultra Improved Campaign System v2.0')
    
    parser.add_argument('--size', type=int, default=200,
                      help='Number of professors to contact (default: 200)')
    
    parser.add_argument('--start-from', type=int, default=0,
                      help='Start from this professor index (default: 0)')
    
    parser.add_argument('--delay-min', type=float, default=0.2,
                      help='Minimum delay between batches in seconds (default: 0.2)')
    
    parser.add_argument('--delay-max', type=float, default=0.8,
                      help='Maximum delay between batches in seconds (default: 0.8)')
    
    parser.add_argument('--parallel', type=int, default=20,
                      help='Number of parallel processors (default: 20)')
    
    parser.add_argument('--test', action='store_true',
                      help='Run in test mode (send all emails to test address)')
    
    parser.add_argument('--no-skip-contacted', action='store_true',
                      help='Do not skip previously contacted professors')
    
    parser.add_argument('--max-retries', type=int, default=3,
                      help='Maximum email send retries (default: 3)')
    
    return parser.parse_args()

async def main():
    """Main function"""
    
    print("🚀 ULTRA IMPROVED CAMPAIGN SYSTEM V2.0")
    print("=" * 60)
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Validate arguments
    if args.size <= 0:
        print("❌ Error: Sample size must be positive")
        sys.exit(1)
    
    if args.delay_min < 0 or args.delay_max < 0:
        print("❌ Error: Delay values must be non-negative")
        sys.exit(1)
    
    if args.delay_min > args.delay_max:
        print("❌ Error: Minimum delay cannot be greater than maximum delay")
        sys.exit(1)
    
    # Display configuration
    print(f"📊 Configuration:")
    print(f"   Sample Size: {args.size:,}")
    print(f"   Start From: {args.start_from:,}")
    print(f"   Delay Range: {args.delay_min:.1f}s - {args.delay_max:.1f}s")
    print(f"   Parallel Workers: {args.parallel}")
    print(f"   Test Mode: {'YES' if args.test else 'NO'}")
    print(f"   Skip Contacted: {'NO' if args.no_skip_contacted else 'YES'}")
    print(f"   Max Email Retries: {args.max_retries}")
    print("=" * 60)
    
    # Create campaign configuration
    config = CampaignConfig(
        max_parallel_professors=args.parallel,
        max_parallel_sources=8,
        success_rate_target=0.90,
        email_batch_size=5
    )
    
    # Create and configure campaign
    campaign = UltraImprovedCampaign(config)
    
    # Set max retries for email manager
    campaign.email_manager.max_retries = args.max_retries
    
    # Configure test mode
    if args.test:
        campaign.test_email = "tripathy.anamay23@gmail.com"
        print(f"🧪 Test mode enabled - all emails will be sent to: {campaign.test_email}")
    
    # Configure skip contacted
    if not args.no_skip_contacted:
        print("📋 Loading contacted professors tracker...")
        # This will be handled by the existing system
    
    print("\n🚀 Starting Ultra Improved Campaign...")
    print("=" * 60)
    
    try:
        # Run the improved campaign
        results = await campaign.run_improved_campaign(
            sample_size=args.size,
            start_from=args.start_from,
            delay_range=(args.delay_min, args.delay_max),
            test_mode=args.test
        )
        
        print("\n🎉 Campaign completed successfully!")
        print(f"📊 Total results: {len(results) if results else 0}")
        
        # Show detailed error analysis if there were failures
        if results:
            failed_results = [r for r in results if not r.email_sent]
            if failed_results:
                print(f"\n❌ Failed emails analysis:")
                error_types = {}
                for result in failed_results:
                    error_msg = result.error_message or "Unknown error"
                    error_types[error_msg] = error_types.get(error_msg, 0) + 1
                
                for error, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
                    print(f"   {error}: {count} occurrences")
        
    except KeyboardInterrupt:
        print("\n⏹️ Campaign interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Campaign failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
