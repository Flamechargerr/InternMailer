#!/usr/bin/env python3
"""
💼 INTERNMAILING - CORPORATE OUTREACH MODULE (PROTOTYPE)
======================================================
Corporate expansion for job referrals, informational interviews, and professional networking

This is a prototype module showing how InternMailing can expand beyond academic outreach
to include corporate professionals, hiring managers, and industry leaders.
"""

import re
import time
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import csv
from pathlib import Path

@dataclass
class CorporateContact:
    """📊 Corporate contact data structure"""
    name: str
    email: str
    company: str
    title: str
    department: str
    linkedin_url: Optional[str] = None
    industry: str = "Technology"
    location: str = ""
    hiring_indicator: bool = False
    referral_potential: int = 0  # 0-100 score
    contact_source: str = "manual"

class CorporateDataExtractor:
    """🔍 Extract corporate contact data from various sources"""
    
    def __init__(self):
        self.company_domains = {
            # Tech Giants
            'google': 'google.com',
            'microsoft': 'microsoft.com', 
            'apple': 'apple.com',
            'amazon': 'amazon.com',
            'meta': 'meta.com',
            'netflix': 'netflix.com',
            'tesla': 'tesla.com',
            'nvidia': 'nvidia.com',
            
            # Consulting & Finance
            'mckinsey': 'mckinsey.com',
            'bain': 'bain.com',
            'bcg': 'bcg.com',
            'goldman': 'gs.com',
            'jpmorgan': 'jpmorganchase.com',
            'blackrock': 'blackrock.com',
            
            # Startups & Scale-ups
            'openai': 'openai.com',
            'anthropic': 'anthropic.com',
            'stripe': 'stripe.com',
            'airbnb': 'airbnb.com',
            'uber': 'uber.com',
            'spotify': 'spotify.com'
        }
        
        self.hiring_indicators = [
            'hiring', 'recruiting', 'talent', 'hr', 'people',
            'manager', 'director', 'lead', 'head', 'vp',
            'chief', 'senior', 'principal', 'staff'
        ]
    
    def load_verified_contacts(self) -> List[CorporateContact]:
        """📂 Load verified contacts from CSV"""
        # Assuming script is in root of project, data is in data/
        csv_path = Path(__file__).parent / 'data' / 'hiring_managers.csv'
        
        if not csv_path.exists():
            print(f"⚠️ Verified contacts file not found: {csv_path}")
            return []
            
        contacts = []
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Basic validation
                    if not row.get('Email') or not row.get('Name'):
                        continue
                        
                    contact = CorporateContact(
                        name=row['Name'],
                        email=row['Email'],
                        company=row['Company'],
                        title=row['Role'],
                        department=row['Department'],
                        contact_source=row['Source'],
                        hiring_indicator=True,
                        referral_potential=95, # High for verified list
                        industry="Technology"
                    )
                    contacts.append(contact)
            print(f"✅ Loaded {len(contacts)} verified contacts from CSV")
        except Exception as e:
            print(f"⚠️ Error loading verified contacts: {e}")
            
        return contacts

    def extract_from_company_website(self, company_domain: str) -> List[CorporateContact]:
        """🌐 Extract contacts from company website (prototype)"""
        # In production, this would use web scraping.
        # Since we only want authentic data, we return empty here 
        # and rely on the verified CSV list.
        return []
    

    
    def extract_from_linkedin_api(self, company_name: str) -> List[CorporateContact]:
        """👔 Extract contacts from LinkedIn API (prototype)"""
        # Prototype implementation - would integrate with LinkedIn API
        # Returning empty list to ensure only authentic CSV data is used
        return []

    def extract_hiring_managers(self, company_domain: str, department: str = "") -> List[CorporateContact]:
        """👨‍💼 Extract hiring managers and recruiters"""
        contacts = self.extract_from_company_website(company_domain)
        
        # Filter for hiring potential
        hiring_contacts = [
            contact for contact in contacts 
            if contact.hiring_indicator and contact.referral_potential > 70
        ]
        
        return hiring_contacts

    def generate_email_permutations(self, first_name: str, last_name: str, domain: str) -> List[str]:
        """📧 Generate common corporate email permutations"""
        f = first_name.lower()
        l = last_name.lower()
        
        permutations = [
            f"{f}.{l}@{domain}",       # first.last@company.com
            f"{f}{l}@{domain}",        # firstlast@company.com
            f"{f}@{domain}",           # first@company.com
            f"{f[0]}{l}@{domain}",     # flast@company.com
            f"{f}.{l[0]}@{domain}",    # first.l@company.com
            f"{f}_{l}@{domain}",       # first_last@company.com
        ]
        return permutations

class CorporateEmailPersonalizer:
    """✨ Personalize emails for corporate outreach"""
    
    def __init__(self):
        self.templates = {
            'job_application': self._get_job_application_template(),
            'informational_interview': self._get_informational_interview_template(), 
            'referral_request': self._get_referral_request_template(),
            'industry_insights': self._get_industry_insights_template(),
            'follow_up': self._get_follow_up_template()
        }
        
        self.company_research = {
            'Google': {
                'recent_news': 'AI advancements in Bard and Gemini',
                'culture': 'innovation-driven, collaborative, data-focused',
                'values': 'user focus, technical excellence, bold thinking'
            },
            'Microsoft': {
                'recent_news': 'Azure growth and AI integration',
                'culture': 'growth mindset, inclusive, customer-obsessed', 
                'values': 'empowerment, partnership, diverse perspectives'
            }
        }
    
    def personalize_corporate_email(self, template_type: str, contact: CorporateContact, 
                                  job_title: str = "", specific_request: str = "") -> Tuple[str, str]:
        """📧 Generate personalized corporate outreach email"""
        
        template = self.templates.get(template_type, self.templates['informational_interview'])
        company_info = self.company_research.get(contact.company, {})
        
        # Personalization variables
        variables = {
            'recipient_name': contact.name,
            'company': contact.company,
            'title': contact.title,
            'department': contact.department,
            'recent_news': company_info.get('recent_news', f'recent developments at {contact.company}'),
            'company_culture': company_info.get('culture', 'innovative and dynamic work environment'),
            'values': company_info.get('values', 'excellence and innovation'),
            'job_title': job_title or 'software engineering roles',
            'specific_request': specific_request or 'guidance on opportunities',
            'location': contact.location or contact.company
        }
        
        # Generate subject and body
        subject = template['subject'].format(**variables)
        body = template['body'].format(**variables)
        
        return subject, body
    
    def _get_job_application_template(self) -> Dict[str, str]:
        """💼 Job application template"""
        return {
            'subject': "Application for {job_title} - Referral Request",
            'body': """Dear {recipient_name},

I hope this email finds you well. I'm reaching out regarding {job_title} opportunities at {company}, where I see you work as {title} in the {department} team.

I've been following {company}'s {recent_news} with great interest, and I'm particularly drawn to your {company_culture}. Your expertise in {department} aligns perfectly with my background and career aspirations.

Background & Interest:
I'm a passionate software engineer with experience in [your relevant skills]. I'm particularly excited about {company}'s commitment to {values}, which resonates strongly with my own professional values.

Specific Request:
I would be incredibly grateful for any guidance you might offer regarding:
- Current or upcoming opportunities in {department}
- Insights into the team culture and what {company} looks for in candidates
- Any advice for someone looking to contribute to {company}'s mission

I understand your time is valuable, and I'd be happy to keep this conversation brief. Would you be open to a 15-minute coffee chat or phone call in the coming weeks?

Thank you for considering my request. I look forward to the possibility of connecting with you.

Best regards,
[Your Name]
[Your LinkedIn Profile]
[Your Contact Information]"""
        }
    
    def _get_informational_interview_template(self) -> Dict[str, str]:
        """🤝 Informational interview template"""
        return {
            'subject': "Seeking Industry Insights - {company} Professional Guidance",
            'body': """Dear {recipient_name},

I hope you're having a great week! I came across your profile and was impressed by your role as {title} at {company}. Your experience in {department} is exactly the type of career path I'm interested in exploring.

About Me:
I'm currently [your background] and am passionate about transitioning into [relevant field]. I've been following {company}'s work, particularly {recent_news}, and I'm fascinated by the impact your team is making.

My Request:
I would love to learn from your experience and insights about:
- Career progression in {department} at {company}
- Skills and qualities that make someone successful in your role
- Industry trends you're excited about
- Advice for someone looking to break into this field

I completely understand if your schedule doesn't permit, but I'd be honored to buy you coffee or have a brief 20-minute phone conversation at your convenience.

Thank you for your time and consideration. I look forward to potentially connecting with you.

Warm regards,
[Your Name]
[Your Contact Information]"""
        }
    
    def _get_referral_request_template(self) -> Dict[str, str]:
        """🌟 Referral request template"""
        return {
            'subject': "Referral Request - Passionate About Joining {company}",
            'body': """Dear {recipient_name},

I hope this message finds you well. I'm reaching out because I'm deeply interested in joining {company} and would be grateful for your guidance as someone who works in {department}.

Why {company}:
I've been following {company}'s journey, especially {recent_news}. The company's focus on {values} aligns perfectly with my professional goals and personal values. I'm particularly excited about the opportunity to contribute to {department}'s mission.

My Background:
[Brief relevant background - 2-3 sentences about your experience and skills]

My Request:
If there are any current or upcoming opportunities in {department} that might be a good fit, I would be incredibly grateful for a referral or introduction to the appropriate hiring manager. I've attached my resume for your reference.

I understand that referrals are valuable and not given lightly. I'm confident that my skills, enthusiasm, and cultural fit would make me a strong addition to the {company} team.

Would you be open to a brief conversation about potential opportunities? I'm happy to work around your schedule.

Thank you for your time and consideration.

Best regards,
[Your Name]
[Your LinkedIn Profile]
[Your Resume Attached]"""
        }
    
    def _get_industry_insights_template(self) -> Dict[str, str]:
        """📈 Industry insights template"""
        return {
            'subject': "Industry Insights Request from Aspiring {department} Professional",
            'body': """Dear {recipient_name},

I hope you're doing well! I discovered your profile while researching professionals in {department} at leading companies like {company}. Your experience and insights would be invaluable to someone like me who is passionate about this industry.

Industry Interest:
I'm particularly interested in understanding how the industry is evolving, especially with {recent_news}. Your perspective from {company} would provide incredible insights into where the field is heading.

What I'm Hoping to Learn:
- Key trends you're seeing in {department}
- Skills that are becoming increasingly important
- Challenges and opportunities in the industry
- Advice for someone looking to make a meaningful impact

I would be honored to learn from your experience over a brief coffee chat or phone call. I'm happy to accommodate your schedule and location preferences.

Thank you for considering my request. I look forward to the possibility of connecting with you.

Best regards,
[Your Name]
[Your Contact Information]"""
        }
    
    def _get_follow_up_template(self) -> Dict[str, str]:
        """🔄 Follow-up template"""
        return {
            'subject': "Following Up - {specific_request}",
            'body': """Dear {recipient_name},

I hope you're having a great week! I wanted to follow up on my previous message regarding {specific_request}.

I completely understand that you receive many requests and have a busy schedule. If the timing isn't right for a conversation, I completely understand.

If you do have any insights or suggestions - even just a brief email response - I would be incredibly grateful. Any guidance from someone with your experience at {company} would be invaluable.

Thank you again for your time and consideration.

Best regards,
[Your Name]"""
        }

class CorporateOutreachSystem:
    """🚀 Main corporate outreach system"""
    
    def __init__(self):
        self.data_extractor = CorporateDataExtractor()
        self.email_personalizer = CorporateEmailPersonalizer()
        self.contact_database = []
        
    def discover_corporate_contacts(self, company_list: List[str], 
                                  target_departments: List[str] = None) -> List[CorporateContact]:
        """🔍 Discover corporate contacts from multiple sources"""
        all_contacts = []
        
        if target_departments is None:
            target_departments = ['Engineering', 'Product', 'Data Science', 'AI/ML', 'Cloud']
        
        # Load verified contacts from CSV first
        verified_contacts = self.data_extractor.load_verified_contacts()
        if verified_contacts:
            all_contacts.extend(verified_contacts)
        
        for company in company_list:
            print(f"🏢 Discovering contacts at {company}...")
            
            # Get company domain
            domain = self.data_extractor.company_domains.get(company.lower(), f"{company.lower()}.com")
            
            # Extract from various sources
            website_contacts = self.data_extractor.extract_from_company_website(domain)
            linkedin_contacts = self.data_extractor.extract_from_linkedin_api(company)
            hiring_contacts = self.data_extractor.extract_hiring_managers(domain)
            
            # Combine and deduplicate
            company_contacts = website_contacts + linkedin_contacts + hiring_contacts
            unique_contacts = self._deduplicate_contacts(company_contacts)
            
            # Filter by target departments
            filtered_contacts = [
                contact for contact in unique_contacts
                if any(dept.lower() in contact.department.lower() for dept in target_departments)
            ]
            
            all_contacts.extend(filtered_contacts)
            print(f"   ✅ Found {len(filtered_contacts)} relevant contacts")
        
        # Final deduplication
        self.contact_database = self._deduplicate_contacts(all_contacts)
        return self.contact_database
    
    def launch_corporate_campaign(self, contacts: List[CorporateContact], 
                                campaign_type: str = 'informational_interview',
                                job_title: str = "", max_emails: int = 20) -> Dict:
        """🚀 Launch corporate outreach campaign"""
        
        print(f"💼 LAUNCHING CORPORATE OUTREACH CAMPAIGN")
        print(f"   📧 Campaign Type: {campaign_type}")
        print(f"   👥 Target Contacts: {len(contacts)}")
        print(f"   📈 Max Emails: {max_emails}")
        print()
        
        results = {
            'sent': 0,
            'failed': 0,
            'contacts_processed': [],
            'campaign_type': campaign_type,
            'start_time': datetime.now().isoformat()
        }
        
        for i, contact in enumerate(contacts[:max_emails], 1):
            try:
                print(f"📧 Email {i}/{min(len(contacts), max_emails)}: {contact.email}")
                print(f"   👤 {contact.name} - {contact.title}")
                print(f"   🏢 {contact.company} - {contact.department}")
                
                # Generate personalized email
                subject, body = self.email_personalizer.personalize_corporate_email(
                    campaign_type, contact, job_title
                )
                
                print(f"   📋 Subject: {subject}")
                print(f"   📝 Body: {body[:100]}...")
                
                # In production, would actually send email here
                print(f"   ✅ [PROTOTYPE] Email generated successfully")
                
                results['sent'] += 1
                results['contacts_processed'].append({
                    'name': contact.name,
                    'email': contact.email,
                    'company': contact.company,
                    'status': 'sent'
                })
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Failed to process {contact.name}: {e}")
                results['failed'] += 1
                results['contacts_processed'].append({
                    'name': contact.name,
                    'email': contact.email,
                    'company': contact.company,
                    'status': 'failed',
                    'error': str(e)
                })
        
        results['end_time'] = datetime.now().isoformat()
        results['success_rate'] = (results['sent'] / (results['sent'] + results['failed']) * 100) if (results['sent'] + results['failed']) > 0 else 0
        
        print(f"\n📊 CORPORATE CAMPAIGN RESULTS:")
        print(f"   ✅ Emails Sent: {results['sent']}")
        print(f"   ❌ Failed: {results['failed']}")
        print(f"   📈 Success Rate: {results['success_rate']:.1f}%")
        
        return results
    
    def _deduplicate_contacts(self, contacts: List[CorporateContact]) -> List[CorporateContact]:
        """🔄 Remove duplicate contacts"""
        seen_emails = set()
        unique_contacts = []
        
        for contact in contacts:
            if contact.email not in seen_emails:
                seen_emails.add(contact.email)
                unique_contacts.append(contact)
        
        return unique_contacts
    
    def get_campaign_analytics(self) -> Dict:
        """📊 Get campaign analytics and insights"""
        if not self.contact_database:
            return {'error': 'No contacts in database'}
        
        analytics = {
            'total_contacts': len(self.contact_database),
            'companies': list(set(contact.company for contact in self.contact_database)),
            'departments': list(set(contact.department for contact in self.contact_database)),
            'avg_referral_potential': sum(contact.referral_potential for contact in self.contact_database) / len(self.contact_database),
            'hiring_contacts': len([c for c in self.contact_database if c.hiring_indicator]),
            'top_companies': self._get_top_companies(),
            'contact_sources': self._get_contact_sources()
        }
        
        return analytics
    
    def _get_top_companies(self) -> List[Dict]:
        """🏆 Get top companies by contact count"""
        company_counts = {}
        for contact in self.contact_database:
            company_counts[contact.company] = company_counts.get(contact.company, 0) + 1
        
        return [
            {'company': company, 'contacts': count}
            for company, count in sorted(company_counts.items(), key=lambda x: x[1], reverse=True)
        ]
    
    def _get_contact_sources(self) -> Dict[str, int]:
        """📈 Get contact source distribution"""
        sources = {}
        for contact in self.contact_database:
            sources[contact.contact_source] = sources.get(contact.contact_source, 0) + 1
        return sources

def demo_corporate_outreach():
    """🎬 Demonstration of corporate outreach system"""
    print("💼 INTERNMAILING - CORPORATE OUTREACH DEMO")
    print("=" * 60)
    
    # Initialize system
    corporate_system = CorporateOutreachSystem()
    
    # Target companies
    target_companies = ['Google', 'Microsoft', 'Apple', 'NetApp', 'Expedia Group', 'JP Morgan Chase']
    target_departments = ['Engineering', 'AI/ML', 'Product']
    
    # Discover contacts
    print("🔍 DISCOVERING CORPORATE CONTACTS...")
    contacts = corporate_system.discover_corporate_contacts(target_companies, target_departments)
    
    print(f"\n📊 CONTACT DISCOVERY RESULTS:")
    print(f"   👥 Total Contacts Found: {len(contacts)}")
    
    # Show sample contacts
    print(f"\n👥 SAMPLE CONTACTS:")
    for i, contact in enumerate(contacts[:5], 1):
        print(f"   {i}. {contact.name} - {contact.title}")
        print(f"      🏢 {contact.company} | 📧 {contact.email}")
        print(f"      🎯 Referral Potential: {contact.referral_potential}%")
    
    # Launch campaign
    print(f"\n🚀 LAUNCHING DEMO CAMPAIGN...")
    results = corporate_system.launch_corporate_campaign(
        contacts, 
        campaign_type='informational_interview',
        job_title='Software Engineer',
        max_emails=5
    )
    
    # Show analytics
    print(f"\n📊 CAMPAIGN ANALYTICS:")
    analytics = corporate_system.get_campaign_analytics()
    print(f"   🏢 Companies: {len(analytics['companies'])}")
    print(f"   👨‍💼 Avg Referral Potential: {analytics['avg_referral_potential']:.1f}%")
    print(f"   🎯 Hiring Contacts: {analytics['hiring_contacts']}")
    
    print(f"\n🎉 CORPORATE EXPANSION DEMO COMPLETE!")
    print(f"💡 This prototype shows InternMailing's potential for corporate outreach")

if __name__ == "__main__":
    demo_corporate_outreach()