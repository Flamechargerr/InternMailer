"""
📧 Gmail Agent - Full Inbox Management
======================================
Intelligent Gmail inbox management with:
- Smart email categorization (jobs, interviews, rejections, general)
- Auto-draft responses for all categories
- Meeting detection and calendar link sending
- Priority inbox management
- Email thread tracking
- Auto-archive completed threads
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from pathlib import Path

from core.agents.base_agent import BaseAgent, AgentContext, AgentResponse
from core.agents.scheduler import get_scheduler_agent
from utils.config import config


class GmailAgent(BaseAgent):
    """
    Advanced Gmail inbox management agent.
    
    Features:
    - Categorize emails into: interested, not_interested, question, ooo, rejection, interview_request, general
    - Draft contextual responses
    - Detect meeting requests and delegate to scheduler
    - Track email threads
    - Auto-archive completed conversations
    """
    
    def __init__(self):
        self.db_path = config.INBOX_DB_PATH
        super().__init__("GmailAgent", db_path=config.AGENTS_DB_PATH)
        self._init_database()
        self.scheduler = get_scheduler_agent()
    
    def _init_database(self):
        """Initialize Gmail agent database tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Thread tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS email_threads (
                    thread_id TEXT PRIMARY KEY,
                    subject TEXT,
                    contact_email TEXT,
                    contact_name TEXT,
                    company TEXT,
                    category TEXT,
                    status TEXT DEFAULT 'active',
                    message_count INTEGER DEFAULT 1,
                    last_activity TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Pending responses
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT UNIQUE,
                    thread_id TEXT,
                    from_email TEXT,
                    subject TEXT,
                    body_preview TEXT,
                    category TEXT,
                    suggested_response TEXT,
                    confidence REAL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    responded_at TIMESTAMP
                )
            """)
            
            # Priority senders
            conn.execute("""
                CREATE TABLE IF NOT EXISTS priority_senders (
                    email TEXT PRIMARY KEY,
                    name TEXT,
                    company TEXT,
                    priority_level INTEGER DEFAULT 1,
                    last_contact TIMESTAMP,
                    notes TEXT
                )
            """)
            
            conn.commit()
    
    def run(self, context: AgentContext, **kwargs) -> AgentResponse:
        """
        Main entry point for Gmail agent.
        
        Args:
            action: Action to perform ('categorize', 'draft_response', 'process_inbox',
                   'get_priority', 'archive_completed')
            email_data: Email data for categorization/drafting
            message_id: Message ID for specific operations
        """
        action = kwargs.get("action", "process_inbox")
        
        if action == "process_inbox":
            return self._process_inbox(context, kwargs)
        elif action == "categorize":
            return self._categorize_email(context, kwargs)
        elif action == "draft_response":
            return self._draft_response(context, kwargs)
        elif action == "get_priority":
            return self._get_priority_emails(context, kwargs)
        elif action == "archive_completed":
            return self._archive_completed_threads(context, kwargs)
        else:
            return AgentResponse(
                success=False,
                agent_name=self.name,
                action_taken="run",
                message=f"Unknown action: {action}",
            )
    
    def _process_inbox(self, context: AgentContext, params: Dict) -> AgentResponse:
        """Process all unprocessed emails in inbox."""
        dry_run = params.get("dry_run", False)
        
        self.log("process_inbox", "info", "Starting inbox processing")
        
        # Get unprocessed emails from inbox monitor
        try:
            from core.inbox_monitor import get_inbox_monitor
            monitor = get_inbox_monitor()
            
            # Check inbox (dry_run means don't mark as read)
            emails = monitor.check_inbox(dry_run=dry_run)
            
            if not emails:
                return AgentResponse(
                    success=True,
                    agent_name=self.name,
                    action_taken="process_inbox",
                    message="No new emails to process",
                    data={"processed": 0, "drafted": 0},
                )
            
            processed = []
            drafted = []
            meetings_detected = []
            
            for email_data in emails:
                # Categorize
                category_result = self._classify_email(email_data)
                category = category_result.get("category", "general")
                
                # Check for meeting requests
                meeting_info = None
                if category in ["interested", "interview_request", "question"]:
                    meeting_result = self.scheduler.execute(
                        context,
                        action="detect_request",
                        email_content=email_data.get("body", ""),
                    )
                    if meeting_result.success and meeting_result.data.get("meeting_detected"):
                        meeting_info = meeting_result.result
                        meetings_detected.append({
                            "email": email_data.get("from"),
                            "subject": email_data.get("subject"),
                            "meeting_type": meeting_info.get("meeting_type"),
                        })
                
                # Store in database
                self._store_email(email_data, category, category_result.get("confidence", 0))
                
                # Draft response if enabled
                if config.GMAIL_AUTO_REPLY_ENABLED and not dry_run:
                    draft = self._create_draft(context, email_data, category, meeting_info)
                    if draft:
                        self._store_pending_response(email_data, category, draft)
                        drafted.append({
                            "email": email_data.get("from"),
                            "subject": email_data.get("subject"),
                            "category": category,
                        })
                
                processed.append({
                    "message_id": email_data.get("message_id"),
                    "from": email_data.get("from"),
                    "category": category,
                    "confidence": category_result.get("confidence"),
                })
            
            self.log("process_inbox", "success", 
                    f"Processed {len(processed)} emails, drafted {len(drafted)} responses")
            
            return AgentResponse(
                success=True,
                agent_name=self.name,
                action_taken="process_inbox",
                result={"processed": processed, "drafted": drafted, "meetings": meetings_detected},
                message=f"Processed {len(processed)} emails",
                data={
                    "total_processed": len(processed),
                    "responses_drafted": len(drafted),
                    "meetings_detected": len(meetings_detected),
                    "by_category": self._count_by_category(processed),
                },
            )
            
        except Exception as e:
            self.log("process_inbox", "error", str(e))
            return AgentResponse(
                success=False,
                agent_name=self.name,
                action_taken="process_inbox",
                message=f"Processing failed: {e}",
            )
    
    def _classify_email(self, email_data: Dict) -> Dict[str, Any]:
        """Classify an email into categories."""
        # Use existing reply classifier
        try:
            from core.reply_classifier import get_reply_classifier
            classifier = get_reply_classifier()
            
            result = classifier.classify_reply(
                email_data.get("body", ""),
                email_data.get("subject", ""),
            )
            
            return {
                "category": result["category"].value,
                "confidence": result["confidence"],
                "sentiment": result.get("sentiment", 0),
                "suggested_action": result.get("suggested_action", ""),
            }
        except Exception:
            # Fallback classification
            return self._fallback_classification(email_data)
    
    def _fallback_classification(self, email_data: Dict) -> Dict[str, Any]:
        """Fallback rule-based classification."""
        body = email_data.get("body", "").lower()
        subject = email_data.get("subject", "").lower()
        text = body + " " + subject
        
        # Category detection rules
        if any(kw in text for kw in ["not interested", "not a fit", "not moving forward", "rejected", "regret to inform"]):
            return {"category": "not_interested", "confidence": 0.9}
        
        if any(kw in text for kw in ["out of office", "ooo", "automated reply", "auto-reply"]):
            return {"category": "out_of_office", "confidence": 0.95}
        
        if any(kw in text for kw in ["interview", "schedule", "chat", "call", "zoom", "teams", "meet"]):
            if any(kw in text for kw in ["question", "questions", "ask", "wondering", "confirm"]):
                return {"category": "question", "confidence": 0.75}
            return {"category": "interested", "confidence": 0.85}
        
        if any(kw in text for kw in ["question", "questions", "ask", "wondering", "clarify"]):
            return {"category": "question", "confidence": 0.8}
        
        if any(kw in text for kw in ["interested", "looks great", "impressive", "resume", "cv"]):
            return {"category": "interested", "confidence": 0.7}
        
        return {"category": "general", "confidence": 0.5}
    
    def _create_draft(self, context: AgentContext, email_data: Dict, 
                     category: str, meeting_info: Optional[Dict] = None) -> Optional[str]:
        """Create a response draft based on category."""
        from_email = email_data.get("from", "")
        subject = email_data.get("subject", "")
        body = email_data.get("body", "")[:2000]
        
        # Get contact info
        contact_name = self._extract_name(from_email)
        company = self._extract_company(from_email, body)
        
        # Generate response based on category
        if category == "interested":
            if meeting_info:
                # Delegate to scheduler
                return self.scheduler.generate_scheduling_response(
                    context, body,
                    {
                        "contact_email": from_email,
                        "contact_name": contact_name,
                        "company": company,
                        "email_thread_id": email_data.get("message_id", ""),
                        "meeting_type": meeting_info.get("meeting_type", "interview"),
                    }
                )
            else:
                return self._generate_interested_response(context, contact_name, company)
        
        elif category == "not_interested":
            return self._generate_not_interested_response(context, contact_name, company)
        
        elif category == "question":
            return self._generate_question_response(context, contact_name, company, body)
        
        elif category == "interview_request":
            # Always use scheduler for interview requests
            return self.scheduler.generate_scheduling_response(
                context, body,
                {
                    "contact_email": from_email,
                    "contact_name": contact_name,
                    "company": company,
                    "email_thread_id": email_data.get("message_id", ""),
                    "meeting_type": "interview",
                }
            )
        
        elif category == "out_of_office":
            return None  # No response needed for OOO
        
        else:
            return self._generate_general_response(context, contact_name, company, body)
    
    def _generate_interested_response(self, context: AgentContext, contact_name: str, company: str) -> str:
        """Generate response for interested reply."""
        profile = context.profile
        
        return f"""Hi {contact_name},

Thank you for your response! I'm excited about the opportunity at {company}.

I'd be happy to discuss this further. Here is my availability for the next two weeks:

• Monday-Friday: 9:00 AM - 5:00 PM IST

Alternatively, you can book a time directly through my calendar: {config.CALENDAR_LINK}

Please let me know what works best for you.

Best regards,
{profile.get('name', '')}

---
This is an auto-generated response. Please reply if you need any additional information."""
    
    def _generate_not_interested_response(self, context: AgentContext, contact_name: str, company: str) -> str:
        """Generate professional response to rejection."""
        profile = context.profile
        
        return f"""Hi {contact_name},

Thank you for considering my application and for taking the time to respond.

I appreciate the opportunity to learn about {company} and would welcome the chance to be considered for future openings that match my skills.

Wishing you and the team all the best.

Kind regards,
{profile.get('name', '')}"""
    
    def _generate_question_response(self, context: AgentContext, contact_name: str, 
                                   company: str, body: str) -> str:
        """Generate response for questions using AI."""
        profile = context.profile
        
        # Use AI to draft response to questions
        if self.ai_provider:
            prompt = f"""Draft a professional response to this email:

FROM: {contact_name} at {company}
SUBJECT: Question about application
BODY: {body[:1000]}

MY PROFILE:
Name: {profile.get('name', '')}
Role: Software Engineering Intern
Skills: {', '.join(profile.get('skills', [])[:10])}
Experience: {profile.get('experience_highlights', [''])[0] if profile.get('experience_highlights') else ''}

Draft a helpful, professional response that answers their questions based on the profile information provided.
Keep it concise (2-3 paragraphs) and professional."""
            
            try:
                return self.call_ai(prompt)
            except Exception:
                pass
        
        # Fallback response
        return f"""Hi {contact_name},

Thank you for your email and for the opportunity to provide additional information.

I'd be happy to answer your questions. {profile.get('name', '')} has experience with {', '.join(profile.get('skills', [])[:5])} and would be a strong fit for the role at {company}.

Please let me know if you need any specific details or clarification.

Best regards,
{profile.get('name', '')}"""
    
    def _generate_general_response(self, context: AgentContext, contact_name: str, 
                                  company: str, body: str) -> str:
        """Generate general response."""
        profile = context.profile
        
        return f"""Hi {contact_name},

Thank you for reaching out regarding my application to {company}.

I remain very interested in the opportunity and would welcome any additional information or next steps you can share.

Best regards,
{profile.get('name', '')}"""
    
    def _store_email(self, email_data: Dict, category: str, confidence: float):
        """Store email in thread tracking."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if thread exists
                thread_id = email_data.get("thread_id", email_data.get("message_id", ""))
                
                cursor = conn.execute(
                    "SELECT message_count FROM email_threads WHERE thread_id = ?",
                    (thread_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    # Update existing thread
                    conn.execute(
                        """UPDATE email_threads 
                           SET message_count = message_count + 1,
                               last_activity = ?,
                               category = ?
                           WHERE thread_id = ?""",
                        (datetime.now().isoformat(), category, thread_id)
                    )
                else:
                    # Create new thread
                    conn.execute(
                        """INSERT INTO email_threads 
                           (thread_id, subject, contact_email, contact_name, company, 
                            category, last_activity)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            thread_id,
                            email_data.get("subject", ""),
                            email_data.get("from", ""),
                            self._extract_name(email_data.get("from", "")),
                            self._extract_company(email_data.get("from", ""), email_data.get("body", "")),
                            category,
                            datetime.now().isoformat(),
                        )
                    )
                
                conn.commit()
        except Exception as e:
            self.log("store_email", "warning", f"Failed to store email: {e}")
    
    def _store_pending_response(self, email_data: Dict, category: str, draft: str):
        """Store pending response for review."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO pending_responses 
                       (message_id, thread_id, from_email, subject, body_preview, 
                        category, suggested_response, confidence, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')""",
                    (
                        email_data.get("message_id", ""),
                        email_data.get("thread_id", email_data.get("message_id", "")),
                        email_data.get("from", ""),
                        email_data.get("subject", ""),
                        email_data.get("body", "")[:200],
                        category,
                        draft,
                        0.8,  # Confidence in draft
                    )
                )
                conn.commit()
        except Exception as e:
            self.log("store_pending", "warning", f"Failed to store pending: {e}")
    
    def _get_priority_emails(self, context: AgentContext, params: Dict) -> AgentResponse:
        """Get priority emails that need attention."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get pending responses for important categories
                cursor = conn.execute(
                    """SELECT * FROM pending_responses 
                       WHERE status = 'pending' 
                       AND category IN ('interested', 'interview_request', 'question')
                       ORDER BY created_at DESC
                       LIMIT 20"""
                )
                pending = [dict(row) for row in cursor.fetchall()]
                
                # Get recent threads that need follow-up
                cutoff = (datetime.now() - timedelta(days=3)).isoformat()
                cursor = conn.execute(
                    """SELECT * FROM email_threads 
                       WHERE last_activity < ? 
                       AND status = 'active'
                       AND category IN ('interested', 'interview_request')
                       ORDER BY last_activity ASC
                       LIMIT 10""",
                    (cutoff,)
                )
                needs_followup = [dict(row) for row in cursor.fetchall()]
                
                return AgentResponse(
                    success=True,
                    agent_name=self.name,
                    action_taken="get_priority",
                    result={"pending_responses": pending, "needs_followup": needs_followup},
                    message=f"Found {len(pending)} pending responses, {len(needs_followup)} need follow-up",
                    data={
                        "pending_count": len(pending),
                        "followup_count": len(needs_followup),
                    },
                )
        except Exception as e:
            return AgentResponse(
                success=False,
                agent_name=self.name,
                action_taken="get_priority",
                message=f"Failed to get priority: {e}",
            )
    
    def _archive_completed_threads(self, context: AgentContext, params: Dict) -> AgentResponse:
        """Archive threads that are completed (rejected or no response for long time)."""
        archive_after_days = config.GMAIL_ARCHIVE_AFTER_DAYS
        cutoff = (datetime.now() - timedelta(days=archive_after_days)).isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Mark not_interested as completed
                conn.execute(
                    """UPDATE email_threads 
                       SET status = 'archived'
                       WHERE category = 'not_interested' 
                       AND status = 'active'"""
                )
                
                # Mark old inactive threads as archived
                conn.execute(
                    """UPDATE email_threads 
                       SET status = 'archived'
                       WHERE last_activity < ?
                       AND status = 'active'""",
                    (cutoff,)
                )
                
                conn.commit()
                
                # Count archived
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM email_threads WHERE status = 'archived'"
                )
                archived_count = cursor.fetchone()[0]
                
                return AgentResponse(
                    success=True,
                    agent_name=self.name,
                    action_taken="archive_completed",
                    message=f"Archived {archived_count} threads",
                    data={"archived_count": archived_count},
                )
        except Exception as e:
            return AgentResponse(
                success=False,
                agent_name=self.name,
                action_taken="archive_completed",
                message=f"Archive failed: {e}",
            )
    
    def _extract_name(self, email_str: str) -> str:
        """Extract name from email address."""
        if "<" in email_str:
            name = email_str.split("<")[0].strip()
            return name if name else "Hiring Manager"
        return "Hiring Manager"
    
    def _extract_company(self, email: str, body: str) -> str:
        """Extract company name from email or body."""
        # Try to extract from email domain
        if "@" in email:
            domain = email.split("@")[-1]
            company = domain.split(".")[0]
            if company not in ["gmail", "yahoo", "hotmail", "outlook"]:
                return company.capitalize()
        
        # Try to find in body
        patterns = [
            r"at ([A-Z][a-zA-Z\s]+)\.",
            r"from ([A-Z][a-zA-Z\s]+)\.",
        ]
        for pattern in patterns:
            match = re.search(pattern, body)
            if match:
                return match.group(1).strip()
        
        return "your company"
    
    def _count_by_category(self, processed: List[Dict]) -> Dict[str, int]:
        """Count emails by category."""
        counts = {}
        for item in processed:
            cat = item.get("category", "unknown")
            counts[cat] = counts.get(cat, 0) + 1
        return counts
    
    def get_pending_responses(self) -> List[Dict]:
        """Get all pending responses."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """SELECT * FROM pending_responses 
                       WHERE status = 'pending'
                       ORDER BY created_at DESC"""
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception:
            return []
    
    def approve_response(self, message_id: str, approved: bool = True) -> bool:
        """Mark a response as approved or rejected."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """UPDATE pending_responses 
                       SET status = ?, responded_at = ?
                       WHERE message_id = ?""",
                    ("approved" if approved else "rejected", datetime.now().isoformat(), message_id)
                )
                conn.commit()
                return True
        except Exception:
            return False


# Singleton instance
_gmail_agent: Optional[GmailAgent] = None


def get_gmail_agent() -> GmailAgent:
    """Get singleton Gmail agent instance."""
    global _gmail_agent
    if _gmail_agent is None:
        _gmail_agent = GmailAgent()
    return _gmail_agent
