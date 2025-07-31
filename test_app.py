#!/usr/bin/env python3
"""
Simple test script to verify the application functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.azure_ai_client import get_azure_ai_client

def test_app_components():
    """Test main application components"""
    
    print("🔍 Testing Application Components...")
    print("-" * 50)
    
    # Test Azure AI client
    print("1. Testing Azure AI Client...")
    client = get_azure_ai_client()
    
    if client.is_available():
        print("   ✅ Azure AI client is available and configured")
        
        # Test email generation
        test_prompt = """Generate a professional email to Prof. Johnson at MIT about a research internship in computer vision. 
        Student name: Anamay Tripathy
        University: MIT Manipal, India
        Field: Data Science"""
        
        try:
            response = client.generate_with_fallback(test_prompt)
            if response and len(response) > 100:
                print("   ✅ Email generation working")
                print(f"   📝 Generated {len(response)} characters")
            else:
                print("   ❌ Email generation failed or too short")
        except Exception as e:
            print(f"   ❌ Email generation error: {e}")
    else:
        print("   ❌ Azure AI client not available")
    
    # Test professor tracker
    print("\n2. Testing Professor Tracker...")
    try:
        from src.professor_tracker import ProfessorTracker
        tracker = ProfessorTracker()
        print("   ✅ Professor tracker imported successfully")
        
        # Load existing data
        tracker.load_tracker()
        prof_count = len(tracker.professors)
        print(f"   📊 Found {prof_count} professors in tracker")
        
    except Exception as e:
        print(f"   ❌ Professor tracker error: {e}")
    
    # Test CSV data
    print("\n3. Testing Professor Data...")
    try:
        import pandas as pd
        df = pd.read_csv('professors_final.csv')
        print(f"   ✅ Loaded {len(df)} professors from CSV")
        print(f"   📋 Columns: {list(df.columns)}")
    except Exception as e:
        print(f"   ❌ CSV loading error: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Application component test completed!")

if __name__ == "__main__":
    test_app_components()
