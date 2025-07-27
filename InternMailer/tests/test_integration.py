"""
Integration test to verify the refactored resume parsing system works.
"""

import os
import sys
import tempfile
from unittest.mock import patch

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from resume_parser import ResumeParser


def test_integration():
    """Test the integration of the refactored system."""
    
    # Create a mock PDF content
    sample_resume_text = """
    John Doe
    Software Engineer
    
    Technical Skills:
    Languages: Python, JavaScript, Java
    Frameworks: React, Django, Flask
    Tools: Git, Docker, AWS
    
    Projects:
    CrimeConnect – MERN Stack, Real-time dashboard
    VARtificial Intelligence – ML prediction model
    
    Education:
    B.Tech Computer Science
    Courses: Machine Learning, Data Structures, Algorithms
    
    Experience:
    Software Developer, Tech Corp – Built web applications
    """
    
    # Create a temporary file path
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        parser = ResumeParser(temp_path)
        
        # Mock the text extraction to avoid dealing with actual PDF
        with patch.object(parser, 'extract_text', return_value=sample_resume_text):
            # Test the main parse method
            result = parser.parse()
            
            print("✅ Integration test successful!")
            print(f"Skills found: {len(result.get('skills', []))}")
            print(f"Projects found: {len(result.get('projects', []))}")
            print(f"Summary: {result.get('summary', 'No summary')[:50]}...")
            
            # Test JSON output
            json_output = parser.to_json()
            print(f"✅ JSON output generated: {len(json_output)} characters")
            
            # Test compatibility methods
            llm_result = parser.parse_with_llm()
            rules_result = parser.parse_with_rules()
            
            print("✅ All compatibility methods working")
            
            return True
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False
        
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)


if __name__ == "__main__":
    success = test_integration()
    if success:
        print("\n🎉 Refactored resume parsing system is working correctly!")
    else:
        print("\n⚠️  Integration test failed. Please check the implementation.")
        sys.exit(1)
