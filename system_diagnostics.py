#!/usr/bin/env python3
"""
🔍 ULTRA CAMPAIGN SYSTEM DIAGNOSTICS
====================================
Comprehensive system health check and diagnostics for the Ultra Improved Campaign System

Features:
- Database integrity verification
- Email credentials testing
- Campaign history analysis
- Performance metrics calculation
- Issue detection and fixes
- Optimization recommendations
- System readiness assessment
"""

import pandas as pd
import os
import json
import re
import smtplib
import ssl
import base64
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemDiagnostics:
    def __init__(self):
        """Initialize the diagnostics system"""
        self.issues = []
        self.warnings = []
        self.recommendations = []
        self.metrics = {}
        
        # File patterns to check
        self.required_files = [
            'ultra_improved_campaign_v2.py',
            'enhanced_background_emails.csv'
        ]
        
        self.optional_files = [
            'email_credentials.json',
            'database_cleaner_optimizer.py',
            'ultra_followup_system.py'
        ]
    
    def check_file_system(self) -> Dict[str, any]:
        """Check file system integrity"""
        print("📁 Checking file system...")
        
        file_status = {
            'required_missing': [],
            'optional_missing': [],
            'database_files': [],
            'campaign_results': [],
            'total_files': 0
        }
        
        # Check required files
        for file in self.required_files:
            if not Path(file).exists():
                file_status['required_missing'].append(file)
                self.issues.append(f"Required file missing: {file}")
        
        # Check optional files
        for file in self.optional_files:
            if not Path(file).exists():
                file_status['optional_missing'].append(file)
                self.warnings.append(f"Optional file missing: {file}")
        
        # Count database files
        for file in os.listdir('.'):
            if file.endswith('.csv') and ('professor' in file.lower() or 'email' in file.lower()):
                file_status['database_files'].append(file)
            elif file.startswith('ultra_campaign_results_'):
                file_status['campaign_results'].append(file)
        
        file_status['total_files'] = len(os.listdir('.'))
        
        print(f"   ✅ Total files: {file_status['total_files']}")
        print(f"   📊 Database files: {len(file_status['database_files'])}")
        print(f"   📧 Campaign result files: {len(file_status['campaign_results'])}")
        
        return file_status
    
    def check_database_integrity(self) -> Dict[str, any]:
        """Check database integrity and quality"""
        print("\n📊 Checking database integrity...")
        
        database_status = {
            'main_db_exists': False,
            'main_db_records': 0,
            'valid_emails': 0,
            'corrupted_emails': 0,
            'duplicates': 0,
            'missing_names': 0,
            'missing_affiliations': 0
        }
        
        main_db_path = 'enhanced_background_emails.csv'
        
        if Path(main_db_path).exists():
            try:
                df = pd.read_csv(main_db_path, dtype=str)
                database_status['main_db_exists'] = True
                database_status['main_db_records'] = len(df)
                
                if 'email' in df.columns:
                    # Check email quality
                    email_pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
                    
                    for email in df['email'].dropna():
                        email_str = str(email)
                        # Check for corrupted emails (extra text attached)
                        clean_email = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', email_str)
                        if clean_email and email_pattern.match(clean_email.group(1)):
                            database_status['valid_emails'] += 1
                        else:
                            database_status['corrupted_emails'] += 1
                    
                    # Check duplicates
                    if 'email' in df.columns:
                        database_status['duplicates'] = df.duplicated(subset=['email']).sum()
                
                # Check missing data
                if 'name' in df.columns:
                    database_status['missing_names'] = df['name'].isna().sum()
                
                if 'affiliation' in df.columns:
                    database_status['missing_affiliations'] = df['affiliation'].isna().sum()
                
                print(f"   ✅ Main database found: {database_status['main_db_records']:,} records")
                print(f"   📧 Valid emails: {database_status['valid_emails']:,}")
                print(f"   ⚠️ Corrupted emails: {database_status['corrupted_emails']:,}")
                print(f"   🔁 Duplicates: {database_status['duplicates']:,}")
                
                # Add issues/recommendations
                if database_status['corrupted_emails'] > 1000:
                    self.issues.append(f"High number of corrupted emails ({database_status['corrupted_emails']:,})")
                    self.recommendations.append("Run database_cleaner_optimizer.py to fix corrupted emails")
                
                if database_status['duplicates'] > 500:
                    self.warnings.append(f"Many duplicate emails found ({database_status['duplicates']:,})")
                
            except Exception as e:
                self.issues.append(f"Failed to analyze main database: {e}")
                
        else:
            self.issues.append("Main database file not found: enhanced_background_emails.csv")
        
        return database_status
    
    def check_email_credentials(self) -> Dict[str, any]:
        """Check email credentials configuration"""
        print("\n🔐 Checking email credentials...")
        
        cred_status = {
            'credentials_exist': False,
            'credentials_valid': False,
            'smtp_connection': False,
            'username': None
        }
        
        cred_file = 'email_credentials.json'
        
        if Path(cred_file).exists():
            try:
                with open(cred_file, 'r') as f:
                    creds = json.load(f)
                
                cred_status['credentials_exist'] = True
                
                # Decode credentials
                username = base64.b64decode(creds['username']).decode()
                password = base64.b64decode(creds['password']).decode()
                
                cred_status['username'] = username
                cred_status['credentials_valid'] = True
                
                print(f"   ✅ Credentials found for: {username}")
                
                # Test SMTP connection
                try:
                    context = ssl.create_default_context()
                    with smtplib.SMTP('smtp.gmail.com', 587) as server:
                        server.starttls(context=context)
                        server.login(username, password)
                        cred_status['smtp_connection'] = True
                        print("   ✅ SMTP connection successful")
                        
                except Exception as e:
                    self.issues.append(f"SMTP connection failed: {e}")
                    print("   ❌ SMTP connection failed")
                
            except Exception as e:
                self.issues.append(f"Failed to load credentials: {e}")
        else:
            self.warnings.append("Email credentials not saved - will need to enter manually")
            print("   ⚠️ No saved credentials found")
        
        return cred_status
    
    def analyze_campaign_history(self) -> Dict[str, any]:
        """Analyze previous campaign performance"""
        print("\n📈 Analyzing campaign history...")
        
        history = {
            'total_campaigns': 0,
            'total_emails_sent': 0,
            'total_emails_failed': 0,
            'success_rate': 0.0,
            'daily_limit_hits': 0,
            'recent_campaigns': [],
            'contacted_professors': set(),
            'top_errors': {}
        }
        
        # Find campaign result files
        campaign_files = []
        for file in os.listdir('.'):
            if file.startswith('ultra_campaign_results_v2_') and file.endswith('.csv'):
                campaign_files.append(file)
        
        history['total_campaigns'] = len(campaign_files)
        
        for file in campaign_files:
            try:
                df = pd.read_csv(file)
                
                # Extract timestamp from filename
                timestamp_str = file.split('_')[-1].replace('.csv', '')
                campaign_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                
                # Analyze this campaign
                campaign_stats = {
                    'file': file,
                    'date': campaign_date,
                    'total_processed': len(df),
                    'successful': len(df[df['status'] == 'success']),
                    'failed': len(df[df['status'] == 'failed']),
                    'daily_limit_hit': False
                }
                
                # Check for daily limit errors
                daily_limit_errors = df[df['error'].str.contains('Daily.*limit|sending quota', na=False, case=False)]
                if len(daily_limit_errors) > 0:
                    campaign_stats['daily_limit_hit'] = True
                    history['daily_limit_hits'] += 1
                
                # Collect contacted emails
                successful_emails = df[df['status'] == 'success']['email'].tolist()
                history['contacted_professors'].update(successful_emails)
                
                # Count errors
                for error in df[df['status'] == 'failed']['error'].dropna():
                    error_key = str(error)[:50]  # First 50 chars
                    history['top_errors'][error_key] = history['top_errors'].get(error_key, 0) + 1
                
                history['total_emails_sent'] += campaign_stats['successful']
                history['total_emails_failed'] += campaign_stats['failed']
                
                history['recent_campaigns'].append(campaign_stats)
                
            except Exception as e:
                logger.warning(f"Could not analyze {file}: {e}")
        
        # Calculate overall success rate
        total_attempts = history['total_emails_sent'] + history['total_emails_failed']
        if total_attempts > 0:
            history['success_rate'] = (history['total_emails_sent'] / total_attempts) * 100
        
        # Sort recent campaigns by date
        history['recent_campaigns'].sort(key=lambda x: x['date'], reverse=True)
        
        print(f"   📊 Total campaigns run: {history['total_campaigns']}")
        print(f"   ✅ Total emails sent: {history['total_emails_sent']:,}")
        print(f"   ❌ Total emails failed: {history['total_emails_failed']:,}")
        print(f"   📈 Overall success rate: {history['success_rate']:.1f}%")
        print(f"   👥 Unique professors contacted: {len(history['contacted_professors']):,}")
        print(f"   ⚠️ Daily limit hits: {history['daily_limit_hits']}")
        
        # Analysis and recommendations
        if history['success_rate'] < 70:
            self.issues.append(f"Low email success rate: {history['success_rate']:.1f}%")
            self.recommendations.append("Check email credentials and SMTP configuration")
        
        if history['daily_limit_hits'] > 2:
            self.recommendations.append("Consider using multiple email accounts or pacing campaigns")
        
        if len(history['contacted_professors']) > 800:
            self.recommendations.append("Consider expanding to new professor databases")
        
        return history
    
    def check_system_performance(self) -> Dict[str, any]:
        """Check system performance metrics"""
        print("\n⚡ Checking system performance...")
        
        performance = {
            'python_version': f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}",
            'required_modules': {},
            'disk_space_mb': 0,
            'database_size_mb': 0
        }
        
        # Check required Python modules
        required_modules = [
            'pandas', 'smtplib', 'ssl', 'requests', 'asyncio', 
            'concurrent.futures', 'logging', 'datetime'
        ]
        
        for module in required_modules:
            try:
                __import__(module)
                performance['required_modules'][module] = 'Available'
            except ImportError:
                performance['required_modules'][module] = 'Missing'
                self.issues.append(f"Required module missing: {module}")
        
        # Check disk space (simplified)
        try:
            import shutil
            disk_usage = shutil.disk_usage('.')
            performance['disk_space_mb'] = disk_usage.free // (1024 * 1024)
        except:
            performance['disk_space_mb'] = 0
        
        # Check database file size
        db_path = 'enhanced_background_emails.csv'
        if Path(db_path).exists():
            performance['database_size_mb'] = Path(db_path).stat().st_size // (1024 * 1024)
        
        print(f"   🐍 Python version: {performance['python_version']}")
        print(f"   📦 Required modules: {len([m for m in performance['required_modules'].values() if m == 'Available'])}/{len(required_modules)}")
        print(f"   💾 Free disk space: {performance['disk_space_mb']:,} MB")
        print(f"   📊 Database size: {performance['database_size_mb']} MB")
        
        return performance
    
    def generate_recommendations(self) -> List[str]:
        """Generate system optimization recommendations"""
        recommendations = []
        
        # Add specific recommendations based on analysis
        if len(self.issues) > 0:
            recommendations.append("🔧 CRITICAL FIXES NEEDED:")
            for issue in self.issues:
                recommendations.append(f"   • {issue}")
        
        if len(self.warnings) > 0:
            recommendations.append("\n⚠️ WARNINGS:")
            for warning in self.warnings:
                recommendations.append(f"   • {warning}")
        
        if len(self.recommendations) > 0:
            recommendations.append("\n💡 RECOMMENDATIONS:")
            for rec in self.recommendations:
                recommendations.append(f"   • {rec}")
        
        return recommendations
    
    def run_full_diagnostics(self) -> Dict[str, any]:
        """Run complete system diagnostics"""
        print("🔍 ULTRA CAMPAIGN SYSTEM DIAGNOSTICS")
        print("=" * 60)
        
        # Run all diagnostic checks
        file_status = self.check_file_system()
        db_status = self.check_database_integrity()
        cred_status = self.check_email_credentials()
        history = self.analyze_campaign_history()
        performance = self.check_system_performance()
        
        # Calculate system health score
        health_score = self.calculate_health_score(file_status, db_status, cred_status, history, performance)
        
        # Generate comprehensive report
        report = {
            'timestamp': datetime.now().isoformat(),
            'health_score': health_score,
            'file_system': file_status,
            'database': db_status,
            'credentials': cred_status,
            'campaign_history': history,
            'performance': performance,
            'issues': self.issues,
            'warnings': self.warnings,
            'recommendations': self.generate_recommendations()
        }
        
        self.display_summary_report(report)
        return report
    
    def calculate_health_score(self, file_status, db_status, cred_status, history, performance) -> int:
        """Calculate overall system health score (0-100)"""
        score = 100
        
        # File system issues
        score -= len(file_status['required_missing']) * 20
        score -= len(file_status['optional_missing']) * 5
        
        # Database issues
        if not db_status['main_db_exists']:
            score -= 30
        elif db_status['corrupted_emails'] > 1000:
            score -= 15
        
        # Credential issues
        if not cred_status['smtp_connection']:
            score -= 20
        
        # Performance issues
        if history['success_rate'] < 70:
            score -= 15
        
        # Critical issues
        score -= len(self.issues) * 10
        score -= len(self.warnings) * 3
        
        return max(0, score)
    
    def display_summary_report(self, report: Dict[str, any]) -> None:
        """Display comprehensive summary report"""
        
        print(f"\n🎯 SYSTEM HEALTH REPORT")
        print("=" * 60)
        
        health_score = report['health_score']
        
        # Health score with color coding
        if health_score >= 90:
            status = "🟢 EXCELLENT"
        elif health_score >= 75:
            status = "🟡 GOOD"
        elif health_score >= 50:
            status = "🟠 NEEDS ATTENTION"
        else:
            status = "🔴 CRITICAL ISSUES"
        
        print(f"Overall Health Score: {health_score}/100 - {status}")
        
        print(f"\n📊 SYSTEM OVERVIEW:")
        print(f"   • Database Records: {report['database']['main_db_records']:,}")
        print(f"   • Valid Emails: {report['database']['valid_emails']:,}")
        print(f"   • Total Campaigns: {report['campaign_history']['total_campaigns']}")
        print(f"   • Total Emails Sent: {report['campaign_history']['total_emails_sent']:,}")
        print(f"   • Success Rate: {report['campaign_history']['success_rate']:.1f}%")
        print(f"   • Professors Contacted: {len(report['campaign_history']['contacted_professors']):,}")
        
        # Display recommendations
        if report['recommendations']:
            print("\n" + "\n".join(report['recommendations']))
        
        # System readiness
        if health_score >= 75:
            print(f"\n✅ SYSTEM READY FOR CAMPAIGNS")
            print("   The system is in good condition and ready for email campaigns.")
        else:
            print(f"\n⚠️ SYSTEM NEEDS ATTENTION")
            print("   Please address the issues above before running campaigns.")

def main():
    """Main function to run system diagnostics"""
    
    print("🔍 ULTRA CAMPAIGN SYSTEM DIAGNOSTICS")
    print("=" * 60)
    print("Comprehensive health check for your email campaign system")
    print()
    
    # Initialize diagnostics
    diagnostics = SystemDiagnostics()
    
    # Run full diagnostics
    report = diagnostics.run_full_diagnostics()
    
    # Save report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"system_diagnostics_report_{timestamp}.json"
    
    # Remove non-serializable items for JSON
    json_report = dict(report)
    json_report['campaign_history']['contacted_professors'] = list(json_report['campaign_history']['contacted_professors'])
    json_report['campaign_history']['recent_campaigns'] = []  # Remove datetime objects
    
    with open(report_file, 'w') as f:
        json.dump(json_report, f, indent=2)
    
    print(f"\n💾 Full diagnostics report saved to: {report_file}")
    print("\n🔧 Next steps:")
    print("   1. Address any critical issues identified above")
    print("   2. Run 'python database_cleaner_optimizer.py' if database issues exist")
    print("   3. Test email credentials if SMTP issues found")
    print("   4. Run 'python ultra_improved_campaign_v2.py' for main campaigns")
    print("   5. Use 'python ultra_followup_system.py' for follow-up campaigns")

if __name__ == "__main__":
    main()
