#!/usr/bin/env python3
"""
📬 InternMailing - Response Tracker
==================================
Track and analyze professor responses to optimize outreach
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum

class ResponseType(Enum):
    """📊 Types of professor responses"""
    POSITIVE = "positive"
    INTERESTED = "interested"
    NOT_AVAILABLE = "not_available"
    NO_RESPONSE = "no_response"
    NEGATIVE = "negative"
    REQUEST_MORE_INFO = "request_more_info"

class ResponseTracker:
    """📬 Track and analyze email responses"""
    
    def __init__(self, db_path: str = "campaign_results/response_tracking.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """🔧 Initialize response tracking database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                professor_email TEXT NOT NULL,
                professor_name TEXT,
                university TEXT,
                response_type TEXT NOT NULL,
                response_date TEXT NOT NULL,
                response_time_hours INTEGER,
                response_content TEXT,
                sentiment_score REAL,
                follow_up_required BOOLEAN DEFAULT 0,
                follow_up_sent BOOLEAN DEFAULT 0,
                meeting_scheduled BOOLEAN DEFAULT 0,
                opportunity_type TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_response(self,
                    professor_email: str,
                    response_type: ResponseType,
                    professor_name: str = "",
                    university: str = "",
                    response_content: str = "",
                    response_time_hours: int = 0,
                    sentiment_score: float = 0.0,
                    opportunity_type: str = "") -> int:
        """📝 Log a professor response"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Determine follow-up requirements
        follow_up_required = response_type in [
            ResponseType.INTERESTED, 
            ResponseType.REQUEST_MORE_INFO,
            ResponseType.POSITIVE
        ]
        
        cursor.execute('''
            INSERT INTO responses 
            (professor_email, professor_name, university, response_type, 
             response_date, response_time_hours, response_content, 
             sentiment_score, follow_up_required, opportunity_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            professor_email, professor_name, university, response_type.value,
            datetime.now().isoformat(), response_time_hours, response_content,
            sentiment_score, follow_up_required, opportunity_type
        ))
        
        response_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return response_id
    
    def get_response_stats(self) -> Dict:
        """📊 Get response statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Overall response rate
        cursor.execute('SELECT COUNT(*) FROM responses')
        total_responses = cursor.fetchone()[0]
        
        # Response type breakdown
        cursor.execute('''
            SELECT response_type, COUNT(*) 
            FROM responses 
            GROUP BY response_type
            ORDER BY COUNT(*) DESC
        ''')
        response_breakdown = dict(cursor.fetchall())
        
        # Average response time
        cursor.execute('''
            SELECT AVG(response_time_hours) 
            FROM responses 
            WHERE response_time_hours > 0
        ''')
        avg_response_time = cursor.fetchone()[0] or 0
        
        # Follow-up required
        cursor.execute('''
            SELECT COUNT(*) FROM responses 
            WHERE follow_up_required = 1 AND follow_up_sent = 0
        ''')
        pending_followups = cursor.fetchone()[0]
        
        # University response rates
        cursor.execute('''
            SELECT university, COUNT(*) 
            FROM responses 
            WHERE university != ""
            GROUP BY university
            ORDER BY COUNT(*) DESC
            LIMIT 10
        ''')
        university_responses = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_responses': total_responses,
            'response_breakdown': response_breakdown,
            'avg_response_time_hours': round(avg_response_time, 2),
            'pending_followups': pending_followups,
            'university_responses': university_responses,
            'response_rate_percent': self._calculate_response_rate()
        }
    
    def _calculate_response_rate(self) -> float:
        """📈 Calculate overall response rate"""
        # This would typically compare against sent emails
        # For now, return a placeholder calculation
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM responses WHERE response_type != "no_response"')
        actual_responses = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM responses')
        total_tracked = cursor.fetchone()[0]
        
        conn.close()
        
        if total_tracked == 0:
            return 0.0
        
        return round((actual_responses / total_tracked) * 100, 2)
    
    def get_pending_followups(self) -> List[Dict]:
        """📋 Get professors requiring follow-up"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT professor_email, professor_name, university, 
                   response_type, response_date, opportunity_type
            FROM responses 
            WHERE follow_up_required = 1 AND follow_up_sent = 0
            ORDER BY response_date ASC
        ''')
        
        followups = []
        for row in cursor.fetchall():
            followups.append({
                'email': row[0],
                'name': row[1],
                'university': row[2],
                'response_type': row[3],
                'response_date': row[4],
                'opportunity_type': row[5]
            })
        
        conn.close()
        return followups
    
    def mark_followup_sent(self, professor_email: str) -> bool:
        """✅ Mark follow-up as sent"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE responses 
            SET follow_up_sent = 1
            WHERE professor_email = ? AND follow_up_required = 1
        ''', (professor_email,))
        
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return updated
    
    def add_sample_responses(self):
        """🎭 Add sample responses for testing"""
        sample_responses = [
            {
                'email': 'dr.smith@mit.edu',
                'name': 'Dr. John Smith',
                'university': 'MIT',
                'type': ResponseType.POSITIVE,
                'hours': 48,
                'content': 'Thank you for your interest. I would be happy to discuss research opportunities.',
                'sentiment': 0.8,
                'opportunity': 'research_position'
            },
            {
                'email': 'prof.johnson@stanford.edu',
                'name': 'Prof. Sarah Johnson',
                'university': 'Stanford',
                'type': ResponseType.REQUEST_MORE_INFO,
                'hours': 72,
                'content': 'Could you send me your CV and research interests?',
                'sentiment': 0.6,
                'opportunity': 'research_position'
            },
            {
                'email': 'dr.wilson@berkeley.edu',
                'name': 'Dr. Michael Wilson',
                'university': 'UC Berkeley',
                'type': ResponseType.NOT_AVAILABLE,
                'hours': 24,
                'content': 'I am not taking new students this semester.',
                'sentiment': 0.3,
                'opportunity': 'none'
            }
        ]
        
        for response in sample_responses:
            self.log_response(
                professor_email=response['email'],
                professor_name=response['name'],
                university=response['university'],
                response_type=response['type'],
                response_content=response['content'],
                response_time_hours=response['hours'],
                sentiment_score=response['sentiment'],
                opportunity_type=response['opportunity']
            )
    
    def generate_response_report(self) -> str:
        """📋 Generate comprehensive response report"""
        stats = self.get_response_stats()
        pending = self.get_pending_followups()
        
        report = f"""
📬 INTERNMAILING RESPONSE TRACKER REPORT
======================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 RESPONSE STATISTICS:
{'-' * 23}
• Total Responses: {stats['total_responses']}
• Response Rate: {stats['response_rate_percent']}%
• Avg Response Time: {stats['avg_response_time_hours']} hours
• Pending Follow-ups: {stats['pending_followups']}

📈 RESPONSE BREAKDOWN:
{'-' * 22}
"""
        
        for response_type, count in stats['response_breakdown'].items():
            percentage = (count / stats['total_responses'] * 100) if stats['total_responses'] > 0 else 0
            report += f"• {response_type.replace('_', ' ').title()}: {count} ({percentage:.1f}%)\n"
        
        report += f"""
🏫 TOP RESPONDING UNIVERSITIES:
{'-' * 31}
"""
        
        for university, count in list(stats['university_responses'].items())[:5]:
            report += f"• {university}: {count} responses\n"
        
        if pending:
            report += f"""
📋 PENDING FOLLOW-UPS ({len(pending)}):
{'-' * 25}
"""
            for followup in pending[:5]:
                report += f"• {followup['name']} ({followup['university']}) - {followup['response_type']}\n"
        
        return report

def demo_response_tracker():
    """🎬 Demonstrate response tracking"""
    print("📬 RESPONSE TRACKER DEMO")
    print("=" * 30)
    
    tracker = ResponseTracker()
    
    # Add sample data
    tracker.add_sample_responses()
    
    # Generate report
    report = tracker.generate_response_report()
    print(report)
    
    # Show pending follow-ups
    pending = tracker.get_pending_followups()
    print(f"\n📋 You have {len(pending)} pending follow-ups!")

if __name__ == "__main__":
    demo_response_tracker()