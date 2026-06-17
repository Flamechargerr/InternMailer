"""
Production Readiness Checker
============================
Comprehensive checks for production deployment readiness
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
from utils.config import config
from utils.validate_setup import SetupValidator

logger = logging.getLogger(__name__)


class ProductionChecker:
    """Check production readiness"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def check_all(self) -> Dict[str, Any]:
        """Run all production checks"""
        self.errors.clear()
        self.warnings.clear()
        self.info.clear()
        
        # Security checks
        self._check_security()
        
        # Configuration checks
        self._check_production_config()
        
        # Environment checks
        self._check_environment()
        
        # Dependency checks
        self._check_dependencies()
        
        # Performance checks
        self._check_performance_settings()
        
        return {
            'production_ready': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info
        }
    
    def _check_security(self):
        """Check security settings"""
        # Check debug mode
        if config.DEBUG:
            self.errors.append(
                "❌ DEBUG mode is enabled - disable in production\n"
                "   Set ENVIRONMENT=production or DEBUG=false"
            )
        else:
            self.info.append("✅ Debug mode disabled")
        
        # Check secret key
        if config.SECRET_KEY == os.urandom(32).hex():
            self.warnings.append(
                "⚠️  SECRET_KEY is using default - set a strong secret in production"
            )
        else:
            self.info.append("✅ Secret key configured")
        
        # Check HTTPS/secure cookies
        from utils.config import Environment
        if config.SESSION_SECURE and config.ENV == Environment.PRODUCTION:
            self.info.append("✅ Secure session cookies enabled")
        elif config.ENV == Environment.PRODUCTION:
            self.warnings.append(
                "⚠️  SESSION_SECURE should be true in production for HTTPS"
            )
        
        # Check CORS
        if config.FRONTEND_ORIGIN and config.FRONTEND_ORIGIN != '*':
            self.info.append("✅ CORS origin configured")
        else:
            self.warnings.append(
                "⚠️  FRONTEND_ORIGIN should be set to specific domain in production"
            )
    
    def _check_production_config(self):
        """Check production-specific configuration"""
        from utils.config import Environment
        
        if config.ENV != Environment.PRODUCTION:
            self.warnings.append(
                f"⚠️  Environment is '{config.ENV}' - set ENVIRONMENT=production for production"
            )
        else:
            self.info.append("✅ Production environment set")
        
        # Check rate limits are reasonable
        if config.RATE_LIMIT_PER_MINUTE > 1000:
            self.warnings.append(
                f"⚠️  Rate limit very high ({config.RATE_LIMIT_PER_MINUTE}/min) - consider lowering"
            )
        
        # Check email limits
        if config.MAX_EMAILS_PER_DAY > 500:
            self.warnings.append(
                f"⚠️  Daily email limit very high ({config.MAX_EMAILS_PER_DAY}) - ensure compliance"
            )
    
    def _check_environment(self):
        """Check environment variables"""
        required_vars = [
            'GMAIL_USER',
            'GMAIL_APP_PASSWORD'
        ]
        
        missing = []
        for var in required_vars:
            if not getattr(config, var, None):
                missing.append(var)
        
        if missing:
            self.errors.append(
                f"❌ Missing required environment variables: {', '.join(missing)}"
            )
        else:
            self.info.append("✅ Required environment variables set")
    
    def _check_dependencies(self):
        """Check critical dependencies"""
        critical_deps = {
            'flask': 'flask',
            'requests': 'requests',
            'beautifulsoup4': 'bs4',
            'pyyaml': 'yaml',
        }
        
        missing = []
        for package, import_name in critical_deps.items():
            try:
                __import__(import_name)
            except ImportError:
                missing.append(package)
        
        if missing:
            self.errors.append(
                f"❌ Missing critical dependencies: {', '.join(missing)}\n"
                "   Run: pip install -r requirements.txt"
            )
        else:
            self.info.append("✅ All critical dependencies installed")
    
    def _check_performance_settings(self):
        """Check performance-related settings"""
        # Check database paths are on fast storage
        db_paths = [
            config.DATABASE_PATH,
            config.JOBS_DB_PATH,
            config.INBOX_DB_PATH,
        ]
        
        for db_path in db_paths:
            if db_path and os.path.exists(db_path):
                # Check if on tmpfs or fast storage
                if '/tmp/' in db_path:
                    self.info.append(f"✅ Database on tmpfs: {db_path}")
                else:
                    self.warnings.append(
                        f"⚠️  Consider using /tmp/ for database in production: {db_path}"
                    )
        
        # Check connection pool size
        if config.SMTP_POOL_SIZE < 3:
            self.warnings.append(
                f"⚠️  SMTP pool size is low ({config.SMTP_POOL_SIZE}) - consider increasing"
            )
        elif config.SMTP_POOL_SIZE > 20:
            self.warnings.append(
                f"⚠️  SMTP pool size is high ({config.SMTP_POOL_SIZE}) - may cause issues"
            )
        else:
            self.info.append(f"✅ SMTP pool size reasonable: {config.SMTP_POOL_SIZE}")
    
    def print_report(self):
        """Print production readiness report"""
        result = self.check_all()
        
        print("\n" + "=" * 70)
        print("🚀 PRODUCTION READINESS CHECK")
        print("=" * 70)
        
        if result['info']:
            print("\n✅ Checks Passed:")
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
        
        if result['production_ready']:
            print("✅ System is production-ready!")
        else:
            print("❌ System is NOT production-ready. Fix errors above.")
        
        print("=" * 70 + "\n")
        
        return result['production_ready']


def main():
    """Run production check from command line"""
    checker = ProductionChecker()
    is_ready = checker.print_report()
    
    # Also run setup validation
    print("\n" + "=" * 70)
    print("Running setup validation...")
    print("=" * 70)
    validator = SetupValidator()
    validator.print_report()
    
    sys.exit(0 if is_ready else 1)


if __name__ == '__main__':
    main()
