#!/usr/bin/env python3
"""
Deployment preparation script for InternMailer
Ensures the project is ready for GitHub deployment
"""

import os
import subprocess
import sys
import json
from pathlib import Path

def check_git_status():
    """Check if git is initialized and ready"""
    print("=== Checking Git Status ===")
    
    try:
        # Check if git is initialized
        result = subprocess.run(['git', 'status'], capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            print("✓ Git repository is initialized")
            return True
        else:
            print("⚠ Git repository not initialized")
            return False
    except FileNotFoundError:
        print("✗ Git not found. Please install Git first.")
        return False

def initialize_git():
    """Initialize git repository if needed"""
    print("\n=== Initializing Git Repository ===")
    
    try:
        # Initialize git
        subprocess.run(['git', 'init'], check=True, cwd='.')
        print("✓ Git repository initialized")
        
        # Add remote origin
        remote_url = "https://github.com/Flamechargerr/InternMailer.git"
        try:
            subprocess.run(['git', 'remote', 'add', 'origin', remote_url], check=True, cwd='.')
            print(f"✓ Remote origin added: {remote_url}")
        except subprocess.CalledProcessError:
            print("⚠ Remote origin may already exist")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Git initialization failed: {e}")
        return False

def check_sensitive_files():
    """Check for sensitive files that shouldn't be committed"""
    print("\n=== Checking for Sensitive Files ===")
    
    sensitive_files = [
        '.env',
        'token.json',
        'credentials.json',
        'send_log.csv'
    ]
    
    found_sensitive = []
    for file in sensitive_files:
        if os.path.exists(file):
            found_sensitive.append(file)
    
    if found_sensitive:
        print("⚠ Found sensitive files (should be in .gitignore):")
        for file in found_sensitive:
            print(f"  - {file}")
        
        # Check if they're in .gitignore
        if os.path.exists('.gitignore'):
            with open('.gitignore', 'r') as f:
                gitignore_content = f.read()
            
            protected = []
            for file in found_sensitive:
                if file in gitignore_content:
                    protected.append(file)
            
            print(f"✓ {len(protected)}/{len(found_sensitive)} sensitive files are protected by .gitignore")
        else:
            print("✗ No .gitignore file found!")
            return False
    else:
        print("✓ No sensitive files found in root directory")
    
    return True

def clean_project():
    """Clean up temporary and cache files"""
    print("\n=== Cleaning Project ===")
    
    # Remove Python cache
    cache_dirs = []
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            cache_dirs.append(os.path.join(root, '__pycache__'))
    
    for cache_dir in cache_dirs:
        try:
            import shutil
            shutil.rmtree(cache_dir)
            print(f"✓ Removed {cache_dir}")
        except Exception as e:
            print(f"⚠ Could not remove {cache_dir}: {e}")
    
    # Remove test artifacts
    test_files = ['test_report.json', 'security_audit.py', 'full_flow_test.py', 'deploy_prep.py']
    for file in test_files:
        if os.path.exists(file):
            print(f"⚠ Test file {file} will remain (add to .gitignore if needed)")
    
    print("✓ Project cleaned")

def run_final_test():
    """Run a final quick test"""
    print("\n=== Running Final Test ===")
    
    try:
        # Test basic imports
        sys.path.append('.')
        from ui import app_fixed
        from mailer import generate_emails
        from scraper import csrankings_scraper
        from utils import gmail_auth
        
        print("✓ All main modules import successfully")
        
        # Check if Streamlit app can be imported
        import streamlit
        print("✓ Streamlit is available")
        
        return True
    except Exception as e:
        print(f"✗ Final test failed: {e}")
        return False

def create_deployment_summary():
    """Create a deployment summary"""
    print("\n=== Creating Deployment Summary ===")
    
    summary = {
        "project_name": "InternMailer Winter '25-'26 MVP",
        "repository": "https://github.com/Flamechargerr/InternMailer",
        "main_app": "ui/app_fixed.py",
        "test_command": "python full_flow_test.py",
        "run_command": "streamlit run ui/app_fixed.py",
        "dependencies": "requirements.txt",
        "environment": ".env.example",
        "security_features": [
            "Pinned dependencies",
            "Environment variables",
            "OAuth authentication",
            "Comprehensive .gitignore"
        ],
        "key_features": [
            "Smart professor discovery",
            "AI-powered email generation",
            "Skill matching",
            "Gmail integration",
            "Campaign tracking",
            "Follow-up scheduling"
        ]
    }
    
    with open('deployment_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("✓ Deployment summary created: deployment_summary.json")

def main():
    """Main deployment preparation function"""
    print("InternMailer Deployment Preparation")
    print("=" * 50)
    
    # Run all checks
    checks = [
        ("Git Status", check_git_status),
        ("Sensitive Files", check_sensitive_files),
        ("Final Test", run_final_test),
    ]
    
    passed_checks = 0
    for check_name, check_func in checks:
        if check_func():
            passed_checks += 1
        print()
    
    # Clean project
    clean_project()
    
    # Create deployment summary
    create_deployment_summary()
    
    print("\n" + "=" * 50)
    print("DEPLOYMENT PREPARATION SUMMARY")
    print("=" * 50)
    
    print(f"Checks passed: {passed_checks}/{len(checks)}")
    
    if passed_checks == len(checks):
        print("\n🎉 Project is ready for GitHub deployment!")
        print("\nNext steps:")
        print("1. git add .")
        print("2. git commit -m 'Initial commit: InternMailer Winter 25-26 MVP'")
        print("3. git push -u origin main")
        print("\nOr use GitHub Desktop/VS Code Git integration")
    else:
        print("\n⚠ Please fix the issues above before deployment")
    
    print(f"\n📊 Deployment summary saved to: deployment_summary.json")
    print(f"🚀 Main application: streamlit run ui/app_fixed.py")
    print(f"🧪 Test command: python full_flow_test.py")

if __name__ == "__main__":
    main()
