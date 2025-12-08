"""
InternMailer - Fully Autonomous Campaign Scheduler
Automatically sends new emails daily + handles all replies
TRUE JARVIS MODE - Zero human intervention
"""

import schedule
import time
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inbox_monitor import get_inbox_monitor
from auto_action_engine import get_auto_action_engine
from followup_scheduler import get_followup_scheduler

class JarvisMode:
    """
    Fully autonomous job hunting agent
    - Sends new emails daily
    - Monitors inbox hourly
    - Replies automatically
    - Archives rejections
    - Sends follow-ups
    NO HUMAN NEEDED!
    """
    
    def __init__(self):
        self.inbox_monitor = get_inbox_monitor()
        self.action_engine = get_auto_action_engine()
        self.followup_scheduler = get_followup_scheduler()
        self.log_file = 'campaign_results/jarvis_log.txt'
        self.daily_send_count = 50  # How many emails to send daily
    
    def log(self, message: str):
        """Log to file and console"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_msg + '\n')
    
    def send_daily_emails(self):
        """
        TASK: Send new emails daily automatically
        Uses existing system.py to send campaigns
        """
        try:
            self.log("="*60)
            self.log("📧 JARVIS: Starting daily email campaign...")
            
            # Import the verified email system
            from system import VerifiedEmailSystem
            
            # Create system instance
            email_system = VerifiedEmailSystem()
            
            # Send to professors (research opportunities)
            self.log(f"   Sending {self.daily_send_count} research emails...")
            
            # Run the campaign (sends to professors by default)
            import subprocess
            result = subprocess.run(
                ['python', 'system.py', '--count', str(self.daily_send_count), '--template', 'research'],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            if result.returncode == 0:
                self.log(f"✅ Daily campaign complete - {self.daily_send_count} emails sent")
            else:
                self.log(f"⚠️ Campaign finished with warnings")
                
        except Exception as e:
            self.log(f"❌ Error in daily email send: {e}")
    
    def check_inbox_and_reply(self):
        """
        TASK: Check inbox and auto-respond
        """
        try:
            self.log("="*60)
            self.log("📬 JARVIS: Checking inbox for replies...")
            
            results = self.inbox_monitor.check_inbox()
            
            if results:
                self.log(f"   Found {len(results)} new replies")
                
                # Auto-process actions
                self.log("🤖 JARVIS: Taking automated actions...")
                stats = self.action_engine.process_all_pending()
                
                self.log(f"✅ Actions complete:")
                for category, count in stats.items():
                    if count > 0:
                        self.log(f"   {category}: {count}")
            else:
                self.log("   No new replies")
                
        except Exception as e:
            self.log(f"❌ Error checking inbox: {e}")
    
    def send_followups(self):
        """
        TASK: Auto-send follow-ups
        """
        try:
            self.log("="*60)
            self.log("🔄 JARVIS: Checking for follow-ups...")
            
            self.followup_scheduler.run_followup_cycle()
            
        except Exception as e:
            self.log(f"❌ Error in follow-ups: {e}")
    
    def daily_report(self):
        """Daily summary"""
        try:
            self.log("="*60)
            self.log("📊 JARVIS: Daily Report")
            
            stats = self.inbox_monitor.get_stats()
            self.log(f"   Total replies processed: {stats['total_processed']}")
            self.log(f"   Priority contacts: {stats['priority_contacts']}")
            
        except Exception as e:
            self.log(f"❌ Error in report: {e}")
    
    def start_jarvis(self):
        """
        Start JARVIS - Fully autonomous mode
        """
        self.log("""
╔════════════════════════════════════════════════════╗
║                                                    ║
║              🤖 JARVIS MODE ACTIVATED              ║
║                                                    ║
║        Fully Autonomous Job Hunting Agent          ║
║              Zero Human Intervention               ║
║                                                    ║
╚════════════════════════════════════════════════════╝
        """)
        
        self.log("⚙️  JARVIS CONFIGURATION:")
        self.log(f"   Daily emails: {self.daily_send_count}")
        self.log(f"   Inbox checks: Every 1 hour")
        self.log(f"   Follow-ups: Every 6 hours")
        self.log(f"   Reports: Daily at 9 AM")
        self.log("="*60)
        
        # Schedule all tasks
        schedule.every().day.at("09:00").do(self.send_daily_emails)  # Daily emails at 9 AM
        schedule.every(1).hours.do(self.check_inbox_and_reply)       # Check inbox hourly
        schedule.every(6).hours.do(self.send_followups)              # Follow-ups every 6h
        schedule.every().day.at("18:00").do(self.daily_report)       # Report at 6 PM
        
        # Run initial tasks immediately
        self.log("🚀 JARVIS: Running initial checks...")
        self.check_inbox_and_reply()
        
        self.log("\n✅ JARVIS: Fully operational - running autonomously")
        self.log("   Press Ctrl+C to stop\n")
        
        # Main loop
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                self.log("\n⏹️  JARVIS: Shutdown requested by user")
                break
            except Exception as e:
                self.log(f"❌ JARVIS: Error in main loop: {e}")
                time.sleep(300)  # Wait 5 min before retry

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='JARVIS - Fully Autonomous Job Agent')
    parser.add_argument('--start', action='store_true', help='Start JARVIS mode')
    parser.add_argument('--daily-emails', type=int, default=50, help='Emails to send daily (default: 50)')
    
    args = parser.parse_args()
    
    jarvis = JarvisMode()
    
    if args.daily_emails:
        jarvis.daily_send_count = args.daily_emails
    
    if args.start:
        jarvis.start_jarvis()
    else:
        print("""
🤖 JARVIS - Fully Autonomous Job Hunting Agent

Usage:
  python jarvis_mode.py --start                Start JARVIS (50 emails/day)
  python jarvis_mode.py --start --daily-emails 100   Send 100/day

What JARVIS does automatically:
  ✅ Sends new emails daily (9 AM)
  ✅ Checks inbox every hour
  ✅ Replies to interested parties
  ✅ Archives rejections
  ✅ Sends follow-ups
  ✅ Daily reports (6 PM)

👉 Start with: python jarvis_mode.py --start
        """)
