#!/usr/bin/env python3
"""
InternMailer Security & Setup Validation Script

This script performs security checks and setup validation before starting the app.
"""

import os
import sys
import shutil
from pathlib import Path
import hashlib

def check_env_security():
    """Check for security issues in environment configuration."""
    issues = []
    warnings = []
    
    env_file = Path('.env')
    if not env_file.exists():
        issues.append("❌ .env file not found - Gmail credentials required")
        return issues, warnings
    
    # Read .env file
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    # Check for Gmail credentials
    if 'GMAIL_USER=' not in env_content:
        issues.append("❌ GMAIL_USER not set in .env file")
    
    if 'GMAIL_APP_PASSWORD=' not in env_content:
        issues.append("❌ GMAIL_APP_PASSWORD not set in .env file")
    elif 'GMAIL_APP_PASSWORD=nbwehsncdrlghllz' in env_content:
        warnings.append("⚠️ WARNING: Default/example Gmail password detected - please update with your actual app password")
    
    # Check for empty values
    lines = env_content.strip().split('\n')
    for line in lines:
        if '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            if not value.strip() and key.strip() in ['GMAIL_USER', 'GMAIL_APP_PASSWORD']:
                issues.append(f"❌ {key.strip()} is empty in .env file")
    
    return issues, warnings

def check_file_permissions():
    """Check file permissions for sensitive files."""
    warnings = []
    
    # Check .env file permissions (should not be world-readable on Unix)
    env_file = Path('.env')
    if env_file.exists():
        # On Windows, we can't easily check Unix-style permissions
        # But we can warn about the file being present
        warnings.append("ℹ️ .env file contains sensitive credentials - ensure it's not committed to version control")
    
    return warnings

def setup_directory_structure():
    """Ensure required directories exist."""
    directories = [
        'data',
        'resumes',
        'InternMailer/data'
    ]
    
    created = []
    for dir_path in directories:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path))
    
    return created

def check_professor_data():
    """Check for professor CSV data."""
    csv_paths = [
        'data/proffesor.csv',
        'InternMailer/data/proffesor.csv'
    ]
    
    found_paths = []
    for path in csv_paths:
        if Path(path).exists():
            found_paths.append(path)
    
    # Copy from InternMailer/data to data if needed
    if 'InternMailer/data/proffesor.csv' in found_paths and 'data/proffesor.csv' not in found_paths:
        shutil.copy2('InternMailer/data/proffesor.csv', 'data/proffesor.csv')
        found_paths.append('data/proffesor.csv')
        print("✅ Copied professor data to main data directory")
    
    return found_paths

def clean_sensitive_files():
    """Remove sensitive files that shouldn't be in production."""
    sensitive_patterns = [
        'campaign_*.log',
        'email_log.csv',
        'test_*.csv',
        '*.backup'
    ]
    
    removed = []
    for pattern in sensitive_patterns:
        for file_path in Path('.').glob(pattern):
            if file_path.is_file():
                file_path.unlink()
                removed.append(str(file_path))
    
    return removed

def validate_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = {
        'streamlit': 'streamlit',
        'pandas': 'pandas',
        'requests': 'requests', 
        'python-dotenv': 'dotenv',
        'beautifulsoup4': 'bs4'
    }
    
    missing = []
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)
    
    return missing

def main():
    """Main security and setup validation."""
    print("🔒 InternMailer Security & Setup Validator")
    print("=" * 50)
    
    # Check current directory
    if not Path('InternMailer').exists():
        print("❌ Please run this script from the InternMailer project root directory")
        return False
    
    all_good = True
    
    # Security checks
    print("\n🔍 Security Checks:")
    env_issues, env_warnings = check_env_security()
    
    for issue in env_issues:
        print(f"  {issue}")
        all_good = False
    
    for warning in env_warnings:
        print(f"  {warning}")
    
    perm_warnings = check_file_permissions()
    for warning in perm_warnings:
        print(f"  {warning}")
    
    # Setup checks
    print("\n📁 Directory Setup:")
    created_dirs = setup_directory_structure()
    for dir_path in created_dirs:
        print(f"  ✅ Created directory: {dir_path}")
    
    # Data validation
    print("\n📊 Data Validation:")
    prof_csvs = check_professor_data()
    if prof_csvs:
        print(f"  ✅ Professor data found: {', '.join(prof_csvs)}")
    else:
        print("  ❌ No professor CSV data found")
        all_good = False
    
    # Dependency check
    print("\n📦 Dependencies:")
    missing_deps = validate_dependencies()
    if missing_deps:
        print(f"  ❌ Missing packages: {', '.join(missing_deps)}")
        print("  💡 Run: pip install -r requirements.txt")
        all_good = False
    else:
        print("  ✅ All required packages installed")
    
    # Cleanup
    print("\n🧹 Cleanup:")
    removed_files = clean_sensitive_files()
    for file_path in removed_files:
        print(f"  🗑️ Removed sensitive file: {file_path}")
    
    print("\n" + "=" * 50)
    if all_good:
        print("✅ All checks passed! Ready to start InternMailer.")
        print("💡 Run: python start_app.py")
        return True
    else:
        print("❌ Issues found. Please fix the above problems before starting.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
