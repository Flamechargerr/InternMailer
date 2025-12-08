"""
🦙 OLLAMA AI EMAIL GENERATOR
100% Free, runs locally on your machine
Generates personalized emails using Llama 3 via Ollama
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

EMAIL = 'tripathy.anamay23@gmail.com'
PASSWORD = 'xctf elgn llfo aohf'

OLLAMA_API = "http://localhost:11434/api/generate"

def fetch_papers(professor_name):
    """Fetch real papers from Semantic Scholar"""
    try:
        search_url = f"https://api.semanticscholar.org/graph/v1/author/search?query={quote_plus(professor_name)}"
        resp = requests.get(search_url, timeout=15)
        
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        if not data.get('data') or len(data['data']) == 0:
            return None
        
        
        author_id = data['data'][0]['authorId']
        
        papers_url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}/papers"
        papers_resp = requests.get(
            papers_url,
            params={'fields': 'title,year,abstract,citationCount', 'limit': 10},
            timeout=15
        )
        
        if papers_resp.status_code != 200:
            return None
        
        papers_data = papers_resp.json()
        papers = []
        
        for p in papers_data.get('data', []):
            if p.get('year', 0) >= 2018 and p.get('title'):
                papers.append({
                    'title': p['title'],
                    'year': p.get('year', ''),
                    'abstract': p.get('abstract', '')[:400] if p.get('abstract') else '',
                    'citations': p.get('citationCount', 0)
                })
        
        papers.sort(key=lambda x: (x['year'], x['citations']), reverse=True)
        return papers[:3] if papers else None
        
    except Exception as e:
        print(f"    ⚠️ Paper fetch error: {e}")
        return None

def generate_with_ollama(prompt, model="llama3"):
    """Generate text using Ollama (local, free)"""
    try:
        response = requests.post(
            OLLAMA_API,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 250
                }
            },
            timeout=180  # Increased timeout for slower machines
        )
        
        if response.status_code == 200:
            result = response.json()
            text = result.get('response', '').strip()
            
            # Clean up AI meta-commentary
            text = text.replace('Here is a possible email opening:', '')
            text = text.replace('Here is a possible opening:', '')
            text = text.replace('Here is the email:', '')
            text = text.replace('Here is my response:', '')
            text = text.replace('Dear Professor Belay,', f'Dear Professor {name},') if 'name' in locals() else text
            
            # Remove any text before "Dear Professor"
            if 'Dear Professor' in text:
                text = text[text.index('Dear Professor'):]
            
            # Remove multiple blank lines
            while '\n\n\n' in text:
                text = text.replace('\n\n\n', '\n\n')
            
            text = text.strip()
            
            if len(text) > 50:
                print(f"    ✓ Generated {len(text)} chars")
                return text
            else:
                print(f"    ⚠️ Output too short ({len(text)} chars)")
        else:
            print(f"    ❌ Ollama error {response.status_code}")
        
        return None
        
    except requests.exceptions.ConnectionError:
        print(f"    ❌ Cannot connect to Ollama. Is it running?")
        print(f"       Start with: ollama serve")
        return None
    except Exception as e:
        print(f"    ❌ Ollama error: {e}")
        return None

def create_ai_email(name, university, papers):
    """Generate email with Ollama AI"""
    
    if not papers:
        print("  ❌ No papers - cannot personalize")
        return None, None
    
    paper_list = "\n".join([f"- {p['title']} ({p['year']})" for p in papers[:2]])
    
    print(f"\n  🦙 Generating with Ollama...")
    
    # Opening paragraph
    opening_prompt = f"""You are writing an email to Professor {name} at {university}.

Their recent papers:
{paper_list}

Write ONLY 2-3 professional sentences for the email opening. You are Anamay Tripathy, Data Science student at MIT Manipal.

Requirements:
- Start with "I am writing to..."
- Mention their specific paper title from the list above
- Show genuine interest
- NO meta-commentary like "Here is..." or "Dear Professor..."
- Output ONLY the 2-3 sentences, nothing else

Output:"""

    opening = generate_with_ollama(opening_prompt)
    
    if not opening:
        return None, None
    
    # Research connection
    connection_prompt = f"""Explain why this professor's research interests you.

Paper: "{papers[0]['title']}" ({papers[0]['year']})

Your background:
- Led ML waste management system at YaanBarpe (34% efficiency gain)
- Optimized financial data processing at Intellect Design Arena (67% faster)
- Skills: Python, PyTorch, TensorFlow

Write 2-3 sentences explaining:
- What interests you about this paper
- How it connects to your experience
- How you could contribute

Be specific. Write ONLY the explanation:"""

    connection = generate_with_ollama(connection_prompt)
    
    if not connection:
        return None, None
    
    # Build email
    email_html = f"""<p>Dear Professor {name},</p>

<p>{opening}</p>

<p>{connection}</p>

<p>My technical background includes:</p>

<ul>
    <li><strong>Research Leadership:</strong> Technical Head at YaanBarpe, leading ML-powered waste management (34% efficiency improvement)</li>
    <li><strong>Industry Experience:</strong> Optimized financial data processing at Intellect Design Arena (2.3M+ transactions/day, 67% faster)</li>
    <li><strong>Skills:</strong> Python, PyTorch, TensorFlow, SQL, distributed systems, ML pipelines</li>
</ul>

<p>I am eager to contribute to your research. I have attached my CV for your review.</p>

<p>Thank you for considering my application.</p>

<p>Sincerely,<br><br>
<strong>Anamay Tripathy</strong><br>
B.Tech Data Science Engineering<br>
MIT Manipal, India<br>
<a href="mailto:tripathy.anamay23@gmail.com">tripathy.anamay23@gmail.com</a><br>
<a href="https://anamay.vercel.app">anamay.vercel.app</a><br>
+91-9877454747</p>
"""
    
    subject = f"Research Inquiry - {papers[0]['title'][:60]}"
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
        
        print(f"  ✅ Sent!")
        return True
        
    except Exception as e:
        print(f"  ❌ Send error: {e}")
        return False

def main():
    print("\n🦙 OLLAMA AI EMAIL GENERATOR")
    print("=" * 70)
    print("Using local Llama 3 model (100% free)")
    print("=" * 70)
    
    # Check Ollama
    try:
        requests.get("http://localhost:11434", timeout=2)
    except:
        print("\n❌ Ollama is not running!")
        print("   Install: https://ollama.com/download")
        print("   Start: ollama serve")
        print("   Pull model: ollama pull llama3")
        return
    
    # Get professor
    conn = sqlite3.connect('data/clean_40k_professors.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, affiliation FROM verified_contacts LIMIT 1")
    prof = cursor.fetchone()
    conn.close()
    
    if not prof:
        print("No professors found!")
        return
    
    name, email, affiliation = prof
    university = affiliation if affiliation else email.split('@')[1]
    
    print(f"\n📧 Target: {name}")
    print(f"   Email: {email}")
    print(f"   University: {university}")
    
    # Fetch research
    print(f"\n📚 Fetching papers...")
    papers = fetch_papers(name)
    
    if not papers:
        print("\n⚠️ No papers found. Using generic research area for demo...")
        # Create dummy paper for demo
        papers = [{
            'title': f'Research in Computer Systems at {university.split()[0]}',
            'year': '2024',
            'abstract': 'Systems research',
            'citations': 0
        }]
    else:
        print(f"\n📄 Found {len(papers)} papers:")
        for i, p in enumerate(papers, 1):
            print(f"   {i}. {p['title'][:70]}... ({p['year']})")
    
    # Generate
    subject, body = create_ai_email(name, university, papers)
    
    if not subject:
        print("\n❌ AI generation failed")
        return
    
    # Send
    print(f"\n📨 Sending to YOUR inbox for testing...")
    # Send to YOUR email instead of professor's for testing
    test_email = EMAIL  # Send to yourself
    if send_email(test_email, subject, body, name):
        print(f"\n✅ SUCCESS!")
        print(f"\nSubject: {subject}")
        print(f"\nCheck {test_email} for the test email!")

if __name__ == "__main__":
    main()
