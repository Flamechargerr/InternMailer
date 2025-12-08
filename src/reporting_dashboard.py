"""
Reporting Dashboard for InternMailer
Generates comprehensive reports and analytics for internship applications
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sqlite3
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from dataclasses import dataclass

@dataclass
class ReportMetrics:
    total_applications: int
    response_rate: float
    interview_rate: float
    offer_rate: float
    rejection_rate: float
    tier_distribution: Dict[str, int]
    top_companies: List[Dict]
    application_timeline: List[Dict]

class ReportingDashboard:
    def __init__(self, db_path: str = "data/internmailer.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Create reports directory
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
        
        # Set up plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def generate_daily_report(self, date: str = None) -> Dict:
        """
        Generate daily application report in JSON format
        
        Args:
            date: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Daily report in canonical JSON format
        """
        if not date:
            date = datetime.now().date().isoformat()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get applications for the day
            cursor.execute("""
                SELECT id, job_title, company, location, apply_link, 
                       prestige_tier, prestige_score, match_score, status,
                       created_at
                FROM applications
                WHERE DATE(created_at) = ?
                ORDER BY prestige_score DESC, match_score DESC
            """, (date,))
            
            applications = []
            for row in cursor.fetchall():
                applications.append({
                    'application_id': row[0],
                    'job_title': row[1],
                    'company': row[2],
                    'location': row[3],
                    'apply_link': row[4],
                    'prestige_tier': row[5],
                    'prestige_score': row[6],
                    'match_score': row[7],
                    'status': row[8],
                    'created_at': row[9]
                })
            
            # Get contact information for applications
            opportunities_ranked = []
            for app in applications:
                cursor.execute("""
                    SELECT email FROM contacts 
                    WHERE company = ? 
                    ORDER BY email_confidence DESC 
                    LIMIT 1
                """, (app['company'],))
                
                contact_result = cursor.fetchone()
                contact_email = contact_result[0] if contact_result else ""
                
                opportunities_ranked.append({
                    'job_title': app['job_title'],
                    'company': app['company'],
                    'location': app['location'],
                    'apply_link': app['apply_link'],
                    'contact_email': contact_email,
                    'match_score': app['match_score'],
                    'prestige_tier': app['prestige_tier'],
                    'prestige_score': app['prestige_score']
                })
            
            # Calculate summary statistics
            total_found = len(applications)
            shortlisted = len([app for app in applications if app['match_score'] >= 0.65])
            auto_applied = 0  # No auto-application in this system
            manual_required = shortlisted
            
            # Count by tiers
            tier_counts = {'Tier 1': 0, 'Tier 2': 0, 'Tier 3': 0}
            for app in applications:
                tier = app.get('prestige_tier', 'Unknown')
                if tier in tier_counts:
                    tier_counts[tier] += 1
            
            # Get application logs
            cursor.execute("""
                SELECT application_id, status, timestamp, notes, source
                FROM application_status_history
                WHERE DATE(timestamp) = ?
                ORDER BY timestamp DESC
            """, (date,))
            
            application_logs = []
            for row in cursor.fetchall():
                application_logs.append({
                    'application_id': row[0],
                    'timestamp': row[2],
                    'action': 'status_update',
                    'status': row[1],
                    'notes': row[3],
                    'source': row[4]
                })
            
            # Get application materials
            materials = []
            for app in applications:
                cursor.execute("""
                    SELECT resume_content, cover_letter_content
                    FROM application_materials
                    WHERE application_id = ?
                """, (app['application_id'],))
                
                material_result = cursor.fetchone()
                if material_result:
                    materials.append({
                        'application_id': app['application_id'],
                        'resume_content': material_result[0],
                        'cover_letter_content': material_result[1]
                    })
            
            conn.close()
            
            # Create daily report
            daily_report = {
                'date': date,
                'summary': {
                    'total_found': total_found,
                    'shortlisted': shortlisted,
                    'auto_applied': auto_applied,
                    'manual_required': manual_required,
                    'tiers': tier_counts
                },
                'opportunities_ranked': opportunities_ranked,
                'application_logs': application_logs,
                'materials': materials
            }
            
            return daily_report
            
        except Exception as e:
            self.logger.error(f"Error generating daily report: {e}")
            return {}
    
    def generate_weekly_report(self, end_date: str = None) -> Dict:
        """Generate weekly summary report"""
        if not end_date:
            end_date = datetime.now().date().isoformat()
        
        start_date = (datetime.fromisoformat(end_date) - timedelta(days=7)).date().isoformat()
        
        return self._generate_period_report(start_date, end_date, "weekly")
    
    def generate_monthly_report(self, month: str = None) -> Dict:
        """Generate monthly summary report"""
        if not month:
            now = datetime.now()
            start_date = now.replace(day=1).date().isoformat()
            end_date = now.date().isoformat()
        else:
            # Parse month in YYYY-MM format
            year, month_num = month.split('-')
            start_date = f"{year}-{month_num}-01"
            # Calculate last day of month
            if month_num == '12':
                next_month = f"{int(year)+1}-01-01"
            else:
                next_month = f"{year}-{int(month_num)+1:02d}-01"
            end_date = (datetime.fromisoformat(next_month) - timedelta(days=1)).date().isoformat()
        
        return self._generate_period_report(start_date, end_date, "monthly")
    
    def _generate_period_report(self, start_date: str, end_date: str, period_type: str) -> Dict:
        """Generate report for a specific period"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get applications in period
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN prestige_tier = 'Tier 1' THEN 1 ELSE 0 END) as tier1,
                       SUM(CASE WHEN prestige_tier = 'Tier 2' THEN 1 ELSE 0 END) as tier2,
                       SUM(CASE WHEN prestige_tier = 'Tier 3' THEN 1 ELSE 0 END) as tier3,
                       AVG(match_score) as avg_match_score,
                       AVG(prestige_score) as avg_prestige_score
                FROM applications
                WHERE DATE(created_at) BETWEEN ? AND ?
            """, (start_date, end_date))
            
            stats = cursor.fetchone()
            
            # Get status distribution
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM applications
                WHERE DATE(created_at) BETWEEN ? AND ?
                GROUP BY status
            """, (start_date, end_date))
            
            status_distribution = dict(cursor.fetchall())
            
            # Get top companies
            cursor.execute("""
                SELECT company, COUNT(*) as applications,
                       AVG(match_score) as avg_match,
                       MAX(prestige_score) as max_prestige
                FROM applications
                WHERE DATE(created_at) BETWEEN ? AND ?
                GROUP BY company
                ORDER BY applications DESC, max_prestige DESC
                LIMIT 10
            """, (start_date, end_date))
            
            top_companies = []
            for row in cursor.fetchall():
                top_companies.append({
                    'company': row[0],
                    'applications': row[1],
                    'avg_match_score': round(row[2], 2) if row[2] else 0,
                    'max_prestige_score': row[3] if row[3] else 0
                })
            
            # Calculate rates
            total_apps = stats[0] if stats[0] else 0
            responses = status_distribution.get('under_review', 0) + \
                       status_distribution.get('interview_scheduled', 0) + \
                       status_distribution.get('interview_completed', 0) + \
                       status_distribution.get('offer_received', 0) + \
                       status_distribution.get('rejected', 0)
            
            response_rate = (responses / total_apps * 100) if total_apps > 0 else 0
            interview_rate = ((status_distribution.get('interview_scheduled', 0) + 
                             status_distribution.get('interview_completed', 0)) / total_apps * 100) if total_apps > 0 else 0
            offer_rate = (status_distribution.get('offer_received', 0) / total_apps * 100) if total_apps > 0 else 0
            rejection_rate = (status_distribution.get('rejected', 0) / total_apps * 100) if total_apps > 0 else 0
            
            conn.close()
            
            return {
                'period': {
                    'type': period_type,
                    'start_date': start_date,
                    'end_date': end_date
                },
                'summary': {
                    'total_applications': total_apps,
                    'tier_distribution': {
                        'Tier 1': stats[1] if stats[1] else 0,
                        'Tier 2': stats[2] if stats[2] else 0,
                        'Tier 3': stats[3] if stats[3] else 0
                    },
                    'average_scores': {
                        'match_score': round(stats[4], 2) if stats[4] else 0,
                        'prestige_score': round(stats[5], 2) if stats[5] else 0
                    }
                },
                'performance': {
                    'response_rate': round(response_rate, 2),
                    'interview_rate': round(interview_rate, 2),
                    'offer_rate': round(offer_rate, 2),
                    'rejection_rate': round(rejection_rate, 2)
                },
                'status_distribution': status_distribution,
                'top_companies': top_companies
            }
            
        except Exception as e:
            self.logger.error(f"Error generating {period_type} report: {e}")
            return {}
    
    def generate_analytics_dashboard(self, output_path: str = None) -> str:
        """Generate visual analytics dashboard"""
        try:
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = self.reports_dir / f"analytics_dashboard_{timestamp}.png"
            
            # Get data for last 30 days
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            conn = sqlite3.connect(self.db_path)
            
            # Create subplots
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('InternMailer Analytics Dashboard', fontsize=16, fontweight='bold')
            
            # 1. Applications by Prestige Tier
            tier_data = pd.read_sql_query("""
                SELECT prestige_tier, COUNT(*) as count
                FROM applications
                WHERE DATE(created_at) >= ?
                GROUP BY prestige_tier
            """, conn, params=(start_date,))
            
            if not tier_data.empty:
                colors = ['#e74c3c', '#f39c12', '#27ae60', '#95a5a6']
                ax1.pie(tier_data['count'], labels=tier_data['prestige_tier'], 
                       autopct='%1.1f%%', colors=colors)
                ax1.set_title('Applications by Prestige Tier')
            
            # 2. Application Status Distribution
            status_data = pd.read_sql_query("""
                SELECT status, COUNT(*) as count
                FROM applications
                WHERE DATE(created_at) >= ?
                GROUP BY status
            """, conn, params=(start_date,))
            
            if not status_data.empty:
                ax2.bar(status_data['status'], status_data['count'])
                ax2.set_title('Application Status Distribution')
                ax2.tick_params(axis='x', rotation=45)
            
            # 3. Applications Timeline
            timeline_data = pd.read_sql_query("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM applications
                WHERE DATE(created_at) >= ?
                GROUP BY DATE(created_at)
                ORDER BY date
            """, conn, params=(start_date,))
            
            if not timeline_data.empty:
                timeline_data['date'] = pd.to_datetime(timeline_data['date'])
                ax3.plot(timeline_data['date'], timeline_data['count'], marker='o')
                ax3.set_title('Applications Over Time')
                ax3.tick_params(axis='x', rotation=45)
            
            # 4. Match Score vs Prestige Score
            scatter_data = pd.read_sql_query("""
                SELECT match_score, prestige_score, prestige_tier
                FROM applications
                WHERE DATE(created_at) >= ?
                AND match_score IS NOT NULL 
                AND prestige_score IS NOT NULL
            """, conn, params=(start_date,))
            
            if not scatter_data.empty:
                tier_colors = {'Tier 1': '#e74c3c', 'Tier 2': '#f39c12', 'Tier 3': '#27ae60'}
                for tier in scatter_data['prestige_tier'].unique():
                    tier_data = scatter_data[scatter_data['prestige_tier'] == tier]
                    ax4.scatter(tier_data['match_score'], tier_data['prestige_score'], 
                              label=tier, color=tier_colors.get(tier, '#95a5a6'), alpha=0.7)
                ax4.set_xlabel('Match Score')
                ax4.set_ylabel('Prestige Score')
                ax4.set_title('Match Score vs Prestige Score')
                ax4.legend()
            
            conn.close()
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.logger.info(f"Analytics dashboard saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Error generating analytics dashboard: {e}")
            return ""
    
    def export_applications_csv(self, output_path: str = None) -> str:
        """Export all applications to CSV"""
        try:
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = self.reports_dir / f"applications_export_{timestamp}.csv"
            
            conn = sqlite3.connect(self.db_path)
            
            # Get all applications with details
            df = pd.read_sql_query("""
                SELECT a.id, a.job_title, a.company, a.location, a.duration,
                       a.apply_link, a.description, a.eligibility, a.posted_date,
                       a.deadline, a.source, a.prestige_tier, a.prestige_score,
                       a.match_score, a.status, a.created_at, a.updated_at
                FROM applications a
                ORDER BY a.created_at DESC
            """, conn)
            
            conn.close()
            
            # Export to CSV
            df.to_csv(output_path, index=False)
            
            self.logger.info(f"Applications exported to CSV: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Error exporting applications to CSV: {e}")
            return ""
    
    def get_performance_metrics(self, days: int = 30) -> ReportMetrics:
        """Get performance metrics for the last N days"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get basic metrics
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN status IN ('under_review', 'interview_scheduled', 
                                               'interview_completed', 'offer_received', 'rejected') 
                           THEN 1 ELSE 0 END) as responses,
                       SUM(CASE WHEN status IN ('interview_scheduled', 'interview_completed') 
                           THEN 1 ELSE 0 END) as interviews,
                       SUM(CASE WHEN status = 'offer_received' THEN 1 ELSE 0 END) as offers,
                       SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejections
                FROM applications
                WHERE DATE(created_at) >= ?
            """, (start_date,))
            
            metrics = cursor.fetchone()
            total_apps = metrics[0] if metrics[0] else 0
            
            # Calculate rates
            response_rate = (metrics[1] / total_apps * 100) if total_apps > 0 else 0
            interview_rate = (metrics[2] / total_apps * 100) if total_apps > 0 else 0
            offer_rate = (metrics[3] / total_apps * 100) if total_apps > 0 else 0
            rejection_rate = (metrics[4] / total_apps * 100) if total_apps > 0 else 0
            
            # Get tier distribution
            cursor.execute("""
                SELECT prestige_tier, COUNT(*) as count
                FROM applications
                WHERE DATE(created_at) >= ?
                GROUP BY prestige_tier
            """, (start_date,))
            
            tier_distribution = dict(cursor.fetchall())
            
            # Get top companies
            cursor.execute("""
                SELECT company, COUNT(*) as count, AVG(match_score) as avg_match
                FROM applications
                WHERE DATE(created_at) >= ?
                GROUP BY company
                ORDER BY count DESC, avg_match DESC
                LIMIT 5
            """, (start_date,))
            
            top_companies = []
            for row in cursor.fetchall():
                top_companies.append({
                    'company': row[0],
                    'applications': row[1],
                    'avg_match_score': round(row[2], 2) if row[2] else 0
                })
            
            # Get application timeline
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM applications
                WHERE DATE(created_at) >= ?
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (start_date,))
            
            application_timeline = []
            for row in cursor.fetchall():
                application_timeline.append({
                    'date': row[0],
                    'applications': row[1]
                })
            
            conn.close()
            
            return ReportMetrics(
                total_applications=total_apps,
                response_rate=round(response_rate, 2),
                interview_rate=round(interview_rate, 2),
                offer_rate=round(offer_rate, 2),
                rejection_rate=round(rejection_rate, 2),
                tier_distribution=tier_distribution,
                top_companies=top_companies,
                application_timeline=application_timeline
            )
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return ReportMetrics(0, 0, 0, 0, 0, {}, [], [])
    
    def generate_comprehensive_report(self, output_path: str = None) -> str:
        """Generate comprehensive JSON report with all metrics"""
        try:
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = self.reports_dir / f"comprehensive_report_{timestamp}.json"
            
            # Get metrics for different periods
            metrics_7d = self.get_performance_metrics(7)
            metrics_30d = self.get_performance_metrics(30)
            metrics_90d = self.get_performance_metrics(90)
            
            # Generate daily report for today
            daily_report = self.generate_daily_report()
            
            # Generate weekly and monthly reports
            weekly_report = self.generate_weekly_report()
            monthly_report = self.generate_monthly_report()
            
            comprehensive_report = {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'comprehensive',
                'daily_report': daily_report,
                'weekly_report': weekly_report,
                'monthly_report': monthly_report,
                'performance_metrics': {
                    '7_days': {
                        'total_applications': metrics_7d.total_applications,
                        'response_rate': metrics_7d.response_rate,
                        'interview_rate': metrics_7d.interview_rate,
                        'offer_rate': metrics_7d.offer_rate,
                        'rejection_rate': metrics_7d.rejection_rate,
                        'tier_distribution': metrics_7d.tier_distribution,
                        'top_companies': metrics_7d.top_companies
                    },
                    '30_days': {
                        'total_applications': metrics_30d.total_applications,
                        'response_rate': metrics_30d.response_rate,
                        'interview_rate': metrics_30d.interview_rate,
                        'offer_rate': metrics_30d.offer_rate,
                        'rejection_rate': metrics_30d.rejection_rate,
                        'tier_distribution': metrics_30d.tier_distribution,
                        'top_companies': metrics_30d.top_companies
                    },
                    '90_days': {
                        'total_applications': metrics_90d.total_applications,
                        'response_rate': metrics_90d.response_rate,
                        'interview_rate': metrics_90d.interview_rate,
                        'offer_rate': metrics_90d.offer_rate,
                        'rejection_rate': metrics_90d.rejection_rate,
                        'tier_distribution': metrics_90d.tier_distribution,
                        'top_companies': metrics_90d.top_companies
                    }
                }
            }
            
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(comprehensive_report, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Comprehensive report saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive report: {e}")
            return ""

if __name__ == "__main__":
    # Test the reporting dashboard
    dashboard = ReportingDashboard()
    
    print("🚀 InternMailer Reporting Dashboard")
    print("=" * 50)
    
    # Generate daily report
    print("📊 Generating daily report...")
    daily_report = dashboard.generate_daily_report()
    if daily_report:
        summary = daily_report.get('summary', {})
        print(f"✅ Daily Report Generated")
        print(f"   Total Found: {summary.get('total_found', 0)}")
        print(f"   Shortlisted: {summary.get('shortlisted', 0)}")
        print(f"   Tier 1: {summary.get('tiers', {}).get('Tier 1', 0)}")
    
    # Get performance metrics
    print("\n📈 Getting performance metrics...")
    metrics = dashboard.get_performance_metrics(30)
    print(f"✅ Performance Metrics (30 days)")
    print(f"   Total Applications: {metrics.total_applications}")
    print(f"   Response Rate: {metrics.response_rate}%")
    print(f"   Interview Rate: {metrics.interview_rate}%")
    print(f"   Offer Rate: {metrics.offer_rate}%")
    
    print("\n🎯 Reporting dashboard ready for use!")