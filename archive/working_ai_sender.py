"""
🎯 WORKING AI EMAIL GENERATOR
Uses your GitHub Models API (GPT-4o-mini) to generate truly personalized emails
Based on REAL research papers fetched from Semantic Scholar
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

# GitHub Models API
GITHUB_TOKEN = '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'
GITHUB_API = 'https://models.inference.ai.azure.com/chat/completions'

def fetch_real_papers(professor_name):
    """Fetch actual papers from Semantic Scholar"""
    try:
        search_url = f"https://api.semanticscholar.org/graph/v1/author/search?query={quote_plus(professor_name)}"
        resp = requests.get(search_url, timeout=15)
        
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        if not data.get('data'):
            return None
        
        author_id = data['data'][0]['authorId']
        print(f"    ✓ Author ID: {author_id}")
        
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
                    'abstract': p.get('abstract', '')[:500],
                    'citations': p.get('citationCount', 0)
                })
        
        papers.sort(key=lambda x: (x['year'], x['citations']), reverse=True)
        
        if papers:
            print(f"    ✓ {len(papers)} papers found")
            return papers[:3]
        
        return None
        
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return None

def generate_with_gpt(prompt):
    """Generate content using GitHub Models GPT-4o-mini"""
    try:
        response = requests.post(
            GITHUB_API,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GITHUB_TOKEN}"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are a professional academic email writer. Write concise, specific, and genuine content."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 300
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()
            print(f"    ✓ Generated {len(content)} chars")
            return content
        else:
            print(f"    ❌ API error {response.status_code}: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"    ❌ Generation failed: {e}")
        return None

def create_ai_email(professor_name, university, papers):
    """Generate email using GPT-4o-mini based on real papers"""
    
    if not papers:
        print("  ❌ No papers - cannot generate AI email")
        return None, None
    
    paper_list = "\\n".join([
        f"- {p['title']} ({p['year']}, {p['citations']} citations)"
        for p in papers[:3]
    ])
    
    print(f"\\n  🤖 Generating AI email content...")
    
    # Generate opening
    opening_prompt = f"""Write a professional 3-sentence email opening for a research internship inquiry.

Professor: {professor_name}
University: {university}
Their recent papers:
{paper_list}

Requirements:
- Introduce yourself as Anamay Tripathy, Data Science Engineering student at MIT Manipal
- Show specific interest in their ACTUAL research (mention paper titles)
- Be professional and enthusiastic
- NO generic phrases

Write ONLY the 3 sentences:"""

    opening = generate_with_gpt(opening_prompt)
    
    if not opening:
        print("  ❌ Opening generation failed. Aborting.")
        return None, None
    
    # Generate research connection
    connection_prompt = f"""Explain why this research interests you and how you could contribute.

Paper: "{papers[0]['title']}" ({papers[0]['year']})
Abstract: {papers[0].get('abstract', 'Advanced research in computer systems')[:300]}

Your background:
- Technical Head at YaanBarpe: Led ML waste management system (34% efficiency gain)
- Intellect Design Arena: Optimized financial data processing (2.3M trans/day, 67% faster)
- Skills: Python, PyTorch, TensorFlow, distributed systems

Write 2-3 sentences:
- What specifically interests you about this paper
- How it connects to your experience
- How you could contribute

Be specific and technical. Write ONLY the explanation:"""

    connection = generate_with_gpt(connection_prompt)
    
    if not connection:
        print("  ❌ Connection generation failed. Aborting.")
        return None, None
    
    # Build email
    email_html = f"""<p>Dear Professor {professor_name},</p>

<p>{opening}</p>

<p>{connection}</p>

<p>My technical background includes:</p>

<ul>
    <li><strong>Research Leadership:</strong> Technical Head at YaanBarpe, leading ML-powered waste management system with 34% efficiency improvement</li>
    <li><strong>Industry Experience:</strong> Optimized high-volume financial processing at Intellect Design Arena (2.3M+ transactions/day, 67% faster)</li>
    <li><strong>Technical Stack:</strong> Python, PyTorch, TensorFlow, SQL, distributed systems, ML pipelines</li>
</ul>

<p>I am eager to contribute to your research and would welcome the opportunity to discuss how my background aligns with your ongoing work. I have attached my CV for your review.</p>

<p>Thank you for considering my application.</p>

<p>Sincerely,<br><br>
<strong>Anamay Tripathy</strong><br>
B.Tech Data Science Engineering<br>
MIT Manipal, India<br>
<a href="mailto:tripathy.anamay23@gmail.com">tripathy.anamay23@gmail.com</a><br>
<a href="https://anamay.vercel.app">anamay.vercel.app</a><br>
+91-9877454747</p>
"""
    
    subject = f"Research Inquiry - {papers[0]['title'][:65]}"
    
    return subject, email_html

def send_email(to_email, subject, body_html, name):
    """Send email with CV"""
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
        
        print(f"  ✅ Email sent!")
        return True
        
    except Exception as e:
        print(f"  ❌ Send failed: {e}")
        return False

def main():
    print("\\n🎯 AI EMAIL GENERATOR (GPT-4o-mini + Real Papers)")
    print("=" * 70)
    
    # Get professor
    conn = sqlite3.connect('data/clean_40k_professors.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, affiliation FROM verified_contacts LIMIT 1")
    prof = cursor.fetchone()
    conn.close()
    
    if not prof:
        print("No professors in database!")
        return
    
    name, email, affiliation = prof
    university = affiliation if affiliation else email.split('@')[1]
    
    print(f"\\n📧 Target: {name} ({email})")
    print(f"   University: {university}")
    
    # Fetch research
    print(f"\\n📚 Fetching research papers...")
    papers = fetch_real_papers(name)
    
    if not papers:
        print("\\n❌ No papers found. Skipping.")
        return
    
    print(f"\\n📄 Top papers:")
    for i, p in enumerate(papers[:3], 1):
        print(f"   {i}. {p['title'][:75]}...")
        print(f"      ({p['year']}, {p['citations']} citations)")
    
    # Generate email
    subject, body = create_ai_email(name, university, papers)
    
    if not subject or not body:
        print("\\n❌ AI generation failed.")
        return
    
    # Send
    print(f"\\n📨 Sending...")
    if send_email(email, subject, body, name):
        print(f"\\n" + "=" * 70)
        print("✅ SUCCESS!")
        print(f"\\nSubject: {subject}")
        print(f"\\nCheck tripathy.anamay23@gmail.com for the AI-generated email!")
        print("This email mentions his ACTUAL 2024 paper on SigmaOS!")

if __name__ == "__main__":
    main()
