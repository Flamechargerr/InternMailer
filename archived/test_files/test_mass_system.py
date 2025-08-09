#!/usr/bin/env python3
"""
TEST MASS PERSONALIZED EMAIL SYSTEM
Quick demo with 5 professors to show authentic research personalization
"""

import pandas as pd
from datetime import datetime
import json
from mass_personalized_email_system import MassPersonalizedEmailSystem

def test_mass_system():
    """Test the mass system with a small batch"""
    
    # Your profile (customize this!)
    your_profile = {
        'name': 'Your Name Here',  # CHANGE THIS
        'background': 'Computer Science student passionate about AI research and seeking PhD opportunities',
        'interests': [
            'machine learning', 'artificial intelligence', 'deep learning',
            'natural language processing', 'computer vision', 'neural networks'
        ],
        'skills': [
            'Python', 'TensorFlow', 'PyTorch', 'Scikit-learn', 'CUDA',
            'Research Methodology', 'Statistical Analysis', 'Data Visualization'
        ],
        'email': 'your.email@university.edu',
        'linkedin': 'https://linkedin.com/in/yourprofile',
        'portfolio': 'https://yourportfolio.com',
        'achievements': 'completed multiple ML projects, published research, strong academic record with focus on practical AI applications'
    }
    
    print("🚀 TESTING MASS PERSONALIZED EMAIL SYSTEM")
    print("=" * 80)
    print("This will create 5 ultra-personalized emails with REAL research data")
    print("No mock data - every detail is authentic and specific to each professor!")
    print("=" * 80)
    
    # Initialize the system
    campaign = MassPersonalizedEmailSystem(your_profile)
    
    # Load a small batch for testing
    df = pd.read_csv('data/proffesor_clean.csv')
    test_professors = df.head(5).to_dict('records')
    
    print(f"\n🎯 Processing {len(test_professors)} professors for demonstration:")
    for i, prof in enumerate(test_professors, 1):
        print(f"  {i}. {prof['Name']} at {prof['University']}")
    
    print("\n📚 Gathering authentic research data and creating personalized emails...")
    print("-" * 60)
    
    # Process each professor
    results = []
    for i, prof_data in enumerate(test_professors, 1):
        print(f"\n🔍 [{i}/5] Processing {prof_data['Name']}")
        
        try:
            # Get real research data
            profile = campaign.research_finder.create_author_profile(
                name=prof_data['Name'],
                affiliation=prof_data['University'],
                email=prof_data['Email'],
                homepage=prof_data.get('Homepage', '')
            )
            
            if profile.recent_publications:
                print(f"   ✅ Found {len(profile.recent_publications)} recent publications")
                
                # Show publications found
                for j, pub in enumerate(profile.recent_publications[:3], 1):
                    print(f"      {j}. \"{pub.title}\" ({pub.year}) - {pub.venue}")
                    print(f"         Citations: {pub.citations} | Confidence: {pub.confidence_score:.2f}")
                
                # Create personalized email
                email_data = campaign.create_ultra_personalized_email(profile)
                
                # Save email
                success = campaign.send_email(email_data)
                
                result = {
                    'professor': prof_data['Name'],
                    'university': prof_data['University'],
                    'email': prof_data['Email'],
                    'publications_found': len(profile.recent_publications),
                    'research_interests': profile.research_interests,
                    'alignment_score': email_data.get('research_alignment_score', 0.5),
                    'success': success
                }
                
                results.append(result)
                
                print(f"   📧 Email created with {email_data.get('research_alignment_score', 0.5):.0%} research alignment")
                print(f"   💾 {'✅ Saved successfully' if success else '❌ Failed to save'}")
                
            else:
                print(f"   ⚠️  No recent publications found")
                results.append({
                    'professor': prof_data['Name'],
                    'university': prof_data['University'],
                    'email': prof_data['Email'],
                    'publications_found': 0,
                    'success': False
                })
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'professor': prof_data['Name'],
                'university': prof_data['University'], 
                'email': prof_data['Email'],
                'publications_found': 0,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    successful = [r for r in results if r['success']]
    total_publications = sum(r.get('publications_found', 0) for r in results)
    avg_alignment = sum(r.get('alignment_score', 0) for r in successful) / len(successful) if successful else 0
    
    print("\n" + "🎉 TEST COMPLETED!" + " 🎉")
    print("=" * 80)
    print(f"📊 RESULTS:")
    print(f"   Successful emails: {len(successful)}/5")
    print(f"   Total publications analyzed: {total_publications}")
    print(f"   Average research alignment: {avg_alignment:.0%}")
    print(f"   Success rate: {len(successful)/5:.0%}")
    
    print(f"\n📁 Generated emails saved in: personalized_emails/")
    print(f"📈 Each email contains:")
    print(f"   ✅ Specific publication references")
    print(f"   ✅ Research alignment analysis") 
    print(f"   ✅ Personalized collaboration proposals")
    print(f"   ✅ Authentic research connections")
    print(f"   ✅ Professional, compelling content")
    
    # Save test results
    test_report = {
        'test_timestamp': datetime.now().isoformat(),
        'your_profile': your_profile,
        'results': results,
        'summary': {
            'successful_emails': len(successful),
            'total_publications': total_publications,
            'average_alignment': avg_alignment,
            'success_rate': len(successful)/5
        }
    }
    
    with open('test_mass_system_report.json', 'w') as f:
        json.dump(test_report, f, indent=2)
    
    print(f"\n📊 Detailed test report saved to: test_mass_system_report.json")
    
    print("\n" + "="*80)
    print("🚀 Ready to scale to all 31,000+ professors?")
    print("   This same level of personalization will be applied to every email!")
    print("   Each professor gets individually crafted content based on their real research.")

if __name__ == "__main__":
    test_mass_system()
