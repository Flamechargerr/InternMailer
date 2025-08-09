#!/usr/bin/env python3
"""
Debug script for ResearchPublicationFinder publication retrieval issues
"""

from research_publication_finder import ResearchPublicationFinder


def debug_finder():
    """Debug the finder to understand why no publications are returned"""
    finder = ResearchPublicationFinder()
    
    print("🔍 DEBUGGING RESEARCH PUBLICATION FINDER")
    print("=" * 60)
    
    # Test with Andrew Ng
    test_name = "Andrew Ng"
    print(f"\nTesting: {test_name}")
    
    # Enable debug mode to see detailed output
    finder.debug = True
    
    try:
        publications = finder.get_professor_publications(test_name, max_results=3)
        
        print(f"\nResult: Found {len(publications)} publications")
        
        if publications:
            for i, pub in enumerate(publications, 1):
                print(f"\n   Publication {i}:")
                print(f"      Title: {pub.get('title', 'N/A')}")
                print(f"      Year: {pub.get('year', 'N/A')}")
                print(f"      Venue: {pub.get('venue', 'N/A')}")
                print(f"      Summary: {pub.get('summary', 'N/A')}")
        else:
            print("\nNo publications were returned despite match")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Debug complete!")


if __name__ == "__main__":
    debug_finder()
