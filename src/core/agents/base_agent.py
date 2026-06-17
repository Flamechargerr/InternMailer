"""
🤖 Base Agent - Foundation for all InternMailer AI Agents
=========================================================
Provides common functionality: AI integration, logging, state management.
"""

from __future__ import annotations

import json
import time
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from utils.config import config
from utils.profile import get_profile


class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"


@dataclass
class AgentContext:
    """Context passed between agents for coordination."""
    profile: Dict[str, Any] = field(default_factory=dict)
    current_job: Optional[Dict[str, Any]] = None
    current_company: Optional[Dict[str, Any]] = None
    current_email: Optional[Dict[str, Any]] = None
    session_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(cls) -> "AgentContext":
        """Create a new context with profile loaded."""
        profile = get_profile()
        return cls(
            profile=profile,
            session_id=datetime.now().strftime("%Y%m%d_%H%M%S")
        )


@dataclass
class AgentResponse:
    """Standardized response from any agent."""
    success: bool
    agent_name: str
    action_taken: str
    result: Any = None
    message: str = ""
    next_action: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "agent": self.agent_name,
            "action": self.action_taken,
            "result": self.result,
            "message": self.message,
            "next_action": self.next_action,
            "data": self.data,
            "duration_ms": self.duration_ms,
        }


class BaseAgent(ABC):
    """
    Abstract base class for all InternMailer agents.
    
    Each agent is responsible for a specific domain:
    - LeadFinder: Finding company contacts
    - JobMatcher: Scoring and matching jobs
    - ResumeOptimizer: Tailoring resumes
    - CoverLetter: Generating cover letters
    - EmailReply: Drafting email responses
    - Scheduler: Managing calendar and meetings
    """
    
    def __init__(self, name: str, db_path: Optional[str] = None):
        self.name = name
        self.status = AgentStatus.IDLE
        self.db_path = db_path or config.AGENTS_DB_PATH
        self.ai_provider = None
        self.last_run: Optional[datetime] = None
        self.run_count = 0
        
        # Initialize AI provider
        self._init_ai()
        
        # Ensure database exists
        self._init_db()
    
    def _init_ai(self):
        """Initialize the AI provider for this agent."""
        try:
            from core.unified_ai_provider import get_unified_ai_provider
            self.ai_provider = get_unified_ai_provider()
        except Exception as e:
            print(f"⚠️ {self.name}: AI provider not available: {e}")
    
    def _init_db(self):
        """Initialize agent state database."""
        # Ensure directory exists
        db_path = Path(self.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with sqlite3.connect(str(db_path)) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS agent_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent_name TEXT,
                        action TEXT,
                        status TEXT,
                        message TEXT,
                        data TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS agent_state (
                        agent_name TEXT PRIMARY KEY,
                        state TEXT,
                        last_run TIMESTAMP,
                        run_count INTEGER DEFAULT 0
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"⚠️ {self.name}: Failed to initialize database at {self.db_path}: {e}")
    
    def log(self, action: str, status: str, message: str = "", data: Optional[Dict] = None):
        """Log agent activity to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO agent_logs (agent_name, action, status, message, data)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (self.name, action, status, message, json.dumps(data or {})),
                )
                conn.commit()
        except Exception as e:
            print(f"⚠️ {self.name}: Failed to log: {e}")
        
        # Also print
        emoji = "✅" if status == "success" else "❌" if status == "error" else "📋"
        print(f"{emoji} [{self.name}] {action}: {message}")
    
    def save_state(self, state: Dict[str, Any]):
        """Persist agent state."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO agent_state (agent_name, state, last_run, run_count)
                    VALUES (?, ?, ?, ?)
                    """,
                    (self.name, json.dumps(state), datetime.now().isoformat(), self.run_count),
                )
                conn.commit()
        except Exception as e:
            print(f"⚠️ {self.name}: Failed to save state: {e}")
    
    def load_state(self) -> Dict[str, Any]:
        """Load persisted agent state."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT state, last_run, run_count FROM agent_state WHERE agent_name = ?",
                    (self.name,),
                )
                row = cursor.fetchone()
                if row:
                    self.last_run = datetime.fromisoformat(row[1]) if row[1] else None
                    self.run_count = row[2] or 0
                    return json.loads(row[0]) if row[0] else {}
        except Exception as e:
            print(f"⚠️ {self.name}: Failed to load state: {e}")
        return {}
    
    def call_ai(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Call the AI provider with a prompt."""
        if not self.ai_provider:
            raise RuntimeError(f"{self.name}: AI provider not available")
        
        try:
            # Use the unified AI provider's completion method
            result = self.ai_provider.complete(
                prompt=prompt,
                system_prompt=system_prompt or f"You are {self.name}, an AI agent for job application automation.",
                temperature=0.7,
            )
            return result.content if hasattr(result, 'content') else str(result)
        except Exception as e:
            self.log("ai_call", "error", str(e))
            raise
    
    def call_ai_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Call AI and parse JSON response."""
        response = self.call_ai(prompt, system_prompt)
        
        # Try to extract JSON from response
        try:
            # Handle markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            return json.loads(response.strip())
        except json.JSONDecodeError:
            # Try to find JSON object in response
            import re
            match = re.search(r'\{[\s\S]*\}', response)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
            
            # Return as message if parsing fails
            return {"message": response, "raw": True}
    
    @abstractmethod
    def run(self, context: AgentContext, **kwargs) -> AgentResponse:
        """
        Execute the agent's main task.
        
        Args:
            context: Shared context between agents
            **kwargs: Agent-specific parameters
            
        Returns:
            AgentResponse with results
        """
        pass
    
    def execute(self, context: AgentContext, **kwargs) -> AgentResponse:
        """
        Wrapper around run() with timing and error handling.
        """
        self.status = AgentStatus.RUNNING
        self.run_count += 1
        start_time = time.time()
        
        try:
            response = self.run(context, **kwargs)
            response.duration_ms = (time.time() - start_time) * 1000
            
            self.status = AgentStatus.COMPLETED if response.success else AgentStatus.FAILED
            self.last_run = datetime.now()
            
            self.log(
                response.action_taken,
                "success" if response.success else "error",
                response.message,
                response.data,
            )
            
            return response
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            duration_ms = (time.time() - start_time) * 1000
            
            self.log("execute", "error", str(e))
            
            return AgentResponse(
                success=False,
                agent_name=self.name,
                action_taken="execute",
                message=f"Agent execution failed: {e}",
                duration_ms=duration_ms,
            )
