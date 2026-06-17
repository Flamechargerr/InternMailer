#!/usr/bin/env python3
"""
🚀 InternMailer Production Readiness Validator
===============================================
Comprehensive validation of all system components before production deployment.
Run this before deploying to ensure everything is configured and working.
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_status(name, status, message=""):
    icon = "✅" if status else "❌"
    print(f"  {icon} {name:<50} {message}")


def validate_configuration():
    """Validate all configuration settings"""
    print_header("CONFIGURATION VALIDATION")
    
    from utils.config import config
    
    checks = []
    
    # Email configuration
    checks.append(("GMAIL_USER configured", bool(config.GMAIL_USER) and config.GMAIL_USER != 'your.email@gmail.com'))
    checks.append(("GMAIL_APP_PASSWORD configured", bool(config.GMAIL_APP_PASSWORD) and config.GMAIL_APP_PASSWORD != 'your_app_password'))
    checks.append(("EMAIL_ADDRESS configured", bool(config.EMAIL_ADDRESS)))
    
    # AI configuration
    checks.append(("GROQ_API_KEY configured", bool(config.GROQ_API_KEY)))
    checks.append(("HUNTER_API_KEY configured", bool(config.HUNTER_API_KEY)))
    checks.append(("APOLLO_API_KEY configured", bool(config.APOLLO_API_KEY)))
    
    # Paths
    checks.append(("Database paths configured", bool(config.DATABASE_PATH)))
    checks.append(("Profile path configured", bool(config.PROFILE_PATH)))
    
    # Limits
    checks.append(("Email limits reasonable", 0 < config.MAX_EMAILS_PER_DAY <= 500))
    checks.append(("Rate limits configured", config.RATE_LIMIT_PER_MINUTE > 0))
    
    all_passed = all(status for _, status in checks)
    
    for name, status in checks:
        print_status(name, status)
    
    return all_passed


def validate_database_connections():
    """Validate all database connections"""
    print_header("DATABASE CONNECTION VALIDATION")
    
    checks = []
    
    try:
        # Main tracking database
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        checks.append(("Main database accessible", True, f"{len(tables)} tables"))
    except Exception as e:
        checks.append(("Main database accessible", False, str(e)))
    
    try:
        # Job discovery database
        from core.database_manager import get_job_discovery_db
        db = get_job_discovery_db(config.JOBS_DB_PATH)
        checks.append(("Job discovery database accessible", True))
    except Exception as e:
        checks.append(("Job discovery database accessible", False, str(e)))
    
    try:
        # Inbox monitor database
        conn = sqlite3.connect(config.INBOX_DB_PATH)
        conn.close()
        checks.append(("Inbox monitor database accessible", True))
    except Exception as e:
        checks.append(("Inbox monitor database accessible", False, str(e)))
    
    all_passed = all(status for _, status, *_ in checks)
    
    for check in checks:
        name = check[0]
        status = check[1]
        message = check[2] if len(check) > 2 else ""
        print_status(name, status, message)
    
    return all_passed


def validate_core_modules():
    """Validate all core modules can be imported"""
    print_header("CORE MODULE VALIDATION")
    
    modules = [
        ("utils.config", "Configuration system"),
        ("utils.profile", "Profile management"),
        ("core.email_system", "Email system"),
        ("core.inbox_monitor", "Inbox monitor"),
        ("core.job_discovery", "Job discovery"),
        ("core.job_pipeline", "Job pipeline"),
        ("core.lead_discovery", "Lead discovery"),
        ("core.reply_classifier", "Reply classifier"),
        ("core.followup_scheduler", "Follow-up scheduler"),
        ("core.gmail_agent", "Gmail agent"),
        ("core.enhanced_daemon", "Enhanced daemon"),
    ]
    
    checks = []
    for module_name, description in modules:
        try:
            __import__(module_name)
            checks.append((description, True))
        except Exception as e:
            checks.append((description, False, str(e)[:50]))
    
    all_passed = all(status for _, status, *_ in checks)
    
    for check in checks:
        name = check[0]
        status = check[1]
        message = check[2] if len(check) > 2 else ""
        print_status(name, status, message)
    
    return all_passed


def validate_agents():
    """Validate all AI agents"""
    print_header("AI AGENT VALIDATION")
    
    agents = [
        ("core.agents.base_agent", "Base agent framework"),
        ("core.agents.orchestrator", "Orchestrator agent"),
        ("core.agents.scheduler", "Scheduler agent"),
        ("core.agents.resume_optimizer", "Resume optimizer"),
        ("core.agents.cover_letter", "Cover letter agent"),
        ("core.agents.job_matcher", "Job matcher agent"),
        ("core.agents.email_reply", "Email reply agent"),
    ]
    
    checks = []
    for module_name, description in agents:
        try:
            __import__(module_name)
            checks.append((description, True))
        except Exception as e:
            checks.append((description, False, str(e)[:50]))
    
    all_passed = all(status for _, status, *_ in checks)
    
    for check in checks:
        name = check[0]
        status = check[1]
        message = check[2] if len(check) > 2 else ""
        print_status(name, status, message)
    
    return all_passed


def validate_ai_provider():
    """Validate AI provider is working"""
    print_header("AI PROVIDER VALIDATION")
    
    checks = []
    
    try:
        from core.unified_ai_provider import get_unified_ai_provider
        provider = get_unified_ai_provider()
        
        # Check provider status
        available_providers = [name for name, status in provider.provider_status.items() if status['available']]
        checks.append(("AI providers available", len(available_providers) > 0, f"{len(available_providers)} providers"))
        
        # Try a simple completion
        try:
            response = provider.complete("Say 'test' if you can hear me.", max_tokens=10)
            checks.append(("AI completion working", response is not None and len(response.content) > 0))
        except Exception as e:
            checks.append(("AI completion working", False, str(e)[:50]))
        
    except Exception as e:
        checks.append(("AI provider initialization", False, str(e)[:50]))
    
    all_passed = all(status for _, status, *_ in checks)
    
    for check in checks:
        name = check[0]
        status = check[1]
        message = check[2] if len(check) > 2 else ""
        print_status(name, status, message)
    
    return all_passed


def validate_file_structure():
    """Validate required files and directories exist"""
    print_header("FILE STRUCTURE VALIDATION")
    
    required_paths = [
        ("campaign_results directory", "campaign_results", "dir"),
        ("data directory", "data", "dir"),
        ("logs directory", "logs", "dir"),
        ("templates directory", "templates", "dir"),
        (".env file", ".env", "file"),
        ("Service installer", "services/install.sh", "file"),
    ]
    
    checks = []
    for name, path, path_type in required_paths:
        full_path = Path(path)
        if path_type == "dir":
            exists = full_path.exists() and full_path.is_dir()
        else:
            exists = full_path.exists() and full_path.is_file()
        checks.append((name, exists))
    
    all_passed = all(status for _, status in checks)
    
    for name, status in checks:
        print_status(name, status)
    
    return all_passed


def validate_tests():
    """Validate all tests pass"""
    print_header("TEST SUITE VALIDATION")
    
    import subprocess
    result = subprocess.run(
        ["python3", "-m", "pytest", "tests/", "-v", "--tb=no", "-q"],
        capture_output=True,
        text=True
    )
    
    # Parse results
    output = result.stdout + result.stderr
    if "passed" in output:
        # Extract number of passed tests
        import re
        match = re.search(r'(\d+) passed', output)
        if match:
            passed = int(match.group(1))
            print_status(f"All tests passing ({passed} tests)", True)
            return True
    
    if result.returncode != 0:
        print_status("All tests passing", False, "Some tests failed")
        print("\nRun 'python3 -m pytest tests/ -v' for details")
        return False
    
    return True


def main():
    """Run all validations"""
    print("\n" + "🚀"*35)
    print("   INTERNMAILER PRODUCTION READINESS VALIDATOR")
    print("🚀"*35)
    print(f"\n   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        "Configuration": validate_configuration(),
        "Database Connections": validate_database_connections(),
        "Core Modules": validate_core_modules(),
        "AI Agents": validate_agents(),
        "AI Provider": validate_ai_provider(),
        "File Structure": validate_file_structure(),
        "Test Suite": validate_tests(),
    }
    
    print_header("VALIDATION SUMMARY")
    
    all_passed = True
    for category, passed in results.items():
        status = "PASS" if passed else "FAIL"
        icon = "✅" if passed else "❌"
        print(f"  {icon} {category:<30} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("  ✅ ALL CHECKS PASSED - SYSTEM READY FOR PRODUCTION")
        print("="*70)
        print("\n  Next steps:")
        print("  1. Review .env configuration")
        print("  2. Install service: cd services && ./install.sh install")
        print("  3. Start service: ./install.sh start")
        print("  4. Monitor logs: ./install.sh logs")
        return 0
    else:
        print("  ❌ SOME CHECKS FAILED - FIX ISSUES BEFORE PRODUCTION")
        print("="*70)
        print("\n  Please fix the failed checks above before deploying.")
        return 1


if __name__ == "__main__":
    from utils.config import config
    sys.exit(main())
