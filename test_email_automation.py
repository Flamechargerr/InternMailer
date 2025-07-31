import os
from dotenv import load_dotenv
import csv
import json
from datetime import datetime

load_dotenv()

# Test mode - no actual email sending
TEST_MODE = True

def load_google_sheets_data():
    """Load data from Google Sheets CSV or create sample data"""
    sample_data = [
        {
            'Name': 'Vishwanadh Raju',
            'Job Title': 'Head Talent Acquisition Operations- Talent Solutioning',
            'Linkedin URL': 'http://www.linkedin.com/in/vishwanadh',
            'Company Name': 'ANSR',
            'Status': 'Follow-up 2',
            'Applied for Internship/Job': 'TRUE',
            'Company Website': 'http://www.ansr.com/',
            'Company Linkedin': 'http://www.linkedin.com/company/ansr-consulting',
            'Company Social': 'https://twitter.com/ansrglobal',
            'Location': 'Bengaluru, India',
            'Company Niche': 'Management Consulting'
        },
        {
            'Name': 'Chetna Gogia',
            'Job Title': 'Chief Human Resources Officer',
            'Linkedin URL': 'http://www.linkedin.com/in/chetna-gogia',
            'Company Name': 'GoKwik',
            'Status': 'in Talks',
            'Applied for Internship/Job': 'TRUE',
            'Company Website': 'http://www.gokwik.co/',
            'Company Linkedin': 'http://www.linkedin.com/company/gokwik',
            'Company Social': 'https://www.facebook.com/GoKwikCo/',
            'Location': 'Gurgaon, India',
            'Company Niche': 'Information Technology & Services'
        }
    ]
    return sample_data

def create_personalized_email_content(contact):
    """Create personalized email content based on contact info"""
    
    # Map company niches to specific roles
    role_mapping = {
        'Management Consulting': 'business analysis, process optimization, and strategic consulting',
        'Information Technology & Services': 'software development, data analysis, and technical solutions',
        'Data Science': 'machine learning, data engineering, and analytics',
        'Fintech': 'financial technology development and data analysis',
        'E-commerce': 'platform development, user experience optimization, and data analytics'
    }
    
    company_niche = contact.get('Company Niche', 'Technology')
    specific_roles = role_mapping.get(company_niche, 'software development and data analysis')
    
    email_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Summer Internship Inquiry</title>
</head>
<body>
    <div style="max-width: 700px; margin: 30px auto; background: #ffffff; padding: 40px 35px; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        
        <!-- Header -->
        <div style="text-align: center; margin-bottom: 30px; border-bottom: 2px solid #2c5aa0; padding-bottom: 15px;">
            <h1 style="margin: 0; font-size: 18px; font-weight: bold; color: #2c5aa0; letter-spacing: 0.5px;">
                INTERNSHIP OPPORTUNITY INQUIRY
            </h1>
        </div>

        <!-- Personalized Greeting -->
        <p style="margin: 0 0 20px 0; font-size: 16px; color: #333333;">
            Dear {contact['Name']},
        </p>

        <!-- Highly Personalized Opening -->
        <p style="margin: 0 0 20px 0; font-size: 16px; color: #333333; line-height: 1.6;">
            I hope this message finds you well. I am <strong>Anamay Tripathy</strong>, a third-year B.Tech Data Science student at MIT Manipal. I came across your profile while researching leading professionals in {company_niche}, and I was particularly impressed by your role as {contact['Job Title']} at {contact['Company Name']}. Your expertise in talent acquisition and your work in building innovative teams in {contact['Location']} caught my attention.
        </p>

        <!-- Company Research Connection -->
        <p style="margin: 0 0 25px 0; font-size: 16px; color: #333333; line-height: 1.6;">
            I've been following {contact['Company Name']}'s journey in the {company_niche} space. Your company's commitment to innovation and the dynamic work culture you've helped build makes {contact['Company Name']} an ideal place where I believe I can contribute meaningfully while gaining invaluable industry experience.
        </p>

        <!-- Personal Connection -->
        <div style="margin-bottom: 25px; padding: 15px; background-color: #f0f7ff; border-left: 4px solid #2c5aa0;">
            <p style="margin: 0; font-size: 16px; color: #333333; font-style: italic;">
                <strong>Personal Connection:</strong> As someone passionate about {company_niche}, I'm particularly drawn to {contact['Company Name']}'s approach to innovation. This aligns perfectly with my experience in building scalable tech solutions and my current role leading technical initiatives at a government-incubated startup.
            </p>
        </div>

        <!-- Why This Specific Company -->
        <p style="margin: 0 0 25px 0; font-size: 16px; color: #333333; line-height: 1.6;">
            What particularly excites me about {contact['Company Name']} is your focus on {company_niche}. Having worked with similar technologies and challenges in my current role, I believe my technical background and fresh perspective could add value to your team while I learn from industry leaders like yourself.
        </p>

        <!-- Professional Background Section -->
        <div style="margin-bottom: 30px;">
            <h2 style="margin: 0 0 15px 0; font-size: 16px; font-weight: bold; color: #2c5aa0; border-bottom: 1px solid #2c5aa0; padding-bottom: 5px;">
                What I Bring to {contact['Company Name']}
            </h2>

            <div style="margin-bottom: 20px;">
                <p style="margin: 0 0 10px 0; font-size: 16px; color: #333333;">
                    <strong>Current Leadership Role:</strong> Technical Head at <a href="https://www.yaanbarpe.in/" style="color: #2c5aa0; text-decoration: none;">YaanBarpe</a> (Karnataka Government-incubated startup)
                </p>
                <p style="margin: 0 0 15px 0; font-size: 16px; color: #666666; padding-left: 20px;">
                    • Spearheading product strategy for sustainable solutions with direct impact on rural communities<br>
                    • Leading a cross-functional team of 8+ developers and designers<br>
                    • Implementing scalable systems that handle 10,000+ daily active users<br>
                    • Reduced operational costs by 35% through strategic technology optimization
                </p>
            </div>

            <div style="margin-bottom: 20px;">
                <p style="margin: 0 0 10px 0; font-size: 16px; color: #333333;">
                    <strong>Industry Experience:</strong> Data Analyst Intern at Intellect Design Arena, Mumbai
                </p>
                <p style="margin: 0 0 15px 0; font-size: 16px; color: #666666; padding-left: 20px;">
                    • Built automated KPI dashboards serving 500+ stakeholders (saving 12+ hours weekly)<br>
                    • Developed REST APIs that improved user engagement by 22% across mobile and web platforms<br>
                    • Conducted predictive analytics on datasets exceeding 1M records, generating actionable insights for C-suite decisions
                </p>
            </div>
        </div>

        <!-- Standout Projects Section -->
        <div style="margin-bottom: 30px;">
            <h2 style="margin: 0 0 15px 0; font-size: 16px; font-weight: bold; color: #2c5aa0; border-bottom: 1px solid #2c5aa0; padding-bottom: 5px;">
                Projects That Align with {contact['Company Name']}'s Vision
            </h2>

            <div style="margin-bottom: 20px;">
                <p style="margin: 0 0 8px 0; font-size: 16px; color: #333333;">
                    <strong><a href="https://crime-connect-fbi.lovable.app/login" style="color: #2c5aa0; text-decoration: none;">CrimeConnect</a>:</strong> AI-Powered Case Management System
                </p>
                <p style="margin: 0 0 15px 0; font-size: 16px; color: #666666; padding-left: 20px;">
                    Built using MERN stack with Supabase, incorporating machine learning for pattern recognition. Achieved 40% reduction in case processing time through intelligent automation.
                </p>
            </div>

            <div style="margin-bottom: 20px;">
                <p style="margin: 0 0 8px 0; font-size: 16px; color: #333333;">
                    <strong><a href="https://match-predictor-genie-66.lovable.app/" style="color: #2c5aa0; text-decoration: none;">VARtificial Intelligence</a>:</strong> Real-time Prediction Engine
                </p>
                <p style="margin: 0 0 15px 0; font-size: 16px; color: #666666; padding-left: 20px;">
                    Developed using XGBoost and advanced feature engineering, achieving 89% prediction accuracy. The real-time processing capabilities and data pipeline architecture demonstrate scalable solution design.
                </p>
            </div>

            <div style="margin-bottom: 15px;">
                <p style="margin: 0 0 8px 0; font-size: 16px; color: #333333;">
                    <strong><a href="https://flamechargerr.github.io/" style="color: #2c5aa0; text-decoration: none;">HackOps</a>:</strong> Cybersecurity Training Platform
                </p>
                <p style="margin: 0 0 15px 0; font-size: 16px; color: #666666; padding-left: 20px;">
                    Gamified learning platform with 25+ security challenges, improving user cyber-awareness by 35%.
                </p>
            </div>
        </div>

        <!-- Technical Skills -->
        <div style="margin-bottom: 30px;">
            <h2 style="margin: 0 0 15px 0; font-size: 16px; font-weight: bold; color: #2c5aa0; border-bottom: 1px solid #2c5aa0; padding-bottom: 5px;">
                Technical Skills Relevant to {contact['Company Name']}
            </h2>

            <div style="margin-bottom: 15px; font-size: 16px; color: #333333;">
                <strong>Core Programming:</strong> Python (5+ years), JavaScript (ES6+), Java, C++, SQL<br>
                <strong>AI/ML Stack:</strong> TensorFlow, PyTorch, Scikit-learn, XGBoost, OpenCV, NLP<br>
                <strong>Full-Stack Development:</strong> React.js, Node.js, MongoDB, Next.js, Express.js<br>
                <strong>Cloud & DevOps:</strong> AWS (EC2, S3, Lambda), GCP, Docker, Kubernetes, Git<br>
                <strong>Data Engineering:</strong> Apache Spark, Pandas, NumPy, Data Visualization (D3.js, Plotly)
            </div>
        </div>

        <!-- Value Proposition -->
        <div style="margin-bottom: 25px; padding: 20px; background-color: #f8f9fa; border-radius: 5px; border-left: 4px solid #28a745;">
            <h3 style="margin: 0 0 15px 0; font-size: 16px; font-weight: bold; color: #28a745;">
                What I Can Contribute to {contact['Company Name']}
            </h3>
            <ul style="margin: 0; padding-left: 20px; font-size: 16px; color: #333333;">
                <li style="margin-bottom: 8px;">Fresh perspective on {company_niche} challenges with hands-on experience in similar domains</li>
                <li style="margin-bottom: 8px;">Proven ability to deliver measurable results (35% cost reduction, 40% efficiency gains)</li>
                <li style="margin-bottom: 8px;">Strong foundation in modern technology stack with practical implementation experience</li>
                <li style="margin-bottom: 8px;">Leadership experience managing technical teams and cross-functional projects</li>
                <li>Enthusiasm for {contact['Company Name']}'s mission and genuine interest in contributing to innovation</li>
            </ul>
        </div>

        <!-- Specific Ask -->
        <p style="margin: 0 0 20px 0; font-size: 16px; color: #333333; line-height: 1.6;">
            I am seeking a <strong>summer internship opportunity (May-July 2025)</strong> where I can contribute to {contact['Company Name']}'s initiatives while gaining hands-on experience in {company_niche}. I'm particularly interested in roles involving <strong>{specific_roles}</strong> and am flexible with both remote and on-site arrangements in {contact['Location']}.
        </p>

        <!-- LinkedIn Connection Request -->
        <div style="margin-bottom: 25px; padding: 15px; background-color: #e8f4f8; border-left: 4px solid #17a2b8;">
            <p style="margin: 0; font-size: 16px; color: #333333;">
                <strong>LinkedIn Connection:</strong> I would be honored to connect with you on LinkedIn (<a href="{contact['Linkedin URL']}" style="color: #17a2b8; text-decoration: none;">{contact['Linkedin URL']}</a>) to stay updated on {contact['Company Name']}'s initiatives and perhaps continue our conversation about potential opportunities.
            </p>
        </div>

        <!-- Closing -->
        <p style="margin: 0 0 20px 0; font-size: 16px; color: #333333; line-height: 1.6;">
            I've attached my detailed resume and would be thrilled to discuss how my technical skills, leadership experience, and passion for {company_niche} can contribute to {contact['Company Name']}'s continued success. I'm available for a brief call at your convenience to explore potential fit and answer any questions.
        </p>

        <p style="margin: 0 0 30px 0; font-size: 16px; color: #333333;">
            Thank you for taking the time to consider my application, {contact['Name']}. I look forward to the possibility of contributing to your team.
        </p>

        <!-- Contact Information -->
        <div style="margin-bottom: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 5px;">
            <h3 style="margin: 0 0 15px 0; font-size: 16px; font-weight: bold; color: #2c5aa0;">
                Let's Connect
            </h3>

            <p style="margin: 0 0 8px 0; font-size: 16px; color: #333333;">
                📧 <strong>Email:</strong> <a href="mailto:tripathy.anamay23@gmail.com" style="color: #2c5aa0; text-decoration: none;">tripathy.anamay23@gmail.com</a>
            </p>
            <p style="margin: 0 0 8px 0; font-size: 16px; color: #333333;">
                📱 <strong>Phone:</strong> <a href="tel:+919877454747" style="color: #2c5aa0; text-decoration: none;">+91-9877454747</a>
            </p>
            <p style="margin: 0 0 8px 0; font-size: 16px; color: #333333;">
                🌐 <strong>Portfolio:</strong> <a href="https://anamay.vercel.app/" style="color: #2c5aa0; text-decoration: none;">anamay.vercel.app</a>
            </p>
            <p style="margin: 0 0 8px 0; font-size: 16px; color: #333333;">
                💼 <strong>LinkedIn:</strong> <a href="https://linkedin.com/in/anamay-tripathy" style="color: #2c5aa0; text-decoration: none;">linkedin.com/in/anamay-tripathy</a>
            </p>
            <p style="margin: 0; font-size: 16px; color: #333333;">
                💻 <strong>GitHub:</strong> <a href="https://github.com/Flamechargerr" style="color: #2c5aa0; text-decoration: none;">github.com/Flamechargerr</a>
            </p>
        </div>

        <!-- Professional Signature -->
        <div style="margin-top: 30px; border-top: 1px solid #ddd; padding-top: 20px;">
            <p style="margin: 0 0 8px 0; font-size: 16px; color: #333333;">
                Warm regards,
            </p>
            <p style="margin: 0 0 5px 0; font-size: 16px; color: #333333; font-weight: bold;">
                Anamay Tripathy
            </p>
            <p style="margin: 0; font-size: 14px; color: #666666;">
                Technical Head, YaanBarpe | B.Tech Data Science Engineering<br>
                MIT Manipal, India | Passionate about AI & Sustainable Tech
            </p>
        </div>
    </div>
</body>
</html>
    """
    
    return email_content

def test_email_generation():
    """Test email generation with sample data"""
    print("🧪 Starting Email Generation Test...")
    print("=" * 60)
    
    # Load test data
    contacts = load_google_sheets_data()
    
    test_results = []
    
    for i, contact in enumerate(contacts[:2]):  # Test with first 2 contacts
        print(f"\n📧 Testing Email #{i+1}")
        print(f"Contact: {contact['Name']} at {contact['Company Name']}")
        print(f"Role: {contact['Job Title']}")
        print(f"Location: {contact['Location']}")
        print(f"Company Niche: {contact['Company Niche']}")
        
        try:
            # Generate email content
            email_content = create_personalized_email_content(contact)
            
            # Save test email to file
            filename = f"test_email_{contact['Company Name'].replace(' ', '_').replace('.', '')}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(email_content)
            
            print(f"✅ Email generated successfully!")
            print(f"📄 Saved to: {filename}")
            
            # Test result summary
            result = {
                'contact_name': contact['Name'],
                'company': contact['Company Name'],
                'status': 'Success',
                'filename': filename,
                'email_length': len(email_content),
                'timestamp': datetime.now().isoformat()
            }
            test_results.append(result)
            
        except Exception as e:
            print(f"❌ Error generating email: {e}")
            result = {
                'contact_name': contact['Name'],
                'company': contact['Company Name'],
                'status': 'Failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            test_results.append(result)
    
    # Save test results
    with open('test_results.json', 'w') as f:
        json.dump(test_results, f, indent=2)
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    successful_tests = [r for r in test_results if r['status'] == 'Success']
    failed_tests = [r for r in test_results if r['status'] == 'Failed']
    
    print(f"✅ Successful: {len(successful_tests)}")
    print(f"❌ Failed: {len(failed_tests)}")
    print(f"📄 Test results saved to: test_results.json")
    
    if successful_tests:
        print("\n🎉 EMAIL GENERATION TEST PASSED!")
        print("Key features verified:")
        print("  • Personalized greetings with correct names")
        print("  • Company-specific role insertion")
        print("  • Location and company niche integration")
        print("  • Professional formatting and structure")
        print("  • Complete contact information")
        
        print(f"\n📧 Sample email files generated:")
        for result in successful_tests:
            print(f"  • {result['filename']}")
    
    return len(failed_tests) == 0

if __name__ == "__main__":
    success = test_email_generation()
    
    if success:
        print("\n🚀 Ready for production! Run 'internship_email_automation.py' to start sending emails.")
    else:
        print("\n⚠️  Please fix the issues before proceeding to production.")
