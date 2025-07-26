import logging
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer, util

logging.basicConfig(level=logging.INFO)

class SemanticMatcher:
    """
    Matches resume summary to professor research areas using embeddings.
    """
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)

    def match(self, resume_summary: str, professors: List[Dict[str, Any]], threshold: float = 0.2) -> List[Dict[str, Any]]:
        """
        Compute similarity between resume summary and each professor's research area/homepage content.
        Returns list of professors with similarity > threshold, sorted by score.
        """
        resume_emb = self.model.encode(resume_summary, convert_to_tensor=True)
        matches = []
        for prof in professors:
            research_text = prof.get('research_area', '') or prof.get('homepage_text', '')
            if not research_text:
                continue
            prof_emb = self.model.encode(research_text, convert_to_tensor=True)
            score = float(util.cos_sim(resume_emb, prof_emb))
            if score > threshold:
                prof['similarity'] = score
                matches.append(prof)
        matches.sort(key=lambda x: x['similarity'], reverse=True)
        logging.info(f"Found {len(matches)} matches above threshold {threshold}.")
        return matches

# TODO: Add unit tests for SemanticMatcher 