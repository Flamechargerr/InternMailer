#!/usr/bin/env python3
"""
Mock test script for author matching functionality
Tests the matching algorithm without API calls
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from research_publication_finder import ResearchPublicationFinder

def test_author_matching_mock():
    """Test the author matching functionality with mock data"""
    print("🔍 TESTING AUTHOR MATCHING (MOCK DATA)")
    print("=" * 50)
    
    finder = ResearchPublicationFinder()
    
    # Mock author data (similar to what Semantic Scholar returns)
    mock_authors = [
        {
            'name': 'Andrew Y. Ng',
            'affiliations': ['Stanford University', 'Coursera', 'Landing AI'],
            'paperCount': 200,
            'citationCount': 50000
        },
        {
            'name': 'Andrew Ng',
            'affiliations': ['Google Brain', 'Baidu'],
            'paperCount': 150,
            'citationCount': 30000
        },
        {
            'name': 'Andy Ng',
            'affiliations': ['MIT'],
            'paperCount': 50,
            'citationCount': 5000
        },
        {
            'name': 'P. Sneha',
            'affiliations': [],
            'paperCount': 10,
            'citationCount': 45
        }
    ]
    
    print("\n🧪 Testing with search query: 'Andrew Ng Stanford'")
    print(f"\nFound {len(mock_authors)} potential authors:")
    
    best_author = None
    best_score = 0
    
    # Test matching for each mock author
    for i, author in enumerate(mock_authors, 1):
        name = author.get('name', 'Unknown')
        affils = author.get('affiliations', [])
        papers = author.get('paperCount', 0)
        citations = author.get('citationCount', 0)
        
        print(f"\n   {i}. {name}")
        print(f"      Affiliations: {', '.join(affils) if affils else 'None'}")
        print(f"      Papers: {papers}, Citations: {citations}")
        
        # Calculate match score
        score = finder._calculate_match_score(
            "Andrew Ng", 
            name, 
            "Stanford", 
            affils
        )
        print(f"      Match score: {score:.2f}")
        
        if score > best_score:
            best_score = score
            best_author = author
    
    if best_author:
        print(f"\n🎯 Best match: {best_author.get('name', 'Unknown')} (score: {best_score:.2f})")
        
        if best_score > 0.7:
            print("   ✅ GOOD MATCH")
            print("   This author would be selected for publication search")
        else:
            print("   ❌ POOR MATCH")
            print("   Search would continue or return no results")
    else:
        print("\n❌ No authors found")
    
    # Test edge cases
    print("\n" + "-" * 50)
    print("🧪 Testing edge cases:")
    
    test_cases = [
        ("Andrew Ng", "Andrew Y. Ng", "Stanford", ["Stanford University"]),
        ("John Smith", "Andrew Ng", "Stanford", ["Stanford University"]),
        ("Andrew Ng", "Andrew Ng", "", []),
        ("", "Andrew Ng", "Stanford", ["Stanford University"]),
    ]
    
    for search_name, author_name, search_aff, author_affs in test_cases:
        score = finder._calculate_match_score(search_name, author_name, search_aff, author_affs)
        print(f"\n   Search: '{search_name}' @ '{search_aff}'")
        print(f"   Author: '{author_name}' @ {author_affs}")
        print(f"   Score: {score:.2f} ({'✅' if score > 0.7 else '❌'})")
    
    print("\n" + "=" * 50)
    print("✅ Mock test complete!")

if __name__ == "__main__":
    test_author_matching_mock()
