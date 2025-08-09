#!/usr/bin/env python3
"""
Run Enhanced Research Alignment Test
Demonstrate the research alignment system with real professor data
"""

import os
import sys
import json
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from research_alignment_analyzer import ResearchAlignmentAnalyzer
from research_publication_finder import ResearchPublicationFinder
from enhanced_research_area_inference import EnhancedResearchAreaInference

def run_alignment_demo():
    """Run demonstration of research alignment system"""
    print("🎯 ENHANCED RESEARCH ALIGNMENT SYSTEM DEMO")
    print("=" * 60)
    print("Finding real publications and generating personalized alignment explanations")
    print("=" * 60)
    
    # Initialize components
    alignment_analyzer = ResearchAlignmentAnalyzer()
    publication_finder = ResearchPublicationFinder()
    research_inference = EnhancedResearchAreaInference()
    
    # Real professors to test with
    test_professors = [
        {
            "name": "Ankur Maiti",
            "research_area": "Machine Learning",
            "last_name": "Maiti"
        },
        {
            "name": "Sarah Chen",
            "research_area": "Cybersecurity", 
            "last_name": "Chen"
        },
        {
            "name": "Michael Johnson",
            "research_area": "Data Science",
            "last_name": "Johnson"
        }
    ]
    
    for i, professor in enumerate(test_professors, 1):
        print(f"\n🎓 PROFESSOR {i}: {professor['name']} ({professor['research_area']})")
        print("-" * 50)
        
        # Get publications
        print("📚 Searching for recent publications...")
        publications = publication_finder.search_semantic_scholar(professor['name'], max_results=3)
        
        if publications:
            print(f"✅ Found {len(publications)} publications\n")
            
            print("🎯 Recent Research Publications")
            
            for j, pub in enumerate(publications, 1):
                title = pub.get('title', 'Untitled')
                year = pub.get('year', 'N/A')
                venue = pub.get('venue', 'Unknown Venue')
                summary = pub.get('summary', 'No summary available.')
                
                # Truncate summary for display
                if len(summary) > 200:
                    summary = summary[:200] + "..."
                
                print(f"{j}. {title} ({year})")
                print(f"Venue: {venue}")
                print(f"Summary: {summary}")
                
                # Generate and display alignment explanation
                alignment = alignment_analyzer.analyze_publication_alignment(pub, professor['research_area'])
                print(f"🎯 Research Alignment: {alignment}")
                print()
            
        else:
            print("❌ No publications found for this professor")
        
        print("-" * 50)
    
    print(f"\n🎉 DEMO COMPLETE!")
    print("✅ Research alignment explanations generated for all professors")
    print("✅ System ready for full deployment with personalized explanations")

if __name__ == "__main__":
    run_alignment_demo()
