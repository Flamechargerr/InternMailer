"""
📧 Email Reply Agent - Intelligent Email Response Drafting
==========================================================
Handles all types of email replies intelligently.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.agents.base_agent import BaseAgent, AgentContext, AgentResponse
from utils.config import config


# Response templates for different categories
RESPONSE_TEMPLATES = {
    "interested": {
        "tone": "enthusiastic",
        "include_calendar": True,
        "template": """Thank you so much for your response! I'm thrilled about the opportunity to discuss the {role} position further.

I'd love to schedule a call at your convenience. Please feel free to pick a time that works for you: {calendar_link}

Alternatively, I'm available {availability}. Please let me know what works best for you.

Looking forward to speaking with you!""",
    },
    "question": {
        "tone": "helpful",
        "include_calendar": False,
        "needs_ai": True,  # AI should generate response to the specific question
    },
    "not_interested": {
        "tone": "gracious",
        "template": """Thank you for taking the time to respond and for your consideration.

I appreciate you letting me know. If any suitable opportunities arise in the future, I would be grateful to be considered.

Wishing you and the team continued success!""",
    },
    "out_of_office": {
        "tone": "patient",
        "action": "schedule_followup",
        "days_delay": 14,
    },
    "interview_request": {
        "tone": "enthusiastic",
        "include_calendar": True,
        "template": """Thank you for the opportunity! I'm very excited to move forward with the interview process.

{availability_confirmation}

Please let me know if you need any additional information from my end. I look forward to our conversation!""",
    },
}


class EmailReplyAgent(BaseAgent):
    """
    Specialized agent for handling email replies.
    
    Capabilities:
    - Draft responses based on email category
    - Answer questions intelligently using AI
    - Handle interview scheduling
    - Graceful rejection responses
    - Follow-up scheduling
    """
    
    def __init__(self):
        super().__init__("EmailReply")
    
    def run(self, context: AgentContext, **kwargs) -> AgentResponse:
        """
        Process email replies and draft responses.
        
        Kwargs:
            category: Email category to process ('interested', 'question', etc.)
            email_id: Specific email ID to process
            auto_send: Whether to auto-send responses (default: False)
        """
        category = kwargs.get("category")
        email_id = kwargs.get("email_id")
        auto_send = kwargs.get("auto_send", False)
        
        # Get pending emails to process
        emails = self._get_pending_emails(category, email_id)
        
        if not emails:
            return AgentResponse(
                success=True,
                agent_name=self.name,
                action_taken="process_replies",
                message="No emails to process",
                data={"processed": 0},
            )
        
        self.log("process_replies", "info", f"Processing {len(emails)} emails")
        
        profile = context.profile
        results = []
        
        for email in emails:
            result = self._process_email(email, profile, auto_send)
            results.append(result)
        
        successful = sum(1 for r in results if r.get("success"))
        
        return AgentResponse(
            success=True,
            agent_name=self.name,
            action_taken="process_replies",
            result=results,
            message=f"Processed {successful}/{len(emails)} emails",
            data={
                "processed": len(emails),
                "successful": successful,
                "drafts_created": sum(1 for r in results if r.get("draft_created")),
            },
        )
    
    def _get_pending_emails(self, category: Optional[str], email_id: Optional[str]) -> List[Dict]:
        """Get pending emails to process."""
        try:
            with sqlite3.connect(config.INBOX_DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                
                if email_id:
                    cursor = conn.execute(
                        "SELECT * FROM processed_replies WHERE message_id = ?",
                        (email_id,),
                    )
                elif category:
                    cursor = conn.execute(
                        """
                        SELECT * FROM processed_replies 
                        WHERE category = ? AND action_taken = 'pending'
                        ORDER BY received_date DESC
                        """,
                        (category,),
                    )
                else:
                    cursor = conn.execute(
                        """
                        SELECT * FROM processed_replies 
                        WHERE action_taken = 'pending'
                        ORDER BY received_date DESC
                        LIMIT 20
                        """
                    )
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.log("get_emails", "error", f"Failed to get emails: {e}")
            return []
    
    def _process_email(self, email: Dict, profile: Dict, auto_send: bool) -> Dict:
        """Process a single email and draft response."""
        category = email.get("category", "").lower()
        email_address = email.get("from_email", "")
        subject = email.get("subject", "")
        
        result = {
            "email_id": email.get("message_id"),
            "category": category,
            "from": email_address,
            "success": False,
            "draft_created": False,
        }
        
        # Get template configuration
        template_config = RESPONSE_TEMPLATES.get(category, {})
        
        # Generate response
        if category == "question" or template_config.get("needs_ai"):
            # Use AI for questions
            response_text = self._generate_ai_response(email, profile)
        elif category == "interested":
            response_text = self._generate_interested_response(email, profile)
        elif category == "interview_request":
            response_text = self._generate_interview_response(email, profile)
        elif category == "not_interested":
            response_text = template_config.get("template", "Thank you for your response.")
        elif category == "out_of_office":
            # Schedule follow-up, don't respond
            self._schedule_followup(email, template_config.get("days_delay", 14))
            result["action"] = "followup_scheduled"
            result["success"] = True
            return result
        else:
            # Generic AI response
            response_text = self._generate_ai_response(email, profile)
        
        if response_text:
            # Create draft or send
            if auto_send:
                sent = self._send_response(email_address, subject, response_text)
                result["sent"] = sent
                result["success"] = sent
            else:
                draft_created = self._create_draft(email, response_text, profile)
                result["draft_created"] = draft_created
                result["response_preview"] = response_text[:200]
                result["success"] = draft_created
            
            # Update email status
            self._update_email_status(email.get("message_id"), "responded" if auto_send else "draft_created")
        
        return result
    
    def _generate_interested_response(self, email: Dict, profile: Dict) -> str:
        """Generate response for interested replies."""
        calendar_link = profile.get("calendar_link") or config.CALENDAR_LINK
        name = profile.get("name", "")
        
        template = RESPONSE_TEMPLATES["interested"]["template"]
        
        # Try to extract role from email subject
        subject = email.get("subject", "")
        role = "the position"
        if "intern" in subject.lower():
            role = "the internship"
        elif "engineer" in subject.lower():
            role = "the engineering role"
        
        availability = "Monday through Friday, 9 AM - 6 PM IST"
        
        response = template.format(
            role=role,
            calendar_link=calendar_link or "[Calendar link]",
            availability=availability,
        )
        
        if name:
            response += f"\n\nBest regards,\n{name}"
        
        return response
    
    def _generate_interview_response(self, email: Dict, profile: Dict) -> str:
        """Generate response for interview requests."""
        calendar_link = profile.get("calendar_link") or config.CALENDAR_LINK
        name = profile.get("name", "")
        
        # Extract proposed times if any
        body = email.get("body", "")
        
        availability_confirmation = ""
        if calendar_link:
            availability_confirmation = f"Here's my calendar for easy scheduling: {calendar_link}"
        else:
            availability_confirmation = "I am available Monday through Friday, 9 AM - 6 PM IST. Please let me know what time works best for you."
        
        template = RESPONSE_TEMPLATES["interview_request"]["template"]
        response = template.format(availability_confirmation=availability_confirmation)
        
        if name:
            response += f"\n\nBest regards,\n{name}"
        
        return response
    
    def _generate_ai_response(self, email: Dict, profile: Dict) -> str:
        """Generate AI-powered response for questions or generic emails."""
        if not self.ai_provider:
            return self._generate_fallback_response(email, profile)
        
        sender = email.get("from_email", "")
        subject = email.get("subject", "")
        body = email.get("body", "")[:2000]
        category = email.get("category", "")
        
        name = profile.get("name", "Candidate")
        skills = profile.get("skills", [])
        if isinstance(skills, dict):
            skills = [s for cat in skills.values() for s in (cat if isinstance(cat, list) else [])]
        
        experience = profile.get("experience_highlights", [])
        calendar_link = profile.get("calendar_link") or config.CALENDAR_LINK
        
        prompt = f"""Draft a professional email response.

RECEIVED EMAIL:
From: {sender}
Subject: {subject}
Category: {category}
Body:
{body}

MY PROFILE:
Name: {name}
Key Skills: {', '.join(skills[:10]) if skills else 'N/A'}
Experience: {'; '.join(experience[:2]) if experience else 'N/A'}
Calendar Link: {calendar_link or 'N/A'}

REQUIREMENTS:
- Be professional but personable
- If they asked a question, answer it directly using only info from my profile
- If they're interested, express enthusiasm and suggest next steps
- Keep response concise (3-5 sentences max for simple replies)
- If relevant, mention my calendar link for scheduling
- Do NOT make up facts about my background

Write only the email body (no subject line, greeting, or signature - those will be added):"""

        try:
            response = self.call_ai(prompt)
            
            # Add greeting and signature
            greeting = "Thank you for reaching out!\n\n"
            signature = f"\n\nBest regards,\n{name}"
            
            return greeting + response.strip() + signature
        except Exception as e:
            self.log("ai_response", "error", f"AI generation failed: {e}")
            return self._generate_fallback_response(email, profile)
    
    def _generate_fallback_response(self, email: Dict, profile: Dict) -> str:
        """Generate fallback response when AI is unavailable."""
        name = profile.get("name", "")
        calendar_link = profile.get("calendar_link") or config.CALENDAR_LINK
        
        response = """Thank you for your email! I appreciate you taking the time to reach out.

I'd be happy to discuss this further. """
        
        if calendar_link:
            response += f"Feel free to schedule a time that works for you: {calendar_link}"
        else:
            response += "Please let me know a convenient time to connect."
        
        if name:
            response += f"\n\nBest regards,\n{name}"
        
        return response
    
    def _create_draft(self, email: Dict, response_text: str, profile: Dict) -> bool:
        """Create email draft in Gmail."""
        try:
            # For now, save to database for review
            # In production, would use Gmail API to create actual drafts
            with sqlite3.connect(config.INBOX_DB_PATH) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS email_drafts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        original_message_id TEXT,
                        to_email TEXT,
                        subject TEXT,
                        body TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        sent BOOLEAN DEFAULT 0
                    )
                """)
                
                to_email = email.get("from_email", "")
                subject = email.get("subject", "")
                if not subject.lower().startswith("re:"):
                    subject = f"Re: {subject}"
                
                conn.execute(
                    """
                    INSERT INTO email_drafts (original_message_id, to_email, subject, body)
                    VALUES (?, ?, ?, ?)
                    """,
                    (email.get("message_id"), to_email, subject, response_text),
                )
                conn.commit()
            
            return True
        except Exception as e:
            self.log("create_draft", "error", f"Failed to create draft: {e}")
            return False
    
    def _send_response(self, to_email: str, subject: str, body: str) -> bool:
        """Send the response email."""
        try:
            from core.email_system import get_email_system
            
            if not subject.lower().startswith("re:"):
                subject = f"Re: {subject}"
            
            system = get_email_system()
            return system.send_single_email(
                to_email=to_email,
                subject=subject,
                html_body=f"<html><body><p>{body.replace(chr(10), '</p><p>')}</p></body></html>",
            )
        except Exception as e:
            self.log("send_response", "error", f"Failed to send: {e}")
            return False
    
    def _schedule_followup(self, email: Dict, days_delay: int) -> None:
        """Schedule a follow-up for OOO replies."""
        try:
            from datetime import timedelta
            
            with sqlite3.connect(config.INBOX_DB_PATH) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS followup_queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT,
                        original_subject TEXT,
                        scheduled_date TEXT,
                        sent BOOLEAN DEFAULT 0,
                        message_id TEXT
                    )
                """)
                
                followup_date = (datetime.now() + timedelta(days=days_delay)).isoformat()
                
                conn.execute(
                    """
                    INSERT INTO followup_queue (email, original_subject, scheduled_date, message_id)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        email.get("from_email"),
                        email.get("subject"),
                        followup_date,
                        email.get("message_id"),
                    ),
                )
                conn.commit()
        except Exception as e:
            self.log("schedule_followup", "error", f"Failed to schedule: {e}")
    
    def _update_email_status(self, message_id: str, status: str) -> None:
        """Update email processing status."""
        try:
            with sqlite3.connect(config.INBOX_DB_PATH) as conn:
                conn.execute(
                    "UPDATE processed_replies SET action_taken = ? WHERE message_id = ?",
                    (status, message_id),
                )
                conn.commit()
        except Exception as e:
            self.log("update_status", "error", f"Failed to update: {e}")
    
    def get_pending_drafts(self) -> List[Dict]:
        """Get all pending drafts for review."""
        try:
            with sqlite3.connect(config.INBOX_DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM email_drafts WHERE sent = 0 ORDER BY created_at DESC"
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.log("get_drafts", "error", f"Failed: {e}")
            return []
