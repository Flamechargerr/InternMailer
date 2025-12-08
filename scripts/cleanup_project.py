import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
🧹 PROJECT CLEANUP SCRIPT
Safely removes redundant files while preserving core functionality
"""

import os
from pathlib import Path

# Files to KEEP (essential for project)
ESSENTIAL_FILES = {
    # Core system
    'system.py',
    'config.py',
    
    # AI functionality
    'free_ai_analyzer.py',
    'ai_email_sender.py',
    'gpt4_research_analyzer.py',
    
    # Data import
    'import_contacts.py',
    
    # Templates
    'templates/professor/anamay_detailed_template.html',
    'templates/professor/research_collaboration_template.html',
    
    # Data files
    'data/clean_40k_professors.db',
    'data/clean_40k_professors_full_backup.db',
    'data/country-info.csv',
    
    # Resume
    'resumes/CV_Anamay_Modern.pdf',
    
    # Configuration
    '.env',
    'README.md',
    'requirements.txt',
}

# Files to REMOVE (temporary/redundant scripts)
REDUNDANT_FILES = [
    # Temporary fix scripts
    'fix_system.py',
    'fix_sql.py',
    'fix_personalization.py',
    'fix_personalization_prep.py',
    'update_system_logic.py',
    'update_personalization_logic.py',
    'integrate_free_ai.py',
    'replace_personalize_email.py',
    'quick_fix.py',
    
    # Test scripts
    'test_free_ai.py',
    
    # European filtering scripts (data already filtered)
    'filter_european_universities.py',
    'filter_db_europe.py',
    'check_euro_db.py',
    'download_data.py',
    
    # Downloaded CSRankings data (no longer needed)
    'data/csrankings-*.csv',
    'data/euro_list.csv',
    
    # Old job automation (not used)
    'job_automation_system.py',
    
    # Duplicate InternMailer subdirectory if exists
    'InternMailer/config.py',
    'InternMailer/gpt4_research_analyzer.py',
]

def cleanup():
    """Remove redundant files safely"""
    base_dir = Path('c:/Users/anama/InternMailer')
    
    print("🧹 CLEANING UP PROJECT")
    print("=" * 60)
    
    removed_count = 0
    kept_count = 0
    
    # Remove redundant files
    for pattern in REDUNDANT_FILES:
        if '*' in pattern:
            # Handle wildcards
            parts = pattern.split('/')
            if len(parts) == 2:
                dir_path = base_dir / parts[0]
                if dir_path.exists():
                    import glob
                    files = glob.glob(str(dir_path / parts[1]))
                    for file in files:
                        try:
                            os.remove(file)
                            print(f"🗑️  Removed: {Path(file).name}")
                            removed_count += 1
                        except Exception as e:
                            print(f"⚠️  Could not remove {file}: {e}")
        else:
            file_path = base_dir / pattern
            if file_path.exists():
                try:
                    os.remove(file_path)
                    print(f"🗑️  Removed: {pattern}")
                    removed_count += 1
                except Exception as e:
                    print(f"⚠️  Could not remove {pattern}: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ Cleanup complete!")
    print(f"📊 Removed: {removed_count} files")
    print("\n🔑 ESSENTIAL FILES KEPT:")
    print("-" * 60)
    
    for file in sorted(ESSENTIAL_FILES):
        file_path = base_dir / file
        if file_path.exists():
            print(f"  ✓ {file}")
            kept_count += 1
    
    print(f"\n📈 Total essential files: {kept_count}")
    print("\n💡 To run the AI email campaign, use:")
    print("   python ai_email_sender.py")

if __name__ == "__main__":
    cleanup()
