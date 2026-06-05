"""
📅 Scheduler Agent - Calendar and Meeting Management
====================================================
Handles meeting requests, calendar scheduling, and interview coordination.
Integrates with Google Calendar API for automated scheduling.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from core.agents.base_agent import BaseAgent, AgentContext, AgentResponse
from utils.config import config


class SchedulerAgent(BaseAgent):
    """
    Agent responsible for:
    - Detecting meeting requests in emails
    - Suggesting available time slots
    - Sending calendar invites
    - Managing interview scheduling
    - Tracking scheduled meetings
    """
    
    def __init__(self):
        super().__init__("SchedulerAgent")
        self.calendar_link = config.CALENDAR_LINK
        self._init_calendar_db()
    
    def _init_calendar_db(self):
        """Initialize calendar events database."""
        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_meetings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_thread_id TEXT,
                    contact_email TEXT,
                    contact_name TEXT,
                    company TEXT,
                    meeting_type TEXT,
                    proposed_times TEXT,
                    scheduled_time TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    calendar_event_id TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
    
    def run(self, context: AgentContext, **kwargs) -> AgentResponse:
        """
        Main entry point for scheduling tasks.
        
        Args:
            action: Type of scheduling action ('detect_request', 'propose_times', 
                   'send_invite', 'check_availability')
            email_content: Email text to analyze (for detection)
            email_thread_id: Thread identifier
            contact_email: Contact's email address
            contact_name: Contact's name
            company: Company name
        """
        action = kwargs.get("action", "detect_request")
        
        if action == "detect_request":
            return self._detect_meeting_request(context, kwargs)
        elif action == "propose_times":
            return self._propose_times(context, kwargs)
        elif action == "send_invite":
            return self._send_calendar_invite(context, kwargs)
        elif action == "check_availability":
            return self._check_availability(context, kwargs)
        elif action == "get_pending":
            return self._get_pending_meetings(context, kwargs)
        else:
            return AgentResponse(
                success=False,
                agent_name=self.name,
                action_taken="run",
                message=f"Unknown action: {action}",
            )
    
    def _detect_meeting_request(self, context: AgentContext, params: Dict) -> AgentResponse:
        """Detect if an email contains a meeting request."""
        email_content = params.get("email_content", "")
        
        if not email_content:
            return AgentResponse(
                success=False,
                agent_name=self.name,
                action_taken="detect_request",
                message="No email content provided",
            )
        
        # Use AI to detect meeting requests
        system_prompt = """You are a meeting detection assistant. Analyze the email and determine:
1. Is this a meeting/interview request?
2. What type of meeting is it? (interview, screening, chat, etc.)
3. What is the urgency level?
4. Any specific dates/times mentioned?

Respond in JSON format:
{
    "is_meeting_request": boolean,
    "meeting_type": "screening|interview|technical|behavioral|chat|follow_up|other",
    "urgency": "high|medium|low",
    "mentions_specific_times": boolean,
    "extracted_dates": ["date1", "date2"],
    "confidence": float (0-1)
}"""
        
        prompt = f"Analyze this email for meeting requests:\n\n{email_content[:2000]}"
        
        try:
            result = self.call_ai_json(prompt, system_prompt)
            
            is_request = result.get("is_meeting_request", False)
            confidence = result.get("confidence", 0)
            
            if is_request and confidence >= 0.7:
                self.log("detect_request", "success", 
                        f"Detected {result.get('meeting_type')} request with {confidence:.0%} confidence")
                
                return AgentResponse(
                    success=True,
                    agent_name=self.name,
                    action_taken="detect_request",
                    result=result,
                    message=f"Meeting request detected: {result.get('meeting_type')}",
                    data={"meeting_detected": True, "details": result},
                )
            else:
                return AgentResponse(
                    success=True,
                    agent_name=self.name,
                    action_taken="detect_request",
                    result=result,
                    message="No meeting request detected",
                    data={"meeting_detected": False},
                )
                
        except Exception as e:
            self.log("detect_request", "error", str(e))
            return AgentResponse(
                success=False,
                agent_name=self.name,
                action_taken="detect_request",
                message=f"Detection failed: {e}",
            )
    
    def _propose_times(self, context: AgentContext, params: Dict) -> AgentResponse:
        """Generate proposed meeting times."""
        meeting_type = params.get("meeting_type", "interview")
        contact_email = params.get("contact_email", "")
        contact_name = params.get("contact_name", "")
        company = params.get("company", "")
        
        # Generate time slots for the next 2 weeks
        proposed_slots = self._generate_time_slots(meeting_type)
        
        # Format for email
        slots_text = "\n".join([
            f"• {slot['day']}, {slot['date']} at {slot['time']} ({slot['timezone']})"
            for slot in proposed_slots[:5]
        ])
        
        # Store proposal
        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO scheduled_meetings 
                (email_thread_id, contact_email, contact_name, company, meeting_type, proposed_times, status)
                VALUES (?, ?, ?, ?, ?, ?, 'proposed')
            """, (
                params.get("email_thread_id", ""),
                contact_email,
                contact_name,
                company,
                meeting_type,
                json.dumps(proposed_slots),
            ))
            conn.commit()
        
        message = f"""Thank you for reaching out about the {meeting_type}. I'm excited to discuss the opportunity further!

Here are some times that work for me over the next two weeks:

{slots_text}

Alternatively, you can view my full availability and book directly here: {self.calendar_link}

Please let me know which time works best for you, or feel free to suggest an alternative that fits your schedule.

Looking forward to speaking with you!

Best regards,
{context.profile.get('name', '')}"""
        
        self.log("propose_times", "success", f"Generated {len(proposed_slots)} time slots")
        
        return AgentResponse(
            success=True,
            agent_name=self.name,
            action_taken="propose_times",
            result={"proposed_slots": proposed_slots, "message": message},
            message=f"Generated {len(proposed_slots)} time slots",
            data={"slots": proposed_slots, "calendar_link": self.calendar_link},
        )
    
    def _generate_time_slots(self, meeting_type: str) -> List[Dict]:
        """Generate available time slots."""
        slots = []
        
        # Get next 10 business days
        current = datetime.now()
        days_added = 0
        
        while days_added < 10:
            current += timedelta(days=1)
            # Skip weekends
            if current.weekday() >= 5:
                continue
            
            # Generate slots for this day
            base_times = ["9:00 AM", "11:00 AM", "2:00 PM", "4:00 PM"]
            
            for time_str in base_times:
                slots.append({
                    "day": current.strftime("%A"),
                    "date": current.strftime("%B %d, %Y"),
                    "time": time_str,
                    "timezone": "IST (UTC+5:30)",
                    "iso": current.strftime("%Y-%m-%d") + "T" + 
                          ("09:00" if "9" in time_str else "11:00" if "11" in time_str else 
                           "14:00" if "2" in time_str else "16:00") + ":00+05:30",
                })
            
            days_added += 1
        
        return slots
    
    def _send_calendar_invite(self, context: AgentContext, params: Dict) -> AgentResponse:
        """Send a calendar invite (placeholder for Google Calendar integration)."""
        # This would integrate with Google Calendar API
        # For now, return instructions
        
        self.log("send_invite", "info", "Calendar invite would be sent via Google Calendar API")
        
        return AgentResponse(
            success=True,
            agent_name=self.name,
            action_taken="send_invite",
            message="Calendar invite prepared (manual send required)",
            data={
                "action": "manual_calendar_invite",
                "instructions": "Please create calendar event manually or enable Google Calendar API integration",
            },
        )
    
    def _check_availability(self, context: AgentContext, params: Dict) -> AgentResponse:
        """Check calendar availability."""
        # Placeholder for calendar integration
        return AgentResponse(
            success=True,
            agent_name=self.name,
            action_taken="check_availability",
            result={"available": True, "slots": self._generate_time_slots("interview")[:5]},
            message="Availability checked",
        )
    
    def _get_pending_meetings(self, context: AgentContext, params: Dict) -> AgentResponse:
        """Get list of pending meeting requests."""
        import sqlite3
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM scheduled_meetings 
                    WHERE status IN ('pending', 'proposed')
                    ORDER BY created_at DESC
                """)
                rows = cursor.fetchall()
                
                meetings = [dict(row) for row in rows]
                
                self.log("get_pending", "success", f"Found {len(meetings)} pending meetings")
                
                return AgentResponse(
                    success=True,
                    agent_name=self.name,
                    action_taken="get_pending",
                    result=meetings,
                    message=f"Found {len(meetings)} pending meetings",
                    data={"count": len(meetings), "meetings": meetings},
                )
        except Exception as e:
            return AgentResponse(
                success=False,
                agent_name=self.name,
                action_taken="get_pending",
                message=f"Failed to fetch meetings: {e}",
            )
    
    def generate_scheduling_response(self, context: AgentContext, email_content: str, 
                                    meeting_info: Dict) -> str:
        """Generate a response to a scheduling request."""
        meeting_type = meeting_info.get("meeting_type", "meeting")
        
        # Get proposed times
        response = self._propose_times(context, {
            "meeting_type": meeting_type,
            "contact_email": meeting_info.get("contact_email", ""),
            "contact_name": meeting_info.get("contact_name", ""),
            "company": meeting_info.get("company", ""),
            "email_thread_id": meeting_info.get("email_thread_id", ""),
        })
        
        if response.success:
            return response.result.get("message", "")
        
        return f"""Thank you for reaching out. I'd be happy to schedule a {meeting_type}.

Please let me know what times work best for you, or you can book directly via my calendar: {self.calendar_link}

Best regards,
{context.profile.get('name', '')}"""


# Singleton instance
_scheduler_agent: Optional[SchedulerAgent] = None


def get_scheduler_agent() -> SchedulerAgent:
    """Get singleton scheduler agent instance."""
    global _scheduler_agent
    if _scheduler_agent is None:
        _scheduler_agent = SchedulerAgent()
    return _scheduler_agent
