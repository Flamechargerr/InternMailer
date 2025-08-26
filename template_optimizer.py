#!/usr/bin/env python3
"""
🎨 InternMailing - Email Template Optimizer
==========================================
AI-powered template optimization for higher response rates
"""

import re
import random
from typing import Dict, List, Tuple
from datetime import datetime

class EmailTemplateOptimizer:
    """🎯 Optimize email templates for maximum engagement"""
    
    def __init__(self):
        self.subject_patterns = {
            'research_focused': [
                "Research Collaboration Opportunity - {research_area}",
                "Exploring {research_area} Research Opportunities", 
                "PhD Research Interest in {research_area}",
                "Graduate Research Inquiry - {research_area}",
                "Research Assistant Position - {research_area}"
            ],
            'personal_connection': [
                "Following Your Work in {research_area}",
                "Inspired by Your Research on {research_area}",
                "Question About Your {research_area} Work",
                "Interest in Your {research_area} Research",
                "Admiration for Your {research_area} Publications"
            ],
            'direct_request': [
                "Graduate Student Seeking Research Guidance",
                "Research Opportunity Inquiry",
                "PhD Application - Research Interest Alignment",
                "Potential Research Collaboration",
                "Graduate Research Position"
            ]
        }
        
        self.opening_variations = [
            "I hope this email finds you well.",
            "I hope you're having a great day.",
            "Greetings from {university}!",
            "I trust this message reaches you in good health.",
            "I hope this email finds you in good spirits."
        ]
        
        self.research_interest_phrases = [
            "I am particularly fascinated by",
            "Your work on {topic} has deeply inspired me",
            "I am especially drawn to",
            "I find your research on {topic} incredibly compelling",
            "Your groundbreaking work in {topic} has captured my attention"
        ]
        
        self.closing_variations = [
            "Thank you for your time and consideration.",
            "I appreciate your time and look forward to hearing from you.",
            "Thank you for considering my request.",
            "I would be grateful for any guidance you could provide.",
            "Thank you for your valuable time."
        ]
    
    def optimize_subject_line(self, research_area: str, style: str = "research_focused") -> str:
        """🎯 Generate optimized subject line"""
        patterns = self.subject_patterns.get(style, self.subject_patterns['research_focused'])
        template = random.choice(patterns)
        return template.format(research_area=research_area)
    
    def generate_opening(self, professor_name: str = "", university: str = "") -> str:
        """🎭 Generate personalized opening"""
        opening = random.choice(self.opening_variations)
        if university and "{university}" in opening:
            opening = opening.format(university=university)
        return opening
    
    def optimize_research_mention(self, research_topic: str) -> str:
        """🔬 Optimize research interest expression"""
        phrase = random.choice(self.research_interest_phrases)
        if "{topic}" in phrase:
            phrase = phrase.format(topic=research_topic)
        return phrase
    
    def generate_closing(self) -> str:
        """🎯 Generate professional closing"""
        return random.choice(self.closing_variations)
    
    def create_optimized_template(self, 
                                professor_name: str,
                                university: str,
                                research_area: str,
                                specific_research: str = "",
                                student_background: str = "Data Science Engineering") -> Dict[str, str]:
        """🚀 Create fully optimized email template"""
        
        # Generate components
        subject = self.optimize_subject_line(research_area)
        opening = self.generate_opening(professor_name, university)
        research_phrase = self.optimize_research_mention(specific_research or research_area)
        closing = self.generate_closing()
        
        # Build email body
        body = f"""Dear Prof. {professor_name},

{opening}

I am a {student_background} student at Manipal Institute of Technology, graduating in 2027. {research_phrase} and would love the opportunity to contribute to ongoing research in your lab.

My academic background includes strong foundations in machine learning, data analysis, and research methodologies. I am particularly interested in how {research_area} can be applied to solve real-world challenges.

Would you be available for a brief discussion about potential research opportunities or guidance for someone passionate about {research_area}? I would be grateful for any insights you could share.

{closing}

Best regards,
[Your Name]
{student_background} Student
Manipal Institute of Technology
[Your Email]
[Your LinkedIn Profile]"""

        return {
            'subject': subject,
            'body': body,
            'optimization_score': self._calculate_optimization_score(subject, body),
            'generated_at': datetime.now().isoformat()
        }
    
    def _calculate_optimization_score(self, subject: str, body: str) -> float:
        """📊 Calculate template optimization score"""
        score = 0.0
        
        # Subject line scoring
        if len(subject) > 30 and len(subject) < 60:  # Optimal length
            score += 20
        if any(word in subject.lower() for word in ['research', 'opportunity', 'collaboration']):
            score += 15
        
        # Body scoring
        if 'Dear Prof.' in body:
            score += 10
        if len(body.split()) > 80 and len(body.split()) < 150:  # Optimal length
            score += 20
        if body.count('I') < 5:  # Not too self-focused
            score += 15
        if any(word in body.lower() for word in ['grateful', 'appreciate', 'thank']):
            score += 10
        if body.count('?') >= 1:  # Has questions
            score += 10
        
        return min(score, 100.0)
    
    def A_B_test_templates(self, 
                          professor_name: str,
                          university: str, 
                          research_area: str,
                          num_variants: int = 3) -> List[Dict]:
        """🧪 Generate A/B test template variants"""
        variants = []
        
        styles = ['research_focused', 'personal_connection', 'direct_request']
        
        for i in range(num_variants):
            style = styles[i % len(styles)]
            
            # Create variant with different style
            variant = self.create_optimized_template(
                professor_name, university, research_area
            )
            variant['variant_id'] = f"Template_{chr(65 + i)}"  # A, B, C, etc.
            variant['style'] = style
            
            variants.append(variant)
        
        # Sort by optimization score
        variants.sort(key=lambda x: x['optimization_score'], reverse=True)
        
        return variants
    
    def export_templates(self, templates: List[Dict], filename: str = None) -> str:
        """💾 Export optimized templates"""
        if not filename:
            filename = f"optimized_templates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(templates, f, indent=2, ensure_ascii=False)
        
        return filename

def demo_optimizer():
    """🎬 Demonstrate template optimization"""
    print("🎨 EMAIL TEMPLATE OPTIMIZER DEMO")
    print("=" * 40)
    
    optimizer = EmailTemplateOptimizer()
    
    # Generate A/B test variants
    variants = optimizer.A_B_test_templates(
        professor_name="Dr. Sarah Chen",
        university="Stanford University", 
        research_area="Machine Learning",
        num_variants=3
    )
    
    print(f"📧 Generated {len(variants)} template variants:")
    print()
    
    for variant in variants:
        print(f"🔤 {variant['variant_id']} (Score: {variant['optimization_score']:.1f}%)")
        print(f"📋 Subject: {variant['subject']}")
        print(f"🎯 Style: {variant['style']}")
        print(f"📝 Body Preview: {variant['body'][:100]}...")
        print("-" * 50)
    
    # Export templates
    filename = optimizer.export_templates(variants)
    print(f"💾 Templates exported to: {filename}")

if __name__ == "__main__":
    demo_optimizer()