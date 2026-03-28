"""
📈 Market Sentiment Agent (MVP)
==============================
Agent wrapper around the MarketSentimentEngine so it plugs into the existing
agent framework (BaseAgent/Orchestrator).
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from core.agents.base_agent import BaseAgent, AgentContext, AgentResponse
from core.market_sentiment import MarketSentimentEngine
from core.sentiment_store import SentimentStore

try:
    from utils.config import config
except Exception:
    config = None  # type: ignore


def _default_topics() -> List[str]:
    raw = os.getenv("MARKET_SENTIMENT_TOPICS", "").strip()
    if raw:
        return [t.strip() for t in raw.split(",") if t.strip()]
    # A conservative default that works for both US + India contexts.
    return ["SPY", "NASDAQ", "NIFTY", "BTC"]


class MarketSentimentAgent(BaseAgent):
    def __init__(self, db_path: Optional[str] = None):
        super().__init__("MarketSentiment")
        default_db = "/tmp/internmailer_db/market_sentiment.db"
        cfg_db = getattr(config, "MARKET_SENTIMENT_DB_PATH", None) if config else None
        self.store = SentimentStore(db_path=db_path or cfg_db or default_db)
        self.engine = MarketSentimentEngine(store=self.store)

    def run(self, context: AgentContext, **kwargs) -> AgentResponse:
        topics = kwargs.get("topics") or _default_topics()
        window_hours = int(kwargs.get("window_hours", 24))
        max_items_per_topic = int(kwargs.get("max_items_per_topic", 25))

        try:
            results = self.engine.refresh(
                topics=list(topics),
                window_hours=window_hours,
                max_items_per_topic=max_items_per_topic,
            )
            # Provide a compact top-level summary too.
            summary = {
                "topics": len(results),
                "window_hours": window_hours,
            }
            return AgentResponse(
                success=True,
                agent_name=self.name,
                action_taken="refresh_market_sentiment",
                result=results,
                message=f"Refreshed market sentiment for {len(results)} topic(s)",
                data=summary,
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                agent_name=self.name,
                action_taken="refresh_market_sentiment",
                message=str(e),
                data={"topics": list(topics), "window_hours": window_hours},
            )


# Singleton instance (matches patterns used by scheduler/orchestrator)
_market_sentiment_agent: Optional[MarketSentimentAgent] = None


def get_market_sentiment_agent() -> MarketSentimentAgent:
    """Get a singleton MarketSentimentAgent instance."""
    global _market_sentiment_agent
    if _market_sentiment_agent is None:
        _market_sentiment_agent = MarketSentimentAgent()
    return _market_sentiment_agent
