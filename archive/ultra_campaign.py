"""
🌟 ULTRA-DETAILED CAMPAIGN - 2x Quality Improvement
Most detailed, professional academic emails possible
"""

import sys
sys.path.insert(0, '.')
from smart_campaign import *

# Override the create_enhanced_email function with ULTRA-DETAILED version
def create_ultra_detailed_email(name, university, papers):
    """Generate ultra-detailed, highly professional email (2x quality)"""
    
    if not papers:
        papers = [{'title': 'Advanced Computer Science Research', 'year': '2024', 'abstract': '', 'citations': 0}]
    
    paper_list = "\n".join([f"- {p['title']} ({p['year']}, {p['citations']} citations)" for p in papers[:3]])
    
    # ULTRA-DETAILED Opening (4-5 sentences, highly sophisticated)
    opening_prompt = f"""You are writing an exceptionally professional academic research inquiry email to Professor {name}, a distinguished researcher at {university}.

Their notable recent publications:
{paper_list}

Write a compelling, sophisticated 4-5 sentence opening paragraph. You are Anamay Tripathy, a high-achieving final-year Data Science Engineering student at MIT Manipal with strong research credentials.

Requirements:
- Open with "I am writing to express my profound interest in joining your research group..."
- Reference their MOST RECENT paper by exact title and year
- Discuss a specific technical aspect (methodology, algorithmic innovation, empirical findings, or theoretical contribution)
- Explain why this research represents a significant advancement in the field
- Show deep intellectual engagement and scholarly maturity
- Use sophisticated academic vocabulary naturally
- Demonstrate you've actually read and understood their work

Write ONLY the paragraph (4-5 sentences):"""

    opening = generate_with_ollama(opening_prompt)
    if not opening:
        opening = f"I am writing to express my profound interest in joining your research group at {university}. I have been following your distinguished contributions to the field with great admiration, particularly your {papers[0]['year']} research on {papers[0]['title'][:90]}, which presents groundbreaking methodologies for addressing fundamental computational challenges. The rigor and innovation demonstrated in this work exemplify the kind of impactful research I aspire to contribute to."
    
    # ULTRA-DETAILED Connection (4-5 sentences, very specific)
    connection_prompt = f"""Explain in exceptional detail why you are drawn to this specific research and exactly how you could contribute.

Paper: "{papers[0]['title']}" ({papers[0]['year']}, {papers[0]['citations']} citations)
Abstract/Context: {papers[0].get('abstract', 'Cutting-edge research addressing critical challenges in computer science')[:350]}

Your comprehensive background:
- Technical Leadership: Technical Head at YaanBarpe (government-incubated startup), led cross-functional team of 12 developers implementing ML-powered waste management optimization platform, achieving 34% operational efficiency improvement through predictive analytics and real-time data processing
- Industry Research Experience: Software Engineering Intern at Intellect Design Arena, architected and deployed high-throughput financial transaction processing system handling 2.3M+ daily transactions using distributed Python microservices and Apache Kafka, achieving 67% reduction in processing latency
- Technical Expertise: Advanced proficiency in Python ecosystem (PyTorch, TensorFlow, scikit-learn), distributed systems design, SQL database optimization, statistical modeling, algorithmic problem-solving
- Academic Focus: Machine learning theory and applications, large-scale data systems, computational efficiency, real-time analytics
- Research Interests: Intersection of ML and systems optimization, scalable algorithms, production ML deployment

Write 4-5 exceptionally detailed sentences explaining:
1. What SPECIFIC technical aspect of this research fascinates you (be very precise about methodology, algorithms, or findings)
2. Draw a CONCRETE, detailed connection to your YaanBarpe or Intellect Design Arena experience (specific technologies, challenges, solutions)
3. Explain the UNIQUE perspective, skills, or methodological approach you would bring (be specific about what others might not offer)
4. Propose a SPECIFIC research direction, application domain, or extension of their work you could explore together

Be highly substantive, technically precise, and demonstrate deep engagement. Use sophisticated academic language and show you understand both the research and how to extend it.

Write ONLY the 4-5 sentences:"""

    connection = generate_with_ollama(connection_prompt)
    if not connection:
        connection = f"What particularly captivates me about your work on {papers[0]['title'][:100]} is its elegant approach to {papers[0].get('abstract', 'computational optimization')[:50]}. During my tenure at YaanBarpe, where I architected ML systems processing heterogeneous waste management data streams, I encountered similar challenges in balancing accuracy with computational efficiency at scale. This experience, combined with my work at Intellect Design Arena optimizing distributed transaction processing systems for millions of daily operations, has equipped me with practical insights into deploying sophisticated algorithms in production environments with stringent performance requirements. I believe my background in both theoretical machine learning and production-scale system deployment positions me uniquely to contribute to extending your research methodology to real-time, resource-constrained settings, particularly exploring how your approach could enhance efficiency in large-scale data processing pipelines."
    
    email_html = f"""<p>Dear Professor {name},</p>

<p>{opening}</p>

<p>{connection}</p>

<p>My technical background and research experience include:</p>

<ul>
    <li><strong>Research Leadership:</strong> Technical Head at YaanBarpe (government-incubated startup), leading cross-functional team of 12 developers in developing ML-powered waste management platform with 34% operational efficiency improvement through predictive analytics</li>
    <li><strong>Industry Research:</strong> Software Engineering Intern at Intellect Design Arena, architected distributed financial transaction processing system handling 2.3M+ daily transactions, achieving 67% latency reduction using Python microservices and Apache Kafka</li>
    <li><strong>Technical Expertise:</strong> Advanced Python (PyTorch, TensorFlow, scikit-learn), distributed systems architecture, database optimization, statistical modeling, algorithmic design</li>
    <li><strong>Academic Focus:</strong> Machine learning theory, large-scale data systems, computational efficiency, real-time analytics, production ML deployment</li>
</ul>

<p>I am deeply committed to pursuing research excellence and would be honored to contribute to your ongoing work. I have attached my curriculum vitae for your review and would welcome the opportunity to discuss how my background and research interests align with your group's objectives.</p>

<p>Thank you very much for considering my application. I look forward to the possibility of contributing to your distinguished research program.</p>

<p>Sincerely,<br><br>
<strong>Anamay Tripathy</strong><br>
B.Tech Data Science Engineering (Final Year)<br>
Manipal Institute of Technology, India<br>
<a href="mailto:tripathy.anamay23@gmail.com">tripathy.anamay23@gmail.com</a><br>
<a href="https://anamay.vercel.app">anamay.vercel.app</a><br>
+91-9877454747</p>
"""
    
    subject = f"Research Inquiry - {papers[0]['title'][:65]}"
    return subject, email_html

# Monkey-patch the function
import smart_campaign
smart_campaign.create_enhanced_email = create_ultra_detailed_email

if __name__ == "__main__":
    print("\n🌟 ULTRA-DETAILED CAMPAIGN (2x Quality)")
    print("=" * 70)
    print("Sending ONLY 10 emails tonight")
    print("=" * 70)
    
    sent_emails = load_sent_emails()
    
    conn = sqlite3.connect('data/clean_40k_professors.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, affiliation FROM verified_contacts")
    all_professors = cursor.fetchall()
    conn.close()
    
    european = [p for p in all_professors if is_european(p[2], p[1]) and p[1] not in sent_emails]
    
    print(f"\n🇪🇺 European professors available: {len(european)}")
    print("📨 Sending to first 10 with ultra-detailed personalization")
    print("\nStarting in 3 seconds...")
    time.sleep(3)
    
    professors = european[:10]
    
    global sent_count, failed_count, skipped_count
    sent_count = 0
    failed_count = 0
    skipped_count = 0
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        for i, prof in enumerate(professors, 1):
            future = executor.submit(process_professor, prof, i, len(professors), sent_emails)
            futures.append(future)
            time.sleep(3)
        
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"❌ Error: {e}")
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 70)
    print(f"🌙 TONIGHT'S EMAILS COMPLETE!")
    print(f"✅ Sent: {sent_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"⏱️  Time: {elapsed/60:.1f} minutes")
    print(f"\n📅 Remaining: {len(european) - 10} European professors for tomorrow")
    print(f"💾 Progress saved to: data/sent_emails.log")
