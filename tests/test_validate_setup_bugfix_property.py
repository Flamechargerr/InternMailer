"""
Property-Based Tests for Config Validation Fix (Bugfix Spec)
=============================================================

This test suite validates the fix for the profile validation false warning bug.

**Bug Description**: The setup validation system incorrectly reports "Profile file not found"
warnings when `data/profile.yaml` exists but `PROFILE_PATH` is not explicitly set in `.env`.

**Test Strategy**:
1. Bug Condition Exploration (Task 1): Tests that FAIL on unfixed code, demonstrating the bug
2. Preservation Properties (Task 2): Tests that PASS on unfixed code, ensuring no regressions

**Validates: Requirements 1.1, 1.2, 2.1, 2.2, 2.3**
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest
from hypothesis import given, strategies as st, settings, example

from utils.validate_setup import SetupValidator


# ============================================================================
# Task 1: Bug Condition Exploration Test
# ============================================================================
# **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms bug exists
# **Validates: Requirements 2.1, 2.2, 2.3**

class TestBugConditionExploration:
    """
    Property 1: Fault Condition - Profile Detection in Default Locations
    
    For any validation context where config.PROFILE_PATH is empty or unset AND
    a profile file exists in any default location, the validation function SHALL
    detect the profile file and report success (not warning).
    
    **EXPECTED OUTCOME ON UNFIXED CODE**: This test will FAIL, demonstrating the bug
    **EXPECTED OUTCOME ON FIXED CODE**: This test will PASS, confirming the fix works
    """
    
    def test_profile_detected_in_data_yaml(self):
        """
        Test that validation detects profile at data/profile.yaml when PROFILE_PATH is unset.
        
        **Scoped to concrete failing case for deterministic bug reproduction**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup: Create profile file in default location
            data_dir = Path(tmpdir) / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            profile_file = data_dir / "profile.yaml"
            profile_file.write_text("name: Test User\nemail: test@example.com\n")
            
            # Mock config to have empty PROFILE_PATH
            with patch('utils.validate_setup.config') as mock_config:
                mock_config.PROFILE_PATH = ""  # Bug condition: empty PROFILE_PATH
                mock_config.GMAIL_USER = "test@example.com"
                mock_config.GMAIL_APP_PASSWORD = "test_password"
                mock_config.GROQ_API_KEY = "test_key"
                mock_config.JOB_SOURCES_PATH = str(Path(tmpdir) / "job_sources.yaml")
                mock_config.COMPANY_CONTACTS_CSV = str(Path(tmpdir) / "contacts.csv")
                
                # Create dummy files for other validations
                Path(mock_config.JOB_SOURCES_PATH).write_text("sources: []")
                Path(mock_config.COMPANY_CONTACTS_CSV).write_text("email,name\n")
                
                # Change to temp directory so relative paths work
                original_cwd = os.getcwd()
                try:
                    os.chdir(tmpdir)
                    
                    # Execute validation
                    validator = SetupValidator()
                    result = validator.validate_all()
                    
                    # Assert: Validation should detect the profile file
                    # On UNFIXED code: This will FAIL because validation reports warning
                    # On FIXED code: This will PASS because validation detects the file
                    profile_warnings = [w for w in result['warnings'] if 'Profile file not found' in w]
                    assert len(profile_warnings) == 0, (
                        f"Bug detected: Validation reported 'Profile file not found' warning "
                        f"even though {profile_file} exists. This is the expected failure on unfixed code."
                    )
                    
                    # Should have success message instead
                    profile_info = [i for i in result['info'] if 'Profile file found' in i]
                    assert len(profile_info) > 0, (
                        "Validation should report success when profile exists in default location"
                    )
                    
                finally:
                    os.chdir(original_cwd)
    
    def test_profile_detected_in_data_yml(self):
        """Test that validation detects profile at data/profile.yml when PROFILE_PATH is unset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            profile_file = data_dir / "profile.yml"
            profile_file.write_text("name: Test User\nemail: test@example.com\n")
            
            with patch('utils.validate_setup.config') as mock_config:
                mock_config.PROFILE_PATH = ""
                mock_config.GMAIL_USER = "test@example.com"
                mock_config.GMAIL_APP_PASSWORD = "test_password"
                mock_config.GROQ_API_KEY = "test_key"
                mock_config.JOB_SOURCES_PATH = str(Path(tmpdir) / "job_sources.yaml")
                mock_config.COMPANY_CONTACTS_CSV = str(Path(tmpdir) / "contacts.csv")
                
                Path(mock_config.JOB_SOURCES_PATH).write_text("sources: []")
                Path(mock_config.COMPANY_CONTACTS_CSV).write_text("email,name\n")
                
                original_cwd = os.getcwd()
                try:
                    os.chdir(tmpdir)
                    validator = SetupValidator()
                    result = validator.validate_all()
                    
                    profile_warnings = [w for w in result['warnings'] if 'Profile file not found' in w]
                    assert len(profile_warnings) == 0, "Should not report warning when profile.yml exists"
                    
                    profile_info = [i for i in result['info'] if 'Profile file found' in i]
                    assert len(profile_info) > 0, "Should report success for profile.yml"
                finally:
                    os.chdir(original_cwd)
    
    def test_profile_detected_in_root_yaml(self):
        """Test that validation detects profile at profile.yaml (root) when PROFILE_PATH is unset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            profile_file = Path(tmpdir) / "profile.yaml"
            profile_file.write_text("name: Test User\nemail: test@example.com\n")
            
            with patch('utils.validate_setup.config') as mock_config:
                mock_config.PROFILE_PATH = ""
                mock_config.GMAIL_USER = "test@example.com"
                mock_config.GMAIL_APP_PASSWORD = "test_password"
                mock_config.GROQ_API_KEY = "test_key"
                mock_config.JOB_SOURCES_PATH = str(Path(tmpdir) / "job_sources.yaml")
                mock_config.COMPANY_CONTACTS_CSV = str(Path(tmpdir) / "contacts.csv")
                
                Path(mock_config.JOB_SOURCES_PATH).write_text("sources: []")
                Path(mock_config.COMPANY_CONTACTS_CSV).write_text("email,name\n")
                
                original_cwd = os.getcwd()
                try:
                    os.chdir(tmpdir)
                    validator = SetupValidator()
                    result = validator.validate_all()
                    
                    profile_warnings = [w for w in result['warnings'] if 'Profile file not found' in w]
                    assert len(profile_warnings) == 0, "Should not report warning when root profile.yaml exists"
                    
                    profile_info = [i for i in result['info'] if 'Profile file found' in i]
                    assert len(profile_info) > 0, "Should report success for root profile.yaml"
                finally:
                    os.chdir(original_cwd)
    
    def test_profile_detected_in_data_json(self):
        """Test that validation detects profile at data/profile.json when PROFILE_PATH is unset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            profile_file = data_dir / "profile.json"
            profile_file.write_text('{"name": "Test User", "email": "test@example.com"}')
            
            with patch('utils.validate_setup.config') as mock_config:
                mock_config.PROFILE_PATH = ""
                mock_config.GMAIL_USER = "test@example.com"
                mock_config.GMAIL_APP_PASSWORD = "test_password"
                mock_config.GROQ_API_KEY = "test_key"
                mock_config.JOB_SOURCES_PATH = str(Path(tmpdir) / "job_sources.yaml")
                mock_config.COMPANY_CONTACTS_CSV = str(Path(tmpdir) / "contacts.csv")
                
                Path(mock_config.JOB_SOURCES_PATH).write_text("sources: []")
                Path(mock_config.COMPANY_CONTACTS_CSV).write_text("email,name\n")
                
                original_cwd = os.getcwd()
                try:
                    os.chdir(tmpdir)
                    validator = SetupValidator()
                    result = validator.validate_all()
                    
                    profile_warnings = [w for w in result['warnings'] if 'Profile file not found' in w]
                    assert len(profile_warnings) == 0, "Should not report warning when profile.json exists"
                    
                    profile_info = [i for i in result['info'] if 'Profile file found' in i]
                    assert len(profile_info) > 0, "Should report success for profile.json"
                finally:
                    os.chdir(original_cwd)
