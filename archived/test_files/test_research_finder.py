#!/usr/bin/env python3
"""
Test script for ResearchPublicationFinder
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from research_publication_finder import ResearchPublicationFinder

def test_research_finder():
    """Test the ResearchPublicationFinder with sample professors"""
    print("🔍 TESTING RESEARCH PUBLICATION FINDER")
    print("=" * 50)
    
    finder = ResearchPublicationFinder()
    
    # Test with Andrew Ng (should work)
    print("\n🧪 Testing with Andrew Ng")
    publications = finder.search_semantic_scholar("Andrew Ng", "Stanford", max_results=3)
    
    print("\n📝 Results:")
    if publications:
        print(f"✅ Found {len(publications)} publications:")
        for i, pub in enumerate(publications, 1):
            print(f"\n   {i}. {pub.get('title', 'No title')}")
            print(f"      Year: {pub.get('year', 'N/A')}")
            print(f"      Venue: {pub.get('venue', 'N/A')}")
            print(f"      Citations: {pub.get('citationCount', 0)}")
            print(f"      Summary: {pub.get('summary', 'No summary')[:100]}...")
    else:
        print("❌ No publications found")
    
    print("\n" + "=" * 50)
    print("✅ Test complete!")

if __name__ == "__main__":
    test_research_finder()
