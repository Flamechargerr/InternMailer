"""
Setup Validation - Check if InternMailer is properly configured
===============================================================
Validates that all required data sources and configuration files exist.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict
from utils.config import config


class SetupValidator:
    """Validates InternMailer setup and data sources"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def validate_all(self) -> Dict[str, any]:
        """Run all validation checks"""
        self.errors.clear()
        self.warnings.clear()
        self.info.clear()
        
        # Check configuration
        self._validate_config()
        
        # Check data sources
        self._validate_job_sources()
        self._validate_contact_sources()
        self._validate_profile()
        
        # Check directories
        self._validate_directories()
        
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info
        }
    
    def _validate_config(self):
        """Validate configuration"""
        if not config.GMAIL_USER or not config.GMAIL_APP_PASSWORD:
            self.errors.append(
                "❌ Email credentials not configured\n"
                "   Set GMAIL_USER and GMAIL_APP_PASSWORD in .env file\n"
                "   Get app password from: https://myaccount.google.com/apppasswords"
            )
        else:
            self.info.append("✅ Email credentials configured")
        
        if not config.GROQ_API_KEY:
            self.warnings.append(
                "⚠️  GROQ_API_KEY not set - AI features will be limited\n"
                "   Get free API key from: https://console.groq.com/"
            )
        else:
            self.info.append("✅ AI provider (Groq) configured")
    
    def _validate_job_sources(self):
        """Validate job discovery sources"""
        sources_path = Path(config.JOB_SOURCES_PATH)
        if not sources_path.exists():
            self.errors.append(
                f"❌ Job sources file not found: {sources_path.absolute()}\n"
                f"   Create this file with job source configurations\n"
                f"   See data/job_sources.yaml for reference"
            )
        else:
            self.info.append(f"✅ Job sources file found: {sources_path}")
            
            # Check if file has content
            try:
                content = sources_path.read_text()
                if len(content.strip()) < 100:
                    self.warnings.append(
                        f"⚠️  Job sources file seems empty or minimal\n"
                        f"   File: {sources_path}"
                    )
            except Exception as e:
                self.errors.append(f"❌ Cannot read job sources file: {e}")
    
    def _validate_contact_sources(self):
        """Validate contact data sources"""
        contacts_csv = Path(config.COMPANY_CONTACTS_CSV)
        if not contacts_csv.exists():
            self.errors.append(
                f"❌ Company contacts CSV not found: {contacts_csv.absolute()}\n"
                f"   This file is required for email campaigns\n"
                f"   Run contact discovery or manually create this file"
            )
        else:
            # Check if CSV has data
            try:
                import csv
                with open(contacts_csv, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    if len(rows) == 0:
                        self.warnings.append(
                            f"⚠️  Contacts CSV is empty: {contacts_csv}\n"
                            f"   Add contact data to enable email campaigns"
                        )
                    else:
                        self.info.append(f"✅ Found {len(rows)} contacts in CSV")
            except Exception as e:
                self.warnings.append(f"⚠️  Cannot read contacts CSV: {e}")
    
    def _validate_profile(self):
        """Validate user profile"""
        profile_path = Path(config.PROFILE_PATH) if config.PROFILE_PATH else None
        if not profile_path or not profile_path.exists():
            self.warnings.append(
                "⚠️  Profile file not found\n"
                "   Create data/profile.yaml with your information\n"
                "   Or set profile fields via environment variables"
            )
        else:
            self.info.append(f"✅ Profile file found: {profile_path}")
    
    def _validate_directories(self):
        """Validate required directories exist"""
        required_dirs = [
            Path('data'),
            Path('templates'),
            Path('logs'),
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    self.info.append(f"✅ Created directory: {dir_path}")
                except Exception as e:
                    self.errors.append(f"❌ Cannot create directory {dir_path}: {e}")
            else:
                self.info.append(f"✅ Directory exists: {dir_path}")
    
    def print_report(self):
        """Print validation report"""
        result = self.validate_all()
        
        print("\n" + "=" * 70)
        print("🔍 INTERNMAILER SETUP VALIDATION")
        print("=" * 70)
        
        if result['info']:
            print("\n✅ Configuration:")
            for msg in result['info']:
                print(f"   {msg}")
        
        if result['warnings']:
            print("\n⚠️  Warnings:")
            for msg in result['warnings']:
                print(f"   {msg}")
        
        if result['errors']:
            print("\n❌ Errors (must fix):")
            for msg in result['errors']:
                print(f"   {msg}")
        
        print("\n" + "=" * 70)
        
        if result['valid']:
            print("✅ Setup is valid! You can start using InternMailer.")
        else:
            print("❌ Setup has errors. Please fix the issues above.")
            print("\nQuick fixes:")
            print("1. Copy .env.example to .env and fill in your credentials")
            print("2. Ensure data/job_sources.yaml exists")
            print("3. Add contacts to data/company_contacts.csv")
        
        print("=" * 70 + "\n")
        
        return result['valid']


def main():
    """Run validation from command line"""
    validator = SetupValidator()
    is_valid = validator.print_report()
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
