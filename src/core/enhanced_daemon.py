"""
🤖 Enhanced Automation Daemon with Health Monitoring
====================================================
Advanced daemon with:
- Health monitoring and alerts
- Configurable task scheduling
- Daily/weekly reports
- Systemd/launchd integration support
- Graceful shutdown handling
"""

from __future__ import annotations

import json
import os
import signal
import sys
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import config
from core.agents.base_agent import AgentContext

try:
    from core.agents.orchestrator import get_orchestrator
except Exception:  # pragma: no cover - orchestrator is optional in consolidated app
    def get_orchestrator():
        return None


@dataclass
class HealthStatus:
    """Health check status data."""
    timestamp: str
    status: str  # healthy, warning, critical
    uptime_seconds: int
    last_cycle_success: bool
    consecutive_failures: int
    component_status: Dict[str, bool]
    last_error: Optional[str] = None


@dataclass
class TaskSchedule:
    """Task scheduling configuration."""
    name: str
    interval_minutes: int
    last_run: Optional[datetime]
    enabled: bool
    priority: int  # Higher = runs first
    max_retries: int


class HealthMonitor:
    """Monitors daemon health and sends alerts."""
    
    def __init__(self, db_path: Optional[str] = None):
        # Use env var if provided, otherwise default to TCC-safe path
        self.db_path = db_path or os.environ.get('HEALTH_DB_PATH', '/tmp/internmailer_db/health.db')
        self._init_db()
        self.consecutive_failures = 0
        self.last_error = None
    
    def _init_db(self):
        """Initialize health monitoring database."""
        try:
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
        except (PermissionError, OSError):
            pass
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS health_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT,
                    uptime_seconds INTEGER,
                    component_status TEXT,
                    last_error TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    alert_type TEXT,
                    severity TEXT,
                    message TEXT,
                    acknowledged BOOLEAN DEFAULT 0
                )
            """)
            
            conn.commit()
    
    def check_health(self, components: Dict[str, bool], uptime_seconds: int) -> HealthStatus:
        """Perform health check and return status."""
        failed_components = [name for name, status in components.items() if not status]
        
        if len(failed_components) == 0:
            status = "healthy"
            self.consecutive_failures = 0
        elif len(failed_components) <= 2:
            status = "warning"
            self.consecutive_failures += 1
        else:
            status = "critical"
            self.consecutive_failures += 1
        
        # Create alert if needed
        if status == "critical" or (status == "warning" and self.consecutive_failures >= 3):
            self._create_alert(
                alert_type="health_check",
                severity=status,
                message=f"Health status: {status}. Failed components: {', '.join(failed_components)}",
            )
        
        health = HealthStatus(
            timestamp=datetime.now().isoformat(),
            status=status,
            uptime_seconds=uptime_seconds,
            last_cycle_success=self.consecutive_failures == 0,
            consecutive_failures=self.consecutive_failures,
            component_status=components,
            last_error=self.last_error,
        )
        
        # Store in database
        self._store_health_check(health)
        
        return health
    
    def _store_health_check(self, health: HealthStatus):
        """Store health check in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT INTO health_checks 
                       (status, uptime_seconds, component_status, last_error)
                       VALUES (?, ?, ?, ?)""",
                    (
                        health.status,
                        health.uptime_seconds,
                        json.dumps(health.component_status),
                        health.last_error,
                    )
                )
                conn.commit()
        except Exception as e:
            print(f"⚠️ Failed to store health check: {e}")
    
    def _create_alert(self, alert_type: str, severity: str, message: str):
        """Create an alert."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT INTO alerts (alert_type, severity, message)
                       VALUES (?, ?, ?)""",
                    (alert_type, severity, message)
                )
                conn.commit()
                print(f"🚨 ALERT [{severity.upper()}]: {message}")
        except Exception as e:
            print(f"⚠️ Failed to create alert: {e}")
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """Get recent alerts."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """SELECT * FROM alerts 
                       ORDER BY timestamp DESC
                       LIMIT ?""",
                    (limit,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []


class ReportGenerator:
    """Generates daily and weekly reports."""
    
    def __init__(self, db_path: str = "/tmp/internmailer_db/daemon_status.db"):
        self.db_path = db_path
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """Generate daily activity report."""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM daily_stats WHERE date = ?",
                    (today,)
                )
                today_stats = cursor.fetchone()
                
                cursor = conn.execute(
                    "SELECT * FROM daily_stats WHERE date = ?",
                    (yesterday,)
                )
                yesterday_stats = cursor.fetchone()
                
                report = {
                    "date": today,
                    "today": {
                        "emails_sent": today_stats[1] if today_stats else 0,
                        "replies_received": today_stats[2] if today_stats else 0,
                        "followups_sent": today_stats[3] if today_stats else 0,
                        "actions_taken": today_stats[4] if today_stats else 0,
                    },
                    "yesterday": {
                        "emails_sent": yesterday_stats[1] if yesterday_stats else 0,
                        "replies_received": yesterday_stats[2] if yesterday_stats else 0,
                        "followups_sent": yesterday_stats[3] if yesterday_stats else 0,
                        "actions_taken": yesterday_stats[4] if yesterday_stats else 0,
                    },
                }
                
                return report
        except Exception as e:
            return {"error": str(e), "date": today}
    
    def generate_weekly_report(self) -> Dict[str, Any]:
        """Generate weekly summary report."""
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """SELECT 
                        SUM(emails_sent) as total_sent,
                        SUM(replies_received) as total_replies,
                        SUM(followups_sent) as total_followups,
                        SUM(actions_taken) as total_actions
                       FROM daily_stats
                       WHERE date >= ?""",
                    (week_ago,)
                )
                row = cursor.fetchone()
                
                return {
                    "week_start": week_ago,
                    "week_end": datetime.now().strftime("%Y-%m-%d"),
                    "totals": {
                        "emails_sent": row[0] or 0,
                        "replies_received": row[1] or 0,
                        "followups_sent": row[2] or 0,
                        "actions_taken": row[3] or 0,
                    },
                }
        except Exception as e:
            return {"error": str(e)}
    
    def send_report_email(self, report: Dict[str, Any], report_type: str = "daily"):
        """Send report via email."""
        subject = f"InternMailer {report_type.capitalize()} Report - {report.get('date', datetime.now().strftime('%Y-%m-%d'))}"
        
        if report_type == "daily":
            body = f"""
📊 InternMailer Daily Report
============================

Date: {report.get('date')}

Today's Activity:
- Emails Sent: {report['today']['emails_sent']}
- Replies Received: {report['today']['replies_received']}
- Follow-ups Sent: {report['today']['followups_sent']}
- Actions Taken: {report['today']['actions_taken']}

Yesterday's Activity:
- Emails Sent: {report['yesterday']['emails_sent']}
- Replies Received: {report['yesterday']['replies_received']}
- Follow-ups Sent: {report['yesterday']['followups_sent']}
- Actions Taken: {report['yesterday']['actions_taken']}

---
Generated by InternMailer Automation Daemon
"""
        else:  # weekly
            body = f"""
📈 InternMailer Weekly Report
=============================

Week: {report.get('week_start')} to {report.get('week_end')}

Total Activity:
- Emails Sent: {report['totals']['emails_sent']}
- Replies Received: {report['totals']['replies_received']}
- Follow-ups Sent: {report['totals']['followups_sent']}
- Actions Taken: {report['totals']['actions_taken']}

---
Generated by InternMailer Automation Daemon
"""
        
        # Would integrate with email system here
        print(f"📧 Report email prepared: {subject}")
        return {"subject": subject, "body": body}


class EnhancedAutomationDaemon:
    """
    Enhanced automation daemon with health monitoring and reporting.
    """
    
    def __init__(self):
        self.is_running = False
        self.start_time = None
        self.shutdown_event = threading.Event()
        
        # Components
        self.orchestrator = None
        self.health_monitor = HealthMonitor()
        self.report_generator = ReportGenerator()
        
        # Task schedules
        self.task_schedules: Dict[str, TaskSchedule] = {}
        self._init_task_schedules()
        
        # Statistics
        self.cycle_count = 0
        self.last_cycle_time = None
        
        # Signal handlers (only work in main thread)
        try:
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
        except ValueError:
            # This happens when running in a thread (e.g. from web_dashboard)
            print("⚠️ Signal handlers could not be set (not in main thread)")
        
        print("🤖 Enhanced Automation Daemon initialized")
    
    def _init_task_schedules(self):
        """Initialize task schedules from config."""
        self.task_schedules = {
            "discover_contacts": TaskSchedule(
                name="discover_contacts",
                interval_minutes=360,  # Every 6 hours
                last_run=None,
                enabled=True,
                priority=1,
                max_retries=3,
            ),
            "send_emails": TaskSchedule(
                name="send_emails",
                interval_minutes=config.DAEMON_INTERVAL_MINUTES,
                last_run=None,
                enabled=True,
                priority=2,
                max_retries=2,
            ),
            "check_inbox": TaskSchedule(
                name="check_inbox",
                interval_minutes=30,
                last_run=None,
                enabled=True,
                priority=3,
                max_retries=2,
            ),
            "process_gmail": TaskSchedule(
                name="process_gmail",
                interval_minutes=45,
                last_run=None,
                enabled=config.GMAIL_AGENT_ENABLED,
                priority=4,
                max_retries=2,
            ),
            "discover_jobs": TaskSchedule(
                name="discover_jobs",
                interval_minutes=720,  # Every 12 hours
                last_run=None,
                enabled=True,
                priority=5,
                max_retries=2,
            ),
            "apply_jobs": TaskSchedule(
                name="apply_jobs",
                interval_minutes=240,  # Every 4 hours
                last_run=None,
                enabled=True,
                priority=6,
                max_retries=2,
            ),
            "followups": TaskSchedule(
                name="followups",
                interval_minutes=180,  # Every 3 hours
                last_run=None,
                enabled=True,
                priority=7,
                max_retries=2,
            ),
        }
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n📡 Received signal {signum}, initiating graceful shutdown...")
        self.shutdown()
    
    def _check_component_health(self) -> Dict[str, bool]:
        """Check health of all components."""
        components = {}
        
        # Check orchestrator
        try:
            if self.orchestrator is None:
                self.orchestrator = get_orchestrator()
            components["orchestrator"] = self.orchestrator is not None
        except Exception as e:
            components["orchestrator"] = False
            print(f"❌ Orchestrator error: {e}")
        
        # Check email system
        try:
            from core.email_system import get_email_system
            email_system = get_email_system()
            components["email_system"] = email_system is not None
        except Exception:
            components["email_system"] = False
        
        # Check inbox monitor
        try:
            from core.inbox_monitor import get_inbox_monitor
            monitor = get_inbox_monitor()
            components["inbox_monitor"] = monitor is not None
        except Exception:
            components["inbox_monitor"] = False
        
        # Check database connections
        try:
            import sqlite3
            conn = sqlite3.connect(config.DATABASE_PATH)
            conn.execute("SELECT 1")
            conn.close()
            components["database"] = True
        except Exception:
            components["database"] = False
        
        return components
    
    def _run_task(self, task_name: str) -> bool:
        """Run a specific task."""
        print(f"\n📋 Running task: {task_name}")
        
        try:
            if task_name == "discover_contacts":
                from core.lead_discovery import discover_leads
                result = discover_leads(daily_cap=config.CONTACT_DISCOVERY_DAILY_CAP)
                print(f"   ✅ Contacts discovered: {result.get('contacts_saved', 0)}")
            
            elif task_name == "send_emails":
                if config.DAEMON_SEND_PER_CYCLE > 0:
                    from core.email_system import get_email_system
                    email_system = get_email_system()
                    can_send, remaining = email_system.can_send_today()
                    if can_send and remaining > 0:
                        count = min(config.DAEMON_SEND_PER_CYCLE, remaining)
                        stats = email_system.send_campaign(count=count, use_ai=True)
                        print(f"   ✅ Emails sent: {stats.get('sent', 0)}")
            
            elif task_name == "check_inbox":
                from core.inbox_monitor import get_inbox_monitor
                monitor = get_inbox_monitor()
                results = monitor.check_inbox()
                print(f"   ✅ Inbox checked: {len(results)} new emails")
            
            elif task_name == "process_gmail":
                from core.gmail_agent import get_gmail_agent
                gmail_agent = get_gmail_agent()
                context = AgentContext.create()
                response = gmail_agent.execute(context, action="process_inbox")
                print(f"   ✅ Gmail processed: {response.data.get('total_processed', 0)} emails")
            
            elif task_name == "discover_jobs":
                from core.job_discovery import JobDiscovery
                discovery = JobDiscovery()
                result = discovery.run()
                print(f"   ✅ Jobs discovered: {result.get('total_saved', 0)}")
            
            elif task_name == "apply_jobs":
                from core.job_pipeline import JobPipeline
                pipeline = JobPipeline()
                result = pipeline.apply_pending(limit=config.AGENT_JOBS_PER_CYCLE)
                print(f"   ✅ Jobs applied: {result.get('attempted', 0)}")
            
            elif task_name == "followups":
                from core.followup_scheduler import get_followup_scheduler
                scheduler = get_followup_scheduler()
                scheduler.run_followup_cycle()
                print(f"   ✅ Follow-ups processed")
            
            # Update last run time
            self.task_schedules[task_name].last_run = datetime.now()
            return True
            
        except Exception as e:
            print(f"   ❌ Task failed: {e}")
            self.health_monitor.last_error = str(e)
            return False
    
    def _should_run_task(self, task: TaskSchedule) -> bool:
        """Check if a task should run based on its schedule."""
        if not task.enabled:
            return False
        
        if task.last_run is None:
            return True
        
        next_run = task.last_run + timedelta(minutes=task.interval_minutes)
        return datetime.now() >= next_run
    
    def _send_reports(self):
        """Send scheduled reports."""
        now = datetime.now()
        
        # Daily report at 9 AM
        if now.hour == 9 and now.minute < 5:
            report = self.report_generator.generate_daily_report()
            self.report_generator.send_report_email(report, "daily")
        
        # Weekly report on Monday at 10 AM
        if now.weekday() == 0 and now.hour == 10 and now.minute < 5:
            report = self.report_generator.generate_weekly_report()
            self.report_generator.send_report_email(report, "weekly")
    
    def run_cycle(self):
        """Run a single automation cycle."""
        print("\n" + "="*60)
        print("🔄 AUTOMATION CYCLE START")
        print("="*60)
        
        start_time = time.time()
        
        # Check health
        uptime = int((datetime.now() - self.start_time).total_seconds()) if self.start_time else 0
        components = self._check_component_health()
        health = self.health_monitor.check_health(components, uptime)
        
        print(f"💓 Health Status: {health.status.upper()}")
        if health.status != "healthy":
            print(f"   ⚠️ Components: {health.component_status}")
        
        # Run due tasks
        tasks_run = 0
        tasks_failed = 0
        
        # Sort by priority
        sorted_tasks = sorted(
            self.task_schedules.values(),
            key=lambda t: t.priority
        )
        
        for task in sorted_tasks:
            if self._should_run_task(task):
                success = self._run_task(task.name)
                tasks_run += 1
                if not success:
                    tasks_failed += 1
        
        # Send reports if needed
        self._send_reports()
        
        cycle_time = time.time() - start_time
        self.cycle_count += 1
        self.last_cycle_time = datetime.now()
        
        print(f"\n📊 Cycle Summary:")
        print(f"   Tasks run: {tasks_run}")
        print(f"   Tasks failed: {tasks_failed}")
        print(f"   Cycle time: {cycle_time:.1f}s")
        print(f"   Total cycles: {self.cycle_count}")
        print("="*60)
        print("✅ CYCLE COMPLETE\n")
    
    def start(self, interval_minutes: int = 5):
        """
        Start the enhanced daemon.
        
        Args:
            interval_minutes: How often to check for tasks (default: 5 minutes)
        """
        self.is_running = True
        self.start_time = datetime.now()
        
        print("="*60)
        print("🚀 STARTING ENHANCED AUTOMATION DAEMON")
        print("="*60)
        print(f"   Interval: {interval_minutes} minutes")
        print(f"   Health monitoring: {'✅' if config.HEALTH_CHECK_ENABLED else '❌'}")
        print(f"   Daily reports: ✅")
        print(f"   Weekly reports: ✅")
        print("="*60)
        
        # Initial cycle
        self.run_cycle()
        
        print("\n⏳ Running... Press Ctrl+C to stop\n")
        
        while self.is_running and not self.shutdown_event.is_set():
            try:
                # Sleep in small increments to allow quick shutdown
                for _ in range(interval_minutes * 60):
                    if not self.is_running or self.shutdown_event.is_set():
                        break
                    time.sleep(1)
                
                if not self.is_running or self.shutdown_event.is_set():
                    break
                
                self.run_cycle()
                
            except KeyboardInterrupt:
                print("\n⏸️ Interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                self.health_monitor.last_error = str(e)
                time.sleep(60)  # Wait 1 minute before retry
        
        self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown."""
        print("\n⏹️ Shutting down gracefully...")
        self.is_running = False
        self.shutdown_event.set()
        
        # Save state
        uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
        print(f"   Uptime: {uptime}")
        print(f"   Total cycles: {self.cycle_count}")
        print("👋 Daemon stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current daemon status."""
        uptime = datetime.now() - self.start_time if self.start_time else timedelta(0)
        
        return {
            "running": self.is_running,
            "uptime_seconds": int(uptime.total_seconds()),
            "cycle_count": self.cycle_count,
            "last_cycle": self.last_cycle_time.isoformat() if self.last_cycle_time else None,
            "task_schedules": {
                name: {
                    "enabled": task.enabled,
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "interval_minutes": task.interval_minutes,
                }
                for name, task in self.task_schedules.items()
            },
            "health": asdict(self.health_monitor.check_health(
                self._check_component_health(),
                int(uptime.total_seconds())
            )) if self.is_running else None,
        }


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Enhanced InternMailer Automation Daemon",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python enhanced_daemon.py --start                    # Start daemon
    python enhanced_daemon.py --start --interval 10      # Check every 10 minutes
    python enhanced_daemon.py --status                   # Show status
    python enhanced_daemon.py --cycle                    # Run single cycle
        """
    )
    
    parser.add_argument("--start", action="store_true", help="Start the daemon")
    parser.add_argument("--interval", type=int, default=5, metavar="MIN",
                       help="Minutes between checks (default: 5)")
    parser.add_argument("--status", action="store_true", help="Show daemon status")
    parser.add_argument("--cycle", action="store_true", help="Run single cycle and exit")
    
    args = parser.parse_args()
    
    daemon = EnhancedAutomationDaemon()
    
    if args.status:
        import json
        status = daemon.get_status()
        print(json.dumps(status, indent=2))
    
    elif args.cycle:
        print("🧪 Running single cycle...")
        daemon.run_cycle()
    
    elif args.start:
        daemon.start(interval_minutes=args.interval)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
