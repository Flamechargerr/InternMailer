"""
InternMailer Campaign Demo
Shows complete email generation and sends personalized emails to professors
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from email_campaign_system import EmailCampaignSystem

def main():
    print("🎯 InternMailer: Advanced Email Campaign System")
    print("=" * 60)
    
    # Your student information - CUSTOMIZE THIS WITH YOUR DETAILS
    student_info = {
        'name': 'Anamay Tripathy',  # Change to your name
        'year': 'Final Year',       # Change to your year
        'major': 'Computer Science',
        'university': 'Your University',  # Change to your university
        'email': 'tripathy.anamay23@gmail.com',  # Your actual email
        'phone': '+91-XXXXXXXXXX',   # Your phone number
        'gpa': '3.8/4.0',           # Your GPA
        'graduation_year': '2025',   # Your graduation year
        
        # Customize these based on your experience
        'experience': 'extensive programming experience with Python, machine learning frameworks, and full-stack development',
        'skills': 'Python, TensorFlow, PyTorch, scikit-learn, Django, React, data analysis, statistical modeling, deep learning',
        'coursework': 'Machine Learning, Deep Learning, Data Structures, Algorithms, Statistics, Linear Algebra, Computer Vision, NLP',
        'research_exp': 'multiple projects in machine learning including computer vision, natural language processing, and data science applications',
        'qualifications': 'strong programming foundation, research experience, published papers/projects, and genuine passion for advancing AI research'
    }
    
    # Initialize campaign system
    print("📊 Loading professor database...")
    csv_path = "InternMailer/data/proffesor_verified_emails.csv"
    
    try:
        campaign = EmailCampaignSystem(csv_path)
        print(f"✅ Loaded {len(campaign.professors_df)} professors successfully!")
        
        print("\n📧 Available Email Templates:")
        templates = campaign.template_manager.list_templates_by_category()
        
        print("\n🎨 Sample Email Preview:")
        print("=" * 80)
        
        # Show a sample email
        sample_professor = campaign.professors_df.iloc[0]
        context = campaign.create_personalized_context(sample_professor, student_info)
        
        # Generate email with formal template for preview
        email_content = campaign.template_manager.generate_email('research_internship_formal', context)
        
        if email_content:
            lines = email_content.split('\n')
            subject = lines[0].replace('Subject: ', '') if lines[0].startswith('Subject: ') else f"Research Opportunity Inquiry - {student_info['name']}"
            email_body = '\n'.join(lines[2:]) if lines[0].startswith('Subject: ') else email_content
            
            print(f"📧 TO: {sample_professor['Name']} ({sample_professor['Email']})")
            print(f"🏫 UNIVERSITY: {sample_professor['University']}")
            print(f"🔬 RESEARCH: {sample_professor['Research Area']}")
            print(f"📝 SUBJECT: {subject}")
            print("\n📄 EMAIL CONTENT:")
            print("-" * 80)
            print(email_body)
            print("-" * 80)
        
        print("\n🚀 Campaign Options:")
        print("1. Run DRY RUN (preview emails, no sending)")
        print("2. Send REAL EMAILS (actual email campaign)")
        print("3. Exit")
        
        while True:
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == '1':
                print("\n🧪 Running DRY RUN Campaign...")
                campaign.run_campaign(
                    student_info=student_info,
                    template_name='research_inquiry_concise',  # Change template as needed
                    max_emails=10,   # Number of emails to send
                    delay_seconds=2, # Delay between emails (shorter for dry run)
                    dry_run=True
                )
                break
                
            elif choice == '2':
                print("\n⚠️  WARNING: This will send REAL emails to professors!")
                confirm = input("Are you sure you want to proceed? (yes/no): ").strip().lower()
                
                if confirm == 'yes':
                    print("\n📨 Sending REAL EMAIL Campaign...")
                    campaign.run_campaign(
                        student_info=student_info,
                        template_name='research_inquiry_concise',  # You can change this
                        max_emails=10,      # Start with a small number
                        delay_seconds=30,   # 30 seconds between emails to avoid spam detection
                        dry_run=False
                    )
                else:
                    print("❌ Campaign cancelled.")
                break
                
            elif choice == '3':
                print("👋 Goodbye! Good luck with your research applications!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return

if __name__ == "__main__":
    main()
