#!/usr/bin/env python3
"""
🤖 AUTOMATION DAEMON - Full Gmail Automation for Job Applications
==================================================================
Background daemon that orchestrates the complete automation workflow:
1. Sends personalized job application emails
2. Monitors inbox for replies
3. Classifies and auto-responds to replies
4. Schedules and sends follow-ups

Usage:
    python daemon.py --start      # Start the daemon
    python daemon.py --test       # Run one test cycle
    python daemon.py --status     # Show current status
    python daemon.py --send 10    # Send 10 emails now
"""

import os
import sys
import time
import sqlite3
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import components
try:
    from core.email_system import get_email_system
    EMAIL_SYSTEM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Email system not available: {e}")
    EMAIL_SYSTEM_AVAILABLE = False

try:
    from core.inbox_monitor import get_inbox_monitor
    INBOX_MONITOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Inbox monitor not available: {e}")
    INBOX_MONITOR_AVAILABLE = False

try:
    from core.auto_action_engine import get_auto_action_engine
    ACTION_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Action engine not available: {e}")
    ACTION_ENGINE_AVAILABLE = False

try:
    from core.followup_scheduler import get_followup_scheduler
    FOLLOWUP_SCHEDULER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Followup scheduler not available: {e}")
    FOLLOWUP_SCHEDULER_AVAILABLE = False


class AutomationDaemon:
    """
    Main automation daemon that coordinates all components.
    """
    
    def __init__(self):
        self.email_system = None
        self.inbox_monitor = None
        self.action_engine = None
        self.followup_scheduler = None
        
        self.is_running = False
        self.log_file = 'campaign_results/automation_log.txt'
        self.status_db = 'campaign_results/daemon_status.db'
        
        # Initialize components
        self._init_components()
        self._init_status_db()
        
        print("🤖 Automation Daemon initialized")
    
    def _init_components(self):
        """Initialize all automation components"""
        if EMAIL_SYSTEM_AVAILABLE:
            try:
                self.email_system = get_email_system()
                print("   ✅ Email system ready")
            except Exception as e:
                print(f"   ❌ Email system failed: {e}")
        
        if INBOX_MONITOR_AVAILABLE:
            try:
                self.inbox_monitor = get_inbox_monitor()
                print("   ✅ Inbox monitor ready")
            except Exception as e:
                print(f"   ❌ Inbox monitor failed: {e}")
        
        if ACTION_ENGINE_AVAILABLE:
            try:
                self.action_engine = get_auto_action_engine()
                print("   ✅ Action engine ready")
            except Exception as e:
                print(f"   ❌ Action engine failed: {e}")
        
        if FOLLOWUP_SCHEDULER_AVAILABLE:
            try:
                self.followup_scheduler = get_followup_scheduler()
                print("   ✅ Followup scheduler ready")
            except Exception as e:
                print(f"   ❌ Followup scheduler failed: {e}")
    
    def _init_status_db(self):
        """Initialize status tracking database"""
        os.makedirs('campaign_results', exist_ok=True)
        
        with sqlite3.connect(self.status_db) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS daemon_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT,
                    message TEXT,
                    details TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT PRIMARY KEY,
                    emails_sent INTEGER DEFAULT 0,
                    replies_received INTEGER DEFAULT 0,
                    followups_sent INTEGER DEFAULT 0,
                    actions_taken INTEGER DEFAULT 0
                )
            ''')
            conn.commit()
    
    def log(self, message: str, event_type: str = 'info', details: str = ''):
        """Log message to file and database"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        
        print(log_message)
        
        # Write to log file
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')
        except Exception as e:
            print(f"⚠️ Failed to write to log file: {e}")
        
        # Write to database
        try:
            with sqlite3.connect(self.status_db) as conn:
                conn.execute('''
                    INSERT INTO daemon_log (event_type, message, details)
                    VALUES (?, ?, ?)
                ''', (event_type, message, details))
                conn.commit()
        except Exception as e:
            print(f"⚠️ Failed to write to status db: {e}")
    
    def update_daily_stats(self, **kwargs):
        """Update daily statistics"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        try:
            with sqlite3.connect(self.status_db) as conn:
                # Ensure row exists
                conn.execute('''
                    INSERT OR IGNORE INTO daily_stats (date)
                    VALUES (?)
                ''', (today,))
                
                # Update fields
                for key, value in kwargs.items():
                    if key in ['emails_sent', 'replies_received', 'followups_sent', 'actions_taken']:
                        query = f"UPDATE daily_stats SET {key} = {key} + ? WHERE date = ?"
                        conn.execute(query, (value, today))
                
                conn.commit()
        except Exception as e:
            print(f"⚠️ Failed to update daily stats: {e}")
    
    def send_emails_task(self, count: int = 10):
        """Task: Send job application emails"""
        if not self.email_system:
            self.log("❌ Email system not available", 'error')
            return
        
        self.log("="*50, 'task_start')
        self.log(f"📤 Sending {count} emails...", 'send_start')
        
        try:
            # Check daily limit
            can_send, remaining = self.email_system.can_send_today()
            if not can_send:
                self.log("⚠️ Daily email limit reached", 'limit_reached')
                return
            
            actual_count = min(count, remaining)
            
            # Send emails
            stats = self.email_system.send_campaign(
                count=actual_count,
                use_ai=True,
                dry_run=False
            )
            
            self.update_daily_stats(emails_sent=stats.get('sent', 0))
            
            self.log(f"✅ Sent {stats.get('sent', 0)} emails", 'send_complete', 
                    f"Failed: {stats.get('failed', 0)}, Skipped: {stats.get('skipped', 0)}")
            
        except Exception as e:
            self.log(f"❌ Error sending emails: {e}", 'error', str(e))
    
    def check_inbox_task(self):
        """Task: Check inbox for replies"""
        if not self.inbox_monitor:
            self.log("❌ Inbox monitor not available", 'error')
            return
        
        self.log("="*50, 'task_start')
        self.log("📥 Checking inbox...", 'inbox_check')
        
        try:
            results = self.inbox_monitor.check_inbox()
            
            if results:
                self.log(f"✅ Processed {len(results)} new replies", 'inbox_complete')
                self.update_daily_stats(replies_received=len(results))
                
                # Process actions immediately
                if self.action_engine:
                    self.log("🤖 Processing automated actions...", 'action_start')
                    stats = self.action_engine.process_all_pending()
                    
                    total_actions = sum(stats.values())
                    self.update_daily_stats(actions_taken=total_actions)
                    
                    self.log(f"✅ Actions complete", 'action_complete',
                            f"Interested: {stats.get('interested', 0)}, "
                            f"Not interested: {stats.get('not_interested', 0)}, "
                            f"Questions: {stats.get('question', 0)}, "
                            f"OOO: {stats.get('out_of_office', 0)}")
            else:
                self.log("📭 No new replies", 'inbox_empty')
                
        except Exception as e:
            self.log(f"❌ Error checking inbox: {e}", 'error', str(e))
    
    def followup_task(self):
        """Task: Send follow-up emails"""
        if not self.followup_scheduler:
            self.log("❌ Followup scheduler not available", 'error')
            return
        
        self.log("="*50, 'task_start')
        self.log("📤 Running follow-up check...", 'followup_start')
        
        try:
            self.followup_scheduler.run_followup_cycle()
            self.log("✅ Follow-up check complete", 'followup_complete')
            
        except Exception as e:
            self.log(f"❌ Error in follow-up task: {e}", 'error', str(e))
    
    def daily_report_task(self):
        """Task: Generate daily status report"""
        self.log("="*50, 'task_start')
        self.log("📊 DAILY STATUS REPORT", 'daily_report')
        
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            with sqlite3.connect(self.status_db) as conn:
                cursor = conn.execute('''
                    SELECT emails_sent, replies_received, followups_sent, actions_taken
                    FROM daily_stats WHERE date = ?
                ''', (today,))
                
                row = cursor.fetchone()
                if row:
                    self.log(f"   Emails sent: {row[0]}", 'stats')
                    self.log(f"   Replies received: {row[1]}", 'stats')
                    self.log(f"   Followups sent: {row[2]}", 'stats')
                    self.log(f"   Actions taken: {row[3]}", 'stats')
                else:
                    self.log("   No activity today", 'stats')
                    
        except Exception as e:
            self.log(f"❌ Error generating report: {e}", 'error', str(e))
    
    def run_single_cycle(self, send_count: int = 0):
        """Run a single automation cycle"""
        self.log("\n" + "="*60, 'cycle_start')
        self.log("🔄 AUTOMATION CYCLE START", 'cycle_start')
        self.log("="*60, 'cycle_start')
        
        # Send emails if requested
        if send_count > 0:
            self.send_emails_task(send_count)
        
        # Check inbox
        self.check_inbox_task()
        
        # Run follow-ups
        self.followup_task()
        
        self.log("="*60, 'cycle_complete')
        self.log("✅ CYCLE COMPLETE\n", 'cycle_complete')
    
    def start(self, send_count: int = 0, interval_minutes: int = 60):
        """
        Start the automation daemon.
        
        Args:
            send_count: Number of emails to send per cycle (0 to skip)
            interval_minutes: Minutes between cycles
        """
        self.log("="*60, 'daemon_start')
        self.log("🚀 STARTING AUTOMATION DAEMON", 'daemon_start')
        self.log("="*60, 'daemon_start')
        self.log(f"   Email sending: {'✅' if self.email_system else '❌'}")
        self.log(f"   Inbox monitoring: {'✅' if self.inbox_monitor else '❌'}")
        self.log(f"   Auto-actions: {'✅' if self.action_engine else '❌'}")
        self.log(f"   Follow-ups: {'✅' if self.followup_scheduler else '❌'}")
        self.log(f"   Cycle interval: {interval_minutes} minutes")
        if send_count > 0:
            self.log(f"   Emails per cycle: {send_count}")
        self.log("="*60, 'daemon_start')
        
        self.is_running = True
        
        # Run initial cycle immediately
        self.run_single_cycle(send_count)
        
        # Schedule daily report for 9 AM
        last_report_date = datetime.now().date()
        
        # Main loop
        self.log("\n⏳ Running... Press Ctrl+C to stop\n", 'daemon_running')
        
        while self.is_running:
            try:
                # Sleep for interval
                for _ in range(interval_minutes * 60):
                    if not self.is_running:
                        break
                    time.sleep(1)
                
                if not self.is_running:
                    break
                
                # Run cycle
                self.run_single_cycle(send_count)
                
                # Check if it's time for daily report
                now = datetime.now()
                if now.date() != last_report_date and now.hour >= 9:
                    self.daily_report_task()
                    last_report_date = now.date()
                    
            except KeyboardInterrupt:
                self.log("\n⏸️ Daemon stopped by user", 'daemon_stop')
                self.is_running = False
                break
            except Exception as e:
                self.log(f"❌ Error in main loop: {e}", 'error', str(e))
                time.sleep(300)  # Wait 5 minutes before retry
        
        self.log("⏹️ Daemon stopped", 'daemon_stop')
    
    def stop(self):
        """Stop the daemon"""
        self.is_running = False
        self.log("⏹️ Stopping daemon...", 'daemon_stop')
    
    def get_status(self) -> dict:
        """Get current daemon status"""
        status = {
            'running': self.is_running,
            'components': {
                'email_system': bool(self.email_system),
                'inbox_monitor': bool(self.inbox_monitor),
                'action_engine': bool(self.action_engine),
                'followup_scheduler': bool(self.followup_scheduler)
            },
            'log_file': self.log_file,
            'recent_logs': []
        }
        
        # Get recent logs
        try:
            with sqlite3.connect(self.status_db) as conn:
                cursor = conn.execute('''
                    SELECT timestamp, event_type, message
                    FROM daemon_log
                    ORDER BY timestamp DESC
                    LIMIT 10
                ''')
                
                for row in cursor.fetchall():
                    status['recent_logs'].append({
                        'timestamp': row[0],
                        'event_type': row[1],
                        'message': row[2]
                    })
        except Exception as e:
            status['error'] = str(e)
        
        return status


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='InternMailer - Full Automation Daemon',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python daemon.py --start                    # Start daemon (monitoring only)
    python daemon.py --start --send 10          # Send 10 emails per cycle
    python daemon.py --start --send 5 --interval 30   # Send 5 every 30 min
    python daemon.py --test                     # Run one test cycle
    python daemon.py --status                   # Show current status
    python daemon.py --send-once 20             # Send 20 emails once
        """
    )
    
    parser.add_argument('--start', action='store_true',
                       help='Start the daemon')
    parser.add_argument('--send', type=int, default=0, metavar='N',
                       help='Send N emails per cycle (default: 0)')
    parser.add_argument('--interval', type=int, default=60, metavar='MIN',
                       help='Minutes between cycles (default: 60)')
    parser.add_argument('--test', action='store_true',
                       help='Run one test cycle and exit')
    parser.add_argument('--status', action='store_true',
                       help='Show current status')
    parser.add_argument('--send-once', type=int, metavar='N',
                       help='Send N emails once and exit')
    
    args = parser.parse_args()
    
    daemon = AutomationDaemon()
    
    if args.status:
        print("\n📊 DAEMON STATUS")
        print("="*50)
        status = daemon.get_status()
        print(f"Running: {'✅' if status['running'] else '⏹️'}")
        print(f"\nComponents:")
        for name, available in status['components'].items():
            print(f"   {name}: {'✅' if available else '❌'}")
        print(f"\nRecent activity:")
        for log in status['recent_logs'][:5]:
            print(f"   [{log['timestamp']}] {log['message']}")
        print("="*50 + "\n")
    
    elif args.test:
        print("\n🧪 TEST MODE - Running one cycle\n")
        daemon.run_single_cycle(send_count=args.send)
    
    elif args.send_once:
        print(f"\n📤 Sending {args.send_once} emails...\n")
        if daemon.email_system:
            daemon.email_system.send_campaign(count=args.send_once, use_ai=True)
        else:
            print("❌ Email system not available")
    
    elif args.start:
        daemon.start(send_count=args.send, interval_minutes=args.interval)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
