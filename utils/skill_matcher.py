"""
Function: match_skills(user_domains: List[str], prof_keywords: List[str]) -> float
 - Compute cosine or Jaccard similarity between your domains and their keywords
 - Return match score 0–1
"""

from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def _jaccard_similarity(set1: set, set2: set) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set1 or not set2:
        return 0.0
    intersection = set1 & set2
    union = set1 | set2
    return len(intersection) / len(union)

def _cosine_similarity(list1: List[str], list2: List[str]) -> float:
    """Compute cosine similarity between two lists of strings using TF-IDF."""
    if not list1 or not list2:
        return 0.0
    try:
        vectorizer = TfidfVectorizer().fit(list1 + list2)
        tfidf = vectorizer.transform([" ".join(list1), " ".join(list2)])
        return float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
    except Exception as e:
        print(f"Error in cosine similarity: {e}")
        return 0.0

def match_skills(user_domains: List[str], prof_keywords: List[str]) -> float:
    """
    Compute similarity between user domains and professor keywords.
    Returns match score between 0–1 (max of Jaccard and cosine similarity).
    """
    set_user = set([d.strip().lower() for d in user_domains])
    set_prof = set([k.strip().lower() for k in prof_keywords])
    jaccard = _jaccard_similarity(set_user, set_prof)
    cosine = _cosine_similarity(user_domains, prof_keywords)
    return round(max(jaccard, cosine), 2)
