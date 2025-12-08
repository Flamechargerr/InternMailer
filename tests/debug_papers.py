import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Debug: Check what papers are returned for verified Capkun
"""
import requests

# Get the correct author (276 papers, 23k citations)
url = 'https://api.semanticscholar.org/graph/v1/author/search?query=Srdjan+Capkun&fields=name,affiliations,paperCount,citationCount,authorId'
r = requests.get(url, timeout=10)
data = r.json()

# Find the real one (most citations)
authors = data.get('data', [])
best = max(authors, key=lambda x: x.get('citationCount', 0))
print(f"Best match: {best.get('name')} with {best.get('citationCount')} citations")
print(f"Author ID: {best.get('authorId')}")

# Get their papers
author_id = best.get('authorId')
papers_url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}/papers?fields=title,year,authors&limit=10"
pr = requests.get(papers_url, timeout=10)
papers = pr.json()

print("\nRecent papers:")
for p in papers.get('data', [])[:5]:
    title = p.get('title', '')[:60]
    year = p.get('year', '')
    authors = [a.get('name', '') for a in (p.get('authors', []) or [])][:3]
    print(f"  {year}: {title}...")
    print(f"       Authors: {', '.join(authors)}")
