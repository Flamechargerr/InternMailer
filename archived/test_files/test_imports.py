#!/usr/bin/env python3
"""
Test script to verify all module imports work properly for the Streamlit pages.
"""

import sys
import os

def test_page_imports():
    """Test imports for each Streamlit page"""
    
    print("Testing Page 1: Professor Outreach imports...")
    try:
        # Add src directory to path like the page does
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
        
        from src.outreach_runner import OutreachRunner
        from src.shared.ui_components import UIComponents
        from src.email_generator import EmailGenerator
        print("✅ Page 1 core imports successful")
        
        # Test missing import
        try:
            from send_email_with_cv import send_email_with_cv
            print("✅ send_email_with_cv import successful")
        except ImportError as e:
            print(f"❌ send_email_with_cv import failed: {e}")
            
    except ImportError as e:
        print(f"❌ Page 1 imports failed: {e}")
    
    print("\nTesting Page 2: Job Applications imports...")
    try:
        from hr_email_generator import HREmailGenerator
        from job_parser import JobParser
        from cv_customizer import CVCustomizer
        from application_tracker import ApplicationTracker
        from hr_finder import HRFinder
        print("✅ Page 2 imports successful")
    except ImportError as e:
        print(f"❌ Page 2 imports failed: {e}")
    
    print("\nTesting Page 3: Professor Scraper imports...")
    try:
        from src.professor_scraper import ProfessorScraper
        print("✅ Page 3 imports successful")
    except ImportError as e:
        print(f"❌ Page 3 imports failed: {e}")

if __name__ == "__main__":
    test_page_imports()
