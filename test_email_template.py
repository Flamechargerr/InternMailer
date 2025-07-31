#!/usr/bin/env python3
"""
Test script to generate a sample email using the new concise research template
"""

import sys
import os

# Add the src directory to Python path
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.append(src_path)

from email_generator import EmailGenerator

# Sample student info
student_info = {
    'name': 'Anamay Tripathy',
    'email': 'tripathy.anamay23@gmail.com',
    'university': 'MIT Manipal',
    'cgpa': '7.6/10',
    'skills': [
        'Python', 'TensorFlow', 'PyTorch', 'JavaScript', 'React.js', 
        'Node.js', 'AWS', 'GCP', 'Docker', 'SQL', 'MongoDB',
        'Scikit-learn', 'XGBoost', 'Pandas', 'NumPy'
    ],
    'projects': [
        'CrimeConnect', 'VARtificial Intelligence', 'HackOps'
    ],
    'experience': [
        'Technical Head at YaanBarpe',
        'Data Analyst Intern at Intellect Design Arena'
    ]
}

# Sample professor info for testing academic template
sample_professor = {
    'Name': 'Dr. Barbara Liskov',
    'Research Area': 'Distributed Systems and Programming Languages',
    'University': 'MIT',
    'Department': 'Computer Science'
}

def generate_sample_email():
    """Generate a sample email for testing"""
    print("=== GENERATING SAMPLE EMAIL FOR REVIEW ===\n")
    
    # Initialize email generator
    generator = EmailGenerator(student_info, use_azure_ai=True)
    
    # Generate subject
    subject = generator.generate_subject(sample_professor)
    print(f"SUBJECT: {subject}\n")
    
    # Generate email body using the new template
    try:
        body = generator.generate_body(sample_professor)
        print("EMAIL BODY:")
        print("=" * 60)
        print(body)
        print("=" * 60)
        
        # Save to file for easy copying
        output_file = 'sample_email_output.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Subject: {subject}\n\n")
            f.write(body)
        
        print(f"\n✅ Sample email saved to: {output_file}")
        print(f"📧 You can copy this content and email it to: {student_info['email']}")
        print("\nNext steps:")
        print("1. Open the HTML file in a browser to see the formatted email")
        print("2. Copy and paste the content into your email client")
        print("3. Send it to yourself for review")
        print("4. Once approved, we'll use this template uniformly")
        
    except Exception as e:
        print(f"❌ Error generating email: {e}")
        print("Falling back to enhanced template...")
        try:
            body = generator.generate_enhanced_fallback_body(sample_professor)
            print("FALLBACK EMAIL BODY:")
            print("=" * 60)
            print(body)
            print("=" * 60)
        except Exception as e2:
            print(f"❌ Fallback also failed: {e2}")

if __name__ == "__main__":
    generate_sample_email()
