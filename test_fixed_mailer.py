#!/usr/bin/env python3
"""
Quick test of the fixed professor mailer with 2 emails
"""

from FIXED_professor_mailer import FixedProfessorMailer

def quick_test():
    """Test the fixed system with 2 emails"""
    print("🧪 TESTING FIXED PROFESSOR MAILER")
    print("=" * 50)
    
    try:
        # Initialize the mailer
        mailer = FixedProfessorMailer()
        
        # Run campaign with 2 emails
        print("\n🚀 Running test campaign with 2 emails...")
        results = mailer.run_campaign(max_emails=2)
        
        if results['success']:
            print(f"\n✅ TEST SUCCESSFUL!")
            print(f"📧 Emails sent: {results['stats']['successful']}")
            print(f"🎯 Success rate: {results['success_rate']:.1f}%")
            print(f"⚡ Time taken: {results['total_time']:.1f}s")
            print(f"📁 Results in: {results['results_dir']}")
        else:
            print(f"\n❌ Test failed: {results.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ Test error: {e}")

if __name__ == "__main__":
    quick_test()
