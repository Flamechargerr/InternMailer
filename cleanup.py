"""
Project Cleanup Script for InternMailer

This script helps clean up redundant and temporary files from the project.
"""

import os
import shutil
from pathlib import Path

def remove_file(file_path: str) -> None:
    """Safely remove a file if it exists."""
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"Removed: {file_path}")
        except Exception as e:
            print(f"Error removing {file_path}: {e}")

def remove_dir(dir_path: str) -> None:
    """Safely remove a directory if it exists."""
    if os.path.exists(dir_path):
        try:
            shutil.rmtree(dir_path)
            print(f"Removed directory: {dir_path}")
        except Exception as e:
            print(f"Error removing directory {dir_path}: {e}")

def clean_project():
    """Clean up redundant files and directories."""
    # Remove redundant virtual environments
    for venv_dir in ['venv', 'venv_dev', 'env', '.venv']:
        if os.path.exists(venv_dir):
            remove_dir(venv_dir)
    
    # Remove Python cache directories
    for root, dirs, _ in os.walk('.'):
        if '__pycache__' in dirs:
            remove_dir(os.path.join(root, '__pycache__'))
        if '.pytest_cache' in dirs:
            remove_dir(os.path.join(root, '.pytest_cache'))
    
    # Remove redundant log files
    for log_file in Path('.').glob('*.log'):
        if str(log_file) not in ['app.log']:  # Keep main log file
            remove_file(str(log_file))
    
    # Remove redundant backup files
    for backup_file in Path('.').rglob('*~'):  # Backup files ending with ~
        remove_file(str(backup_file))
    
    # Remove redundant Python files
    redundant_files = [
        # Old versions of app.py
        'app_old.py', 'app_backup.py', 'app_clean.py', 'app_final.py',
        # Old campaign files
        'auto_campaign_old.py', 'auto_campaign_backup.py', 'auto_campaign_final.py',
        # Redundant data files
        'professors_old.csv', 'professors_backup.csv', 'professors_final.csv',
        # Temporary files
        '.DS_Store', 'Thumbs.db', 'desktop.ini'
    ]
    
    for file_pattern in redundant_files:
        for file_path in Path('.').rglob(file_pattern):
            remove_file(str(file_path))
    
    print("\nCleanup complete!")

if __name__ == "__main__":
    print("Starting project cleanup...")
    confirm = input("This will remove redundant files. Continue? (y/n): ")
    if confirm.lower() == 'y':
        clean_project()
    else:
        print("Cleanup cancelled.")
