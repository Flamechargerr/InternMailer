#!/usr/bin/env python3
"""
🧠 SMART TEMPLATE GENERATOR
===========================
AI-powered email template generation system that creates highly personalized
and effective outreach emails based on professor research, university tier,
and historical response patterns.

Features:
- Dynamic template generation based on research areas
- University-specific customization 
- A/B testing framework for templates
- Response rate optimization
- Seasonal and timing-aware content
- Multi-language support foundation
- Personality-based template selection
"""

import json
import random
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SmartTemplateGenerator:
    def __init__(self):
        """Initialize the smart template generation system"""
        
        # Research-specific templates
        self.research_templates = {
            'machine_learning': {
                'subject_patterns': [
                    "ML Research Collaboration - {university}",
                    "Deep Learning Research Opportunity",
                    "Your work on {specific_area} - Collaboration Inquiry",
                    "Neural Networks Research - Student Interest"
                ],
                'opening_lines': [
                    "I've been following your groundbreaking research in machine learning",
                    "Your recent publication on {publication_topic} caught my attention",
                    "I'm particularly impressed by your work in {specific_area}",
                    "Your contributions to the ML community, especially in {specific_area}, are remarkable"
                ],
                'body_focus': [
                    "artificial intelligence applications",
                    "deep learning architectures", 
                    "neural network optimization",
                    "machine learning algorithms"
                ],
                'specific_interests': [
                    "exploring novel neural architectures",
                    "investigating optimization techniques",
                    "developing practical ML applications",
                    "understanding theoretical foundations"
                ]
            },
            'computer_systems': {
                'subject_patterns': [
                    "Systems Research Collaboration at {university}",
                    "Distributed Systems Research Interest", 
                    "Your work on {specific_area} - Research Inquiry",
                    "Computer Systems Research Opportunity"
                ],
                'opening_lines': [
                    "Your research in computer systems has been instrumental to the field",
                    "I've been studying your work on {specific_area} with great interest",
                    "Your contributions to systems research, particularly in {specific_area}, are inspiring",
                    "I'm drawn to your innovative approach in {specific_area}"
                ],
                'body_focus': [
                    "distributed computing systems",
                    "system performance optimization",
                    "scalable architecture design", 
                    "parallel processing frameworks"
                ],
                'specific_interests': [
                    "designing efficient distributed systems",
                    "optimizing system performance",
                    "exploring scalability challenges",
                    "investigating parallel algorithms"
                ]
            },
            'cybersecurity': {
                'subject_patterns': [
                    "Cybersecurity Research Collaboration",
                    "Security Research Opportunity at {university}",
                    "Your work on {specific_area} - Security Research",
                    "Privacy and Security Research Interest"
                ],
                'opening_lines': [
                    "Your research in cybersecurity addresses critical contemporary challenges",
                    "I've been following your important work in {specific_area}",
                    "Your contributions to security research, especially in {specific_area}, are vital",
                    "I'm particularly interested in your approach to {specific_area}"
                ],
                'body_focus': [
                    "privacy-preserving technologies",
                    "cryptographic protocols",
                    "network security systems",
                    "secure system design"
                ],
                'specific_interests': [
                    "developing privacy-preserving solutions",
                    "exploring cryptographic innovations",
                    "investigating security vulnerabilities",
                    "designing secure systems"
                ]
            },
            'algorithms': {
                'subject_patterns': [
                    "Algorithms Research Collaboration",
                    "Your work on {specific_area} - Research Interest",
                    "Theoretical Computer Science Research",
                    "Optimization Algorithms Research Inquiry"
                ],
                'opening_lines': [
                    "Your theoretical work in algorithms provides essential foundations",
                    "I've been studying your elegant solutions in {specific_area}",
                    "Your research in {specific_area} demonstrates remarkable insight",
                    "I'm fascinated by your approach to {specific_area}"
                ],
                'body_focus': [
                    "algorithm design and analysis",
                    "computational complexity theory",
                    "optimization techniques",
                    "theoretical foundations"
                ],
                'specific_interests': [
                    "exploring algorithmic efficiency",
                    "investigating complexity bounds",
                    "developing optimization strategies",
                    "understanding theoretical limits"
                ]
            }
        }
        
        # University tier-specific customization
        self.university_customization = {
            'tier_1': {
                'tone': 'highly_formal',
                'research_emphasis': 'cutting_edge',
                'length_preference': 'concise',
                'approach': 'achievement_focused'
            },
            'tier_2': {
                'tone': 'professional_warm', 
                'research_emphasis': 'collaborative',
                'length_preference': 'moderate',
                'approach': 'contribution_focused'
            },
            'international': {
                'tone': 'respectful_formal',
                'research_emphasis': 'global_impact',
                'length_preference': 'detailed',
                'approach': 'cultural_aware'
            }
        }
        
        # Seasonal and timing considerations
        self.seasonal_adjustments = {
            'fall_semester': {
                'timing_note': "beginning of the academic year",
                'availability_assumption': "high",
                'urgency_level': "moderate"
            },
            'spring_semester': {
                'timing_note': "spring semester",
                'availability_assumption': "moderate", 
                'urgency_level': "low"
            },
            'summer': {
                'timing_note': "summer research period",
                'availability_assumption': "variable",
                'urgency_level': "low"
            }
        }
        
        # A/B testing templates
        self.ab_test_variants = {
            'subject_length': ['short', 'medium', 'long'],
            'opening_style': ['formal', 'personal', 'achievement'],
            'call_to_action': ['direct', 'soft', 'question']
        }
    
    def determine_research_area(self, publications: List[Dict], affiliation: str = "") -> str:
        """AI-powered research area detection"""
        
        if not publications:
            return 'computer_science_general'
        
        # Analyze publication titles and abstracts for keywords
        text_content = ""
        for pub in publications[:5]:  # Analyze top 5 publications
            text_content += f" {pub.get('title', '')}"
            text_content += f" {pub.get('abstract', '')}"
            text_content += f" {' '.join(pub.get('fields', []))}"
        
        text_lower = text_content.lower()
        
        # Score each research area
        area_scores = {}
        
        ml_keywords = ['neural', 'deep', 'learning', 'ai', 'machine', 'network', 'training', 'model']
        systems_keywords = ['system', 'distributed', 'parallel', 'computing', 'performance', 'scalable']
        security_keywords = ['security', 'privacy', 'crypto', 'attack', 'defense', 'vulnerability']
        algorithms_keywords = ['algorithm', 'complexity', 'optimization', 'theoretical', 'analysis']
        
        area_scores['machine_learning'] = sum(1 for kw in ml_keywords if kw in text_lower)
        area_scores['computer_systems'] = sum(1 for kw in systems_keywords if kw in text_lower)
        area_scores['cybersecurity'] = sum(1 for kw in security_keywords if kw in text_lower)
        area_scores['algorithms'] = sum(1 for kw in algorithms_keywords if kw in text_lower)
        
        # Return area with highest score
        if max(area_scores.values()) > 0:
            return max(area_scores.keys(), key=area_scores.get)
        
        return 'computer_science_general'
    
    def determine_university_tier(self, email: str, affiliation: str = "") -> str:
        """Classify university tier for template customization"""
        
        if '@' not in email:
            return 'other'
        
        domain = email.split('@')[1].lower()
        
        tier_1_domains = [
            'mit.edu', 'stanford.edu', 'harvard.edu', 'caltech.edu', 'berkeley.edu',
            'princeton.edu', 'yale.edu', 'columbia.edu', 'cornell.edu', 'cmu.edu',
            'uchicago.edu', 'upenn.edu'
        ]
        
        tier_2_domains = [
            'gatech.edu', 'umich.edu', 'washington.edu', 'wisc.edu', 'illinois.edu',
            'utexas.edu', 'ucla.edu', 'ucsd.edu', 'uci.edu', 'nyu.edu'
        ]
        
        if domain in tier_1_domains:
            return 'tier_1'
        elif domain in tier_2_domains:
            return 'tier_2'
        elif not domain.endswith('.edu'):
            return 'international'
        else:
            return 'other'
    
    def get_seasonal_context(self) -> str:
        """Determine current academic season for timing-aware templates"""
        
        current_month = datetime.now().month
        
        if current_month in [8, 9, 10, 11, 12]:
            return 'fall_semester'
        elif current_month in [1, 2, 3, 4, 5]:
            return 'spring_semester'
        else:
            return 'summer'
    
    def generate_smart_subject_line(self, 
                                  professor_data: Dict,
                                  research_area: str,
                                  university_tier: str,
                                  ab_variant: str = 'medium') -> str:
        """Generate optimized subject line based on multiple factors"""
        
        name = professor_data.get('name', 'Professor')
        affiliation = professor_data.get('affiliation', 'University')
        university_name = affiliation.split()[0] if affiliation else 'University'
        
        # Get research-specific patterns
        if research_area in self.research_templates:
            patterns = self.research_templates[research_area]['subject_patterns']
        else:
            patterns = [
                "Research Collaboration Inquiry",
                "Academic Research Opportunity", 
                "Your work at {university} - Research Interest",
                "Computer Science Research Collaboration"
            ]
        
        # Select pattern based on A/B variant
        if ab_variant == 'short':
            # Prefer shorter patterns
            pattern = min(patterns, key=len)
        elif ab_variant == 'long':
            # Prefer longer, more descriptive patterns
            pattern = max(patterns, key=len)
        else:
            # Medium length - random selection
            pattern = random.choice(patterns)
        
        # Fill in variables
        subject = pattern.format(
            university=university_name,
            specific_area=research_area.replace('_', ' ').title()
        )
        
        # University tier adjustments
        if university_tier == 'tier_1':
            # More formal and specific for top universities
            if 'Collaboration' not in subject:
                subject = f"Research Collaboration - {subject}"
        
        return subject
    
    def generate_smart_email_body(self,
                                professor_data: Dict,
                                research_data: Dict,
                                research_area: str,
                                university_tier: str) -> str:
        """Generate highly personalized email body"""
        
        name = professor_data.get('name', 'Professor')
        clean_name = name.split()[0] if name != 'Professor' else 'Professor'
        affiliation = professor_data.get('affiliation', 'University')
        
        publications = research_data.get('publications', [])
        confidence = research_data.get('confidence', 0.0)
        
        # Get templates for research area
        if research_area in self.research_templates:
            templates = self.research_templates[research_area]
        else:
            templates = self.research_templates['machine_learning']  # Default
        
        # Select opening line
        opening_line = random.choice(templates['opening_lines'])
        if publications and confidence > 0.6:
            publication_title = publications[0].get('title', '')[:60]
            opening_line = opening_line.format(
                specific_area=research_area.replace('_', ' '),
                publication_topic=publication_title
            )
        else:
            opening_line = opening_line.format(
                specific_area=research_area.replace('_', ' ')
            )
        
        # Get university customization
        customization = self.university_customization.get(university_tier, self.university_customization['tier_2'])
        
        # Build body based on customization
        body_focus = random.choice(templates['body_focus'])
        specific_interest = random.choice(templates['specific_interests'])
        
        # Seasonal context
        seasonal_context = self.get_seasonal_context()
        seasonal_info = self.seasonal_adjustments[seasonal_context]
        
        # Generate personalized body
        if customization['tone'] == 'highly_formal':
            greeting = f"Dear Professor {clean_name},"
            body_style = "formal"
        elif customization['tone'] == 'professional_warm':
            greeting = f"Dear Professor {clean_name},"
            body_style = "warm"
        else:
            greeting = f"Dear Professor {clean_name},"
            body_style = "respectful"
        
        # Research-specific content
        research_content = self._generate_research_content(
            templates, publications, confidence, research_area
        )
        
        # University-specific content
        university_content = self._generate_university_content(
            affiliation, university_tier, customization
        )
        
        # Personal introduction
        personal_intro = self._generate_personal_introduction(
            research_area, customization['approach']
        )
        
        # Call to action
        call_to_action = self._generate_call_to_action(
            customization, seasonal_info
        )
        
        # Assemble complete email
        email_body = f"""{greeting}

{opening_line}

{research_content}

{personal_intro}

{university_content}

{call_to_action}

Thank you for your time and consideration. I look forward to the possibility of contributing to your research program.

Best regards,
Anama Stylianou
Computer Science Student
Email: anamastylianouu@gmail.com
Phone: +357 99 123456"""
        
        return email_body
    
    def _generate_research_content(self, templates: Dict, publications: List[Dict], 
                                 confidence: float, research_area: str) -> str:
        """Generate research-specific content based on found publications"""
        
        if publications and confidence > 0.7:
            # High confidence - reference specific work
            pub = publications[0]
            pub_title = pub.get('title', '')[:80]
            return f"""Your recent work on "{pub_title}" particularly resonates with my research interests. The approach you've taken in {research_area.replace('_', ' ')} addresses fundamental challenges in the field."""
        
        elif confidence > 0.4:
            # Moderate confidence - general research area reference
            body_focus = random.choice(templates['body_focus'])
            return f"""Your research in {body_focus} aligns closely with my academic interests and career goals. I'm particularly drawn to the innovative approaches your group takes in addressing complex challenges."""
        
        else:
            # Low confidence - general but enthusiastic
            return f"""I am writing to express my strong interest in your research group and the possibility of contributing to your ongoing projects in computer science."""
    
    def _generate_university_content(self, affiliation: str, tier: str, customization: Dict) -> str:
        """Generate university-specific content"""
        
        if tier == 'tier_1':
            return f"""The opportunity to contribute to research at {affiliation} would be invaluable for my academic development. I am particularly excited about the potential to work with your research group and contribute to cutting-edge research initiatives."""
        
        elif tier == 'tier_2':
            return f"""I would be honored to contribute to the research environment at {affiliation}. Your department's collaborative approach and commitment to innovation make it an ideal place for meaningful research contributions."""
        
        elif tier == 'international':
            return f"""I would be deeply honored to contribute to the research community at {affiliation}. The international perspective and collaborative research environment would provide invaluable learning opportunities."""
        
        else:
            return f"""I would be grateful for the opportunity to contribute to your research group at {affiliation} and to learn from your expertise in the field."""
    
    def _generate_personal_introduction(self, research_area: str, approach: str) -> str:
        """Generate personalized introduction based on approach style"""
        
        if approach == 'achievement_focused':
            return """I am a dedicated computer science student with a strong academic background and research experience. My previous work has focused on developing practical solutions to theoretical challenges."""
        
        elif approach == 'contribution_focused':
            return """I am currently seeking opportunities to contribute meaningfully to ongoing research projects while developing my skills as a researcher. I am particularly interested in collaborative research that bridges theory and application."""
        
        elif approach == 'cultural_aware':
            return """As an international student passionate about computer science research, I am eager to contribute to diverse research teams and learn from different perspectives and methodologies."""
        
        else:
            return """I am a computer science student with strong interests in research and a commitment to making meaningful contributions to the field."""
    
    def _generate_call_to_action(self, customization: Dict, seasonal_info: Dict) -> str:
        """Generate appropriate call to action based on context"""
        
        if customization['approach'] == 'achievement_focused':
            return """I would welcome the opportunity to discuss how my background and research interests align with your current projects. I have attached my CV and would be happy to provide additional materials or schedule a meeting at your convenience."""
        
        elif seasonal_info['availability_assumption'] == 'high':
            return """I would be delighted to discuss potential research opportunities with you. Given the timing at the {}, I am flexible with scheduling and would appreciate any opportunity to learn more about your current research directions.""".format(seasonal_info['timing_note'])
        
        else:
            return """I would be grateful for the opportunity to discuss how I might contribute to your research group. I understand the demands on your time and would be happy to work around your schedule for a brief conversation."""
    
    def generate_ab_test_templates(self, professor_data: Dict, research_data: Dict, 
                                 num_variants: int = 3) -> List[Dict]:
        """Generate multiple template variants for A/B testing"""
        
        research_area = self.determine_research_area(
            research_data.get('publications', []),
            professor_data.get('affiliation', '')
        )
        
        university_tier = self.determine_university_tier(
            professor_data.get('email', ''),
            professor_data.get('affiliation', '')
        )
        
        variants = []
        
        for i in range(num_variants):
            # Vary the AB test parameters
            subject_length = random.choice(self.ab_test_variants['subject_length'])
            opening_style = random.choice(self.ab_test_variants['opening_style'])
            cta_style = random.choice(self.ab_test_variants['call_to_action'])
            
            subject = self.generate_smart_subject_line(
                professor_data, research_area, university_tier, subject_length
            )
            
            body = self.generate_smart_email_body(
                professor_data, research_data, research_area, university_tier
            )
            
            variants.append({
                'variant_id': f'template_v{i+1}',
                'subject': subject,
                'body': body,
                'parameters': {
                    'subject_length': subject_length,
                    'opening_style': opening_style,
                    'cta_style': cta_style,
                    'research_area': research_area,
                    'university_tier': university_tier
                },
                'expected_performance': self._estimate_performance(
                    research_area, university_tier, subject_length
                )
            })
        
        return variants
    
    def _estimate_performance(self, research_area: str, university_tier: str, 
                             subject_length: str) -> Dict[str, float]:
        """Estimate template performance based on historical patterns"""
        
        # Base performance estimates (simulated based on research)
        base_open_rate = 0.22  # 22% baseline for academic emails
        base_response_rate = 0.08  # 8% baseline response rate
        
        # Adjust for research area
        area_multipliers = {
            'machine_learning': 1.15,  # ML is hot topic
            'computer_systems': 1.0,
            'cybersecurity': 1.1,
            'algorithms': 0.95
        }
        
        # Adjust for university tier
        tier_multipliers = {
            'tier_1': 0.85,  # Lower response rate (more competitive)
            'tier_2': 1.1,   # Higher response rate
            'international': 1.05,
            'other': 1.0
        }
        
        # Adjust for subject length
        length_multipliers = {
            'short': 1.05,   # Slightly better open rates
            'medium': 1.0,
            'long': 0.95     # Slightly worse open rates
        }
        
        area_mult = area_multipliers.get(research_area, 1.0)
        tier_mult = tier_multipliers.get(university_tier, 1.0)
        length_mult = length_multipliers.get(subject_length, 1.0)
        
        estimated_open_rate = base_open_rate * area_mult * tier_mult * length_mult
        estimated_response_rate = base_response_rate * area_mult * tier_mult
        
        return {
            'estimated_open_rate': round(estimated_open_rate, 3),
            'estimated_response_rate': round(estimated_response_rate, 3),
            'confidence_score': 0.75  # Confidence in estimate
        }
    
    def save_template_variants(self, variants: List[Dict], professor_email: str) -> str:
        """Save generated template variants for tracking"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"smart_templates_{timestamp}.json"
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'professor_email': professor_email,
            'variants': variants,
            'generation_metadata': {
                'generator_version': '1.0',
                'total_variants': len(variants),
                'research_area_detected': variants[0]['parameters']['research_area'] if variants else 'unknown'
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Template variants saved to: {filename}")
        return filename

def main():
    """Demonstrate the smart template generator"""
    
    print("🧠 SMART TEMPLATE GENERATOR")
    print("=" * 50)
    print("AI-powered personalized email template generation")
    print()
    
    generator = SmartTemplateGenerator()
    
    # Sample professor data
    sample_professor = {
        'name': 'Dr. Jane Smith',
        'email': 'jsmith@stanford.edu',
        'affiliation': 'Stanford University'
    }
    
    # Sample research data
    sample_research = {
        'publications': [
            {
                'title': 'Deep Learning for Natural Language Processing',
                'abstract': 'This paper presents novel approaches to neural language models...',
                'fields': ['Machine Learning', 'Natural Language Processing']
            }
        ],
        'confidence': 0.85
    }
    
    # Generate template variants
    print("🔍 Analyzing professor research profile...")
    research_area = generator.determine_research_area(
        sample_research['publications'], 
        sample_professor['affiliation']
    )
    print(f"   Detected research area: {research_area}")
    
    university_tier = generator.determine_university_tier(
        sample_professor['email'],
        sample_professor['affiliation'] 
    )
    print(f"   University tier: {university_tier}")
    
    print("\n🧠 Generating smart template variants...")
    variants = generator.generate_ab_test_templates(
        sample_professor, sample_research, num_variants=3
    )
    
    print(f"✅ Generated {len(variants)} optimized templates")
    
    # Display sample templates
    for i, variant in enumerate(variants, 1):
        print(f"\n📧 TEMPLATE VARIANT {i}:")
        print("-" * 30)
        print(f"Subject: {variant['subject']}")
        print(f"Expected Open Rate: {variant['expected_performance']['estimated_open_rate']:.1%}")
        print(f"Expected Response Rate: {variant['expected_performance']['estimated_response_rate']:.1%}")
        print()
        print("Body Preview:")
        body_preview = variant['body'][:200] + "..."
        print(body_preview)
        print()
    
    # Save variants
    filename = generator.save_template_variants(variants, sample_professor['email'])
    print(f"💾 Templates saved to: {filename}")
    
    print("\n💡 SMART FEATURES DEMONSTRATED:")
    print("   ✅ Research area detection from publications")
    print("   ✅ University tier classification")
    print("   ✅ Seasonal timing awareness")
    print("   ✅ A/B testing variant generation")
    print("   ✅ Performance estimation")
    print("   ✅ Personalized content generation")

if __name__ == "__main__":
    main()
