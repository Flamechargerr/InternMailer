"""
AI Resume & CV Tailor
=====================
Reads candidate's resume from PDF, stores structured profile, and generates
tailored resume + cover letter for each job using AI. Optimizes for ATS
compatibility and job-specific keyword matching.
"""

from __future__ import annotations

import json
import re
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.unified_ai_provider import get_unified_ai_provider


try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    import docx
except Exception:
    docx = None


@dataclass
class TailoredDocument:
    job_id: str
    company: str
    position: str
    resume_text: str
    cover_letter: str
    resume_path: str
    cover_letter_path: str
    pdf_resume_path: Optional[str] = None
    pdf_cover_letter_path: Optional[str] = None
    ats_score_before: int = 0
    ats_score_after: int = 0
    keywords_injected: List[str] = field(default_factory=list)
    keywords_matched: List[str] = field(default_factory=list)
    keywords_missing: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CandidateProfile:
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""
    summary: str = ""
    education: List[Dict[str, Any]] = field(default_factory=list)
    experience: List[Dict[str, Any]] = field(default_factory=list)
    projects: List[Dict[str, Any]] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    awards: List[str] = field(default_factory=list)
    raw_text: str = ""


class ResumeTailor:
    """AI-powered resume tailoring engine."""
    
    def __init__(self, resume_path: Optional[str] = None):
        self.ai = get_unified_ai_provider()
        self.resume_path = resume_path or self._find_resume()
        self.profile: Optional[CandidateProfile] = None
        self.output_dir = Path("optimized_documents")
        self.output_dir.mkdir(exist_ok=True)
        
        # Load and parse resume
        if self.resume_path and Path(self.resume_path).exists():
            self.profile = self._parse_resume(self.resume_path)
        else:
            # Try to build from candidate_profile.md
            self.profile = self._build_from_candidate_profile()
    
    def _find_resume(self) -> Optional[str]:
        """Find resume PDF in common locations."""
        search_paths = [
            "resume/Anamay_Tripathy_Resume.pdf",
            "resume/Anamay_Tripathy_Resume_Optimised.pdf",
            "Anamay_Tripathy_Resume_Optimised.pdf",
            "resume.pdf",
            "cv.pdf",
            "optimized_documents/optimized_resume.pdf",
        ]
        for path in search_paths:
            if Path(path).exists():
                return path
        # Search for any PDF in resume/ directory
        resume_dir = Path("resume")
        if resume_dir.exists():
            pdfs = list(resume_dir.glob("*.pdf"))
            if pdfs:
                return str(pdfs[0])
        # Search current directory
        for pdf in Path(".").glob("*.pdf"):
            if "resume" in pdf.name.lower() or "cv" in pdf.name.lower() or "anamay" in pdf.name.lower():
                return str(pdf)
        return None
    
    def _parse_resume(self, path: str) -> CandidateProfile:
        """Parse resume PDF to structured profile."""
        profile = CandidateProfile()
        
        if PdfReader is None:
            return self._build_from_candidate_profile()
        
        try:
            reader = PdfReader(path)
            raw_text = ""
            for page in reader.pages:
                raw_text += page.extract_text() + "\n"
            
            profile.raw_text = raw_text
            
            # Use AI to parse structured data
            parsed = self._ai_parse_resume(raw_text)
            profile.name = parsed.get("name", "")
            profile.email = parsed.get("email", "")
            profile.phone = parsed.get("phone", "")
            profile.location = parsed.get("location", "")
            profile.linkedin = parsed.get("linkedin", "")
            profile.github = parsed.get("github", "")
            profile.portfolio = parsed.get("portfolio", "")
            profile.summary = parsed.get("summary", "")
            profile.education = parsed.get("education", [])
            profile.experience = parsed.get("experience", [])
            profile.projects = parsed.get("projects", [])
            profile.skills = parsed.get("skills", [])
            profile.certifications = parsed.get("certifications", [])
            profile.awards = parsed.get("awards", [])
            
        except Exception as e:
            print(f"⚠️  Error parsing resume PDF: {e}")
            return self._build_from_candidate_profile()
        
        return profile
    
    def _ai_parse_resume(self, raw_text: str) -> Dict[str, Any]:
        """Use AI to parse raw resume text into structured data."""
        system_prompt = (
            "You are a resume parsing expert. Extract structured information from the resume text. "
            "Return ONLY a valid JSON object with these exact keys: "
            "name, email, phone, location, linkedin, github, portfolio, summary, "
            "education (list of {degree, school, dates}), "
            "experience (list of {title, company, dates, highlights}), "
            "projects (list of {name, description, technologies}), "
            "skills (list of strings), certifications (list of strings), awards (list of strings). "
            "Do not add any extra text outside the JSON."
        )
        
        try:
            response = self.ai.complete(
                prompt=f"Parse this resume into structured JSON:\n\n{raw_text[:3000]}",
                system_prompt=system_prompt,
            )
            content = response.content.strip()
            # Extract JSON if wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            parsed = json.loads(content)
            return parsed
        except Exception as e:
            print(f"⚠️  AI resume parsing failed: {e}")
            return {}
    
    def _build_from_candidate_profile(self) -> CandidateProfile:
        """Build profile from candidate_profile.md file."""
        profile = CandidateProfile()
        
        # Try to read candidate_profile.md
        profile_path = Path("candidate_profile.md")
        if not profile_path.exists():
            profile_path = Path("../candidate_profile.md")
        
        if profile_path.exists():
            text = profile_path.read_text()
            profile.raw_text = text
            
            # Extract basic info using regex
            email_match = re.search(r'[\w.-]+@[\w.-]+\.\w+', text)
            if email_match:
                profile.email = email_match.group(0)
            
            phone_match = re.search(r'\+?\d[\d\s-]{7,}\d', text)
            if phone_match:
                profile.phone = phone_match.group(0)
            
            linkedin_match = re.search(r'linkedin\.com/[^\s\)\]]+', text)
            if linkedin_match:
                profile.linkedin = linkedin_match.group(0)
            
            github_match = re.search(r'github\.com/[^\s\)\]]+', text)
            if github_match:
                profile.github = github_match.group(0)
            
            # Extract name from first line
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            if lines:
                first_line = lines[0]
                if "Candidate Profile" in first_line:
                    name_match = re.search(r'Candidate Profile:\s*(.+)', first_line)
                    if name_match:
                        profile.name = name_match.group(1).strip()
            
            # Extract skills section
            skills = []
            skill_keywords = [
                "python", "sql", "machine learning", "data science", "pandas", "numpy",
                "scikit-learn", "tensorflow", "pytorch", "deep learning", "nlp", "llm",
                "rag", "langchain", "faiss", "spark", "etl", "data engineering",
                "statistics", "a/b testing", "feature engineering", "data visualization",
                "git", "docker", "aws", "gcp", "azure", "flask", "fastapi", "rest api",
                "javascript", "react", "node.js", "typescript", "java", "scala",
                "mongodb", "postgresql", "mysql", "redis", "kafka", "airflow",
                "financial modeling", "quantitative analysis", "time series", "risk modeling",
                "react", "node.js", "flask", "html/css", "apache spark", "etl pipelines",
                "data modeling", "sql optimization", "statistical analysis",
                "llm deployment", "fine-tuning", "retrieval-augmented generation",
                "langchain", "faiss", "scikit-learn", "pytorch", "nlp", "feature engineering",
            ]
            for skill in skill_keywords:
                if skill.lower() in text.lower():
                    skills.append(skill)
            profile.skills = list(set(skills))
            
            # Extract experience
            experience = []
            # Look for experience sections
            exp_patterns = re.findall(
                r'\*?\*?([^*\n]+?)\*?\*?\s*[-—]\s*([^\n]+)\n\s*-\s*([^\n]+)',
                text
            )
            for match in exp_patterns:
                experience.append({
                    "title": match[0].strip(),
                    "company": match[1].strip(),
                    "highlights": [match[2].strip()],
                })
            profile.experience = experience
            
            # Extract education
            education = []
            if "manipal institute of technology" in text.lower() or "mit manipal" in text.lower():
                education.append({
                    "degree": "B.Tech, Data Science Engineering",
                    "school": "Manipal Institute of Technology (MIT Manipal)",
                    "dates": "Aug 2023 – Expected May 2027",
                })
            profile.education = education
            
            # Extract projects
            projects = []
            project_patterns = re.findall(r'\*\*([^*]+)\*\*\s*[-—]\s*([^\n]+)', text)
            for name, desc in project_patterns:
                if any(kw in name.lower() for kw in ["rag", "quant", "crime", "med", "edge"]):
                    projects.append({
                        "name": name.strip(),
                        "description": desc.strip(),
                        "technologies": [],
                    })
            profile.projects = projects
        
        return profile
    
    def extract_job_keywords(self, job_description: str) -> Dict[str, List[str]]:
        """Extract key requirements and skills from job description using AI."""
        system_prompt = (
            "You are an ATS expert. Extract key information from this job description. "
            "Return ONLY valid JSON with keys: required_skills (list), preferred_skills (list), "
            "required_experience (list), key_responsibilities (list), company_values (list), "
            "ats_keywords (list of important keywords for ATS matching). "
            "Do not add any extra text."
        )
        
        try:
            response = self.ai.complete(
                prompt=f"Extract ATS keywords from this job description:\n\n{job_description[:4000]}",
                system_prompt=system_prompt,
            )
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            return json.loads(content)
        except Exception:
            # Fallback: extract keywords manually
            text = job_description.lower()
            common_skills = [
                "python", "sql", "r", "machine learning", "deep learning", "data science",
                "statistics", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
                "keras", "nlp", "computer vision", "time series", "forecasting",
                "data engineering", "etl", "spark", "hadoop", "kafka", "airflow",
                "aws", "gcp", "azure", "docker", "kubernetes", "ci/cd", "git",
                "flask", "fastapi", "django", "rest api", "graphql", "react", "vue",
                "javascript", "typescript", "node.js", "java", "scala", "c++", "go",
                "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "snowflake",
                "tableau", "power bi", "looker", "matplotlib", "seaborn", "plotly",
                "ab testing", "experimental design", "hypothesis testing", "regression",
                "classification", "clustering", "dimensionality reduction", "feature engineering",
                "model deployment", "mlops", "vector databases", "llm", "rag", "langchain",
                "openai", "huggingface", "transformers", "bert", "gpt", "llama",
            ]
            found = [skill for skill in common_skills if skill in text]
            return {
                "required_skills": found[:20],
                "preferred_skills": [],
                "required_experience": [],
                "key_responsibilities": [],
                "company_values": [],
                "ats_keywords": found[:30],
            }
    
    def tailor_resume(
        self,
        job_description: str,
        company_name: str,
        position: str,
    ) -> TailoredDocument:
        """Generate a tailored resume for a specific job."""
        if not self.profile:
            raise ValueError("No candidate profile loaded. Cannot tailor resume.")
        
        # Extract job keywords
        job_keywords = self.extract_job_keywords(job_description)
        required_skills = job_keywords.get("required_skills", [])
        ats_keywords = job_keywords.get("ats_keywords", [])
        
        # Calculate ATS scores
        profile_text = self.profile.raw_text.lower()
        all_keywords = list(set(required_skills + ats_keywords))
        matched_before = [kw for kw in all_keywords if kw.lower() in profile_text]
        ats_score_before = int((len(matched_before) / max(len(all_keywords), 1)) * 100)
        
        # Generate tailored resume using AI
        system_prompt = (
            "You are an expert resume writer and ATS optimization specialist. "
            "Rewrite the candidate's resume to be highly tailored for this specific job. "
            "Rules:\n"
            "1. Keep all factual information accurate - DO NOT invent fake experiences\n"
            "2. Emphasize skills and experiences most relevant to the job description\n"
            "3. Use keywords from the job description naturally in the text\n"
            "4. Keep the same basic structure: Summary, Education, Experience, Projects, Skills\n"
            "5. Use strong action verbs and quantify achievements where possible\n"
            "6. Format as clean markdown with clear sections\n"
            "7. Keep to 1 page (concise, impactful bullets)\n"
            "8. Include ALL keywords naturally - this is critical for ATS passing"
        )
        
        prompt = f"""JOB DESCRIPTION:
{job_description[:2000]}

COMPANY: {company_name}
POSITION: {position}

CANDIDATE PROFILE:
{self._format_profile_for_ai()}

REQUIRED KEYWORDS TO INCLUDE: {', '.join(all_keywords[:25])}

Generate a tailored resume that maximizes ATS score while keeping all information factual."""
        
        try:
            response = self.ai.complete(prompt=prompt, system_prompt=system_prompt)
            tailored_resume = response.content.strip()
        except Exception as e:
            print(f"⚠️  AI resume tailoring failed: {e}")
            tailored_resume = self.profile.raw_text
        
        # Calculate new ATS score
        tailored_lower = tailored_resume.lower()
        matched_after = [kw for kw in all_keywords if kw.lower() in tailored_lower]
        ats_score_after = int((len(matched_after) / max(len(all_keywords), 1)) * 100)
        
        # Generate cover letter
        cover_letter = self._generate_cover_letter(job_description, company_name, position, required_skills)
        
        # Save files
        safe_company = re.sub(r'[^\w\-]', '_', company_name)[:30]
        safe_position = re.sub(r'[^\w\-]', '_', position)[:30]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{safe_company}_{safe_position}_{timestamp}"
        
        resume_path = self.output_dir / f"{base_name}_resume.md"
        cover_letter_path = self.output_dir / f"{base_name}_cover_letter.md"
        
        resume_path.write_text(tailored_resume, encoding="utf-8")
        cover_letter_path.write_text(cover_letter, encoding="utf-8")
        
        # Generate PDFs if possible
        pdf_resume_path = self._generate_pdf(tailored_resume, resume_path.with_suffix(".pdf"))
        pdf_cover_letter_path = self._generate_pdf(cover_letter, cover_letter_path.with_suffix(".pdf"))
        
        keywords_injected = [kw for kw in all_keywords if kw.lower() in tailored_lower and kw.lower() not in profile_text]
        keywords_missing = [kw for kw in all_keywords if kw.lower() not in tailored_lower]
        
        return TailoredDocument(
            job_id=base_name,
            company=company_name,
            position=position,
            resume_text=tailored_resume,
            cover_letter=cover_letter,
            resume_path=str(resume_path),
            cover_letter_path=str(cover_letter_path),
            pdf_resume_path=str(pdf_resume_path) if pdf_resume_path else None,
            pdf_cover_letter_path=str(pdf_cover_letter_path) if pdf_cover_letter_path else None,
            ats_score_before=ats_score_before,
            ats_score_after=ats_score_after,
            keywords_injected=keywords_injected[:20],
            keywords_matched=matched_after[:30],
            keywords_missing=keywords_missing[:20],
        )
    
    def _format_profile_for_ai(self) -> str:
        """Format profile for AI prompt."""
        parts = []
        
        if self.profile.name:
            parts.append(f"Name: {self.profile.name}")
        if self.profile.summary:
            parts.append(f"Summary: {self.profile.summary}")
        
        if self.profile.education:
            parts.append("Education:")
            for edu in self.profile.education:
                parts.append(f"  - {edu.get('degree', '')} at {edu.get('school', '')} ({edu.get('dates', '')})")
        
        if self.profile.experience:
            parts.append("Experience:")
            for exp in self.profile.experience:
                parts.append(f"  - {exp.get('title', '')} at {exp.get('company', '')}")
                for hl in exp.get('highlights', []):
                    parts.append(f"    * {hl}")
        
        if self.profile.projects:
            parts.append("Projects:")
            for proj in self.profile.projects:
                parts.append(f"  - {proj.get('name', '')}: {proj.get('description', '')}")
        
        if self.profile.skills:
            parts.append(f"Skills: {', '.join(self.profile.skills[:30])}")
        
        if self.profile.certifications:
            parts.append(f"Certifications: {', '.join(self.profile.certifications)}")
        
        return "\n".join(parts)
    
    def _generate_cover_letter(
        self,
        job_description: str,
        company_name: str,
        position: str,
        required_skills: List[str],
    ) -> str:
        """Generate a tailored cover letter."""
        system_prompt = (
            "You are Anamay Tripathy writing a personalized cover letter. "
            "Write a compelling, concise cover letter (250-350 words) that:\n"
            "1. Shows genuine interest in the company and role\n"
            "2. Connects specific experiences to job requirements\n"
            "3. Demonstrates technical depth without being verbose\n"
            "4. Uses a professional but personable tone\n"
            "5. Ends with a clear call to action\n"
            "6. Do NOT invent fake experiences - use only real background\n"
            "7. Mention specific skills from the job description naturally"
        )
        
        prompt = f"""JOB: {position} at {company_name}

JOB DESCRIPTION:
{job_description[:1500]}

MY BACKGROUND:
{self._format_profile_for_ai()}

KEY SKILLS TO MENTION: {', '.join(required_skills[:10])}

Write a personalized cover letter."""
        
        try:
            response = self.ai.complete(prompt=prompt, system_prompt=system_prompt)
            return response.content.strip()
        except Exception:
            return f"""Dear Hiring Team at {company_name},

I am excited to apply for the {position} position. With a strong background in data science, machine learning, and software engineering, I believe I can make a meaningful contribution to your team.

My experience includes building ML-powered systems, working with large-scale data pipelines, and developing production-ready applications. I am particularly skilled in Python, SQL, machine learning frameworks, and data engineering tools.

I would welcome the opportunity to discuss how my background aligns with this role and learn more about the exciting work at {company_name}.

Best regards,
Anamay Tripathy"""
    
    def _generate_pdf(self, text: str, output_path: Path) -> Optional[Path]:
        """Generate PDF from markdown text."""
        try:
            # Try to use markdown -> PDF conversion
            # First, try reportlab
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                
                doc = SimpleDocTemplate(str(output_path), pagesize=letter,
                                       rightMargin=72, leftMargin=72,
                                       topMargin=72, bottomMargin=18)
                styles = getSampleStyleSheet()
                story = []
                
                # Parse simple markdown
                for line in text.split('\n'):
                    line = line.strip()
                    if not line:
                        story.append(Spacer(1, 6))
                    elif line.startswith('# '):
                        story.append(Paragraph(line[2:], styles['Heading1']))
                    elif line.startswith('## '):
                        story.append(Paragraph(line[3:], styles['Heading2']))
                    elif line.startswith('### '):
                        story.append(Paragraph(line[4:], styles['Heading3']))
                    elif line.startswith('- ') or line.startswith('* '):
                        story.append(Paragraph('• ' + line[2:], styles['BodyText']))
                    else:
                        story.append(Paragraph(line, styles['BodyText']))
                
                doc.build(story)
                return output_path
            except Exception:
                pass
            
            # Fallback: save as HTML and use weasyprint if available
            try:
                import weasyprint
                html = f"<!DOCTYPE html><html><body>{self._markdown_to_html(text)}</body></html>"
                weasyprint.HTML(string=html).write_pdf(str(output_path))
                return output_path
            except Exception:
                pass
            
        except Exception:
            pass
        
        return None
    
    def _markdown_to_html(self, text: str) -> str:
        """Simple markdown to HTML conversion."""
        html = []
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                html.append('<br>')
            elif line.startswith('# '):
                html.append(f'<h1>{line[2:]}</h1>')
            elif line.startswith('## '):
                html.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith('### '):
                html.append(f'<h3>{line[4:]}</h3>')
            elif line.startswith('- ') or line.startswith('* '):
                html.append(f'<li>{line[2:]}</li>')
            else:
                html.append(f'<p>{line}</p>')
        return '\n'.join(html)
    
    def batch_tailor(
        self,
        jobs: List[Dict[str, Any]],
        max_jobs: int = 25,
    ) -> List[TailoredDocument]:
        """Tailor resumes for multiple jobs."""
        results = []
        for i, job in enumerate(jobs[:max_jobs]):
            try:
                print(f"📝 Tailoring resume {i+1}/{min(len(jobs), max_jobs)}: {job.get('company', 'Unknown')} - {job.get('title', 'Unknown')}")
                doc = self.tailor_resume(
                    job_description=job.get("description", ""),
                    company_name=job.get("company", "Unknown"),
                    position=job.get("title", "Unknown"),
                )
                results.append(doc)
                print(f"   ✅ ATS score: {doc.ats_score_before} → {doc.ats_score_after}")
                time.sleep(1)  # Rate limit AI calls
            except Exception as e:
                print(f"   ❌ Failed: {e}")
        
        return results


# ==================== STANDALONE RUNNER ====================

if __name__ == "__main__":
    print("📝 AI Resume Tailor")
    print("=" * 50)
    
    tailor = ResumeTailor()
    
    if tailor.profile:
        print(f"✅ Loaded profile for: {tailor.profile.name or 'Unknown'}")
        print(f"   Skills: {len(tailor.profile.skills)} skills found")
        print(f"   Experience: {len(tailor.profile.experience)} entries")
        
        # Example: tailor for a sample job
        sample_job = """
        Data Science Intern - Summer 2025
        
        We are looking for a passionate Data Science Intern to join our team.
        
        Requirements:
        - Strong Python programming skills
        - Experience with SQL and data manipulation
        - Knowledge of machine learning frameworks (scikit-learn, PyTorch)
        - Familiarity with NLP and LLMs
        - Experience with data visualization tools
        - Currently pursuing a degree in Computer Science, Data Science, or related field
        
        Responsibilities:
        - Build and deploy ML models
        - Work with large datasets and ETL pipelines
        - Collaborate with cross-functional teams
        - Present findings to stakeholders
        """
        
        doc = tailor.tailor_resume(sample_job, "SampleCorp", "Data Science Intern")
        print(f"\n✅ Tailored resume generated!")
        print(f"   ATS Score: {doc.ats_score_before} → {doc.ats_score_after}")
        print(f"   Resume: {doc.resume_path}")
        print(f"   Cover Letter: {doc.cover_letter_path}")
    else:
        print("❌ No profile loaded. Please ensure resume PDF or candidate_profile.md exists.")
