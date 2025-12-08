"""
🤖 PURE AI EMAIL GENERATOR - No Templates, Only Real AI
Uses Hugging Face to generate 100% unique content for each professor
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

def fetch_real_papers(professor_name):
    """Fetch actual research papers from Semantic Scholar"""
    try:
        # Search for author
        search_url = f"https://api.semanticscholar.org/graph/v1/author/search?query={quote_plus(professor_name)}"
        resp = requests.get(search_url, timeout=15)
        
        if resp.status_code != 200:
            print(f"    ⚠️ Author search failed: {resp.status_code}")
            return None
        
        data = resp.json()
        if not data.get('data') or len(data['data']) == 0:
            print(f"    ⚠️ No author found")
            return None
        
        author_id = data['data'][0]['authorId']
        print(f"    ✓ Found author ID: {author_id}")
        
        # Get papers
        papers_url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}/papers"
        papers_resp = requests.get(
            papers_url,
            params={'fields': 'title,year,abstract,citationCount', 'limit': 10},
            timeout=15
        )
        
        if papers_resp.status_code != 200:
            print(f"    ⚠️ Papers fetch failed: {papers_resp.status_code}")
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
        
        # Sort by citations and recency
        papers.sort(key=lambda x: (x['year'], x['citations']), reverse=True)
        
        if papers:
            print(f"    ✓ Found {len(papers)} papers, using top 3")
            return papers[:3]
        
        return None
        
    except Exception as e:
        print(f"    ❌ Error fetching papers: {e}")
        return None

def generate_with_huggingface(prompt, temperature=0.8):
    """Force Hugging Face API call - no fallback"""
    api_url = "https://router.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    
    try:
        full_prompt = f"<s>[INST] {prompt} [/INST]"
        
        response = requests.post(
            api_url,
            headers={"Content-Type": "application/json"},
            json={
                "inputs": full_prompt,
                "parameters": {
                    "max_new_tokens": 250,
                    "temperature": temperature,
                    "top_p": 0.95,
                    "do_sample": True,
                    "return_full_text": False,
                    "repetition_penalty": 1.2
                },
                "options": {"wait_for_model": True}
            },
            timeout=45
        )
        
        print(f"    HF API Response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                generated = result[0].get('generated_text', '').strip()
                # Clean up the output
                generated = generated.replace('[/INST]', '').replace('</s>', '').strip()
                
                if len(generated) >= 100:  # Minimum length check
                    print(f"    ✓ Generated {len(generated)} characters")
                    return generated
                else:
                    print(f"    ⚠️ Generated text too short ({len(generated)} chars)")
            else:
                print(f"    ⚠️ Unexpected response format: {result}")
        elif response.status_code == 503:
            print(f"    ⏳ Model loading, waiting 20s...")
            time.sleep(20)
            # Retry once
            return generate_with_huggingface(prompt, temperature)
        else:
            print(f"    ❌ API error: {response.text[:200]}")
        
        return None
        
    except Exception as e:
        print(f"    ❌ HF call failed: {e}")
        return None

def create_ai_email(professor_name, university, papers):
    """Generate email using ONLY AI - no templates"""
    
    if not papers:
        print("  ❌ Cannot generate AI email without research data. Skipping.")
        return None, None
    
    # Prepare paper info for AI
    paper_info = "\\n".join([
        f"- {p['title']} ({p['year']}, {p['citations']} citations)"
        for p in papers[:3]
    ])
    
    print(f"\\n  🤖 Generating AI content...")
    
    # Generate opening paragraph
    opening_prompt = f"""You are writing a professional academic email to Professor {professor_name} at {university}.

Their recent papers:
{paper_info}

Write a compelling 3-sentence opening paragraph for a research internship inquiry email. 
- Introduce yourself as Anamay Tripathy, Data Science student at MIT Manipal
- Show genuine interest in their SPECIFIC research (mention actual paper titles)
- Be professional and enthusiastic

Write ONLY the paragraph, no extra commentary:"""

    opening = generate_with_huggingface(opening_prompt)
    
    if not opening:
        print("  ❌ Failed to generate opening. Aborting.")
        return None, None
    
    time.sleep(2)  # Rate limiting
    
    # Generate research connection
    connection_prompt = f"""You are explaining why Professor {professor_name}'s research interests you.

Their paper: "{papers[0]['title']}"
Abstract: {papers[0].get('abstract', 'No abstract available')[:300]}

Your background: Machine Learning, Data Science, Python/TensorFlow, worked on waste management ML systems (34% efficiency gain), financial data processing

Write 2-3 sentences explaining:
- What specifically interests you about this research
- How it connects to your experience
- Why you could contribute

Be specific and technical. Write ONLY the explanation:"""

    connection = generate_with_huggingface(connection_prompt, temperature=0.7)
    
    if not connection:
        print("  ❌ Failed to generate connection. Aborting.")
        return None, None
    
    # Build email
    email_html = f"""<p>Dear Professor {professor_name},</p>

<p>{opening}</p>

<p>{connection}</p>

<p>My technical background and research experiences include:</p>

<ul>
    <li><strong>Research Leadership:</strong> Technical Head at YaanBarpe (government-incubated startup), leading 12 developers on ML-powered waste management systems with 34% efficiency improvement</li>
    <li><strong>Industry Experience:</strong> Intellect Design Arena internship optimizing high-volume financial processing (2.3M+ daily transactions) using Python and Kafka - 67% processing time reduction</li>
    <li><strong>Technical Stack:</strong> Python, PyTorch, TensorFlow, SQL, distributed systems, ML pipeline deployment</li>
</ul>

<p>I am committed to producing high-quality research and would welcome the opportunity to contribute to your ongoing work. I have attached my CV for your review.</p>

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
        
        print(f"  ✅ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"  ❌ Send failed: {e}")
        return False

def main():
    print("\\n🤖 PURE AI EMAIL GENERATOR (No Templates)")
    print("=" * 70)
    print("This will ONLY send if AI successfully generates content.")
    print("=" * 70)
    
    # Get one professor
    conn = sqlite3.connect('data/clean_40k_professors.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, affiliation FROM verified_contacts LIMIT 1")
    prof = cursor.fetchone()
    conn.close()
    
    if not prof:
        print("No professors found in database!")
        return
    
    name, email, affiliation = prof
    university = affiliation if affiliation else email.split('@')[1]
    
    print(f"\\n📧 Professor: {name}")
    print(f"   Email: {email}")
    print(f"   University: {university}")
    
    # Fetch real research
    print(f"\\n📚 Fetching real research papers...")
    papers = fetch_real_papers(name)
    
    if not papers:
        print("\\n❌ Could not fetch research papers. Cannot generate personalized AI content.")
        print("   Recommendation: Try again later or manually add research data.")
        return
    
    print(f"\\n📄 Top papers:")
    for i, p in enumerate(papers[:3], 1):
        print(f"   {i}. {p['title'][:70]}... ({p['year']}, {p['citations']} cites)")
    
    # Generate AI email
    subject, body = create_ai_email(name, university, papers)
    
    if not subject or not body:
        print("\\n❌ AI generation failed. Email NOT sent.")
        return
    
    # Send
    print(f"\\n📨 Sending AI-generated email...")
    if send_email(email, subject, body, name):
        print(f"\\n" + "=" * 70)
        print("✅ SUCCESS! AI-generated email sent.")
        print(f"Subject: {subject}")
        print(f"\\nCheck your inbox for the personalized email!")
    else:
        print("\\n❌ Failed to send email.")

if __name__ == "__main__":
    main()
