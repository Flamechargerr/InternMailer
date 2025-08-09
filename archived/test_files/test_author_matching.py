#!/usr/bin/env python3
"""
Test script for author matching in ResearchPublicationFinder
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from research_publication_finder import ResearchPublicationFinder

def test_author_matching():
    """Test the author matching functionality"""
    print("🔍 TESTING AUTHOR MATCHING")
    print("=" * 50)
    
    finder = ResearchPublicationFinder()
    
    print("\n🧪 Testing with Andrew Ng (Stanford AI)")
    
    # Search for authors with query
    search_url = "https://api.semanticscholar.org/graph/v1/author/search"
    params = {
        'query': 'Andrew Ng Stanford',
        'limit': 10,
        'fields': 'authorId,name,affiliations,url,paperCount,citationCount'
    }
    
    print("\nSearching for authors with query: Andrew Ng Stanford")
    response = finder.session.get(search_url, params=params)
    
    if response.status_code != 200:
        print(f"❌ Search failed: {response.status_code}")
        if response.status_code == 429:
            print("   Rate limited - trying with just 'Andrew Ng'")
            # Try with simpler query
            params['query'] = 'Andrew Ng'
            response = finder.session.get(search_url, params=params)
        
        if response.status_code != 200:
            print(f"   Still failed: {response.status_code}")
            return
    
    try:
        response_data = response.json()
        authors_data = response_data.get('data', [])
        print(f"\nFound {len(authors_data)} potential authors:")
    except Exception as e:
        print(f"\n❌ Error parsing response: {e}")
        print(f"Response status: {response.status_code}")
        print(f"Response text: {response.text[:200]}...")
        return
    
    best_author = None
    best_score = 0
    
    # Test matching for each author found
    for i, author in enumerate(authors_data[:5], 1):
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
            print("   ✅ GOOD MATCH - Getting papers...")
            
            # Get papers for the best match
            author_id = best_author['authorId']
            papers_url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}/papers"
            params = {
                'limit': 3,
                'fields': 'title,year,abstract,url,venue'
            }
            
            response = finder.session.get(papers_url, params=params)
            if response.status_code == 200:
                papers_data = response.json().get('data', [])
                if papers_data:
                    print(f"\n📚 Recent Papers:")
                    for i, paper in enumerate(papers_data, 1):
                        print(f"\n   {i}. {paper.get('title', 'Untitled')}")
                        print(f"      Year: {paper.get('year', 'N/A')}")
                        print(f"      Venue: {paper.get('venue', 'N/A')}")
                        abstract = paper.get('abstract', '')
                        if abstract:
                            print(f"      Abstract: {abstract[:150]}...")
        else:
            print("   ❌ POOR MATCH")
    else:
        print("\n❌ No authors found")
    
    print("\n" + "=" * 50)
    print("✅ Test complete!")

if __name__ == "__main__":
    test_author_matching()
