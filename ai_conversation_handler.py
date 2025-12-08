"""
InternMailer - Free AI Conversation Handler
Uses Google Gemini (FREE) for intelligent reply generation
No paid APIs - 100% free!
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class FreeAIConversationHandler:
    """
    Uses FREE Google Gemini to handle complex conversations
    - Auto-responds to questions intelligently
    - Generates personalized follow-ups
    - Understands context better than keywords
    """
    
    def __init__(self):
        # Use existing Gemini API key (FREE)
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')  # FREE tier model
        
        # Your background for context
        self.your_background = """
        Name: Anamay Tripathy
        Background: Computer Science student
        Skills: Python, Machine Learning, Full-stack development
        Looking for: Internship/Research opportunities
        Interests: AI, Software Engineering, Data Science
        """
    
    def generate_intelligent_reply(self, original_email: str, their_reply: str) -> str:
        """
        Use FREE Gemini AI to generate smart response
        
        Args:
            original_email: Your original email to them
            their_reply: Their question/response
        
        Returns:
            Intelligent auto-generated reply
        """
        
        prompt = f"""You are Anamay Tripathy, a computer science student looking for internships.

YOUR BACKGROUND:
{self.your_background}

ORIGINAL EMAIL YOU SENT:
{original_email}

THEIR REPLY:
{their_reply}

TASK: Write a professional, concise reply (max 3 paragraphs) that:
1. Answers their specific questions
2. Shows enthusiasm
3. Moves conversation toward interview/meeting
4. Includes a call-to-action

Keep it friendly but professional. Use first person ("I", "my").
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"AI generation failed: {e}")
            return None
    
    def should_auto_respond(self, reply_category: str, confidence: float) -> bool:
        """
        Decide if we should auto-respond with AI
        
        Auto-respond to:
        - QUESTION (if confidence > 0.6)
        - INTERESTED (always)
        - MEETING_REQUEST (always)
        
        Manual review:
        - LOW confidence (<0.6)
        - NOT_INTERESTED
        - SPAM
        """
        auto_respond_categories = ['question', 'interested', 'meeting_request']
        
        if reply_category.lower() in auto_respond_categories:
            if confidence >= 0.6:
                return True
        
        return False
    
    def generate_smart_followup(self, contact_name: str, original_subject: str, days_since: int) -> str:
        """
        Generate personalized follow-up using AI
        Better than generic template
        """
        
        prompt = f"""Generate a brief, professional follow-up email for:

Recipient: {contact_name}
Original subject: {original_subject}
Days since original email: {days_since}

The follow-up should:
1. Be polite and non-pushy
2. Reference the original topic
3. Show continued interest
4. Ask for 15-minute call
5. Be max 4 sentences

Write as if you're Anamay Tripathy (CS student seeking internships).
"""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"AI generation failed: {e}")
            # Fallback to template
            return f"""Hi {contact_name},

Just following up on my previous email about {original_subject}. 
Would you have 15 minutes for a brief call to discuss?

Best,
Anamay"""

# Integration with auto_action_engine
def ai_auto_respond(email: str, reply: str, category: str, confidence: float) -> dict:
    """
    Main function: Decide and generate AI response
    
    Returns:
        {
            'should_respond': bool,
            'response': str or None,
            'method': 'ai' or 'template'
        }
    """
    
    handler = FreeAIConversationHandler()
    
    # Check if we should auto-respond
    if not handler.should_auto_respond(category, confidence):
        return {
            'should_respond': False,
            'response': None,
            'method': 'manual_review'
        }
    
    # Generate AI response
    ai_response = handler.generate_intelligent_reply(email, reply)
    
    if ai_response:
        return {
            'should_respond': True,
            'response': ai_response,
            'method': 'ai_gemini'
        }
    else:
        # Fallback to template
        return {
            'should_respond': True,
            'response': generate_template_response(category),
            'method': 'template_fallback'
        }

def generate_template_response(category: str) -> str:
    """Fallback templates if AI fails"""
    templates = {
        'interested': """Thank you for your interest!

I'd love to discuss this opportunity further. You can schedule a time here: [Calendar Link]

Or let me know your availability and I'll send you some times.

Best regards,
Anamay Tripathy""",
        
        'question': """Thank you for your question!

I'd be happy to provide more details. Would you have 15 minutes for a quick call?

Best regards,
Anamay Tripathy""",
        
        'meeting_request': """I'd be happy to meet!

Here's my availability for this week:
- Monday 2-4 PM
- Wednesday 10 AM - 12 PM
- Friday 1-3 PM

Let me know what works best for you.

Best regards,
Anamay Tripathy"""
    }
    
    return templates.get(category, templates['question'])

# CLI testing
if __name__ == '__main__':
    print("🤖 Testing Free AI Conversation Handler...\n")
    
    handler = FreeAIConversationHandler()
    
    # Test 1: Question response
    test_reply = "Could you tell me more about your machine learning experience?"
    print("Test: Answering technical question")
    response = handler.generate_intelligent_reply("", test_reply)
    print(f"AI Response:\n{response}\n")
    
    # Test 2: Follow-up
    print("Test: Generating smart follow-up")
    followup = handler.generate_smart_followup("Dr. Smith", "Research Internship", 7)
    print(f"AI Follow-up:\n{followup}\n")
    
    print("✅ Free AI working!")
