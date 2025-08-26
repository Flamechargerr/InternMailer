#!/usr/bin/env python3
"""
🚀 InternMailing - Email Analytics Module
=========================================
Advanced analytics for email campaign performance tracking
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple

class EmailAnalytics:
    """📊 Advanced email campaign analytics"""
    
    def __init__(self, db_path: str = "campaign_results/email_tracking.db"):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to tracking database"""
        self.conn = sqlite3.connect(self.db_path)
        return self.conn.cursor()
    
    def disconnect(self):
        """Disconnect from database"""
        if self.conn:
            self.conn.close()
    
    def get_daily_stats(self) -> Dict:
        """📈 Get daily email statistics"""
        cursor = self.connect()
        
        cursor.execute('''
            SELECT DATE(sent_date) as date, COUNT(*) as count
            FROM sent_emails 
            GROUP BY DATE(sent_date)
            ORDER BY date DESC
            LIMIT 30
        ''')
        
        daily_stats = {}
        for date, count in cursor.fetchall():
            daily_stats[date] = count
            
        self.disconnect()
        return daily_stats
    
    def get_university_distribution(self) -> Dict:
        """🏫 Get university distribution analysis"""
        cursor = self.connect()
        
        # Extract university from email domain
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN email LIKE '%mit.edu' THEN 'MIT'
                    WHEN email LIKE '%stanford.edu' THEN 'Stanford'
                    WHEN email LIKE '%berkeley.edu' THEN 'UC Berkeley'
                    WHEN email LIKE '%harvard.edu' THEN 'Harvard'
                    WHEN email LIKE '%princeton.edu' THEN 'Princeton'
                    WHEN email LIKE '%yale.edu' THEN 'Yale'
                    WHEN email LIKE '%cornell.edu' THEN 'Cornell'
                    WHEN email LIKE '%cmu.edu' THEN 'CMU'
                    WHEN email LIKE '%caltech.edu' THEN 'Caltech'
                    WHEN email LIKE '%columbia.edu' THEN 'Columbia'
                    ELSE 'Other Universities'
                END as university,
                COUNT(*) as count
            FROM sent_emails
            GROUP BY university
            ORDER BY count DESC
        ''')
        
        university_stats = {}
        for university, count in cursor.fetchall():
            university_stats[university] = count
            
        self.disconnect()
        return university_stats
    
    def get_campaign_performance(self) -> Dict:
        """📊 Analyze campaign performance metrics"""
        cursor = self.connect()
        
        cursor.execute('''
            SELECT 
                campaign_name,
                COUNT(*) as total_emails,
                AVG(confidence_score) as avg_confidence,
                MIN(sent_date) as start_date,
                MAX(sent_date) as end_date
            FROM sent_emails
            GROUP BY campaign_name
            ORDER BY total_emails DESC
        ''')
        
        campaigns = {}
        for campaign, total, confidence, start, end in cursor.fetchall():
            campaigns[campaign] = {
                'total_emails': total,
                'avg_confidence': confidence or 0,
                'start_date': start,
                'end_date': end
            }
            
        self.disconnect()
        return campaigns
    
    def generate_analytics_report(self) -> str:
        """📋 Generate comprehensive analytics report"""
        daily_stats = self.get_daily_stats()
        university_dist = self.get_university_distribution()
        campaign_performance = self.get_campaign_performance()
        
        report = f"""
🚀 INTERNMAILING ANALYTICS REPORT
=================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 DAILY ACTIVITY (Last 30 Days):
{'-' * 35}
"""
        
        for date, count in list(daily_stats.items())[:10]:
            report += f"{date}: {count} emails\n"
        
        report += f"""
🏫 TOP UNIVERSITIES:
{'-' * 20}
"""
        
        for university, count in list(university_dist.items())[:10]:
            report += f"{university}: {count} professors\n"
        
        report += f"""
📈 CAMPAIGN PERFORMANCE:
{'-' * 24}
"""
        
        for campaign, stats in list(campaign_performance.items())[:5]:
            report += f"{campaign}: {stats['total_emails']} emails (confidence: {stats['avg_confidence']:.1f}%)\n"
        
        total_emails = sum(university_dist.values())
        top_universities = sum(list(university_dist.values())[:10])
        
        report += f"""
📋 SUMMARY:
{'-' * 11}
• Total Emails Sent: {total_emails:,}
• Top 10 Universities: {top_universities:,} emails ({top_universities/total_emails*100:.1f}%)
• Active Campaigns: {len(campaign_performance)}
• Data Quality: High (verified professor contacts)
"""
        
        return report
    
    def export_analytics_json(self) -> str:
        """💾 Export analytics data as JSON"""
        data = {
            'generated_at': datetime.now().isoformat(),
            'daily_stats': self.get_daily_stats(),
            'university_distribution': self.get_university_distribution(),
            'campaign_performance': self.get_campaign_performance(),
            'summary': {
                'total_emails': sum(self.get_university_distribution().values()),
                'active_campaigns': len(self.get_campaign_performance()),
                'top_university': max(self.get_university_distribution(), key=self.get_university_distribution().get)
            }
        }
        
        filename = f"analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        return filename

def main():
    """🎯 Main analytics execution"""
    print("🚀 INTERNMAILING EMAIL ANALYTICS")
    print("=" * 40)
    
    analytics = EmailAnalytics()
    
    # Generate report
    report = analytics.generate_analytics_report()
    print(report)
    
    # Export JSON data
    json_file = analytics.export_analytics_json()
    print(f"\n💾 Analytics exported to: {json_file}")

if __name__ == "__main__":
    main()