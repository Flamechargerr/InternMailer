"""
🎯 SMART AI EMAIL GENERATOR - Hugging Face Powered
Fetches real professor research and generates truly personalized emails
"""

import requests
import json
import sqlite3
import smtplib
import os
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from urllib.parse import quote_plus

# Email credentials
EMAIL = 'tripathy.anamay23@gmail.com'
PASSWORD = 'xctf elgn llfo aohf'

class SmartAIGenerator:
    def __init__(self):
        self.hf_api = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
        
    def fetch_professor_research(self, name, email):
        """Fetch real research data from Semantic Scholar"""
        try:
            print(f"  📚 Fetching research for {name}...")
            
            # Try Semantic Scholar
            search_url = f"https://api.semanticscholar.org/graph/v1/author/search?query={quote_plus(name)}"
            response = requests.get(search_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    author_id = data['data'][0]['authorId']
                    
                    # Get papers
                    papers_url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}/papers?fields=title,year,abstract&limit=5"
                    papers_resp = requests.get(papers_url, timeout=10)
                    
                    if papers_resp.status_code == 200:
                        papers_data = papers_resp.json()
                        papers = []
                        for p in papers_data.get('data', [])[:3]:
                            if p.get('year', 0) >= 2020:
                                papers.append({
                                    'title': p.get('title', ''),
                                    'year': p.get('year', ''),
                                    'abstract': p.get('abstract', '')[:300]
                                })
                        
                        if papers:
                            print(f"  ✅ Found {len(papers)} recent papers")
                            return papers
            
            print(f"  ⚠️ No papers found, using domain-based research")
            return self._get_domain_based_research(email)
            
        except Exception as e:
            print(f"  ⚠️ Research fetch failed: {e}")
            return self._get_domain_based_research(email)
    
    def _get_domain_based_research(self, email):
        """Get research area based on university domain"""
        domain = email.split('@')[1].lower()
        
        research_map = {
            'mit.edu': {'area': 'distributed systems and operating systems', 'focus': 'high-performance computing'},
            'stanford.edu': {'area': 'machine learning and AI', 'focus': 'deep learning systems'},
            'berkeley.edu': {'area': 'data systems and databases', 'focus': 'distributed computing'},
            'imperial.ac.uk': {'area': 'software engineering and verification', 'focus': 'program analysis'},
            'ox.ac.uk': {'area': 'computational science', 'focus': 'scientific computing'},
            'cam.ac.uk': {'area': 'computer systems', 'focus': 'systems architecture'},
        }
        
        for key, value in research_map.items():
            if key in domain:
                return [{'title': f"Research in {value['area']}", 'focus': value['focus']}]
        
        return [{'title': 'Computer Science Research', 'focus': 'computational methods'}]
    
    def generate_with_hf(self, prompt, max_tokens=200):
        """Call Hugging Face API"""
        try:
            response = requests.post(
                self.hf_api,
                headers={"Content-Type": "application/json"},
                json={
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": max_tokens,
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "do_sample": True,
                        "return_full_text": False
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    text = result[0].get('generated_text', '').strip()
                    # Clean up
                    text = text.replace('\\n', ' ').strip()
                    if len(text) > 50:
                        return text
            
            return None
            
        except Exception as e:
            print(f"  ⚠️ HF API error: {e}")
            return None
    
    def create_personalized_email(self, name, university, email, papers):
        """Generate truly personalized email content"""
        
        # Extract real research info
        if papers and len(papers) > 0:
            paper_title = papers[0].get('title', '')
            paper_year = papers[0].get('year', '2023')
            research_focus = papers[0].get('focus', papers[0].get('title', '').split()[0])
        else:
            paper_title = "recent work in computer systems"
            paper_year = "recent"
            research_focus = "systems research"
        
        # Prompt 1: Opening paragraph
        opening_prompt = f"""Write a professional email opening for a research inquiry. 
Professor: {name}
University: {university}
Their Research: {paper_title}

Write 2-3 sentences introducing yourself as Anamay Tripathy, Data Science student at MIT Manipal, expressing interest in their specific work. Be professional and specific. Do not use generic phrases."""

        opening = self.generate_with_hf(opening_prompt, 150)
        
        # Prompt 2: Paper-specific mention
        paper_prompt = f"""Write 2 sentences about why you're interested in a professor's paper.
Paper: {paper_title} ({paper_year})
Your Background: Machine Learning, Data Science, Python/TensorFlow

Connect the paper to your interests specifically. No generic statements."""

        paper_mention = self.generate_with_hf(paper_prompt, 150)
        
        # If HF fails, use detailed templates with real data
        if not opening:
            opening = f"I am writing to express my strong interest in joining your research group at {university}. I have been following your work, particularly your {paper_year} research on {paper_title[:80]}, which addresses fundamental challenges in {research_focus}."
        
        if not paper_mention:
            paper_mention = f"Your approach in '{paper_title[:100]}' is particularly relevant to my interests in applying machine learning to systems research. I believe my experience with large-scale data processing could contribute to extending this work."
        
        # Build complete email
        email_html = f"""<p>Dear Professor {name},</p>

<p>{opening}</p>

<p>{paper_mention}</p>

<p>My academic background and research experiences have prepared me to contribute meaningfully to your lab:</p>

<ul>
    <li><strong>Research Leadership:</strong> As Technical Head at YaanBarpe (government-incubated startup), I led 12 developers building ML-powered waste management systems, achieving 34% efficiency improvement</li>
    <li><strong>Industry Experience:</strong> Interned at Intellect Design Arena optimizing financial transaction processing (2.3M+ daily transactions) using Python and Kafka, reducing processing time by 67%</li>
    <li><strong>Technical Skills:</strong> Python, PyTorch, TensorFlow, SQL, distributed systems, scalable ML pipelines</li>
</ul>

<p>I am particularly interested in how my background in machine learning and large-scale data systems could support your ongoing work in {research_focus}. I am a quick learner, highly motivated, and committed to producing high-quality research outcomes.</p>

<p>I have attached my CV for your review. I would welcome the opportunity to discuss my background and potential fit within your group at your earliest convenience.</p>

<p>Thank you for your time and consideration.</p>

<p>Sincerely,<br><br>
<strong>Anamay Tripathy</strong><br>
B.Tech Data Science Engineering<br>
MIT Manipal, India<br>
<a href="mailto:tripathy.anamay23@gmail.com">tripathy.anamay23@gmail.com</a><br>
<a href="https://anamay.vercel.app">anamay.vercel.app</a><br>
+91-9877454747</p>
"""
        
        subject = f"Research Collaboration Inquiry - {research_focus.title()}"
        
        return subject, email_html

def send_email(to_email, subject, body_html, name):
    """Send email"""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        html_part = MIMEText(body_html, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Attach CV
        cv_path = Path('resumes/CV_Anamay_Modern.pdf')
        if cv_path.exists():
            with open(cv_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="Anamay_Tripathy_CV.pdf"')
            msg.attach(part)
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, to_email, msg.as_string())
        server.quit()
        
        print(f"  ✅ Sent to {name} ({to_email})")
        return True
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

def main():
    print("\\n🎯 SMART AI EMAIL SENDER - Hugging Face Powered")
    print("=" * 60)
    
    # Get professors
    conn = sqlite3.connect('data/clean_40k_professors.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, affiliation FROM verified_contacts LIMIT 1")
    professors = cursor.fetchall()
    conn.close()
    
    ai = SmartAIGenerator()
    
    for name, email, affiliation in professors:
        print(f"\\n🤖 Processing {name}...")
        
        # Fetch real research
        papers = ai.fetch_professor_research(name, email)
        
        # Generate email
        university = affiliation if affiliation else email.split('@')[1].split('.')[0].title()
        subject, body = ai.create_personalized_email(name, university, email, papers)
        
        # Send
        send_email(email, subject, body, name)
        
        # Show preview
        print(f"\\n📧 EMAIL PREVIEW:")
        print(f"Subject: {subject}")
        print(f"Body preview: {body[:200]}...")
        
        time.sleep(3)
    
    print("\\n" + "=" * 60)
    print("✅ Done! Check your inbox.")

if __name__ == "__main__":
    main()
