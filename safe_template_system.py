"""
InternMailer - SAFE Email Template System
NO FAKE DATA - Only verified, honest content

CRITICAL: This replaces the previous template system that was generating
WRONG research paper attributions and FAKE professor information.
"""

SAFE_RESEARCH_TEMPLATE = """Dear Professor {name},

I hope this email finds you well. My name is Anamay Tripathy, and I am a final-year B.Tech student in Data Science Engineering at MIT Manipal, India. I am writing to express my sincere interest in joining your research group at {university} as a research intern or assistant.

I have been exploring opportunities to work on {research_area} research, and your group's work in this area particularly interests me. I am eager to contribute to meaningful research while developing my skills further.

My academic background and experience:

- Research experience: As Technical Head at YaanBarpe (yaanbarpe.in), a government-incubated startup, I led a team of developers to build an immersive cultural tourism platform for Tulu Nadu, featuring AI-powered voice guides and interactive heritage experiences. I also interned at Intellect Design Arena, where I optimized high-volume financial transaction processing pipelines using Python and Kafka, reducing processing time by 67%.

- Technical proficiency: I have extensive experience with Python, PyTorch, TensorFlow, and SQL. I am comfortable implementing models from scratch, training at scale, and working with large datasets.

- Relevant projects: I have worked on several research-oriented projects involving predictive modeling, time-series analysis, and NLP applications, focusing on building robust, data-driven systems.

I am a quick learner, highly motivated, and committed to producing careful, reproducible research. I would be grateful for the opportunity to discuss how I might contribute to your research group.

I have attached my CV, which includes further details on my coursework, projects, and experience. Thank you very much for your time and consideration.

Sincerely,
Anamay Tripathy
B.Tech Data Science Engineering
MIT Manipal, India
tripathy.anamay23@gmail.com
https://anamay.vercel.app
+91-9877454747
"""

SAFE_CORPORATE_TEMPLATE = """Dear {name},

I hope this email finds you well. My name is Anamay Tripathy, and I am a final-year Data Science Engineering student at MIT Manipal, India. I am writing to express my interest in internship opportunities at {company}.

I am particularly interested in {company}'s work and believe my technical skills would be a valuable addition to your team:

- Leadership experience: As Technical Head at YaanBarpe (government-incubated startup), I led a team of 12 developers building ML-powered systems, achieving 34% improvement in operational efficiency.

- Industry experience: At Intellect Design Arena, I optimized financial transaction processing pipelines using Python and Kafka, reducing processing time by 67%.

- Technical skills: Python, PyTorch, TensorFlow, SQL, with experience in production-grade ML systems and data pipelines.

I have attached my resume for your review. I would welcome the opportunity to discuss how I can contribute to {company}.

Thank you for your time and consideration.

Best regards,
Anamay Tripathy
B.Tech Data Science Engineering
MIT Manipal, India
tripathy.anamay23@gmail.com
+91-9877454747
"""

# Research areas that are SAFE to use (general categories only)
SAFE_RESEARCH_AREAS = {
    # Based on email domain patterns
    'cs.': 'Computer Science',
    'ml.': 'Machine Learning',
    'ai.': 'Artificial Intelligence',
    'stat.': 'Statistics and Data Science',
    'eecs.': 'Electrical Engineering and Computer Science',
    'cse.': 'Computer Science and Engineering',
    'ece.': 'Electrical and Computer Engineering',
    'ds.': 'Data Science',
    
    # Default by department
    'default': 'Computer Science and Machine Learning'
}

def get_safe_research_area(email: str) -> str:
    """
    Get a SAFE, GENERIC research area based on email domain.
    Does NOT make specific claims about papers or research topics.
    """
    email_lower = email.lower()
    
    for pattern, area in SAFE_RESEARCH_AREAS.items():
        if pattern in email_lower:
            return area
    
    # Check common university patterns
    if any(x in email_lower for x in ['harvard', 'mit.edu', 'stanford', 'berkeley', 'cmu.edu', 'caltech']):
        return 'Computer Science and Machine Learning'
    
    if any(x in email_lower for x in ['ox.ac.uk', 'cam.ac.uk', 'imperial', 'ucl.ac.uk']):
        return 'Computer Science'
        
    if any(x in email_lower for x in ['ethz.ch', 'epfl.ch', 'tu-']):
        return 'Computer Science and Engineering'
    
    return SAFE_RESEARCH_AREAS['default']


def get_safe_university(email: str, fallback_affiliation: str = '') -> str:
    """
    Extract university name SAFELY from email or affiliation.
    Does NOT guess or fabricate information.
    """
    domain = email.split('@')[1] if '@' in email else ''
    
    # Known university mappings
    university_map = {
        'harvard.edu': 'Harvard University',
        'stanford.edu': 'Stanford University',
        'mit.edu': 'MIT',
        'berkeley.edu': 'UC Berkeley',
        'caltech.edu': 'Caltech',
        'cmu.edu': 'Carnegie Mellon University',
        'ox.ac.uk': 'University of Oxford',
        'cam.ac.uk': 'University of Cambridge',
        'ethz.ch': 'ETH Zurich',
        'epfl.ch': 'EPFL',
        'princeton.edu': 'Princeton University',
        'yale.edu': 'Yale University',
        'columbia.edu': 'Columbia University',
        'uchicago.edu': 'University of Chicago',
        'cornell.edu': 'Cornell University',
        'washington.edu': 'University of Washington',
        'ucla.edu': 'UCLA',
        'ucsd.edu': 'UC San Diego',
        'gatech.edu': 'Georgia Tech',
        'uiuc.edu': 'University of Illinois',
        'umich.edu': 'University of Michigan',
        'utexas.edu': 'UT Austin',
        'ed.ac.uk': 'University of Edinburgh',
        'imperial.ac.uk': 'Imperial College London',
        'ucl.ac.uk': 'University College London',
        'manchester.ac.uk': 'University of Manchester',
    }
    
    for domain_pattern, university_name in university_map.items():
        if domain_pattern in domain:
            return university_name
    
    # Use affiliation if provided and reasonable
    if fallback_affiliation and len(fallback_affiliation) > 3:
        return fallback_affiliation
    
    # Extract from domain (be careful)
    if '.edu' in domain or '.ac.' in domain:
        # Extract institution part
        parts = domain.split('.')
        for part in parts:
            if len(part) > 3 and part not in ['edu', 'com', 'org', 'net', 'ac', 'uk', 'ch', 'de', 'fr']:
                return f"the university"  # Safe fallback - don't guess
    
    return "your university"  # Safe fallback


def create_safe_academic_email(name: str, email: str, affiliation: str = '') -> tuple:
    """
    Create a SAFE academic email that:
    - Does NOT fabricate research papers
    - Does NOT claim specific research topics unless verified
    - Is honest and professional
    """
    # Clean name
    clean_name = name.strip()
    if not clean_name or clean_name.lower() == 'professor':
        clean_name = "Professor"
    
    # Get safe university
    university = get_safe_university(email, affiliation)
    
    # Get safe research area (generic only)
    research_area = get_safe_research_area(email)
    
    # Generate subject (honest, no fake paper titles)
    subject = f"Research Internship Inquiry – {research_area}"
    
    # Generate body using safe template
    body = SAFE_RESEARCH_TEMPLATE.format(
        name=clean_name,
        university=university,
        research_area=research_area
    )
    
    return subject, body


def create_safe_corporate_email(name: str, email: str, company: str = '') -> tuple:
    """
    Create a SAFE corporate email that:
    - Does NOT fabricate company-specific claims
    - Is honest about skills and experience
    """
    # Clean name
    clean_name = name.strip() or "Hiring Manager"
    
    # Get company from domain if not provided
    if not company:
        domain = email.split('@')[1] if '@' in email else ''
        company = domain.split('.')[0].title() if domain else "your company"
    
    subject = f"Internship Application – Data Science & ML"
    
    body = SAFE_CORPORATE_TEMPLATE.format(
        name=clean_name,
        company=company
    )
    
    return subject, body


# Validation function
def validate_email_content(subject: str, body: str, professor_name: str) -> dict:
    """
    Validate that email content doesn't contain obviously wrong information.
    """
    issues = []
    
    # Check for placeholder text
    if '{' in body or '}' in body:
        issues.append("Contains unformatted placeholders")
    
    # Check for wrong name
    if professor_name and professor_name.lower() not in body.lower():
        issues.append(f"Professor name '{professor_name}' not in body")
    
    # Check for repetition
    if body.count('Computer Science') > 3:
        issues.append("Too much repetition of 'Computer Science'")
    
    # Check for obviously templated phrases
    bad_phrases = [
        'your distinguished research on',
        'your recent work on',  # Without actual paper
        'particularly your paper',  # Without verification
    ]
    
    for phrase in bad_phrases:
        if phrase in body.lower() and 'Machine Learning' in body:
            issues.append(f"Potentially fake: '{phrase}'")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'confidence': 1.0 if len(issues) == 0 else max(0.3, 1.0 - len(issues) * 0.2)
    }


if __name__ == '__main__':
    # Test the safe templates
    print("🧪 Testing SAFE Email Templates\n")
    
    # Test 1: Known professor
    subject, body = create_safe_academic_email(
        name="Yarin Gal",
        email="yarin@cs.ox.ac.uk",
        affiliation="University of Oxford"
    )
    
    print(f"Subject: {subject}")
    print("-" * 50)
    print(body[:500] + "...")
    
    # Validate
    result = validate_email_content(subject, body, "Yarin Gal")
    print(f"\n✅ Validation: {result}")
