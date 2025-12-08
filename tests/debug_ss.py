import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
"""
Debug Semantic Scholar author search
"""
import requests
from urllib.parse import quote_plus

# Debug: Check what Semantic Scholar returns for Capkun
url = 'https://api.semanticscholar.org/graph/v1/author/search?query=Srdjan+Capkun&fields=name,affiliations,paperCount,citationCount'
r = requests.get(url, timeout=10)
data = r.json()

print('Authors found for Srdjan Capkun:')
for a in data.get('data', [])[:5]:
    name = a.get('name', 'Unknown')
    affs = a.get('affiliations', [])
    papers = a.get('paperCount', 0)
    cites = a.get('citationCount', 0)
    print(f'  Name: {name}')
    print(f'  Affiliations: {affs}')
    print(f'  Papers: {papers}, Citations: {cites}')
    print()
