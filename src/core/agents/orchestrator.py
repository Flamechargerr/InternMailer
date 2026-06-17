"""
Agent Orchestrator
==================
Coordinates multiple AI agents for job discovery, resume tailoring,
and application pipeline execution.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from core.agents.base_agent import BaseAgent, AgentContext, AgentResponse
from core.agents.scheduler import get_scheduler_agent
from core.agents.resume_optimizer import ResumeOptimizerAgent
from core.agents.cover_letter import CoverLetterAgent
from core.agents.email_reply import EmailReplyAgent
from core.agents.job_matcher import JobMatcherAgent

logger = logging.getLogger(__name__)

_orchestrator_instance = None


class AgentOrchestrator:
    """Orchestrates a pipeline of agents for job application automation."""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.context = AgentContext.create()
        self._register_agents()

    def _register_agents(self):
        self.agents["scheduler"] = get_scheduler_agent()
        self.agents["resume_optimizer"] = ResumeOptimizerAgent()
        self.agents["cover_letter"] = CoverLetterAgent()
        self.agents["email_reply"] = EmailReplyAgent()
        self.agents["job_matcher"] = JobMatcherAgent()

    def run_pipeline(self, pipeline_type: str = "full", **kwargs) -> Dict[str, Any]:
        logger.info("Running pipeline: %s", pipeline_type)
        results = {}
        for name, agent in self.agents.items():
            try:
                response = agent.execute(self.context)
                results[name] = {"status": "ok", "data": response.data if response else {}}
            except Exception as e:
                logger.error("Agent %s failed: %s", name, e)
                results[name] = {"status": "error", "error": str(e)}
        return {"pipeline": pipeline_type, "results": results, "timestamp": datetime.now().isoformat()}


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AgentOrchestrator()
    return _orchestrator_instance
