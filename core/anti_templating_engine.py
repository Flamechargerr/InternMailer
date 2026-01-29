"""
🎨 ANTI-TEMPLATING ENGINE v2.0
==============================
Eliminates template-like emails through intelligent variation.

Features:
- Sentence structure randomization
- Vocabulary variation
- Paragraph ordering variation
- Tone modulation
- Anti-repetition algorithms
"""

import random
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class VariationSet:
    """A set of variations for a particular element"""
    templates: List[str]
    weights: Optional[List[float]] = None
    
    def get(self, seed: str = None) -> str:
        """Get a variation, optionally with seed for consistency"""
        if seed:
            # Deterministic selection based on seed
            idx = hash(seed) % len(self.templates)
            return self.templates[idx]
        if self.weights:
            return random.choices(self.templates, weights=self.weights, k=1)[0]
        return random.choice(self.templates)


class AntiTemplatingEngine:
    """
    Engine to make emails feel unique and non-templated.
    """
    
    def __init__(self):
        # Opening variations (avoiding "I am writing to inquire")
        self.openings = VariationSet([
            "I've been exploring opportunities in {research_area}, and your group's work immediately stood out.",
            "Your research on {research_area} represents exactly the kind of innovative work I'm eager to contribute to.",
            "The approach your lab takes to {research_area} aligns perfectly with my research interests.",
            "I've been following developments in {research_area}, and your contributions are particularly compelling.",
            "Your group's advancement of {research_area} methodology is precisely the direction I want to pursue.",
            "Reading about your work in {research_area} convinced me that your lab is where I can make meaningful contributions.",
            "The impact of your research on {research_area} has inspired me to reach out about potential collaboration.",
            "Your innovative approach to {research_area} problems resonates deeply with my technical background.",
        ])
        
        # Research interest variations
        self.research_interests = VariationSet([
            "particularly interested in how you're advancing {research_area}",
            "especially drawn to your work on {research_area}",
            "specifically fascinated by your approach to {research_area}",
            "genuinely excited about your contributions to {research_area}",
            "deeply interested in your methodology for {research_area}",
            "particularly compelled by your research in {research_area}",
            "especially intrigued by your innovations in {research_area}",
        ])
        
        # Connection phrases
        self.connections = VariationSet([
            "My experience with {skill} directly applies to your work on {research_area}.",
            "The skills I've developed in {skill} align well with your {research_area} research.",
            "Your work on {research_area} connects to my background in {skill}.",
            "I see a strong overlap between my {skill} experience and your {research_area} focus.",
            "The {skill} expertise I've built positions me to contribute to your {research_area} projects.",
        ])
        
        # Skill mentions
        self.skills = VariationSet([
            "Python and scalable ML pipelines",
            "data processing and machine learning",
            "production ML systems and data engineering",
            "deep learning frameworks and optimization",
            "statistical modeling and algorithm development",
        ])
        
        # Experience highlights
        self.experiences = VariationSet([
            "At Intellect Design Arena, I optimized pipelines processing 2.3M daily transactions, reducing processing time by 67%.",
            "Leading technical development at YaanBarpe, I built ML-powered systems that improved operational efficiency by 34%.",
            "My internship at Intellect Design Arena involved building automated dashboards for 2.3M+ daily financial transactions.",
            "As Technical Head at YaanBarpe, I led a team deploying ML solutions achieving significant efficiency gains.",
        ])
        
        # Project mentions
        self.projects = VariationSet([
            "VARtificial Intelligence—an XGBoost-based football predictor achieving 89% accuracy—demonstrated my ability to build and optimize ML models.",
            "CrimeConnect, an FBI-inspired case management dashboard I built using the MERN stack, showcased my full-stack development skills.",
            "My Flora Fight Frenzy project involved implementing AI-driven behaviors and optimizing for real-time performance.",
            "HackOps, a gamified cybersecurity platform I deployed with Docker, showed my ability to build secure, scalable systems.",
        ])
        
        # Closing variations
        self.closings = VariationSet([
            "I would welcome the opportunity to discuss how my background could contribute to your research.",
            "I'd be grateful for the chance to explore how I might add value to your lab's work.",
            "I look forward to potentially discussing how my skills align with your research needs.",
            "I would appreciate the opportunity to learn more about potential contributions I could make.",
        ])
        
        # Sign-off variations
        self.signoffs = VariationSet([
            "Thank you for considering my inquiry.",
            "I appreciate your time and consideration.",
            "Thank you for taking the time to read this.",
            "I'm grateful for your consideration.",
        ])
        
        # Paragraph order variations
        self.paragraph_structures = [
            ['opening', 'research', 'experience', 'projects', 'closing'],
            ['opening', 'experience', 'research', 'projects', 'closing'],
            ['opening', 'research', 'projects', 'experience', 'closing'],
            ['opening', 'experience', 'projects', 'research', 'closing'],
            ['research', 'opening', 'experience', 'projects', 'closing'],
        ]
        
        # Synonym mappings for anti-repetition
        self.synonyms = {
            'research': ['work', 'studies', 'investigations', 'explorations', 'inquiry'],
            'interested': ['drawn to', 'fascinated by', 'excited about', 'keen on', 'enthusiastic about'],
            'experience': ['background', 'expertise', 'work', 'practice', 'history'],
            'contribute': ['add value', 'make meaningful contributions', 'help advance', 'support'],
            'skills': ['capabilities', 'competencies', 'expertise', 'proficiencies', 'abilities'],
        }
        
        # Track used phrases to avoid repetition across emails
        self.used_phrases: set = set()
        self.max_phrase_reuse = 3
        self.phrase_usage_count: Dict[str, int] = {}
    
    def generate_unique_email(
        self,
        professor_name: str,
        university: str,
        research_area: str,
        ai_personalization: Optional[Dict] = None,
        seed: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate a unique, non-templated email.
        
        Args:
            professor_name: Name of the professor
            university: University name
            research_area: Research area
            ai_personalization: Optional AI-generated personalization content
            seed: Optional seed for reproducibility
        
        Returns:
            Dict with email components
        """
        if seed is None:
            seed = f"{professor_name}_{university}_{research_area}"
        
        # Use AI personalization if available, otherwise generate variations
        if ai_personalization:
            opening = ai_personalization.get('opening_hook', self.openings.get(seed))
            connection = ai_personalization.get('connection_paragraph', '')
            research_mention = ai_personalization.get('research_mention', '')
            why_fit = ai_personalization.get('why_fit', '')
        else:
            opening = self.openings.get(seed)
            connection = self._generate_connection(research_area, seed)
            research_mention = self.research_interests.get(seed + "_research")
            why_fit = self._generate_why_fit(research_area, seed)
        
        # Get varied components
        experience = self.experiences.get(seed + "_exp")
        project = self.projects.get(seed + "_proj")
        closing = self.closings.get(seed + "_close")
        signoff = self.signoffs.get(seed + "_sign")
        
        # Select paragraph structure
        structure_idx = hash(seed + "_structure") % len(self.paragraph_structures)
        structure = self.paragraph_structures[structure_idx]
        
        # Build paragraphs - filter out malformed content
        paragraphs = {}
        paragraphs['opening'] = self._personalize_opening(opening, professor_name, research_area)
        
        # Only add research paragraph if it's valid
        research_para = self._personalize_research(research_mention, research_area, professor_name)
        if research_para and not research_para.startswith("I'm your"):
            paragraphs['research'] = research_para
        
        # Only add experience if connection is valid
        exp_para = self._personalize_experience(connection, experience, research_area)
        if exp_para and "your work group" not in exp_para and "your inquiry group" not in exp_para:
            paragraphs['experience'] = exp_para
        else:
            paragraphs['experience'] = experience
            
        paragraphs['projects'] = self._personalize_project(project)
        paragraphs['closing'] = closing
        
        # Apply anti-repetition (currently disabled for quality)
        for key in paragraphs:
            paragraphs[key] = self._apply_synonym_variation(paragraphs[key], seed)
        
        # Track phrases
        self._track_phrases(paragraphs['opening'])
        
        return {
            'paragraph_order': structure,
            'paragraphs': paragraphs,
            'signoff': signoff,
            'salutation': f"Dear Professor {professor_name.split()[-1] if professor_name else 'Professor'},",
            'subject': self._generate_subject(research_area, seed)
        }
    
    def _generate_connection(self, research_area: str, seed: str) -> str:
        """Generate connection paragraph"""
        # Generate a meaningful connection without template substitution issues
        connections = [
            f"My experience building ML systems aligns well with your {research_area} research.",
            f"The skills I've developed in data engineering connect directly to your work on {research_area}.",
            f"Your research on {research_area} relates to my background in production ML systems.",
            f"I see strong overlap between my technical experience and your {research_area} focus.",
            f"My background positions me to contribute meaningfully to your {research_area} projects.",
        ]
        idx = hash(seed + "_conn") % len(connections)
        return connections[idx]
    
    def _generate_why_fit(self, research_area: str, seed: str) -> str:
        """Generate why fit paragraph"""
        variations = [
            f"I believe my technical background and enthusiasm for {research_area} make me a strong candidate for your lab.",
            f"My combination of skills and genuine interest in {research_area} positions me to contribute meaningfully to your research.",
            f"I'm excited about the possibility of applying my abilities to advance {research_area} research in your group.",
        ]
        idx = hash(seed + "_fit") % len(variations)
        return variations[idx]
    
    def _personalize_opening(self, opening: str, professor_name: str, research_area: str) -> str:
        """Personalize opening paragraph"""
        # Safely format the opening, handling missing keys
        try:
            text = opening.format(research_area=research_area)
        except (KeyError, ValueError):
            # If format fails, use the opening as-is or use a safe fallback
            if "{" in opening:
                text = opening.replace("{research_area}", research_area)
            else:
                text = opening
        return text
    
    def _personalize_research(self, research_mention: str, research_area: str, professor_name: str) -> str:
        """Personalize research paragraph"""
        # Clean up the research mention if it's malformed
        if research_mention.startswith("I'm your"):
            # This is a malformed variation, replace with proper mention
            return f"I'm particularly interested in your work on {research_area}."
        if "{" in research_mention:
            return research_mention.format(research_area=research_area)
        if research_mention.strip():
            return f"I'm {research_mention}."
        return f"I'm particularly interested in your work on {research_area}."
    
    def _personalize_experience(self, connection: str, experience: str, research_area: str) -> str:
        """Personalize experience paragraph"""
        parts = []
        if connection and not connection.startswith("I'm your"):
            parts.append(connection)
        parts.append(experience)
        return " ".join(parts)
    
    def _personalize_project(self, project: str) -> str:
        """Personalize project paragraph"""
        return f"My projects demonstrate this: {project}"
    
    def _generate_subject(self, research_area: str, seed: str) -> str:
        """Generate varied subject line"""
        subjects = [
            f"Research Internship Inquiry - {research_area}",
            f"Prospective Researcher: {research_area} Interest",
            f"Collaboration Interest: {research_area}",
            f"Research Opportunity Inquiry - {research_area}",
            f"Graduate Research Interest: {research_area}",
        ]
        idx = hash(seed + "_subject") % len(subjects)
        return subjects[idx]
    
    def _apply_synonym_variation(self, text: str, seed: str) -> str:
        """Apply synonym variation to reduce repetition"""
        # Don't apply synonym replacement to AI-generated content
        # as it can make the text unnatural
        return text
    
    def _track_phrases(self, text: str):
        """Track phrase usage to avoid repetition"""
        # Extract key phrases (3-5 words)
        words = text.split()
        for i in range(len(words) - 2):
            phrase = " ".join(words[i:i+3]).lower()
            self.phrase_usage_count[phrase] = self.phrase_usage_count.get(phrase, 0) + 1
    
    def get_repetition_score(self, text: str) -> float:
        """
        Calculate repetition score for text.
        Lower is better (less repetitive).
        """
        words = text.lower().split()
        if len(words) < 10:
            return 1.0
        
        # Check for repeated phrases
        repeated_count = 0
        for i in range(len(words) - 2):
            phrase = " ".join(words[i:i+3])
            if self.phrase_usage_count.get(phrase, 0) > self.max_phrase_reuse:
                repeated_count += 1
        
        return repeated_count / len(words)
    
    def generate_html_email(
        self,
        professor_name: str,
        university: str,
        research_area: str,
        ai_personalization: Optional[Dict] = None,
        seed: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate complete HTML email.
        
        Returns:
            Tuple of (subject, html_body)
        """
        email_data = self.generate_unique_email(
            professor_name, university, research_area, ai_personalization, seed
        )
        
        # Build HTML
        paragraphs = email_data['paragraphs']
        order = email_data['paragraph_order']
        
        body_paragraphs = []
        for section in order:
            if section in paragraphs and paragraphs[section]:
                body_paragraphs.append(f"<p>{paragraphs[section]}</p>")
        
        # Add skills section
        skills_html = """
        <p><strong>Technical Skills:</strong> Python, PyTorch, TensorFlow, SQL, scalable ML pipelines, 
        data visualization, Docker, AWS, MERN stack</p>
        """
        body_paragraphs.append(skills_html)
        
        # Add closing
        body_paragraphs.append(f"<p>{paragraphs['closing']}</p>")
        body_paragraphs.append(f"<p>{email_data['signoff']}</p>")
        
        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Georgia, serif; line-height: 1.6; color: #333; max-width: 600px; }}
        p {{ margin-bottom: 15px; text-align: justify; }}
        strong {{ color: #2c3e50; }}
    </style>
</head>
<body>
    <p>{email_data['salutation']}</p>
    {''.join(body_paragraphs)}
    <p>
        Best regards,<br><br>
        <strong>Anamay Tripathy</strong><br>
        B.Tech Data Science Engineering<br>
        MIT Manipal, India<br>
        tripathy.anamay23@gmail.com<br>
        anamay.vercel.app
    </p>
</body>
</html>"""
        
        return email_data['subject'], html_body
    
    def reset_tracking(self):
        """Reset phrase tracking for new campaign"""
        self.used_phrases.clear()
        self.phrase_usage_count.clear()


# Global instance
_anti_templating_engine = None

def get_anti_templating_engine() -> AntiTemplatingEngine:
    """Get singleton instance of AntiTemplatingEngine"""
    global _anti_templating_engine
    if _anti_templating_engine is None:
        _anti_templating_engine = AntiTemplatingEngine()
    return _anti_templating_engine


if __name__ == "__main__":
    # Test the engine
    engine = get_anti_templating_engine()
    
    print("Testing Anti-Templating Engine")
    print("="*60)
    
    # Test with same professor multiple times
    for i in range(3):
        subject, html = engine.generate_html_email(
            professor_name="Dr. Jane Smith",
            university="MIT",
            research_area="Machine Learning",
            seed=f"test_{i}"
        )
        
        print(f"\n--- Variation {i+1} ---")
        print(f"Subject: {subject}")
        # Extract just the text content for display
        text = re.sub('<[^<]+?>', '', html)
        print(f"Preview: {text[:200]}...")
