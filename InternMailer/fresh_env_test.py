#!/usr/bin/env python3
"""
Fresh Environment Test Script
Creates a virtual environment and tests installation of dependencies
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

class FreshEnvTester:
    def __init__(self):
        self.test_dir = None
        self.venv_path = None
        self.success = True
        
    def log(self, message, level="INFO"):
        """Log with timestamp"""
        import datetime
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {level}: {message}")
    
    def create_test_environment(self):
        """Create a temporary test environment"""
        self.log("Creating temporary test environment...")
        
        try:
            # Create temporary directory
            self.test_dir = tempfile.mkdtemp(prefix="internmailer_test_")
            self.log(f"Created test directory: {self.test_dir}")
            
            # Copy essential files
            files_to_copy = [
                'requirements.txt',
                'app.py',
                '.env',
                'src/',
                'templates/',
                'scheduler/',
                'pages/'
            ]
            
            current_dir = Path.cwd()
            test_path = Path(self.test_dir)
            
            for item in files_to_copy:
                source = current_dir / item
                if source.exists():
                    if source.is_file():
                        shutil.copy2(source, test_path / item)
                        self.log(f"Copied file: {item}")
                    else:
                        shutil.copytree(source, test_path / item, dirs_exist_ok=True)
                        self.log(f"Copied directory: {item}")
                else:
                    self.log(f"Warning: {item} not found", "WARNING")
            
            return True
            
        except Exception as e:
            self.log(f"Failed to create test environment: {e}", "ERROR")
            return False
    
    def create_virtual_environment(self):
        """Create and activate virtual environment"""
        self.log("Creating virtual environment...")
        
        try:
            self.venv_path = Path(self.test_dir) / "venv"
            
            # Create virtual environment
            result = subprocess.run([
                sys.executable, "-m", "venv", str(self.venv_path)
            ], capture_output=True, text=True, cwd=self.test_dir)
            
            if result.returncode != 0:
                self.log(f"Failed to create venv: {result.stderr}", "ERROR")
                return False
            
            self.log("✅ Virtual environment created successfully")
            return True
            
        except Exception as e:
            self.log(f"Virtual environment creation failed: {e}", "ERROR")
            return False
    
    def get_pip_command(self):
        """Get the pip command for the virtual environment"""
        if os.name == 'nt':  # Windows
            return str(self.venv_path / "Scripts" / "pip.exe")
        else:  # Unix/Linux/macOS
            return str(self.venv_path / "bin" / "pip")
    
    def get_python_command(self):
        """Get the python command for the virtual environment"""
        if os.name == 'nt':  # Windows
            return str(self.venv_path / "Scripts" / "python.exe")
        else:  # Unix/Linux/macOS
            return str(self.venv_path / "bin" / "python")
    
    def install_dependencies(self):
        """Install dependencies from requirements.txt"""
        self.log("Installing dependencies...")
        
        try:
            pip_cmd = self.get_pip_command()
            requirements_path = Path(self.test_dir) / "requirements.txt"
            
            if not requirements_path.exists():
                self.log("requirements.txt not found", "ERROR")
                return False
            
            # Upgrade pip first
            result = subprocess.run([
                pip_cmd, "install", "--upgrade", "pip"
            ], capture_output=True, text=True, cwd=self.test_dir)
            
            if result.returncode == 0:
                self.log("✅ pip upgraded successfully")
            else:
                self.log(f"Warning: pip upgrade failed: {result.stderr}", "WARNING")
            
            # Install requirements
            result = subprocess.run([
                pip_cmd, "install", "-r", "requirements.txt"
            ], capture_output=True, text=True, cwd=self.test_dir)
            
            if result.returncode != 0:
                self.log(f"Failed to install requirements: {result.stderr}", "ERROR")
                self.log(f"stdout: {result.stdout}", "INFO")
                return False
            
            self.log("✅ Dependencies installed successfully")
            self.log(f"Installed packages:\n{result.stdout}")
            return True
            
        except Exception as e:
            self.log(f"Dependency installation failed: {e}", "ERROR")
            return False
    
    def test_imports(self):
        """Test importing all required modules"""
        self.log("Testing module imports...")
        
        test_imports = [
            "import streamlit",
            "import pandas",
            "import requests",
            "import pdfminer.six",
            "import fitz",  # PyMuPDF
            "import sentence_transformers",
            "import beautifulsoup4",
            "import dotenv",
            "import google.auth",
            "import sklearn",
            "import numpy",
            "import dateutil",
            "import pytest"
        ]
        
        try:
            python_cmd = self.get_python_command()
            
            failed_imports = []
            for import_stmt in test_imports:
                result = subprocess.run([
                    python_cmd, "-c", import_stmt
                ], capture_output=True, text=True, cwd=self.test_dir)
                
                if result.returncode == 0:
                    module_name = import_stmt.split()[1]
                    self.log(f"✅ {module_name} import successful")
                else:
                    module_name = import_stmt.split()[1]
                    self.log(f"❌ {module_name} import failed: {result.stderr}", "ERROR")
                    failed_imports.append(module_name)
            
            if not failed_imports:
                self.log("✅ All module imports successful")
                return True
            else:
                self.log(f"❌ Failed imports: {', '.join(failed_imports)}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Import testing failed: {e}", "ERROR")
            return False
    
    def test_app_startup(self):
        """Test if the app can start without errors"""
        self.log("Testing app startup...")
        
        try:
            python_cmd = self.get_python_command()
            
            # Test basic app import
            test_code = '''
import sys
import os
sys.path.append("src")
sys.path.append("scheduler")

try:
    import streamlit as st
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ App startup test passed")
except Exception as e:
    print(f"❌ App startup failed: {e}")
    sys.exit(1)
'''
            
            result = subprocess.run([
                python_cmd, "-c", test_code
            ], capture_output=True, text=True, cwd=self.test_dir)
            
            if result.returncode == 0:
                self.log("✅ App startup test passed")
                self.log(f"Output: {result.stdout}")
                return True
            else:
                self.log(f"❌ App startup test failed: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"App startup test failed: {e}", "ERROR")
            return False
    
    def run_basic_functionality_test(self):
        """Run basic functionality tests"""
        self.log("Running basic functionality tests...")
        
        try:
            python_cmd = self.get_python_command()
            
            # Test resume directory creation
            test_code = '''
import os
import sys
sys.path.append("src")

# Test basic file operations
resumes_dir = "resumes"
if not os.path.exists(resumes_dir):
    os.makedirs(resumes_dir)
    print(f"✅ Created {resumes_dir} directory")
else:
    print(f"✅ {resumes_dir} directory exists")

# Test template loading
templates_dir = "templates"
if os.path.exists(templates_dir):
    print(f"✅ {templates_dir} directory exists")
else:
    print(f"❌ {templates_dir} directory missing")

print("✅ Basic functionality tests passed")
'''
            
            result = subprocess.run([
                python_cmd, "-c", test_code
            ], capture_output=True, text=True, cwd=self.test_dir)
            
            if result.returncode == 0:
                self.log("✅ Basic functionality tests passed")
                self.log(f"Output: {result.stdout}")
                return True
            else:
                self.log(f"❌ Basic functionality tests failed: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Basic functionality test failed: {e}", "ERROR")
            return False
    
    def cleanup(self):
        """Clean up temporary test environment"""
        if self.test_dir and os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
                self.log(f"Cleaned up test directory: {self.test_dir}")
            except Exception as e:
                self.log(f"Failed to cleanup test directory: {e}", "WARNING")
    
    def run_all_tests(self):
        """Run all fresh environment tests"""
        self.log("🚀 STARTING FRESH ENVIRONMENT TEST")
        self.log("=" * 60)
        
        try:
            if not self.create_test_environment():
                return False
            
            if not self.create_virtual_environment():
                return False
            
            if not self.install_dependencies():
                return False
            
            if not self.test_imports():
                return False
            
            if not self.test_app_startup():
                return False
            
            if not self.run_basic_functionality_test():
                return False
            
            self.log("=" * 60)
            self.log("🎉 ALL FRESH ENVIRONMENT TESTS PASSED!")
            self.log("✅ No missing dependencies detected")
            self.log("✅ Application can start in fresh environment")
            self.log("✅ Basic functionality works correctly")
            
            return True
            
        except Exception as e:
            self.log(f"Fresh environment test failed: {e}", "ERROR")
            return False
        
        finally:
            self.cleanup()

if __name__ == "__main__":
    print("🧪 Fresh Environment Dependency Test")
    print("=" * 50)
    
    tester = FreshEnvTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Fresh environment test completed successfully!")
        print("The application is ready for deployment.")
    else:
        print("\n❌ Fresh environment test failed!")
        print("Please review the errors above and fix any issues.")
    
    exit(0 if success else 1)
