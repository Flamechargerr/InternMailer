#!/usr/bin/env python3
"""
Test script for the enhanced configuration manager
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_manager import get_configuration_manager, get_config

def test_configuration_manager():
    """Test the enhanced configuration manager"""
    print("🧪 Testing Enhanced Configuration Manager")
    print("=" * 50)
    
    # Get configuration manager
    manager = get_configuration_manager()
    config = get_config()
    
    # Print configuration summary
    summary = manager.get_configuration_summary()
    
    print("\n📋 Configuration Summary:")
    print(f"  Loaded files: {summary['loaded_files']}")
    
    print("\n📧 Email Configuration:")
    print(f"  User: {summary['email']['user']}")
    print(f"  Source: {summary['email']['source']}")
    if summary['email']['resolved_conflicts']:
        print(f"  Resolved conflicts: {summary['email']['resolved_conflicts']}")
    
    print("\n📄 Resume Configuration:")
    print(f"  Path: {summary['resume']['path']}")
    print(f"  Source: {summary['resume']['source']}")
    
    print("\n🧭 Job Discovery Configuration:")
    print(f"  Sources path: {summary['job_discovery']['sources_path']}")
    print(f"  Score threshold: {summary['job_discovery']['score_threshold']}")
    print(f"  Target locations: {summary['job_discovery']['target_locations']}")
    print(f"  Role keywords: {summary['job_discovery']['role_keywords']}")
    
    print("\n⚙️ Email Settings:")
    print(f"  Max per day: {summary['email_settings']['max_per_day']}")
    print(f"  Max concurrent: {summary['email_settings']['max_concurrent']}")
    print(f"  Rate limit delay: {summary['email_settings']['rate_limit_delay']}")
    
    print("\n🚩 Feature Flags:")
    print(f"  Email skip academic: {summary['feature_flags']['email_skip_academic']}")
    print(f"  Contact discovery enabled: {summary['feature_flags']['contact_discovery_enabled']}")
    print(f"  Contact discovery daily cap: {summary['feature_flags']['contact_discovery_daily_cap']}")
    print(f"  Email strict template: {summary['feature_flags']['email_strict_template']}")
    
    print("\n✅ Validation Results:")
    print(f"  Is valid: {summary['validation']['is_valid']}")
    print(f"  Has warnings: {summary['validation']['has_warnings']}")
    
    if summary['validation']['issues']:
        print(f"\n⚠️  Validation Issues ({len(summary['validation']['issues'])}):")
        for i, issue in enumerate(summary['validation']['issues'], 1):
            print(f"\n  {i}. {issue['severity'].upper()}: {issue['message']}")
            if issue['variable']:
                print(f"     Variable: {issue['variable']}")
            if issue['suggestion']:
                print(f"     Suggestion: {issue['suggestion']}")
    
    # Test backward compatibility
    print("\n" + "=" * 50)
    print("🔙 Testing Backward Compatibility")
    
    from utils.config import config as old_config
    
    print(f"\nOld config GMAIL_USER: {old_config.GMAIL_USER}")
    print(f"Old config RESUME_PATH: {old_config.RESUME_PATH}")
    print(f"Old config JOB_SCORE_THRESHOLD: {old_config.JOB_SCORE_THRESHOLD}")
    
    # Validate configuration
    print("\n" + "=" * 50)
    print("🔍 Configuration Validation")
    
    issues = old_config.validate_config()
    if issues:
        print(f"\n❌ Validation issues found ({len(issues)}):")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("\n✅ No validation issues found")
    
    # Get config summary
    print("\n" + "=" * 50)
    print("📊 Configuration Summary (Backward Compatible)")
    
    summary = old_config.get_config_summary()
    print(f"\nEnvironment: {summary['environment']}")
    print(f"Debug mode: {summary['debug']}")
    print(f"Flask port: {summary['flask']['port']}")
    print(f"Max emails per day: {summary['email']['max_per_day']}")
    print(f"Job score threshold: {summary['jobs']['score_threshold']}")
    
    print("\n" + "=" * 50)
    if config.is_valid():
        print("✅ Configuration is VALID and ready to use")
    else:
        print("❌ Configuration has ERRORS that need to be fixed")
        print("\nPlease check the validation issues above and fix them in your .env file")

if __name__ == "__main__":
    test_configuration_manager()