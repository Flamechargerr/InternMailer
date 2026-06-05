#!/usr/bin/env python3
"""Check all Python files for syntax errors"""

import os
import sys
import py_compile
from pathlib import Path

errors = []

print("🔍 CHECKING ALL PYTHON FILES FOR SYNTAX ERRORS...")
print("=" * 70)

# Find all Python files
python_files = list(Path('.').rglob('*.py'))

# Exclude common non-project directories
exclude_dirs = {'.git', '__pycache__', '.pytest_cache', 'venv', 'env', '.venv'}
python_files = [f for f in python_files if not any(ex in str(f) for ex in exclude_dirs)]

print(f"Found {len(python_files)} Python files to check\n")

for i, file_path in enumerate(python_files, 1):
    try:
        py_compile.compile(str(file_path), doraise=True)
        print(f"✅ {i}/{len(python_files)} {file_path}")
    except py_compile.PyCompileError as e:
        print(f"❌ {i}/{len(python_files)} {file_path}")
        print(f"   ERROR: {e}")
        errors.append((file_path, str(e)))

print("\n" + "=" * 70)
if errors:
    print(f"❌ FOUND {len(errors)} FILES WITH SYNTAX ERRORS:")
    for file_path, error in errors:
        print(f"  - {file_path}: {error}")
    sys.exit(1)
else:
    print(f"✅ ALL {len(python_files)} PYTHON FILES HAVE VALID SYNTAX")
    sys.exit(0)
