import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Debug: Check if author filtering is working
"""
import requests

# Get Capkun's author ID
url = 'https://api.semanticscholar.org/graph/v1/author/search?query=Srdjan+Capkun&fields=name,paperCount,citationCount,authorId'
r = requests.get(url, timeout=10)
data = r.json()
authors = data.get('data', [])
best = max(authors, key=lambda x: x.get('citationCount', 0))
author_id = best.get('authorId')
print(f"Using author: {best.get('name')} (ID: {author_id}, {best.get('citationCount')} citations)")

# Get papers with author details
papers_url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}/papers?fields=title,year,authors&limit=10"
pr = requests.get(papers_url, timeout=10)
papers = pr.json()

print("\nChecking author verification for papers:")
professor_name = "Srdjan Capkun"
last_name = professor_name.lower().split()[-1]  # "capkun"

for p in papers.get('data', [])[:5]:
    title = p.get('title', '')[:50]
    paper_authors = p.get('authors', []) or []
    author_names = [a.get('name', '').lower() for a in paper_authors]
    
    is_author = any(last_name in name for name in author_names)
    
    print(f"\n  Paper: {title}...")
    print(f"  Authors: {', '.join([a.get('name', '') for a in paper_authors][:3])}")
    print(f"  Is Capkun an author? {is_author}")
