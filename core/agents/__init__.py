"""
🤖 InternMailer AI Agents
=========================
Autonomous agents for full job application automation.
"""

from core.agents.base_agent import BaseAgent, AgentResponse, AgentContext, AgentStatus
from core.agents.orchestrator import OrchestratorAgent, get_orchestrator
from core.agents.scheduler import SchedulerAgent, get_scheduler_agent
from core.agents.resume_optimizer import ResumeOptimizerAgent
from core.agents.cover_letter import CoverLetterAgent
from core.agents.job_matcher import JobMatcherAgent
from core.agents.email_reply import EmailReplyAgent
from core.agents.market_sentiment import MarketSentimentAgent, get_market_sentiment_agent

__all__ = [
    "BaseAgent",
    "AgentResponse",
    "AgentContext",
    "AgentStatus",
    "OrchestratorAgent",
    "get_orchestrator",
    "SchedulerAgent",
    "get_scheduler_agent",
    "ResumeOptimizerAgent",
    "CoverLetterAgent",
    "JobMatcherAgent",
    "EmailReplyAgent",
    "MarketSentimentAgent",
    "get_market_sentiment_agent",
]
