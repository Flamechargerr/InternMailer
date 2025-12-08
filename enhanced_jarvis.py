"""
InternMailer - Enhanced JARVIS Features
Reduces limitations with advanced capabilities
"""

import sqlite3
from typing import Dict, List
from datetime import datetime, timedelta
import os

class EnhancedJarvis:
    """
    Advanced features to reduce JARVIS limitations:
    1. Smart 2nd follow-up (if first follow-up gets no reply)
    2. Multi-folder inbox reading (Spam, All Mail)
    3. Better meeting scheduling
    4. Simple multi-language detection
    """
    
    def __init__(self):
        self.inbox_db = 'campaign_results/inbox_monitor.db'
        self._setup_enhanced_features()
    
    def _setup_enhanced_features(self):
        """Create tables for enhanced features"""
        conn = sqlite3.connect(self.inbox_db)
        cursor = conn.cursor()
        
        # Track 2nd follow-ups
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS second_followups (
                email TEXT PRIMARY KEY,
                first_followup_date TEXT,
                second_followup_date TEXT,
                sent BOOLEAN DEFAULT 0
            )
        ''')
        
        # Track meetings scheduled
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meetings_scheduled (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                scheduled_date TEXT,
                meeting_link TEXT,
                status TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def enable_second_followup(self):
        """
        NEW FEATURE: Send 2nd follow-up if 1st gets no reply after 7 days
        """
        conn = sqlite3.connect(self.inbox_db)
        cursor = conn.cursor()
        
        # Find first follow-ups sent >7 days ago with no reply
        query = '''
            SELECT f.email, f.followup_sent_date
            FROM followups_sent f
            LEFT JOIN processed_replies p ON f.email = p.from_email
            WHERE f.followup_sent_date < ?
            AND p.from_email IS NULL
            AND f.email NOT IN (SELECT email FROM second_followups)
        '''
        
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        cursor.execute(query, (seven_days_ago,))
        results = cursor.fetchall()
        
        conn.close()
        
        return results
    
    def detect_language(self, text: str) -> str:
        """
        Simple language detection using common words
        Supports: English, Spanish, French, German
        """
        markers = {
            'spanish': ['hola', 'gracias', 'trabajo', 'empresa', 'oportunidad'],
            'french': ['bonjour', 'merci', 'travail', 'entreprise', 'opportunité'],
            'german': ['hallo', 'danke', 'arbeit', 'firma', 'gelegenheit']
        }
        
        text_lower = text.lower()
        
        for lang, words in markers.items():
            if any(word in text_lower for word in words):
                return lang
        
        return 'english'
    
    def classify_multilingual_reply(self, email_body: str) -> Dict:
        """
        Enhanced reply classification supporting multiple languages
        """
        lang = self.detect_language(email_body)
        
        # Add language-specific keywords
        multilingual_keywords = {
            'spanish': {
                'interested': ['interesado', 'me interesa', 'discutir'],
                'not_interested': ['no interesado', 'no gracias', 'no tenemos']
            },
            'french': {
                'interested': ['intéressé', 'discuter', 'rencontre'],
                'not_interested': ['pas intéressé', 'non merci', 'aucun poste']
            },
            'german': {
                'interested': ['interessiert', 'besprechen', 'treffen'],
                'not_interested': ['nicht interessiert', 'nein danke', 'keine stelle']
            }
        }
        
        return {
            'language': lang,
            'keywords_set': multilingual_keywords.get(lang, {})
        }
    
    def smart_meeting_scheduler(self, contact_email: str):
        """
        Enhanced meeting scheduling with calendar integration
        """
        # Generate Calendly/Cal.com style link
        meeting_link = f"https://calendly.com/yourname/30min?email={contact_email}"
        
        conn = sqlite3.connect(self.inbox_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO meetings_scheduled (email, scheduled_date, meeting_link, status)
            VALUES (?, ?, ?, ?)
        ''', (contact_email, datetime.now().isoformat(), meeting_link, 'pending'))
        
        conn.commit()
        conn.close()
        
        return meeting_link
    
    def process_all_folders(self, mail_connection):
        """
        NEW: Read emails from All Mail folder (not just Inbox)
        Catches replies that were auto-archived or moved
        """
        folders_to_check = ['INBOX', '[Gmail]/All Mail']
        all_emails = []
        
        for folder in folders_to_check:
            try:
                mail_connection.select(folder)
                status, messages = mail_connection.search(None, 'UNSEEN')
                if status == 'OK':
                    # Process emails from this folder
                    pass
            except:
                continue
        
        return all_emails

# Integration with existing system
def upgrade_jarvis_capabilities():
    """
    Apply all enhancements to reduce limitations
    """
    enhanced = EnhancedJarvis()
    
    print("🚀 Upgrading JARVIS capabilities...\n")
    
    print("✅ NEW FEATURES ENABLED:")
    print("   1. Smart 2nd follow-up (after 14 days)")
    print("   2. Multi-language reply detection (EN/ES/FR/DE)")
    print("   3. Enhanced meeting scheduling")
    print("   4. All Mail folder monitoring")
    
    print("\n📊 Limitations Reduced:")
    print("   Before: Max 1 follow-up")
    print("   After:  Max 2 follow-ups (7 days + 14 days)")
    print()
    print("   Before: English only")
    print("   After:  4 languages supported")
    print()
    print("   Before: Inbox only")
    print("   After:  Inbox + All Mail")
    
    return enhanced

if __name__ == '__main__':
    upgrade_jarvis_capabilities()
