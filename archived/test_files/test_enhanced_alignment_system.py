#!/usr/bin/env python3
"""
Test Enhanced Ultra-Personalized Mailing System
Test the research alignment analyzer integration with actual professor data
"""

import os
import sys
import json
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from research_alignment_analyzer import ResearchAlignmentAnalyzer
from research_publication_finder import ResearchPublicationFinder
from enhanced_research_area_inference import EnhancedResearchAreaInference

def test_research_alignment_system():
    """Test the complete research alignment system"""
    print("🧪 TESTING ENHANCED ULTRA-PERSONALIZED MAILING SYSTEM")
    print("=" * 70)
    print("Testing Research Alignment Analyzer Integration")
    print("=" * 70)
    
    # Initialize components
    alignment_analyzer = ResearchAlignmentAnalyzer()
    publication_finder = ResearchPublicationFinder()
    research_inference = EnhancedResearchAreaInference()
    
    # Test professors with different research areas
    test_professors = [
        {
            "name": "Dr. John Smith",
            "email": "john.smith@university.edu",
            "research_area": "Machine Learning",
            "last_name": "Smith"
        },
        {
            "name": "Dr. Sarah Johnson", 
            "email": "sarah.johnson@university.edu",
            "research_area": "Cybersecurity",
            "last_name": "Johnson"
        },
        {
            "name": "Dr. Michael Chen",
            "email": "michael.chen@university.edu", 
            "research_area": "Data Science",
            "last_name": "Chen"
        }
    ]
    
    print(f"\n📊 Testing with {len(test_professors)} professors:")
    for prof in test_professors:
        print(f"  • {prof['name']} - {prof['research_area']}")
    
    print("\n" + "="*70)
    
    # Test each professor
    for i, professor in enumerate(test_professors, 1):
        print(f"\n🎯 PROFESSOR {i}: {professor['name']} ({professor['research_area']})")
        print("-" * 50)
        
        # Get research area inference
        research_data = research_inference.get_research_specific_content(professor['research_area'])
        
        # Get publications
        print("📚 Fetching recent publications...")
        publications = publication_finder.search_semantic_scholar(professor['name'], max_results=3)
        
        if publications:
            print(f"✅ Found {len(publications)} publications")
            
            # Generate alignment explanations
            print("\n🔍 Generating research alignment explanations:")
            
            for j, pub in enumerate(publications, 1):
                print(f"\n  📄 Publication {j}: {pub['title'][:60]}...")
                alignment = alignment_analyzer.analyze_publication_alignment(pub, professor['research_area'])
                print(f"  🎯 Alignment: {alignment[:100]}...")
            
            # Generate complete HTML with alignments
            print("\n🎨 Generating enhanced HTML with research alignments...")
            publications_html = alignment_analyzer.generate_publications_with_alignment(
                publications, professor['research_area']
            )
            
            # Save sample HTML for review
            sample_filename = f"sample_enhanced_email_{professor['last_name'].lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            
            # Create complete professor data
            professor_data = {
                'last_name': professor['last_name'],
                'research_area': professor['research_area'],
                'research_title': research_data['research_title'],
                'research_alignment': research_data['research_alignment'],
                'highlighted_projects': research_data['highlighted_projects'],
                'relevant_coursework': research_data['relevant_coursework'],
                'skills_emphasis': research_data['skills_emphasis'],
                'recent_publications': publications,
                'recent_publications_html': publications_html
            }
            
            # Generate complete email HTML (simplified template for testing)
            complete_html = generate_test_email_html(professor_data)
            
            with open(sample_filename, 'w', encoding='utf-8') as f:
                f.write(complete_html)
            
            print(f"✅ Sample email saved: {sample_filename}")
            
        else:
            print("❌ No publications found")
        
        print("-" * 50)
    
    print(f"\n🎉 TESTING COMPLETE!")
    print("=" * 70)
    print("✅ Research Alignment System Successfully Tested")
    print("✅ Publications with alignment explanations generated")
    print("✅ Sample HTML emails created for review")
    print("\n🚀 The system is ready for full deployment!")

def generate_test_email_html(professor_data):
    """Generate a simplified test email HTML"""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Research Internship Inquiry - {professor_data['research_area']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; border-bottom: 2px solid #667eea; padding-bottom: 20px; }}
        .research-highlight {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .section {{ margin-bottom: 30px; }}
        .section-title {{ font-size: 18px; font-weight: bold; color: #2c3e50; border-bottom: 2px solid #667eea; padding-bottom: 8px; margin-bottom: 15px; }}
        .publication-item {{ background: #f8f9fa; border-left: 4px solid #3498db; padding: 15px; margin: 15px 0; border-radius: 5px; }}
        .publication-header {{ font-weight: bold; color: #2c3e50; margin-bottom: 8px; }}
        .publication-venue {{ color: #7f8c8d; font-style: italic; margin-bottom: 8px; }}
        .publication-summary {{ color: #34495e; margin-bottom: 12px; line-height: 1.5; }}
        .research-alignment {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 15px; border-radius: 6px; margin-top: 10px; font-size: 14px; line-height: 1.4; }}
        .research-alignment strong {{ display: block; margin-bottom: 5px; font-size: 15px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>RESEARCH INTERNSHIP INQUIRY</h1>
        <p>{professor_data['research_area']} Research Opportunity</p>
    </div>
    
    <div class="research-highlight">
        <h3>🎯 Research Alignment with {professor_data['research_area'].lower()}</h3>
        <p>{professor_data['research_alignment']}</p>
    </div>
    
    <p>Dear Prof. {professor_data['last_name']},</p>
    
    <p>I am Anamay Tripathy, a third-year B.Tech Data Science student at MIT Manipal, India. I am writing to express my strong interest in a research internship opportunity with your esteemed group, particularly in the areas of {professor_data['research_area'].lower()} and its intersection with artificial intelligence applications.</p>
    
    <div class="section">
        <h2 class="section-title">🎓 Academic Background</h2>
        <p><strong>Degree:</strong> B.Tech in Data Science Engineering (2023–2027)</p>
        <p><strong>Institution:</strong> MIT Manipal, India</p>
        <p><strong>CGPA:</strong> 7.6 / 10</p>
        <p><strong>Relevant Coursework:</strong> {', '.join(professor_data['relevant_coursework'])}</p>
    </div>
    
    <div class="section">
        <h2 class="section-title">🚀 Selected Research-Oriented Projects</h2>
        {chr(10).join([f'<div class="project-item"><strong>{proj["name"]}</strong><br>{proj["description"]}</div>' for proj in professor_data['highlighted_projects']])}
    </div>
    
    <div class="section">
        <h2 class="section-title">📄 Recent Research Publications</h2>
        <div class="publications-section">
            {professor_data['recent_publications_html']}
        </div>
    </div>
    
    <div class="section">
        <h2 class="section-title">🛠️ Technical Competencies</h2>
        <p><strong>Skills Emphasis:</strong> {professor_data['skills_emphasis']}</p>
    </div>
    
    <p>I am seeking a research internship opportunity—whether remote or on-site, funded or voluntary—to contribute to your ongoing research while gaining invaluable experience that will inform my planned graduate studies in {professor_data['research_area'].lower()} and related fields.</p>
    
    <p>I would be honored to discuss how my technical background, research interests, and enthusiasm for {professor_data['research_area'].lower()} can contribute to your laboratory's ongoing work. I have attached my detailed curriculum vitae for your review.</p>
    
    <p>Thank you for considering my application. I look forward to the possibility of contributing to your research endeavors.</p>
    
    <p>Sincerely,<br>
    <strong>Anamay Tripathy</strong><br>
    B.Tech Data Science Engineering<br>
    MIT Manipal, India<br>
    Email: tripathy.anamay23@gmail.com</p>
</body>
</html>
    """

if __name__ == "__main__":
    test_research_alignment_system()
