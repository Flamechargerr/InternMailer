#!/usr/bin/env python3
"""
Test the enhanced accuracy of the ResearchPublicationFinder
"""

import csv
import os
from research_publication_finder import ResearchPublicationFinder

def test_real_professors():
    """Test the publication finder with real professors from CSV"""
    finder = ResearchPublicationFinder()
    
    # Read professors from CSV
    csv_file_path = "FINAL_MASTER_EMAIL_DATABASE.csv"
    professors_to_test = []
    
    if os.path.exists(csv_file_path):
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = row.get('name', '').strip()
                university = row.get('university', '').strip()
                # Use professors with complete names and university information
                if name and len(name) > 5 and not name.startswith("Prof.") and university:
                    professors_to_test.append({
                        'name': name,
                        'affiliation': university
                    })
                    
                    # Test with first 5 professors that have complete information
                    if len(professors_to_test) >= 5:
                        break
    
    print("🔍 TESTING ENHANCED RESEARCH PUBLICATION FINDER ACCURACY")
    print("=" * 60)
    print(f"Testing with {len(professors_to_test)} real professors from CSV")
    print("=" * 60)
    
    results = finder.get_publications_for_professors(professors_to_test)
    
    success_count = 0
    for professor_name, publications in results.items():
        print(f"\n👤 {professor_name}")
        if publications:
            success_count += 1
            for i, pub in enumerate(publications, 1):
                print(f"   📄 {i}. {pub['title']} ({pub['year']}) - {pub['venue']}")
                if pub['summary']:
                    print(f"      Summary: {pub['summary'][:100]}...")
        else:
            print("   ⚠️ No recent publications found")
    
    print("\n" + "=" * 60)
    print(f"✅ SUCCESS RATE: {success_count}/{len(professors_to_test)} ({success_count/len(professors_to_test)*100:.1f}%)")
    print("=" * 60)

if __name__ == "__main__":
    test_real_professors()
