
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

from utils.config import config

print("🔍 Validating Configuration...")
issues = config.validate_config()

if issues:
    print(f"❌ Found {len(issues)} configuration issues:")
    for issue in issues:
        print(f"  - {issue}")
    sys.exit(1)
else:
    print("✅ Configuration is valid!")
    sys.exit(0)
