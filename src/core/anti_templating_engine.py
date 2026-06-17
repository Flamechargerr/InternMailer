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

from utils.profile import get_profile, Profile


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
    
    def __init__(self, profile: Optional[Profile] = None):
        self.profile = profile or get_profile()

        # Opening variations (avoid template phrasing)
        self.openings = VariationSet([
            "I've been exploring opportunities in {focus_area}, and your team's work at {company} stood out.",
            "Your work in {focus_area} aligns with the kind of impact I want to contribute at {company}.",
            "The approach your team takes to {focus_area} resonates with my background and interests.",
            "I've been following developments in {focus_area}, and your work at {company} is particularly compelling.",
            "Your team's focus on {focus_area} is exactly the direction I want to pursue.",
            "Reading about {company}'s work in {focus_area} convinced me it could be a strong fit.",
            "The impact of your work in {focus_area} inspired me to reach out.",
            "Your approach to {focus_area} problems resonates with my technical background.",
        ])
        
        # Interest variations
        self.research_interests = VariationSet([
            "particularly interested in how your team advances {focus_area}",
            "especially drawn to your work on {focus_area}",
            "specifically fascinated by your approach to {focus_area}",
            "genuinely excited about your contributions to {focus_area}",
            "deeply interested in your methodology for {focus_area}",
            "particularly compelled by your work in {focus_area}",
            "especially intrigued by your innovations in {focus_area}",
        ])
        
        # Connection phrases
        self.connections = VariationSet([
            "My experience with {skill} directly applies to your work in {focus_area}.",
            "The skills I've developed in {skill} align well with your {focus_area} focus.",
            "Your work in {focus_area} connects to my background in {skill}.",
            "I see a strong overlap between my {skill} experience and your {focus_area} goals.",
            "The {skill} expertise I've built positions me to contribute to your {focus_area} initiatives.",
        ])
        
        # Skill mentions
        self.skills = VariationSet(self._build_skill_variations())
        
        # Experience highlights
        self.experiences = VariationSet(
            self.profile.get("experience_highlights")
            or [
                "In a recent role, I delivered system improvements that increased reliability and performance.",
                "I have led cross-functional efforts to ship features that improved user outcomes.",
                "My experience includes building and automating workflows to reduce manual effort.",
            ]
        )
        
        # Project mentions
        self.projects = VariationSet(
            self.profile.get("project_highlights")
            or [
                "I recently delivered a project that combined data processing with automation to improve turnaround time.",
                "One of my projects focused on building a reliable API and monitoring pipeline.",
            ]
        )
        
        # Closing variations
        self.closings = VariationSet([
            "I would welcome the opportunity to discuss how my background could contribute to your team.",
            "I'd be grateful for the chance to explore how I might add value in this role.",
            "I would appreciate the opportunity to learn more about the role and how I can contribute.",
            "If there's a fit, I'd value the chance to discuss how I could help the team.",
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
        contact_name: str,
        company: str,
        focus_area: str,
        ai_personalization: Optional[Dict] = None,
        seed: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate a unique, non-templated email.
        
        Args:
            contact_name: Name of the contact
            company: Company or organization
            focus_area: Target role or focus area
            ai_personalization: Optional AI-generated personalization content
            seed: Optional seed for reproducibility
        
        Returns:
            Dict with email components
        """
        if seed is None:
            seed = f"{contact_name}_{company}_{focus_area}"
        
        # Use AI personalization if available, otherwise generate variations
        if ai_personalization:
            opening = ai_personalization.get('opening_hook', self.openings.get(seed))
            connection = ai_personalization.get('connection_paragraph', '')
            research_mention = ai_personalization.get('research_mention', '')
            why_fit = ai_personalization.get('why_fit', '')
        else:
            opening = self.openings.get(seed)
            connection = self._generate_connection(focus_area, seed)
            research_mention = self.research_interests.get(seed + "_research")
            why_fit = self._generate_why_fit(focus_area, seed)
        
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
        paragraphs['opening'] = self._personalize_opening(opening, contact_name, company, focus_area)
        
        # Only add research paragraph if it's valid
        research_para = self._personalize_research(research_mention, focus_area)
        if research_para and not research_para.startswith("I'm your"):
            paragraphs['research'] = research_para
        
        # Only add experience if connection is valid
        exp_para = self._personalize_experience(connection, experience, focus_area)
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
            'salutation': self._build_salutation(contact_name),
            'subject': self._generate_subject(company, focus_area, seed)
        }
    
    def _generate_connection(self, focus_area: str, seed: str) -> str:
        """Generate connection paragraph"""
        # Generate a meaningful connection without template substitution issues
        connections = [
            f"My experience building reliable systems aligns well with your {focus_area} work.",
            f"The skills I've developed in automation and data workflows connect to your {focus_area} focus.",
            f"Your work in {focus_area} relates to my background in building production systems.",
            f"I see strong overlap between my technical experience and your {focus_area} goals.",
            f"My background positions me to contribute meaningfully to your {focus_area} initiatives.",
        ]
        idx = hash(seed + "_conn") % len(connections)
        return connections[idx]
    
    def _generate_why_fit(self, focus_area: str, seed: str) -> str:
        """Generate why fit paragraph"""
        variations = [
            f"I believe my technical background and enthusiasm for {focus_area} make me a strong candidate for your team.",
            f"My combination of skills and genuine interest in {focus_area} positions me to contribute meaningfully.",
            f"I'm excited about the possibility of applying my abilities to advance {focus_area} work in your group.",
        ]
        idx = hash(seed + "_fit") % len(variations)
        return variations[idx]
    
    def _personalize_opening(self, opening: str, contact_name: str, company: str, focus_area: str) -> str:
        """Personalize opening paragraph"""
        # Safely format the opening, handling missing keys
        try:
            text = opening.format(focus_area=focus_area, company=company)
        except (KeyError, ValueError):
            # If format fails, use the opening as-is or use a safe fallback
            if "{" in opening:
                text = opening.replace("{focus_area}", focus_area).replace("{company}", company)
            else:
                text = opening
        return text
    
    def _personalize_research(self, research_mention: str, focus_area: str) -> str:
        """Personalize research paragraph"""
        if not research_mention:
            return ""
        text = research_mention.strip()
        # Clean up malformed variations
        if text.startswith("I'm your"):
            text = f"I'm particularly interested in {focus_area}"
        if "{" in text:
            try:
                text = text.format(focus_area=focus_area)
            except Exception:
                text = text.replace("{focus_area}", focus_area)
        text = text.strip()
        if not text:
            return ""
        if text[-1] not in ".!?":
            text += "."
        return text
    
    def _personalize_experience(self, connection: str, experience: str, focus_area: str) -> str:
        """Personalize experience paragraph"""
        parts = []
        if connection and not connection.startswith("I'm your"):
            parts.append(connection)
        parts.append(experience)
        return " ".join(parts)
    
    def _personalize_project(self, project: str) -> str:
        """Personalize project paragraph"""
        return f"My projects demonstrate this: {project}"
    
    def _generate_subject(self, company: str, focus_area: str, seed: str) -> str:
        """Generate varied subject line"""
        subjects = [
            f"Application for {focus_area} at {company}",
            f"Interest in {focus_area} opportunities at {company}",
            f"{focus_area} opportunity inquiry - {company}",
            f"Exploring {focus_area} roles at {company}",
            f"{company} - {focus_area} application",
        ]
        idx = hash(seed + "_subject") % len(subjects)
        return subjects[idx]

    def _build_salutation(self, contact_name: str) -> str:
        """Build a salutation with a safe fallback."""
        if contact_name:
            first_name = contact_name.split()[0]
            return f"Dear {first_name},"
        return "Dear Hiring Manager,"

    def _build_skill_variations(self) -> List[str]:
        """Build a set of skill phrases from the profile."""
        skills = self.profile.get("skills") or []
        if isinstance(skills, dict):
            flat = []
            for values in skills.values():
                if isinstance(values, list):
                    flat.extend(values)
            skills = flat

        skills = [s for s in skills if isinstance(s, str)]
        if not skills:
            return [
                "Python, SQL, and automation",
                "data processing and reliable systems",
                "API development and workflow optimization",
            ]

        top = ", ".join(skills[:3])
        alt = ", ".join(skills[3:6]) if len(skills) > 3 else top
        return [
            top,
            alt,
            f"{top} and delivery-focused execution",
        ]
    
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
        contact_name: str,
        company: str,
        focus_area: str,
        ai_personalization: Optional[Dict] = None,
        seed: Optional[str] = None,
        profile: Optional[Profile] = None
    ) -> Tuple[str, str]:
        """
        Generate complete HTML email.
        
        Returns:
            Tuple of (subject, html_body)
        """
        if profile:
            self.profile = profile
        email_data = self.generate_unique_email(
            contact_name, company, focus_area, ai_personalization, seed
        )
        
        # Build HTML
        paragraphs = email_data['paragraphs']
        order = email_data['paragraph_order']
        
        body_paragraphs = []
        for section in order:
            if section in paragraphs and paragraphs[section]:
                if section == "closing":
                    continue
                body_paragraphs.append(f"<p>{self._sanitize_paragraph(paragraphs[section])}</p>")
        
        # Add skills section
        skills = self.profile.get("skills") or []
        if isinstance(skills, dict):
            flat = []
            for values in skills.values():
                if isinstance(values, list):
                    flat.extend(values)
            skills = flat
        skills = [s for s in skills if isinstance(s, str)]
        if skills:
            skills_html = f"<p><strong>Core Skills:</strong> {', '.join(skills[:6])}</p>"
            body_paragraphs.append(skills_html)
        
        # Add closing once
        if paragraphs.get('closing'):
            body_paragraphs.append(f"<p>{self._sanitize_paragraph(paragraphs['closing'])}</p>")
        body_paragraphs.append(f"<p>{email_data['signoff']}</p>")

        # De-duplicate identical paragraphs
        seen = set()
        deduped = []
        for para in body_paragraphs:
            plain = re.sub(r'<[^>]+>', '', para).strip().lower()
            if not plain or plain in seen:
                continue
            seen.add(plain)
            deduped.append(para)
        body_paragraphs = deduped
        
        signature = self.profile.signature_html()
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
        {signature}
    </p>
</body>
</html>"""
        
        return email_data['subject'], html_body

    def _sanitize_paragraph(self, text: str) -> str:
        """Clean up awkward AI phrasing and academic wording."""
        if not text:
            return text
        cleaned = text.strip()
        cleaned = re.sub(r"^I'm the\s+", "The ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^I am the\s+", "The ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\bprofessor\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\blab\b", "team", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\bresearch\b", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        cleaned = re.sub(r"\.{2,}", ".", cleaned)
        return cleaned.strip()
    
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
    
    # Test with same contact multiple times
    for i in range(3):
        subject, html = engine.generate_html_email(
            contact_name="Jane Smith",
            company="Example Corp",
            focus_area="Machine Learning",
            seed=f"test_{i}"
        )
        
        print(f"\n--- Variation {i+1} ---")
        print(f"Subject: {subject}")
        # Extract just the text content for display
        text = re.sub('<[^<]+?>', '', html)
        print(f"Preview: {text[:200]}...")
