#!/usr/bin/env python3
"""
🚀 ULTRA MASTER LAUNCHER
========================
Complete Campaign Management System - All-in-One Solution

Features:
- System diagnostics and health checks
- Database cleaning and optimization
- Main email campaigns (normal and ultra-fast)
- Follow-up campaign management
- Performance monitoring and analytics
- User-friendly menu system
- Automated issue detection and resolution

This is your one-stop solution for professor email outreach campaigns.
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UltraMasterLauncher:
    def __init__(self):
        """Initialize the master launcher"""
        self.version = "2.0.0"
        self.system_name = "Ultra Improved Campaign System"
        
        # Available modules
        self.modules = {
            '1': {
                'name': 'System Diagnostics',
                'description': 'Run comprehensive system health check',
                'script': 'system_diagnostics.py',
                'icon': '🔍'
            },
            '2': {
                'name': 'Database Cleaner',
                'description': 'Clean and optimize professor database',
                'script': 'database_cleaner_optimizer.py', 
                'icon': '🧹'
            },
            '3': {
                'name': 'Main Email Campaign (Original)',
                'description': 'Launch primary outreach campaign - original v2',
                'script': 'ultra_improved_campaign_v2.py',
                'icon': '📧'
            },
            '3b': {
                'name': 'RESTORED Ultra System',
                'description': '🔥 Your ORIGINAL sophisticated system with 478k database & duplicate tracking',
                'script': 'RESTORED_ULTRA_SYSTEM.py',
                'icon': '🚀'
            },
            '4': {
                'name': 'Follow-up System',
                'description': 'Send professional follow-up emails',
                'script': 'ultra_followup_system.py',
                'icon': '📨'
            },
            '5': {
                'name': 'Campaign Analytics',
                'description': 'Analyze campaign performance',
                'function': self.show_campaign_analytics,
                'icon': '📈'
            },
            '6': {
                'name': 'AI Response Tracker',
                'description': 'AI-powered response analysis and optimization',
                'script': 'ai_response_tracker.py',
                'icon': '🤖'
            },
            '7': {
                'name': 'Smart Template Generator',
                'description': 'Generate AI-optimized email templates',
                'script': 'smart_template_generator.py',
                'icon': '🧠'
            },
            '8': {
                'name': 'Intelligent Scheduler',
                'description': 'Optimize campaign timing with AI scheduling',
                'script': 'intelligent_scheduler.py',
                'icon': '⏰'
            },
            '9': {
                'name': 'Quick Setup Guide',
                'description': 'First-time setup assistant',
                'function': self.run_setup_guide,
                'icon': '⚙️'
            },
            '10': {
                'name': 'System Status',
                'description': 'Quick system overview',
                'function': self.show_system_status,
                'icon': '📊'
            }
        }
    
    def display_banner(self):
        """Display the system banner"""
        print("=" * 80)
        print("🚀 ULTRA IMPROVED CAMPAIGN SYSTEM v2.0")
        print("=" * 80)
        print("🎯 Complete Professor Email Outreach Management System")
        print("⚡ Features: Database Management, Email Campaigns, Follow-ups, Analytics")
        print("📊 Professional-grade system for academic research collaboration")
        print("=" * 80)
        print()
    
    def display_menu(self):
        """Display the main menu"""
        print("🎛️ SYSTEM CONTROL PANEL")
        print("-" * 40)
        
        for key, module in self.modules.items():
            icon = module['icon']
            name = module['name']
            desc = module['description']
            print(f"   {key}. {icon} {name}")
            print(f"      └─ {desc}")
            print()
        
        print("   0. 🚪 Exit System")
        print()
    
    def run_script(self, script_name: str) -> bool:
        """Run a Python script"""
        if not Path(script_name).exists():
            print(f"❌ Script not found: {script_name}")
            print("💡 Make sure all system files are properly installed.")
            return False
        
        try:
            print(f"🚀 Launching {script_name}...")
            print("-" * 50)
            
            # Run the script
            result = subprocess.run([sys.executable, script_name], 
                                  capture_output=False, 
                                  text=True)
            
            print("-" * 50)
            if result.returncode == 0:
                print(f"✅ {script_name} completed successfully")
            else:
                print(f"⚠️ {script_name} finished with issues (exit code: {result.returncode})")
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Failed to run {script_name}: {e}")
            return False
    
    def show_system_status(self):
        """Show quick system status"""
        print("📊 QUICK SYSTEM STATUS")
        print("=" * 50)
        
        # Check key files
        key_files = {
            'ultra_improved_campaign_v2.py': 'Main Campaign System',
            'enhanced_background_emails.csv': 'Professor Database',
            'email_credentials.json': 'Email Credentials',
            'database_cleaner_optimizer.py': 'Database Cleaner',
            'ultra_followup_system.py': 'Follow-up System'
        }
        
        print("📁 Core Files Status:")
        for file, description in key_files.items():
            if Path(file).exists():
                size = Path(file).stat().st_size
                size_mb = size / (1024 * 1024)
                print(f"   ✅ {description}: Found ({size_mb:.1f} MB)")
            else:
                print(f"   ❌ {description}: Missing")
        print()
        
        # Check campaign history
        campaign_files = [f for f in os.listdir('.') if f.startswith('ultra_campaign_results_v2_')]
        followup_files = [f for f in os.listdir('.') if f.startswith('followup_campaign_results_')]
        
        print("📈 Campaign History:")
        print(f"   • Total Campaigns: {len(campaign_files)}")
        print(f"   • Follow-up Campaigns: {len(followup_files)}")
        
        if campaign_files:
            latest_campaign = max(campaign_files)
            print(f"   • Latest Campaign: {latest_campaign}")
        print()
        
        # Database statistics
        if Path('enhanced_background_emails.csv').exists():
            try:
                import pandas as pd
                df = pd.read_csv('enhanced_background_emails.csv')
                print("📊 Database Statistics:")
                print(f"   • Total Records: {len(df):,}")
                if 'email' in df.columns:
                    valid_emails = df['email'].dropna()
                    print(f"   • Email Records: {len(valid_emails):,}")
                print()
            except Exception as e:
                print(f"   ⚠️ Could not analyze database: {e}")
        
        print("💡 Recommendations:")
        if not Path('email_credentials.json').exists():
            print("   • Run Main Email Campaign to setup credentials")
        if len(campaign_files) == 0:
            print("   • Run System Diagnostics first, then Main Campaign")
        if len(followup_files) == 0 and len(campaign_files) > 0:
            print("   • Consider running Follow-up System for better response rates")
        
        input("\nPress Enter to return to main menu...")
    
    def show_campaign_analytics(self):
        """Show comprehensive campaign analytics"""
        print("📈 CAMPAIGN ANALYTICS DASHBOARD")
        print("=" * 60)
        
        try:
            import pandas as pd
            
            # Load all campaign results
            campaign_files = [f for f in os.listdir('.') if f.startswith('ultra_campaign_results_v2_')]
            
            if not campaign_files:
                print("📭 No campaign data found.")
                print("💡 Run some email campaigns first to see analytics.")
                input("\nPress Enter to return to main menu...")
                return
            
            all_results = []
            total_sent = 0
            total_failed = 0
            total_processed = 0
            
            print("📊 Campaign Summary:")
            print("-" * 30)
            
            for file in campaign_files:
                try:
                    df = pd.read_csv(file)
                    
                    # Extract date from filename
                    date_str = file.split('_')[-1].replace('.csv', '')
                    campaign_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                    
                    sent = len(df[df['status'] == 'success'])
                    failed = len(df[df['status'] == 'failed'])
                    processed = len(df)
                    
                    success_rate = (sent / processed * 100) if processed > 0 else 0
                    
                    print(f"📅 {campaign_date.strftime('%Y-%m-%d %H:%M')}")
                    print(f"   • Processed: {processed:,}")
                    print(f"   • Sent: {sent:,}")
                    print(f"   • Failed: {failed:,}")
                    print(f"   • Success Rate: {success_rate:.1f}%")
                    print()
                    
                    total_sent += sent
                    total_failed += failed
                    total_processed += processed
                    all_results.extend(df.to_dict('records'))
                    
                except Exception as e:
                    logger.warning(f"Could not analyze {file}: {e}")
            
            print("🎯 OVERALL STATISTICS:")
            print("-" * 25)
            overall_success = (total_sent / total_processed * 100) if total_processed > 0 else 0
            print(f"📧 Total Emails Processed: {total_processed:,}")
            print(f"✅ Total Emails Sent: {total_sent:,}")
            print(f"❌ Total Failed: {total_failed:,}")
            print(f"📈 Overall Success Rate: {overall_success:.1f}%")
            
            # Unique professors contacted
            if all_results:
                unique_emails = set()
                for result in all_results:
                    if result.get('status') == 'success' and result.get('email'):
                        unique_emails.add(result['email'])
                print(f"👥 Unique Professors Contacted: {len(unique_emails):,}")
            
            print()
            
            # Performance recommendations
            print("💡 PERFORMANCE INSIGHTS:")
            print("-" * 25)
            
            if overall_success >= 90:
                print("🟢 Excellent performance! System is working optimally.")
            elif overall_success >= 75:
                print("🟡 Good performance with room for minor improvements.")
            elif overall_success >= 50:
                print("🟠 Moderate performance. Consider database cleaning.")
            else:
                print("🔴 Performance needs attention. Check credentials and database.")
            
            if total_sent > 1000:
                print("🎖️ High volume achievement! Consider follow-up campaigns.")
            
            print()
            
        except ImportError:
            print("❌ Pandas not available for analytics")
        except Exception as e:
            print(f"❌ Error analyzing campaigns: {e}")
        
        input("\nPress Enter to return to main menu...")
    
    def run_setup_guide(self):
        """Run first-time setup guide"""
        print("⚙️ FIRST-TIME SETUP GUIDE")
        print("=" * 50)
        print("This guide will help you set up the system for first use.")
        print()
        
        steps = [
            {
                'title': '1. System Health Check',
                'description': 'Check if all components are properly installed',
                'action': 'Run System Diagnostics',
                'script': 'system_diagnostics.py'
            },
            {
                'title': '2. Database Optimization',
                'description': 'Clean and optimize the professor email database',
                'action': 'Run Database Cleaner',
                'script': 'database_cleaner_optimizer.py'
            },
            {
                'title': '3. Email Configuration',
                'description': 'Set up email credentials and test connection',
                'action': 'Run Main Campaign (will prompt for credentials)',
                'script': 'ultra_improved_campaign_v2.py'
            },
            {
                'title': '4. Test Campaign',
                'description': 'Run a small test campaign to verify everything works',
                'action': 'Recommended: Start with 10-20 emails',
                'script': None
            }
        ]
        
        print("📋 Setup Steps:")
        print("-" * 15)
        
        for i, step in enumerate(steps, 1):
            print(f"{step['title']}")
            print(f"   📝 {step['description']}")
            print(f"   🎯 {step['action']}")
            print()
        
        print("🤔 Would you like to run the automated setup?")
        print("   This will run steps 1-2 automatically.")
        
        choice = input("Run automated setup? (y/n): ").strip().lower()
        
        if choice in ['y', 'yes']:
            print("\n🚀 Starting automated setup...")
            
            # Step 1: System Diagnostics
            print("\n" + "="*50)
            print("STEP 1: SYSTEM DIAGNOSTICS")
            print("="*50)
            self.run_script('system_diagnostics.py')
            
            input("\nPress Enter to continue to database cleaning...")
            
            # Step 2: Database Cleaning
            print("\n" + "="*50)
            print("STEP 2: DATABASE CLEANING")
            print("="*50)
            self.run_script('database_cleaner_optimizer.py')
            
            print("\n✅ Automated setup completed!")
            print("💡 Next steps:")
            print("   • Run Main Email Campaign to configure email credentials")
            print("   • Start with a small test campaign (10-20 emails)")
            print("   • Once satisfied, run larger campaigns")
            print("   • Use Follow-up System for better response rates")
        
        input("\nPress Enter to return to main menu...")
    
    def run_main_loop(self):
        """Run the main application loop"""
        while True:
            # Clear screen (cross-platform)
            os.system('cls' if os.name == 'nt' else 'clear')
            
            self.display_banner()
            self.display_menu()
            
            choice = input("Select an option (0-10): ").strip()
            
            if choice == '0':
                print("\n👋 Thank you for using Ultra Improved Campaign System!")
                print("🎯 Happy researching and networking!")
                break
            
            elif choice in self.modules:
                module = self.modules[choice]
                print(f"\n🚀 Launching {module['name']}...")
                
                # Check if it's a script or function
                if 'script' in module:
                    self.run_script(module['script'])
                elif 'function' in module:
                    module['function']()
                
                # Pause before returning to menu
                if choice != '7':  # Status page handles its own pause
                    input("\nPress Enter to return to main menu...")
            
            else:
                print("❌ Invalid choice. Please select 0-10.")
                input("Press Enter to try again...")

def main():
    """Main entry point"""
    
    # Check Python version
    if sys.version_info < (3, 6):
        print("❌ Python 3.6+ required. You have:", sys.version)
        sys.exit(1)
    
    # Initialize and run launcher
    launcher = UltraMasterLauncher()
    
    try:
        launcher.run_main_loop()
    except KeyboardInterrupt:
        print("\n\n👋 System interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ System error: {e}")
        logger.error(f"System error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
