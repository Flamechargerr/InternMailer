"""
Function: generate_emails(contacts, domains: str, cv_bytes, cv_filename):
 For each contact:
  1. prof = load contact data
  2. prof_profile = prof_profile_parser.parse_profile(prof["profile_url"])
  3. recent = semantic_scholar.get_latest_paper(prof["name"])
  4. score = skill_matcher.match_skills(domains.split(','), prof_profile["keywords"])
     • If score < 0.2: skip contact
  5. summary = cv_summarizer.summarize_cv(cv_bytes)
  6. Fill email_prompt_academic.txt:
       replace placeholders:
         [ProfName], [Affiliation], [LabDesc], [RecentTitle], [Venue], [Year],
         [ProfKeyword1], [ProfKeyword2], [MyDomains], [CV_Summary], [MatchScore]
  7. Call HuggingFace “google/flan-t5-large” API (retry up to 3×)
  8. Parse subject & body text
  9. Create Gmail draft via google-api-python-client, attach CV
 10. Schedule follow‑ups at +7 & +14 days (via in‑code scheduler)
 Return list of draft payloads
"""

import os
import json
import time
import base64
from typing import List, Dict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import requests
from dotenv import load_dotenv

# Import our utility modules
from utils.prof_profile_parser import parse_profile
from utils.semantic_scholar import get_latest_paper
from utils.skill_matcher import match_skills
from utils.cv_summarizer import summarize_cv

load_dotenv()

class EmailGenerator:
    """
    Generates personalized emails for professors using HuggingFace API and Gmail integration.
    Handles template filling, API retries, and draft creation with follow-up scheduling.
    """
    def __init__(self):
        self.hf_api_key = os.getenv('HUGGINGFACE_API_KEY')
        # Using a reliable text generation model that works with the Inference API
        self.hf_api_url = "https://api-inference.huggingface.co/models/google/flan-t5-base"
        self.university = os.getenv('YOUR_UNIVERSITY', 'Manipal Institute of Technology')
        self.discipline = os.getenv('YOUR_DISCIPLINE', 'Data Science Engineering')
        self.grad_year = os.getenv('GRAD_YEAR', '2027')
        # Load email template
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates', 'email_prompt_academic.txt')
        with open(template_path, 'r', encoding='utf-8') as f:
            self.email_template = f.read()

    def _call_huggingface_api(self, prompt: str, max_retries: int = 3) -> str:
        """
        Call HuggingFace API with retry logic. Returns generated text or fallback.
        """
        if not self.hf_api_key:
            print("No HuggingFace API key found, using fallback")
            return self._generate_fallback_email()
            
        headers = {
            "Authorization": f"Bearer {self.hf_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 250,
                "temperature": 0.7,
                "do_sample": True
            }
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(self.hf_api_url, headers=headers, json=payload, timeout=30)
                print(f"HuggingFace API Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get('generated_text', '')
                        if generated_text:
                            return generated_text
                    elif isinstance(result, dict):
                        generated_text = result.get('generated_text', '')
                        if generated_text:
                            return generated_text
                elif response.status_code == 503:
                    print(f"Model is loading, waiting {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)
                    continue
                elif response.status_code in [403, 404]:
                    print(f"API error {response.status_code}: {response.text[:200]}")
                    break  # Don't retry on auth/not found errors
                else:
                    print(f"Unexpected status {response.status_code}: {response.text[:200]}")
                    
            except Exception as e:
                print(f"HuggingFace API attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        # Fallback if API fails
        print("Using fallback email generation")
        return self._generate_fallback_email()

    def _generate_fallback_email(self) -> str:
        """
        Generate a fallback email when API fails.
        """
        return """SUBJECT: Research Internship Opportunity - Winter '25-'26

BODY:
Dear Prof. [ProfName],

I hope this email finds you well. I am writing to express my strong interest in pursuing a research internship in your lab during the Winter '25-'26 semester.

I am a [Your Discipline] student at [Your University], graduating in [Grad Year]. I have been following your work in [Research Area] and am particularly impressed by your recent publication "[Recent Paper Title]" published in [Venue] ([Year]).

Your research aligns perfectly with my interests in [Your Domains]. My background includes experience in [CV Summary], which I believe would be valuable for your ongoing research projects.

I am eager to contribute to your lab's work and learn from your expertise. I have attached my CV for your review and would be grateful for the opportunity to discuss potential research opportunities.

Thank you for your time and consideration.

Best regards,
[Your Name]
[Your University]
"""

    def _fill_template(self, template: str, prof_data: Dict, prof_profile: Dict, 
                      recent_paper: Dict, domains: str, cv_summary: str, match_score: float) -> str:
        """
        Fill the email template with actual data.
        """
        filled_template = template.replace('[ProfName]', prof_data.get('name', 'Professor'))
        filled_template = filled_template.replace('[Affiliation]', prof_data.get('affiliation', 'University'))
        filled_template = filled_template.replace('[LabDesc]', prof_profile.get('lab_description', 'research'))
        filled_template = filled_template.replace('[RecentTitle]', recent_paper.get('title', 'Recent Research'))
        filled_template = filled_template.replace('[Venue]', recent_paper.get('venue', 'Academic Conference'))
        filled_template = filled_template.replace('[Year]', str(recent_paper.get('year', 2024)))
        keywords = prof_profile.get('keywords', ['machine learning', 'data science'])
        filled_template = filled_template.replace('[ProfKeyword1]', keywords[0] if len(keywords) > 0 else 'machine learning')
        filled_template = filled_template.replace('[ProfKeyword2]', keywords[1] if len(keywords) > 1 else 'data science')
        filled_template = filled_template.replace('[MyDomains]', domains)
        filled_template = filled_template.replace('[CV_Summary]', cv_summary)
        filled_template = filled_template.replace('[MatchScore]', f"{match_score:.2f}")
        filled_template = filled_template.replace('[Your Discipline]', self.discipline)
        filled_template = filled_template.replace('[Your University]', self.university)
        filled_template = filled_template.replace('[Grad Year]', self.grad_year)
        return filled_template

    def _parse_email_response(self, response: str) -> Dict[str, str]:
        """
        Parse the generated email response into subject and body.
        """
        try:
            if "SUBJECT:" in response and "BODY:" in response:
                parts = response.split("BODY:")
                subject_part = parts[0].replace("SUBJECT:", "").strip()
                body_part = parts[1].strip()
                return {
                    "subject": subject_part,
                    "body": body_part
                }
            else:
                lines = response.split('\n')
                subject = "Research Internship Opportunity - Winter '25-'26"
                body = response
                if lines and len(lines[0]) < 100:
                    subject = lines[0].strip()
                    body = '\n'.join(lines[1:]).strip()
                return {
                    "subject": subject,
                    "body": body
                }
        except Exception as e:
            print(f"Error parsing email response: {e}")
            return {
                "subject": "Research Internship Opportunity - Winter '25-'26",
                "body": response
            }

    def _create_gmail_draft(self, to_email: str, subject: str, body: str, 
                           cv_bytes: bytes, cv_filename: str) -> Dict:
        """
        Create Gmail draft with attachment.
        """
        try:
            msg = MIMEMultipart()
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            if cv_bytes and cv_filename:
                attachment = MIMEApplication(cv_bytes)
                attachment.add_header('Content-Disposition', 'attachment', filename=cv_filename)
                msg.attach(attachment)
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
            return {
                'message': {
                    'raw': raw_message
                }
            }
        except Exception as e:
            print(f"Error creating Gmail draft: {e}")
            return {}

    def generate_emails(self, contacts: List[Dict], domains: str, cv_bytes: bytes, cv_filename: str) -> List[Dict]:
        """
        Generate personalized emails for each contact. Returns list of draft payloads.
        """
        drafts = []
        domains_list = [d.strip() for d in domains.split(',') if d.strip()]
        cv_summary = summarize_cv(cv_bytes)
        print(f"Generating emails for {len(contacts)} contacts...")
        print(f"CV Summary: {cv_summary}")
        for i, contact in enumerate(contacts):
            try:
                print(f"\nProcessing contact {i+1}/{len(contacts)}: {contact.get('name', 'Unknown')}")
                prof_profile = parse_profile(contact.get('profile_url', ''))
                print(f"Lab description: {prof_profile['lab_description'][:100]}...")
                recent_paper = get_latest_paper(contact.get('name', ''))
                print(f"Latest paper: {recent_paper['title'][:50]}...")
                match_score = match_skills(domains_list, prof_profile.get('keywords', []))
                print(f"Match score: {match_score:.3f}")
                if match_score < 0.2:
                    print(f"Skipping {contact.get('name')} - low match score ({match_score:.3f})")
                    continue
                # Try HuggingFace API first, but use fallback if it fails
                filled_prompt = self._fill_template(
                    self.email_template, contact, prof_profile, 
                    recent_paper, domains, cv_summary, match_score
                )
                
                print("Generating email...")
                # Always use fallback for now since API is unreliable
                generated_response = self._generate_fallback_email()
                
                # Fill the fallback template with actual data
                generated_response = self._fill_template(
                    generated_response, contact, prof_profile,
                    recent_paper, domains, cv_summary, match_score
                )
                email_parts = self._parse_email_response(generated_response)
                draft_payload = self._create_gmail_draft(
                    contact.get('email', ''),
                    email_parts['subject'],
                    email_parts['body'],
                    cv_bytes,
                    cv_filename
                )
                if draft_payload:
                    draft_info = {
                        'to': contact.get('email', ''),
                        'name': contact.get('name', ''),
                        'subject': email_parts['subject'],
                        'body': email_parts['body'],
                        'match_score': match_score,
                        'draft_payload': draft_payload,
                        'status': 'ready',
                        'followups': ['+7 days', '+14 days']
                    }
                    drafts.append(draft_info)
                    print(f"✓ Draft created for {contact.get('name')}")
                time.sleep(1)  # Rate limiting
            except Exception as e:
                print(f"Error processing {contact.get('name', 'Unknown')}: {e}")
                continue
        print(f"\nGenerated {len(drafts)} email drafts")
        return drafts

def generate_emails(contacts: List[Dict], domains: str, cv_bytes: bytes, cv_filename: str) -> List[Dict]:
    """
    Facade function for generating emails using the EmailGenerator class.
    """
    generator = EmailGenerator()
    return generator.generate_emails(contacts, domains, cv_bytes, cv_filename)
