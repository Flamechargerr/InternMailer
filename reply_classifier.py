"""
InternMailer - Reply Categorization System
NLP-based email response classification (100% free - no APIs)
"""

import re
from typing import Dict, List, Tuple
from enum import Enum

class ReplyCategory(Enum):
    """Reply categories for auto-actions"""
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    OUT_OF_OFFICE = "out_of_office"
    QUESTION = "question"
    MEETING_REQUEST = "meeting_request"
    ALREADY_HIRED = "already_hired"
    SPAM = "spam"
    REFERRAL = "referral"
    UNKNOWN = "unknown"

class ReplyClassifier:
    """
    Classify email replies using keyword matching and pattern recognition
    No external APIs needed - 100% free
    """
    
    def __init__(self):
        # Keywords for each category (case-insensitive matching)
        self.keywords = {
            ReplyCategory.INTERESTED: [
                'interested', 'im interested', 'interested in', 'sounds good', 'lets talk', 
                'schedule', 'available', 'meet', 'interview', 'discuss', 'discussing this', 'discussing',
                'impressive', 'would like to', 'please send', 'looking forward', 'reaching out',
                'tell me more', 'more information', 'resume looks', 'background looks', 'further'
            ],
            
            ReplyCategory.NOT_INTERESTED: [
                'not interested', 'im not interested', 'but im not', 'not at this time',
                'no thank you', 'not hiring', 'no positions',
                'no openings', 'unfortunately', 'regret to',
                'unable to', 'dont have', 'do not have', 'no vacancy',
                'not a good fit', 'doesnt match', 'does not match',
                'overqualified', 'underqualified', 'different direction'
            ],
            
            ReplyCategory.OUT_OF_OFFICE: [
                'out of office', 'away from', 'on vacation', 'will return',
                'automatic reply', 'auto-reply', 'currently away', 'limited access',
                'on leave', 'back on', 'return on', 'ooo', 'currently unavailable'
            ],
            
            ReplyCategory.QUESTION: [
                'could you', 'could you send', 'can you', 'would you', 'what is your', 'tell me about',
                'do you have', 'are you', 'clarify', 'wondering if', 'question about',
                'more details', 'additional information', 'curious about',
                'send me more', 'more information about', 'about your', 'your background'
            ],
            
            ReplyCategory.MEETING_REQUEST: [
                'can we meet', 'let\'s schedule', 'coffee chat', 'phone call',
                'video call', 'zoom', 'teams meeting', 'calendar', 'availability',
                'free on', 'available on', 'book a time', 'calendly'
            ],
            
            ReplyCategory.ALREADY_HIRED: [
                'already accepted', 'accepted another', 'filled the position',
                'position filled', 'hired someone', 'moving forward with',
                'selected another', 'accepted an offer'
            ],
            
            ReplyCategory.SPAM: [
                'unsubscribe', 'remove me', 'stop emailing', 'do not contact',
                'harassment', 'report spam', 'unsolicited'
            ],
            
            ReplyCategory.REFERRAL: [
                'put you in contact', 'contact my colleague', 'copied here', 'ccing', 
                'ccd', 'cced', 'reach out to', 'refer you to', 'speak with', 'talk to',
                'forwarding this to', 'check with', 'connecting you with',
                'introducing you to', 'copying', 'contact my', 'my student', 
                'my colleague', 'my postdoc'
            ]
        }
        
        # Sentiment indicators
        self.positive_indicators = [
            'great', 'excellent', 'perfect', 'fantastic', 'impressive',
            'strong', 'outstanding', 'amazing', 'wonderful'
        ]
        
        self.negative_indicators = [
            'unfortunately', 'sorry', 'regret', 'unable', 'cannot',
            'wont', 'will not', 'no longer', 'closed'
        ]
    
    def preprocess_text(self, text: str) -> str:
        """Clean and normalize email text"""
        # Convert to lowercase
        text = text.lower()
        # Normalize apostrophes (convert all types to standard apostrophe)
        text = text.replace("'", "'").replace("'", "'").replace("`", "'")
        # Remove apostrophes entirely for matching (I'm -> im, don't -> dont)
        text = text.replace("'", "")
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    def extract_signature_cutoff(self, text: str) -> str:
        """
        Remove email signature to focus on actual reply content
        Common signature markers: "Best regards", "Sincerely", "Sent from"
        """
        signature_markers = [
            'best regards', 'sincerely', 'sent from', 'get outlook', '---', '___', 
            'this email', 'confidential'
        ]
        
        lines = text.split('\n')
        cutoff_index = len(lines)
        
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            for marker in signature_markers:
                if marker in line_lower and i < cutoff_index:
                    cutoff_index = i
                    break
        
        # Return only content before signature
        return '\n'.join(lines[:cutoff_index])
    
    def calculate_sentiment_score(self, text: str) -> float:
        """
        Calculate sentiment score from -1.0 (negative) to 1.0 (positive)
        """
        text_lower = text.lower()
        
        positive_count = sum(1 for word in self.positive_indicators if word in text_lower)
        negative_count = sum(1 for word in self.negative_indicators if word in text_lower)
        
        total = positive_count + negative_count
        if total == 0:
            return 0.0
        
        return (positive_count - negative_count) / total
    
    def classify_reply(self, email_body: str, subject: str = "") -> Dict:
        """
        Classify email reply into categories
        
        Returns:
            {
                'category': ReplyCategory,
                'confidence': float (0.0 to 1.0),
                'sentiment': float (-1.0 to 1.0),
                'matched_keywords': list,
                'suggested_action': str
            }
        """
        # Preprocess
        full_text = f"{subject} {email_body}"
        text = self.preprocess_text(full_text)
        
        # Remove signature for better accuracy
        content = self.extract_signature_cutoff(text)
        
        # Score each category
        category_scores = {}
        matched_keywords = {}
        
        for category, keywords in self.keywords.items():
            score = 0
            matches = []
            for keyword in keywords:
                if keyword in content:
                    score += 1
                    matches.append(keyword)
            
            if score > 0:
                category_scores[category] = score
                matched_keywords[category] = matches
        
        # Determine primary category
        if not category_scores:
            primary_category = ReplyCategory.UNKNOWN
            confidence = 0.0
        else:
            primary_category = max(category_scores, key=category_scores.get)
            max_score = category_scores[primary_category]
            # Confidence based on number of keyword matches
            confidence = min(max_score / 3.0, 1.0)  # Cap at 1.0
        
        # Calculate sentiment
        sentiment = self.calculate_sentiment_score(content)
        
        # Suggest action based on category
        suggested_action = self._get_suggested_action(primary_category, sentiment)
        
        return {
            'category': primary_category,
            'confidence': confidence,
            'sentiment': sentiment,
            'matched_keywords': matched_keywords.get(primary_category, []),
            'suggested_action': suggested_action
        }
    
    def _get_suggested_action(self, category: ReplyCategory, sentiment: float) -> str:
        """Determine suggested action based on category"""
        actions = {
            ReplyCategory.INTERESTED: "🎯 PRIORITY: Move to high-priority queue for immediate response",
            ReplyCategory.NOT_INTERESTED: "📭 UNSUBSCRIBE: Auto-add to unsubscribe list",
            ReplyCategory.OUT_OF_OFFICE: "⏰ RESCHEDULE: Auto-reschedule follow-up for 2 weeks",
            ReplyCategory.QUESTION: "❓ MANUAL REVIEW: Flag for personalized response",
            ReplyCategory.MEETING_REQUEST: "📅 SCHEDULE: Send calendar link or availability",
            ReplyCategory.ALREADY_HIRED: "✅ ARCHIVE: Mark as closed/resolved",
            ReplyCategory.SPAM: "🚫 BLOCK: Add to blacklist immediately",
            ReplyCategory.REFERRAL: "🔄 REFERRAL: Auto-reply to all (including CC)",
            ReplyCategory.UNKNOWN: "👀 MANUAL REVIEW: Needs human classification"
        }
        return actions.get(category, "👀 MANUAL REVIEW: Unknown category")

# Singleton instance
_classifier_instance = None

def get_reply_classifier():
    """Get singleton reply classifier instance"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = ReplyClassifier()
    return _classifier_instance

# Example usage and testing
if __name__ == '__main__':
    classifier = get_reply_classifier()
    
    # Test cases
    test_emails = [
        {
            'subject': 'Re: Research Inquiry',
            'body': '''Hi Anamay,

Thank you for reaching out! Your background looks impressive. I'd be interested in 
discussing potential opportunities. Are you available for a quick call next week?

Best regards,
Dr. Smith'''
        },
        {
            'subject': 'Out of Office',
            'body': '''I am currently out of office and will return on March 15th.
For urgent matters, please contact admin@university.edu.

This is an automatic reply.'''
        },
        {
            'subject': 'Re: Internship Application',
            'body': '''Thank you for your interest, but unfortunately we are not hiring 
at this time. We don't have any openings that match your profile.

Sincerely,
HR Team'''
        },
        {
            'subject': 'Re: Your Email',
            'body': '''Could you send me more information about your projects? 
Also, what is your availability for an internship?

Thanks,
Professor'''
        }
    ]
    
    print("🤖 Reply Classification Test Results:\n")
    for i, email in enumerate(test_emails, 1):
        result = classifier.classify_reply(email['body'], email['subject'])
        
        print(f"📧 Test Email #{i}: {email['subject']}")
        print(f"   Category: {result['category'].value.upper()}")
        print(f"   Confidence: {result['confidence']:.0%}")
        print(f"   Sentiment: {result['sentiment']:+.2f}")
        print(f"   Keywords: {', '.join(result['matched_keywords'][:3])}")
        print(f"   Action: {result['suggested_action']}")
        print()
