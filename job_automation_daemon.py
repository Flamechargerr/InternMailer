"""
InternMailer - Job Automation Daemon
Runs continuously in the background checking inbox and taking actions
"""

import time
import schedule
from datetime import datetime
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from inbox_monitor import get_inbox_monitor
from auto_action_engine import get_auto_action_engine
from followup_scheduler import get_followup_scheduler

class JobAutomationDaemon:
    """
    Background daemon that runs automation tasks on a schedule:
    - Check inbox every hour
    - Process actions immediately after inbox check
    - Send follow-ups every 6 hours
    """
    
    def __init__(self):
        self.inbox_monitor = get_inbox_monitor()
        self.action_engine = get_auto_action_engine()
        self.followup_scheduler = get_followup_scheduler()
        self.is_running = False
        self.log_file = 'campaign_results/automation_log.txt'
    
    def log(self, message: str):
        """Log message to file and console"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        
        print(log_message)
        
        # Append to log file
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def check_inbox_task(self):
        """Scheduled task: Check inbox for new replies"""
        try:
            self.log("="*50)
            self.log("🔄 Running inbox check...")
            
            results = self.inbox_monitor.check_inbox()
            
            if results:
                self.log(f"✅ Processed {len(results)} new replies")
                
                # Immediately process actions
                self.log("🤖 Processing automated actions...")
                stats = self.action_engine.process_all_pending()
                
                self.log(f"✅ Actions complete:")
                self.log(f"   Interested: {stats['interested']}")
                self.log(f"   Not interested: {stats['not_interested']}")
                self.log(f"   Questions: {stats['question']}")
                self.log(f"   Out of office: {stats['out_of_office']}")
            else:
                self.log("📭 No new replies found")
                
        except Exception as e:
            self.log(f"❌ Error in inbox check: {e}")
    
    def followup_task(self):
        """Scheduled task: Send follow-up emails"""
        try:
            self.log("="*50)
            self.log("📤 Running follow-up check...")
            
            self.followup_scheduler.run_followup_cycle()
            
        except Exception as e:
            self.log(f"❌ Error in follow-up task: {e}")
    
    def status_report_task(self):
        """Daily status report"""
        try:
            self.log("="*50)
            self.log("📊 DAILY STATUS REPORT")
            
            stats = self.inbox_monitor.get_stats()
            self.log(f"   Total replies processed: {stats['total_processed']}")
            self.log(f"   Priority contacts: {stats['priority_contacts']}")
            self.log(f"   By category: {stats['by_category']}")
            
        except Exception as e:
            self.log(f"❌ Error in status report: {e}")
    
    def start(self):
        """Start the automation daemon"""
        self.log("🚀 Starting Job Automation Daemon...")
        self.log("   Inbox check: Every 60 minutes")
        self.log("   Follow-ups: Every 6 hours")
        self.log("   Status report: Daily at 9 AM")
        self.log("="*50)
        
        # Schedule tasks
        schedule.every(60).minutes.do(self.check_inbox_task)
        schedule.every(6).hours.do(self.followup_task)
        schedule.every().day.at("09:00").do(self.status_report_task)
        
        # Run inbox check immediately on start
        self.log("🔄 Running initial inbox check...")
        self.check_inbox_task()
        
        self.is_running = True
        
        # Main loop
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute for due tasks
            except KeyboardInterrupt:
                self.log("\n⏸️  Daemon stopped by user")
                self.is_running = False
                break
            except Exception as e:
                self.log(f"❌ Error in main loop: {e}")
                time.sleep(300)  # Wait 5 minutes before retry
    
    def stop(self):
        """Stop the daemon"""
        self.log("⏹️  Stopping automation daemon...")
        self.is_running = False

# CLI
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='InternMailer Automation Daemon')
    parser.add_argument('--start', action='store_true', help='Start the daemon')
    parser.add_argument('--test', action='store_true', help='Run test cycle (dry run)')
    parser.add_argument('--status', action='store_true', help='Show current status')
    
    args = parser.parse_args()
    
    daemon = JobAutomationDaemon()
    
    if args.test:
        print("🧪 TEST MODE - Running one cycle (dry run)")
        print("\n1. Checking inbox...")
        monitor = get_inbox_monitor()
        results = monitor.check_inbox(dry_run=True)
        
        print(f"\n2. Would process {len(results)} replies")
        
        print("\n3. Checking follow-ups...")
        scheduler = get_followup_scheduler()
        scheduler.run_followup_cycle(dry_run=True)
        
        print("\n✅ Test complete!")
        
    elif args.status:
        print("📊 Automation Status")
        stats = daemon.inbox_monitor.get_stats()
        print(f"   Total processed: {stats['total_processed']}")
        print(f"   Priority contacts: {stats['priority_contacts']}")
        print(f"   By category: {stats['by_category']}")
        
    elif args.start:
        print("""
╔═══════════════════════════════════════════╗
║   InternMailer Automation Daemon          ║
║   Full hands-off job application agent    ║
╚═══════════════════════════════════════════╝
        """)
        daemon.start()
    
    else:
        parser.print_help()
        print("\nQuick start:")
        print("  python job_automation_daemon.py --test    # Test run")
        print("  python job_automation_daemon.py --start   # Start automation")
        print("  python job_automation_daemon.py --status  # Check status")
