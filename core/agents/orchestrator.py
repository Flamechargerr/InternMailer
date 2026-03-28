"""
🎯 Orchestrator Agent - Master Coordinator
==========================================
Decides what actions to take and coordinates all other agents.
This is the brain of the autonomous system.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.agents.base_agent import BaseAgent, AgentContext, AgentResponse
from utils.config import config


class OrchestratorAgent(BaseAgent):
    """
    Master coordinator that:
    1. Analyzes current state (inbox, jobs, leads)
    2. Decides priority actions
    3. Delegates to specialized agents
    4. Tracks overall progress
    """

    def __init__(self):
        super().__init__("Orchestrator")
        self.agents: Dict[str, BaseAgent] = {}

    def get_agent(self, name: str) -> Optional[BaseAgent]:
        """Get or create a specialized agent."""
        if name not in self.agents:
            try:
                if name == "job_matcher":
                    from core.agents.job_matcher import JobMatcherAgent
                    self.agents[name] = JobMatcherAgent()
                elif name == "market_sentiment":
                    from core.agents.market_sentiment import MarketSentimentAgent
                    self.agents[name] = MarketSentimentAgent()
                elif name == "resume_optimizer":
                    from core.agents.resume_optimizer import ResumeOptimizerAgent
                    self.agents[name] = ResumeOptimizerAgent()
                elif name == "cover_letter":
                    from core.agents.cover_letter import CoverLetterAgent
                    self.agents[name] = CoverLetterAgent()
                elif name == "email_reply":
                    from core.agents.email_reply import EmailReplyAgent
                    self.agents[name] = EmailReplyAgent()
                elif name == "scheduler":
                    from core.agents.scheduler import SchedulerAgent
                    self.agents[name] = SchedulerAgent()
                elif name == "gmail":
                    from core.gmail_agent import GmailAgent
                    self.agents[name] = GmailAgent()
                elif name == "market_sentiment":
                    from core.agents.market_sentiment import MarketSentimentAgent
                    self.agents[name] = MarketSentimentAgent()
            except ImportError as e:
                self.log("get_agent", "error", f"Failed to load {name}: {e}")
                return None

        return self.agents.get(name)

    def analyze_state(self, context: AgentContext) -> Dict[str, Any]:
        """
        Analyze current system state to determine priorities.
        """
        state = {
            "timestamp": datetime.now().isoformat(),
            "pending_actions": [],
            "stats": {},
            "priorities": [],
        }

        # Check inbox for unprocessed emails
        try:
            from core.inbox_monitor import get_inbox_monitor
            monitor = get_inbox_monitor()
            inbox_stats = monitor.get_stats()
            state["stats"]["inbox"] = inbox_stats

            # High priority: questions and interested replies
            if inbox_stats.get("by_category", {}).get("question", 0) > 0:
                state["priorities"].append({
                    "type": "process_gmail",
                    "urgency": "high",
                    "count": inbox_stats["by_category"]["question"],
                })

            if inbox_stats.get("by_category", {}).get("interested", 0) > 0:
                state["priorities"].append({
                    "type": "process_gmail",
                    "urgency": "high",
                    "count": inbox_stats["by_category"]["interested"],
                })
        except Exception as e:
            state["stats"]["inbox_error"] = str(e)

        # Check job discovery queue
        try:
            from core.database_manager import get_job_discovery_db
            db = get_job_discovery_db(config.JOBS_DB_PATH)
            pending = db.fetch_all(
                "SELECT COUNT(*) as count FROM jobs WHERE status IN ('new', 'pending') OR status IS NULL"
            )
            pending_count = pending[0]["count"] if pending else 0
            state["stats"]["pending_jobs"] = pending_count

            if pending_count > 0:
                state["priorities"].append({
                    "type": "apply_to_jobs",
                    "urgency": "medium",
                    "count": pending_count,
                })
        except Exception as e:
            state["stats"]["jobs_error"] = str(e)

        # Check contact discovery needs
        try:
            import csv
            contacts_path = Path(config.COMPANY_CONTACTS_CSV)
            if contacts_path.exists():
                with open(contacts_path, 'r') as f:
                    reader = csv.DictReader(f)
                    contacts = list(reader)
                    state["stats"]["total_contacts"] = len(contacts)
            else:
                state["stats"]["total_contacts"] = 0
                state["priorities"].append({
                    "type": "discover_contacts",
                    "urgency": "high",
                    "reason": "No contacts available",
                })
        except Exception as e:
            state["stats"]["contacts_error"] = str(e)

        # Check email sending capacity without booting the SMTP-heavy email system.
        try:
            remaining, sent_today = self._get_email_capacity_snapshot()
            state["stats"]["emails_sent_today"] = sent_today
            state["stats"]["emails_remaining_today"] = remaining

            if remaining > 0 and state["stats"].get("total_contacts", 0) > 0:
                state["priorities"].append({
                    "type": "send_emails",
                    "urgency": "medium",
                    "count": min(remaining, 20),
                })
        except Exception as e:
            state["stats"]["email_error"] = str(e)

        # Sort priorities by urgency
        urgency_order = {"high": 0, "medium": 1, "low": 2}
        state["priorities"].sort(key=lambda x: urgency_order.get(x.get("urgency", "low"), 3))

        return state

    def _get_email_capacity_snapshot(self) -> tuple[int, int]:
        """
        Read the daily email quota directly from the tracking database.

        This keeps read-only orchestration from instantiating EmailSystem,
        which performs SMTP validation and pool setup during construction.
        """
        tracking_db = Path(config.DATABASE_PATH)
        if not tracking_db.exists():
            return config.MAX_EMAILS_PER_DAY, 0

        today = datetime.now().strftime("%Y-%m-%d")
        try:
            with sqlite3.connect(tracking_db) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM sent_emails WHERE DATE(sent_at) = ? AND status = 'sent'",
                    (today,),
                )
                row = cursor.fetchone()
                sent_today = int(row[0]) if row else 0
        except Exception as e:
            self.log("analyze_state", "warning", f"Failed to read email capacity snapshot: {e}")
            return config.MAX_EMAILS_PER_DAY, 0

        remaining = max(config.MAX_EMAILS_PER_DAY - sent_today, 0)
        return remaining, sent_today

    def execute_action(self, action_type: str, context: AgentContext, **params) -> AgentResponse:
        """Execute a specific action."""
        self.log("execute_action", "info", f"Executing: {action_type}")

        try:
            if action_type == "send_emails":
                from core.email_system import get_email_system
                system = get_email_system()
                result = system.send_campaign(count=params.get("count", 10), use_ai=True)
                return AgentResponse(
                    success=True,
                    agent_name=self.name,
                    action_taken="send_emails",
                    result=result,
                    message=f"Sent {result.get('sent', 0)} emails",
                    data=result,
                )

            elif action_type == "discover_contacts":
                from core.lead_discovery import discover_leads
                result = discover_leads(daily_cap=config.CONTACT_DISCOVERY_DAILY_CAP)
                return AgentResponse(
                    success=True,
                    agent_name=self.name,
                    action_taken="discover_contacts",
                    result=result,
                    message=f"Discovered {result.get('contacts_saved', 0)} contacts",
                    data=result,
                )

            elif action_type == "process_gmail":
                agent = self.get_agent("gmail")
                if agent:
                    return agent.execute(context, action="process_inbox", dry_run=params.get("dry_run", False))
                return AgentResponse(
                    success=False,
                    agent_name=self.name,
                    action_taken="process_gmail",
                    message="Gmail agent not available",
                )

            elif action_type == "apply_to_jobs":
                from core.job_pipeline import JobPipeline
                pipeline = JobPipeline()
                result = pipeline.apply_pending(limit=params.get("limit", config.AGENT_JOBS_PER_CYCLE))
                return AgentResponse(
                    success=True,
                    agent_name=self.name,
                    action_taken="apply_to_jobs",
                    result=result,
                    message=f"Applied to {result.get('attempted', 0)} jobs",
                    data=result,
                )

            elif action_type == "analyze_market_sentiment":
                agent = self.get_agent("market_sentiment")
                if agent:
                    return agent.execute(
                        context,
                        limit_per_entity=params.get("limit_per_entity", 6),
                        watchlist=params.get("watchlist"),
                    )
                return AgentResponse(
                    success=False,
                    agent_name=self.name,
                    action_taken="analyze_market_sentiment",
                    message="Market sentiment agent not available",
                )

            else:
                return AgentResponse(
                    success=False,
                    agent_name=self.name,
                    action_taken=action_type,
                    message=f"Unknown action: {action_type}",
                )

        except Exception as e:
            return AgentResponse(
                success=False,
                agent_name=self.name,
                action_taken=action_type,
                message=str(e),
            )

    def run(self, context: AgentContext, **kwargs) -> AgentResponse:
        """
        Main orchestration loop.
        """
        max_actions = kwargs.get("max_actions", 5)
        dry_run = kwargs.get("dry_run", False)

        self.log("run", "info", f"Starting orchestration cycle (max_actions={max_actions})")

        results = []
        actions_taken = 0

        while actions_taken < max_actions:
            state = self.analyze_state(context)

            if not state["priorities"]:
                self.log("run", "info", "No more actions to take")
                break

            top_priority = state["priorities"][0]
            action_type = top_priority.get("type")

            if dry_run:
                self.log("run", "info", f"[DRY RUN] Would execute: {action_type}")
                results.append({"action": action_type, "status": "dry_run"})
                actions_taken += 1
                continue

            response = self.execute_action(action_type, context, **top_priority)
            results.append(response.to_dict())
            actions_taken += 1

            if not response.success:
                self.log("run", "warning", f"Action failed: {response.message}")

        self.save_state({
            "last_run": datetime.now().isoformat(),
            "actions_taken": actions_taken,
            "results": results,
        })

        return AgentResponse(
            success=True,
            agent_name=self.name,
            action_taken="orchestrate",
            result=results,
            message=f"Completed {actions_taken} actions",
            data={"actions_taken": actions_taken, "results": results},
        )

    def run_full_cycle(self, context: Optional[AgentContext] = None) -> Dict[str, Any]:
        """
        Run a complete automation cycle covering all tasks.
        """
        if context is None:
            context = AgentContext.create()

        self.log("run_full_cycle", "info", "Starting full automation cycle")

        cycle_results = {
            "start_time": datetime.now().isoformat(),
            "steps": [],
            "errors": [],
        }

        tasks = [
            ("job_discovery", lambda: self._run_job_discovery()),
            ("contact_discovery", lambda: self._run_contact_discovery()),
            ("inbox_processing", lambda: self._run_inbox_processing(context)),
            ("email_outreach", lambda: self._run_email_outreach()),
            ("job_applications", lambda: self._run_job_applications()),
            ("followups", lambda: self._run_followups()),
        ]

        for task_name, task_func in tasks:
            try:
                result = task_func()
                cycle_results["steps"].append({"step": task_name, "result": result})
            except Exception as e:
                cycle_results["errors"].append(f"{task_name}: {e}")

        cycle_results["end_time"] = datetime.now().isoformat()
        cycle_results["success"] = len(cycle_results["errors"]) == 0

        self.log(
            "run_full_cycle",
            "success" if cycle_results["success"] else "warning",
            f"Cycle complete: {len(cycle_results['steps'])} steps, {len(cycle_results['errors'])} errors",
        )

        return cycle_results

    def _run_job_discovery(self):
        from core.job_discovery import JobDiscovery
        discovery = JobDiscovery()
        return discovery.run()

    def _run_contact_discovery(self):
        from core.lead_discovery import discover_leads
        return discover_leads(daily_cap=config.CONTACT_DISCOVERY_DAILY_CAP)

    def _run_inbox_processing(self, context: AgentContext):
        agent = self.get_agent("gmail")
        if agent:
            response = agent.execute(context, action="process_inbox")
            return {"processed": response.data.get("total_processed", 0)}
        return {"processed": 0}

    def _run_email_outreach(self):
        from core.email_system import get_email_system
        email_system = get_email_system()
        can_send, remaining = email_system.can_send_today()
        if can_send and remaining > 0:
            send_count = min(remaining, config.AGENT_EMAILS_PER_CYCLE)
            return email_system.send_campaign(count=send_count, use_ai=True)
        return {"sent": 0, "skipped": "daily_limit_reached"}

    def _run_job_applications(self):
        from core.job_pipeline import JobPipeline
        pipeline = JobPipeline()
        return pipeline.apply_pending(limit=config.AGENT_JOBS_PER_CYCLE)

    def _run_followups(self):
        from core.followup_scheduler import get_followup_scheduler
        followup = get_followup_scheduler()
        followup.run_followup_cycle()
        return {"status": "completed"}


# Singleton instance
_orchestrator: Optional[OrchestratorAgent] = None


def get_orchestrator() -> OrchestratorAgent:
    """Get singleton orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()
    return _orchestrator


if __name__ == "__main__":
    import sys

    orchestrator = get_orchestrator()
    context = AgentContext.create()

    if "--full-cycle" in sys.argv:
        print("🚀 Running full automation cycle...")
        result = orchestrator.run_full_cycle(context)
        print(json.dumps(result, indent=2))

    elif "--analyze" in sys.argv:
        print("📊 Analyzing system state...")
        state = orchestrator.analyze_state(context)
        print(json.dumps(state, indent=2))

    elif "--dry-run" in sys.argv:
        print("🧪 Dry run orchestration...")
        response = orchestrator.execute(context, max_actions=5, dry_run=True)
        print(json.dumps(response.to_dict(), indent=2))

    else:
        print("🤖 Running orchestration...")
        response = orchestrator.execute(context, max_actions=5)
        print(json.dumps(response.to_dict(), indent=2))
