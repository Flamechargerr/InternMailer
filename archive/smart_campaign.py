"""
🎯 SMART CAMPAIGN - No Duplicates, Europe First, Enhanced Quality
Tracks sent emails, prioritizes European professors, uses detailed AI prompts
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
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from datetime import datetime

EMAIL = 'tripathy.anamay23@gmail.com'
PASSWORD = 'xctf elgn llfo aohf'
OLLAMA_API = "http://localhost:11434/api/generate"
SENT_LOG = "data/sent_emails.log"

# Thread-safe counters
sent_count = 0
failed_count = 0
skipped_count = 0
counter_lock = Lock()

# European universities (QS Top 200)
EUROPEAN_UNIS = [
    'oxford', 'cambridge', 'imperial', 'eth', 'ucl', 'edinburgh', 'manchester',
    'kings college', 'lse', 'warwick', 'bristol', 'glasgow', 'southampton',
    'epfl', 'tu munich', 'lmu munich', 'heidelberg', 'tu berlin', 'karolinska',
    'tu delft', 'amsterdam', 'utrecht', 'leiden', 'wageningen',
    'sorbonne', 'psl', 'polytechnique', 'sciences po',
    'barcelona', 'madrid', 'autonoma', 'pompeu fabra',
    'sapienza', 'bologna', 'milan', 'padua',
    'kth', 'lund', 'uppsala', 'chalmers',
    'copenhagen', 'oslo', 'helsinki', 'aalto',
    'trinity', 'dublin', 'zurich', 'bern', 'geneva',
    'louvain', 'ghent', 'brussels'
]

def is_european(affiliation, email):
    """Check if professor is from European university"""
    if not affiliation:
        affiliation = email.split('@')[1] if '@' in email else ''
    
    affiliation_lower = affiliation.lower()
    
    # Check against European university list
    for uni in EUROPEAN_UNIS:
        if uni in affiliation_lower:
            return True
    
    # Check domain endings
    european_domains = ['.uk', '.de', '.fr', '.nl', '.se', '.no', '.dk', 
                       '.fi', '.ch', '.at', '.be', '.ie', '.it', '.es', '.pt']
    for domain in european_domains:
        if domain in email.lower():
            return True
    
    return False

def load_sent_emails():
    """Load list of already sent emails"""
    if not os.path.exists(SENT_LOG):
        return set()
    
    with open(SENT_LOG, 'r') as f:
        return set(line.strip() for line in f if line.strip())

def log_sent_email(email):
    """Log an email as sent"""
    with open(SENT_LOG, 'a') as f:
        f.write(f"{email}\n")

def fetch_papers(professor_name):
    """Fetch papers from Semantic Scholar"""
    try:
        search_url = f"https://api.semanticscholar.org/graph/v1/author/search?query={quote_plus(professor_name)}"
        resp = requests.get(search_url, timeout=15)
        
        if resp.status_code != 200:
            return None
        
        data = resp.json()
        if not data.get('data'):
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
    except:
        return None

def generate_with_ollama(prompt):
    """Generate with Ollama"""
    try:
        response = requests.post(
            OLLAMA_API,
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 300}
            },
            timeout=180
        )
        
        if response.status_code == 200:
            result = response.json()
            text = result.get('response', '').strip()
            
            # Clean meta-commentary
            for phrase in ['Here is a possible', 'Here is the', 'Here is my', 'Dear Professor']:
                if phrase in text:
                    text = text[text.index(phrase) + len(phrase):].strip()
            
            text = text.replace('\n\n\n', '\n\n').strip()
            
            if len(text) > 50:
                return text
        
        return None
    except:
        return None

def create_enhanced_email(name, university, papers):
    """Generate enhanced detailed email"""
    
    if not papers:
        papers = [{'title': 'Computer Science Research', 'year': '2024', 'abstract': '', 'citations': 0}]
    
    paper_list = "\n".join([f"- {p['title']} ({p['year']})" for p in papers[:2]])
    
    # ENHANCED Opening (3-4 sentences)
    opening_prompt = f"""You are writing a professional academic email to Professor {name} at {university}.

Their recent papers:
{paper_list}

Write a compelling 3-4 sentence opening paragraph for a research internship inquiry. You are Anamay Tripathy, a final-year Data Science Engineering student at MIT Manipal.

Requirements:
- Start with "I am writing to express my strong interest..."
- Reference their SPECIFIC paper title and year
- Mention a specific aspect (methodology, findings, or impact)
- Show genuine enthusiasm and intellectual curiosity
- Use sophisticated academic language
- NO meta-commentary

Write ONLY the paragraph:"""

    opening = generate_with_ollama(opening_prompt)
    if not opening:
        opening = f"I am writing to express my strong interest in joining your research group at {university}. I have been following your work with great interest, particularly your {papers[0]['year']} research on {papers[0]['title'][:80]}, which presents innovative approaches to addressing fundamental challenges in the field."
    
    # ENHANCED Connection (3-4 sentences)
    connection_prompt = f"""Explain why you are drawn to this research and how you could contribute.

Paper: "{papers[0]['title']}" ({papers[0]['year']})
Abstract: {papers[0].get('abstract', 'Advanced research in computer science')[:300]}

Your background:
- Technical Head at YaanBarpe: Led 12 developers building ML waste management (34% efficiency gain)
- Intellect Design Arena: Optimized financial processing (2.3M+ transactions/day, 67% faster)
- Skills: Python, PyTorch, TensorFlow, SQL, distributed systems

Write 3-4 detailed sentences:
1. What specifically interests you (be technical)
2. How it connects to your YaanBarpe/Intellect experience
3. What unique skills you bring
4. A specific research direction you could explore

Be substantive and technical. Use sophisticated language.

Write ONLY the explanation:"""

    connection = generate_with_ollama(connection_prompt)
    if not connection:
        connection = f"Your work on {papers[0]['title'][:100]} addresses critical challenges that resonate with my experience in building scalable ML systems. My background in optimizing large-scale data processing at Intellect Design Arena has prepared me to contribute meaningfully to this research direction."
    
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

def send_email(to_email, subject, body_html):
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
        
        return True
    except:
        return False

def process_professor(prof_data, index, total, sent_emails):
    """Process one professor"""
    global sent_count, failed_count, skipped_count
    
    name, email, affiliation = prof_data
    
    # Check if already sent
    if email in sent_emails:
        with counter_lock:
            skipped_count += 1
        print(f"[{index}/{total}] {name} - ⏭️  SKIPPED (already sent)")
        return False
    
    university = affiliation if affiliation else email.split('@')[1]
    
    print(f"\n[{index}/{total}] {name} ({'EU' if is_european(affiliation, email) else 'Other'})")
    
    # Fetch papers
    print(f"  📚 Fetching papers...")
    papers = fetch_papers(name)
    
    if papers:
        print(f"  ✓ Found {len(papers)} papers")
    else:
        print(f"  ⚠️ No papers, using generic")
    
    # Generate
    print(f"  🤖 Generating enhanced AI content...")
    subject, body = create_enhanced_email(name, university, papers)
    
    # Send
    print(f"  📨 Sending...")
    success = send_email(email, subject, body)
    
    with counter_lock:
        if success:
            sent_count += 1
            log_sent_email(email)
            print(f"  ✅ Sent!")
        else:
            failed_count += 1
            print(f"  ❌ Failed")
    
    time.sleep(5)
    return success

def main():
    print("\n🎯 SMART CAMPAIGN - Europe First, No Duplicates")
    print("=" * 70)
    
    # Load sent emails
    sent_emails = load_sent_emails()
    print(f"📋 Already sent to: {len(sent_emails)} professors")
    
    # Get all professors
    conn = sqlite3.connect('data/clean_40k_professors.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, affiliation FROM verified_contacts")
    all_professors = cursor.fetchall()
    conn.close()
    
    # Separate European and others
    european = [p for p in all_professors if is_european(p[2], p[1]) and p[1] not in sent_emails]
    others = [p for p in all_professors if not is_european(p[2], p[1]) and p[1] not in sent_emails]
    
    print(f"🇪🇺 European professors: {len(european)} (not yet sent)")
    print(f"🌍 Other professors: {len(others)} (not yet sent)")
    
    # Prioritize European
    professors = european + others
    
    limit = input(f"\nHow many to send? (max {len(professors)}): ").strip()
    limit = int(limit) if limit.isdigit() else len(professors)
    
    professors = professors[:limit]
    
    print(f"\n✅ Will send to {len(professors)} professors")
    print(f"   European: {sum(1 for p in professors if is_european(p[2], p[1]))}")
    print(f"   Other: {sum(1 for p in professors if not is_european(p[2], p[1]))}")
    print(f"\n⏱️  Estimated: ~{len(professors) * 0.5:.0f} minutes")
    print("\nStarting in 5 seconds...")
    time.sleep(5)
    
    start_time = time.time()
    
    # Process with parallelism
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for i, prof in enumerate(professors, 1):
            future = executor.submit(process_professor, prof, i, len(professors), sent_emails)
            futures.append(future)
            time.sleep(2)
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"  ❌ Error: {e}")
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 70)
    print(f"🎉 CAMPAIGN COMPLETE!")
    print(f"✅ Sent: {sent_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"⏭️  Skipped (duplicates): {skipped_count}")
    print(f"⏱️  Time: {elapsed/60:.1f} minutes")
    print(f"📈 Success: {sent_count/(sent_count+failed_count)*100:.1f}%")

if __name__ == "__main__":
    main()
