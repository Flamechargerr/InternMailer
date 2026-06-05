#!/usr/bin/env python3
"""
🎯 ATS OPTIMIZER - LaTeX Resume & Cover Letter Customization
============================================================
AI-powered tool to optimize LaTeX resume and cover letter templates
based on job descriptions for maximum ATS compatibility.

Features:
- Extract keywords from job descriptions using AI
- Automatically modify LaTeX templates with relevant keywords
- Compile LaTeX to PDF
- Generate ATS score report

Usage:
    python ats_optimizer.py --job-desc "path/to/job.txt" --output-dir "./optimized"
    python ats_optimizer.py --interactive
"""

import os
import re
import sys
import json
import subprocess
import argparse
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

# Try to import AI provider
try:
    from core.unified_ai_provider import get_unified_ai_provider
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("⚠️ AI provider not available - using fallback keyword extraction")

from utils.profile import get_profile


@dataclass
class ATSOptimizationResult:
    """Result of ATS optimization"""
    resume_path: str
    cover_letter_path: str
    pdf_resume_path: Optional[str]
    pdf_cover_letter_path: Optional[str]
    keywords_found: List[str]
    keywords_added: List[str]
    ats_score_before: int
    ats_score_after: int
    company_name: str
    position_title: str


class ATSOptimizer:
    """
    Optimizes LaTeX resume and cover letter for ATS systems
    based on job description analysis.
    """
    
    # Default LaTeX templates (will be saved if not present)
    DEFAULT_RESUME_TEMPLATE = r'''\documentclass[a4paper,10pt]{article}

% ---------- Packages ----------
\usepackage[margin=0.48in, bottom=0.4in]{geometry}
\usepackage[T1]{fontenc}
\usepackage{mathpazo}
\usepackage{hyperref}
\usepackage{xcolor}
\usepackage{enumitem}
\usepackage{titlesec}

% ---------- Layout Control ----------
\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\linespread{0.96}

\setlist[itemize]{leftmargin=*, itemsep=0.5pt, topsep=0.5pt, parsep=0pt}

% ---------- Section Formatting ----------
\titleformat{\section}
  {\large\bfseries}
  {}
  {0pt}
  {}
  [\vspace{0.2ex}\titlerule\vspace{0.4ex}]

\titlespacing*{\section}{0pt}{0.5ex}{0.4ex}

\hypersetup{
  colorlinks=true,
  urlcolor=blue
}

\begin{document}

% ---------- Header ----------
\begin{flushright}
{\small Last updated: {{DATE}}}
\end{flushright}
\vspace{-20pt}

\begin{center}
{\fontsize{28}{32}\selectfont \textbf{{{NAME}}}}\\[2pt]
{{CONTACT_LINE}}\\[1pt]
{{LINKS_LINE}}
\end{center}
\vspace{-2pt}

% ---------- Summary ----------
\section*{Summary}
{{SUMMARY}}

% ---------- Education ----------
\section*{Education}
{{EDUCATION}}

% ---------- Experience ----------
\section*{Experience}

{{EXPERIENCE}}

% ---------- Projects ----------
\section*{Projects}

{{PROJECTS}}

% ---------- Technical Skills ----------
\section*{Technical Skills}
{{SKILLS}}

% ---------- Achievements & Certifications ----------
\section*{Achievements & Certifications}
\textbf{Competitive Programming}: 150+ LeetCode problems \;|\; \textbf{Certifications}: Machine Learning (Johns Hopkins), IBM Generative AI

\end{document}
'''

    DEFAULT_COVER_LETTER_TEMPLATE = r'''\documentclass[11pt,a4]{article}

\usepackage{geometry}
\geometry{margin=1cm}

\usepackage{fontspec}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{color}
\usepackage{titlesec}
\usepackage{fancyhdr}
\usepackage{ragged2e}

\setmainfont{Arial}
\pagestyle{empty}
\hypersetup{colorlinks=true,urlcolor=blue}

\begin{document}

%---------------------- HEADER ----------------------%
\begin{center}
    \textbf{\Large {{NAME}}} \\[4pt]
    \textit{{{POSITION}}} \\
    {{LOCATION}} \\[4pt]
    {{CONTACT_LINE}} \\[2pt]
    {{LINKS_LINE}}
\end{center}

\vspace{0.2cm}
\hrule
\vspace{0.4cm}

\begin{center}
    {\LARGE \textbf{COVER LETTER}}
\end{center}

\vspace{0.2cm}
\textbf{Date:} \today

\vspace{0.3cm}
\textbf{Dear {{RECIPIENT}},}

\justify

{{OPENING_PARAGRAPH}}

{{BODY_PARAGRAPHS}}

{{CLOSING_PARAGRAPH}}

\vspace{0.5cm}
\textbf{Yours faithfully,} \\[6pt]
{{SIGNATURE_BLOCK}}

\end{document}
'''

    def __init__(self, templates_dir: str = "templates/ats"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        self.resume_template_path = self.templates_dir / "resume_template.tex"
        self.cover_letter_template_path = self.templates_dir / "cover_letter_template.tex"
        
        # Ensure templates exist
        self._ensure_templates_exist()
        
        # Initialize AI provider if available
        self.ai_provider = None
        if AI_AVAILABLE:
            try:
                self.ai_provider = get_unified_ai_provider()
            except Exception as e:
                print(f"⚠️ Could not initialize AI provider: {e}")

        self.profile = get_profile()
    
    def _ensure_templates_exist(self):
        """Create default templates if they don't exist"""
        if not self.resume_template_path.exists():
            self.resume_template_path.write_text(self.DEFAULT_RESUME_TEMPLATE)
            print(f"✅ Created default resume template: {self.resume_template_path}")
        
        if not self.cover_letter_template_path.exists():
            self.cover_letter_template_path.write_text(self.DEFAULT_COVER_LETTER_TEMPLATE)
            print(f"✅ Created default cover letter template: {self.cover_letter_template_path}")
    
    def extract_keywords_with_ai(self, job_description: str) -> Dict:
        """
        Use AI to extract keywords and requirements from job description
        Returns structured data for resume optimization
        """
        if not self.ai_provider:
            return self._extract_keywords_fallback(job_description)
        
        prompt = f'''Analyze this job description and extract key information for resume optimization.

Job Description:
{job_description}

Extract and return ONLY a JSON object with this structure:
{{
    "company_name": "Company Name",
    "position_title": "Job Title",
    "required_skills": ["skill1", "skill2", ...],
    "preferred_skills": ["skill1", "skill2", ...],
    "key_responsibilities": ["responsibility1", ...],
    "industry_keywords": ["keyword1", "keyword2", ...],
    "tools_technologies": ["tool1", "tool2", ...],
    "soft_skills": ["skill1", "skill2", ...],
    "experience_level": "entry/mid/senior",
    "education_requirements": ["requirement1", ...],
    "ats_keywords": ["keyword1", "keyword2", ...]
}}

Focus on ATS-relevant keywords that should appear in the resume.'''
        
        try:
            # Use the AI provider to generate
            response = self._call_ai_for_extraction(prompt)
            
            # Parse JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return self._extract_keywords_fallback(job_description)
        except Exception as e:
            print(f"⚠️ AI extraction failed: {e}")
            return self._extract_keywords_fallback(job_description)
    
    def _call_ai_for_extraction(self, prompt: str) -> str:
        """Call AI provider for keyword extraction"""
        # Try different providers
        providers = ['groq', 'openrouter', 'github']
        
        for provider in providers:
            try:
                if provider == 'groq' and self.ai_provider.provider_status['groq']['available']:
                    return self._call_groq(prompt)
                elif provider == 'openrouter':
                    return self._call_openrouter(prompt)
                elif provider == 'github' and self.ai_provider.provider_status['github']['available']:
                    return self._call_github_models(prompt)
            except Exception as e:
                continue
        
        raise Exception("No AI provider available")
    
    def _call_groq(self, prompt: str) -> str:
        """Call Groq API"""
        import requests
        
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            raise Exception("Groq API key not found")
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 2000
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception(f"Groq API error: {response.status_code}")
    
    def _call_openrouter(self, prompt: str) -> str:
        """Call OpenRouter API"""
        import requests
        
        api_key = os.getenv('OPENROUTER_API_KEY', '')
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/internmailer",
            "X-Title": "InternMailer ATS Optimizer"
        }
        
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={
                "model": "meta-llama/llama-3.1-8b-instruct:free",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 2000
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception(f"OpenRouter API error: {response.status_code}")
    
    def _call_github_models(self, prompt: str) -> str:
        """Call GitHub Models API"""
        import requests
        
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            raise Exception("GitHub token not found")
        
        response = requests.post(
            "https://models.inference.ai.azure.com/chat/completions",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 2000
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception(f"GitHub Models API error: {response.status_code}")
    
    def _extract_keywords_fallback(self, job_description: str) -> Dict:
        """Fallback keyword extraction using regex patterns"""
        text = job_description.lower()
        
        # Common tech skills
        tech_skills = [
            'python', 'sql', 'java', 'javascript', 'react', 'node.js', 'aws', 'azure',
            'gcp', 'docker', 'kubernetes', 'tensorflow', 'pytorch', 'scikit-learn',
            'pandas', 'numpy', 'matplotlib', 'tableau', 'powerbi', 'git', 'jenkins',
            'ci/cd', 'mongodb', 'postgresql', 'mysql', 'redis', 'kafka', 'spark',
            'hadoop', 'airflow', 'dbt', 'snowflake', 'bigquery', 'looker', 'etl',
            'machine learning', 'deep learning', 'nlp', 'computer vision', 'statistics',
            'a/b testing', 'data analysis', 'data visualization', 'cloud computing',
            'microservices', 'rest api', 'graphql', 'fastapi', 'flask', 'django',
            'spring boot', 'angular', 'vue', 'typescript', 'go', 'rust', 'c++', 'c#',
            'scala', 'r', 'sas', 'spss', 'excel', 'vba', 'linux', 'bash', 'powershell'
        ]
        
        found_skills = [skill for skill in tech_skills if skill in text]
        
        # Soft skills
        soft_skills = [
            'communication', 'leadership', 'teamwork', 'problem solving', 'analytical',
            'detail-oriented', 'self-motivated', 'collaboration', 'time management',
            'adaptability', 'creativity', 'critical thinking', 'organization'
        ]
        
        found_soft = [skill for skill in soft_skills if skill in text]
        
        # Experience level
        experience_level = 'entry'
        if 'senior' in text or '5+' in text or '5 years' in text:
            experience_level = 'senior'
        elif 'mid' in text or '2-3' in text or '3 years' in text:
            experience_level = 'mid'
        
        # Extract company name (common patterns)
        company_patterns = [
            r'at\s+([A-Z][A-Za-z0-9\s&]+?)(?:\s+(?:is\s+looking|seeks|hiring)|[\.,;]|$)',
            r'([A-Z][A-Za-z0-9\s&]+?)\s+is\s+(?:looking|seeking|hiring)',
        ]
        
        company_name = "Company"
        for pattern in company_patterns:
            match = re.search(pattern, job_description)
            if match:
                company_name = match.group(1).strip()
                break
        
        # Extract position title
        position_patterns = [
            r'(Data\s+Scientist|Software\s+Engineer|Machine\s+Learning\s+Engineer|Data\s+Analyst|Business\s+Analyst|Product\s+Manager|DevOps\s+Engineer|Full\s+Stack\s+Developer|Backend\s+Engineer|Frontend\s+Engineer)',
            r'(Intern|Internship|Analyst|Engineer|Developer|Manager)',
        ]
        
        position_title = "Position"
        for pattern in position_patterns:
            match = re.search(pattern, job_description, re.IGNORECASE)
            if match:
                position_title = match.group(1).strip()
                break
        
        return {
            "company_name": company_name,
            "position_title": position_title,
            "required_skills": found_skills[:10],
            "preferred_skills": [],
            "key_responsibilities": [],
            "industry_keywords": found_skills[:5],
            "tools_technologies": found_skills[:8],
            "soft_skills": found_soft,
            "experience_level": experience_level,
            "education_requirements": [],
            "ats_keywords": found_skills + found_soft
        }
    
    def calculate_ats_score(self, content: str, keywords: List[str]) -> int:
        """Calculate ATS compatibility score (0-100)"""
        if not keywords:
            return 50
        
        content_lower = content.lower()
        matches = sum(1 for kw in keywords if kw.lower() in content_lower)
        score = int((matches / len(keywords)) * 100)
        return min(score, 100)

    def _latex_escape(self, text: str) -> str:
        """Escape LaTeX special characters."""
        if not text:
            return ""
        replacements = {
            "\\": r"\textbackslash{}",
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\textasciicircum{}",
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text

    def _build_contact_line(self) -> str:
        """Build a LaTeX-ready contact line."""
        parts = []
        location = self.profile.get("location", "")
        email = self.profile.get("email", "")
        phone = self.profile.get("phone", "")
        if location:
            parts.append(self._latex_escape(location))
        if email:
            parts.append(rf"\href{{mailto:{email}}}{{{self._latex_escape(email)}}}")
        if phone:
            parts.append(self._latex_escape(phone))
        return r" \;|\; ".join(parts) if parts else ""

    def _build_links_line(self) -> str:
        """Build a LaTeX-ready links line."""
        parts = []
        linkedin = self.profile.get("linkedin", "")
        github = self.profile.get("github", "")
        portfolio = self.profile.get("portfolio", "")
        if linkedin:
            parts.append(rf"\href{{{linkedin}}}{{LinkedIn}}")
        if github:
            parts.append(rf"\href{{{github}}}{{GitHub}}")
        if portfolio:
            parts.append(rf"\href{{{portfolio}}}{{Portfolio}}")
        return r" \;|\; ".join(parts) if parts else ""

    def _build_signature_block(self) -> str:
        """Build a LaTeX signature block."""
        lines = []
        name = self.profile.get("name", "Your Name")
        lines.append(self._latex_escape(name))
        phone = self.profile.get("phone", "")
        if phone:
            lines.append(self._latex_escape(phone))
        email = self.profile.get("email", "")
        if email:
            lines.append(rf"\href{{mailto:{email}}}{{{self._latex_escape(email)}}}")
        return r" \\ ".join(lines)

    def _build_education_block(self) -> str:
        """Build LaTeX education section from profile."""
        education = self.profile.get("ats", {}).get("education", [])
        if not education:
            return r"\textbf{University Name} \hfill 2020 -- 2024\\\textbf{Degree} \hfill\\Relevant Coursework: {{COURSEWORK}}"

        blocks = []
        for item in education:
            school = self._latex_escape(item.get("school", "University Name"))
            degree = self._latex_escape(item.get("degree", "Degree"))
            dates = self._latex_escape(item.get("dates", ""))
            details = self._latex_escape(item.get("details", ""))
            line1 = rf"\textbf{{{school}}} \hfill {dates}\\"
            line2 = rf"\textbf{{{degree}}} \hfill\\"
            line3 = f"{details}" if details else ""
            block = line1 + line2 + (f"{line3}" if line3 else "")
            blocks.append(block)
        return "\n\n".join(blocks)
    
    def optimize_resume(self, job_data: Dict, output_dir: Path) -> str:
        """
        Optimize resume LaTeX based on job description
        Returns path to optimized file
        """
        # Read template
        template = self.resume_template_path.read_text()
        
        # Get current date
        date_str = datetime.now().strftime("%B %Y")
        
        # Build optimized summary
        summary = self._generate_summary(job_data)
        
        # Build coursework section with relevant keywords
        coursework = self._generate_coursework(job_data)
        
        # Build experience section
        experience = self._generate_experience(job_data)
        
        # Build projects section
        projects = self._generate_projects(job_data)
        
        # Build skills section with job-specific keywords
        skills = self._generate_skills(job_data)

        contact_line = self._build_contact_line()
        links_line = self._build_links_line()
        education_block = self._build_education_block()
        
        # Replace placeholders
        optimized = template
        optimized = optimized.replace("{{DATE}}", date_str)
        optimized = optimized.replace("{{NAME}}", self._latex_escape(self.profile.get("name", "Your Name")))
        optimized = optimized.replace("{{CONTACT_LINE}}", contact_line)
        optimized = optimized.replace("{{LINKS_LINE}}", links_line)
        optimized = optimized.replace("{{SUMMARY}}", summary)
        optimized = optimized.replace("{{COURSEWORK}}", coursework)
        optimized = optimized.replace("{{EXPERIENCE}}", experience)
        optimized = optimized.replace("{{PROJECTS}}", projects)
        optimized = optimized.replace("{{SKILLS}}", skills)
        optimized = optimized.replace("{{EDUCATION}}", education_block)
        
        # Save optimized resume
        output_path = output_dir / f"resume_{job_data['company_name'].lower().replace(' ', '_')}.tex"
        output_path.write_text(optimized)
        
        return str(output_path)
    
    def _generate_summary(self, job_data: Dict) -> str:
        """Generate ATS-optimized summary"""
        position = job_data.get('position_title', 'the position')
        skills = job_data.get('required_skills', [])[:5]
        
        profile_summary = self.profile.get("ats", {}).get("summary", "").strip()
        if profile_summary:
            return profile_summary

        core_skills = ', '.join(skills[:3]) if skills else 'Python, SQL, and automation'
        summary = (
            "Results-driven professional with hands-on experience delivering reliable systems and data workflows. "
            f"Strong foundation in {core_skills} with a focus on measurable impact. "
            "Proficient in building scalable solutions and collaborating across teams to deliver production-ready outcomes."
        )
        return summary
    
    def _generate_coursework(self, job_data: Dict) -> str:
        """Generate relevant coursework section"""
        coursework = self.profile.get("ats", {}).get("coursework", [])
        if coursework:
            if isinstance(coursework, list):
                base_courses = ", ".join([self._latex_escape(c) for c in coursework])
            else:
                base_courses = self._latex_escape(str(coursework))
        else:
            base_courses = "Data Structures \\& Algorithms, Machine Learning, Database Systems"
        
        # Add job-specific courses
        if any(kw in job_data.get('ats_keywords', []) for kw in ['statistics', 'statistical']):
            base_courses += ", Statistical Analysis"
        if any(kw in job_data.get('ats_keywords', []) for kw in ['big data', 'spark', 'hadoop']):
            base_courses += ", Big Data Analytics"
        if any(kw in job_data.get('ats_keywords', []) for kw in ['software engineering', 'agile']):
            base_courses += ", Software Engineering"
        
        base_courses += ", Operating Systems"
        return base_courses
    
    def _generate_experience(self, job_data: Dict) -> str:
        """Generate experience section with job-specific keywords"""
        keywords = job_data.get('ats_keywords', [])
        profile_experience = self.profile.get("ats", {}).get("experience", [])
        if not profile_experience:
            return r'''\textbf{Company Name} -- City, Country \hfill 2022 -- 2023\\
\textit{Role Title}
\begin{itemize}
\item Delivered key features that improved reliability and performance.
\item Collaborated cross-functionally to ship production-ready systems.
\end{itemize}'''

        blocks = []
        for item in profile_experience:
            company = self._latex_escape(item.get("company", "Company Name"))
            location = self._latex_escape(item.get("location", "City, Country"))
            role = self._latex_escape(item.get("role", "Role Title"))
            dates = self._latex_escape(item.get("dates", ""))
            link = item.get("link", "")
            header = rf"\textbf{{{company}}} -- {location} \hfill {dates}\\"
            role_line = rf"\textit{{{role}}}"
            if link:
                role_line += rf" \hfill \href{{{link}}}{{{self._latex_escape(link)}}}"

            bullets = item.get("bullets", []) or []
            bullet_lines = []
            for bullet in bullets:
                bullet_lines.append(rf"\item {self._latex_escape(str(bullet))}")
            if keywords:
                bullet_lines.append(rf"\item Relevant keywords: {self._latex_escape(', '.join(keywords[:5]))}")

            block = "\n".join([
                header,
                role_line,
                r"\begin{itemize}",
                *bullet_lines,
                r"\end{itemize}",
            ])
            blocks.append(block)

        return "\n\n".join(blocks)
    
    def _generate_projects(self, job_data: Dict) -> str:
        """Generate projects section"""
        projects_data = self.profile.get("ats", {}).get("projects", [])
        if not projects_data:
            return r'''\textbf{Project Name} \hfill 2024 \\
\textit{Python, SQL, APIs} \hfill
\href{https://github.com/yourhandle/project}{GitHub}
\begin{itemize}
\item Built a system that automated data processing and improved turnaround time.
\end{itemize}'''

        blocks = []
        for item in projects_data:
            name = self._latex_escape(item.get("name", "Project Name"))
            year = self._latex_escape(item.get("year", ""))
            tech = self._latex_escape(item.get("tech", ""))
            link = item.get("link", "")
            header = rf"\textbf{{{name}}} \hfill {year} \\"
            tech_line = rf"\textit{{{tech}}}"
            if link:
                tech_line += rf" \hfill \href{{{link}}}{{GitHub}}"

            bullets = item.get("bullets", []) or []
            bullet_lines = [rf"\item {self._latex_escape(str(b))}" for b in bullets]
            block = "\n".join([
                header,
                tech_line,
                r"\begin{itemize}",
                *bullet_lines,
                r"\end{itemize}",
            ])
            blocks.append(block)

        return "\n\n".join(blocks)
    
    def _generate_skills(self, job_data: Dict) -> str:
        """Generate skills section with job-specific keywords"""
        required = job_data.get('required_skills', [])
        tools = job_data.get('tools_technologies', [])
        
        # Base skills
        languages = ['Python', 'SQL', 'Java', 'JavaScript']
        data_skills = ['ETL Pipelines', 'Data Modeling', 'Database Design', 'SQL Query Optimization', 'Dashboard Development']
        databases = ['PostgreSQL', 'MongoDB', 'NoSQL']
        tools_frameworks = ['Git', 'GitHub Actions', 'CI/CD', 'Flask', 'Node.js', 'Express', 'React', 'PyTest', 'JUnit', 'Jest']
        ai_ml = ['PyTorch', 'TensorFlow', 'scikit-learn', 'LangChain', 'RAG Systems', 'NLP', 'Deep Learning (CNN, RNN, LSTM)']
        
        # Add job-specific skills
        for skill in required[:5]:
            skill_title = skill.title()
            if skill_title not in languages and skill_title not in data_skills:
                if any(db in skill.lower() for db in ['sql', 'database', 'db']):
                    if skill_title not in databases:
                        databases.append(skill_title)
                elif any(tool in skill.lower() for tool in ['git', 'docker', 'aws', 'azure', 'kubernetes']):
                    if skill_title not in tools_frameworks:
                        tools_frameworks.append(skill_title)
        
        skills_text = f"""\\textbf{{Languages}}: {', '.join(languages)}\\\\
\\textbf{{Data \\& Analytics}}: {', '.join(data_skills)}\\\\
\\textbf{{Databases}}: {', '.join(databases)}\\\\
\\textbf{{Tools \\& Frameworks}}: {', '.join(tools_frameworks)}\\\\
\\textbf{{AI/ML}}: {', '.join(ai_ml)}"""
        
        return skills_text
    
    def optimize_cover_letter(self, job_data: Dict, output_dir: Path) -> str:
        """
        Optimize cover letter LaTeX based on job description
        Returns path to optimized file
        """
        template = self.cover_letter_template_path.read_text()
        
        company = job_data.get('company_name', 'the company')
        position = job_data.get('position_title', 'the position')
        location = job_data.get('location', '')
        
        # Generate content sections
        opening = self._generate_cover_opening(job_data)
        body = self._generate_cover_body(job_data)
        closing = self._generate_cover_closing(job_data)
        
        # Replace placeholders
        optimized = template
        optimized = optimized.replace("{{POSITION}}", position)
        optimized = optimized.replace("{{LOCATION}}", location if location else "")
        optimized = optimized.replace("{{RECIPIENT}}", "Hiring Committee")
        optimized = optimized.replace("{{OPENING_PARAGRAPH}}", opening)
        optimized = optimized.replace("{{BODY_PARAGRAPHS}}", body)
        optimized = optimized.replace("{{CLOSING_PARAGRAPH}}", closing)
        
        # Save optimized cover letter
        output_path = output_dir / f"cover_letter_{company.lower().replace(' ', '_')}.tex"
        output_path.write_text(optimized)
        
        return str(output_path)
    
    def _generate_cover_opening(self, job_data: Dict) -> str:
        """Generate opening paragraph for cover letter"""
        company = job_data.get('company_name', 'your company')
        position = job_data.get('position_title', 'the position')
        
        return f"""I'm Anamay Tripathy, a third-year Data Science Engineering student at Manipal Institute of Technology, writing to apply for the \\textbf{{{position}}} position at \\textbf{{{company}}}.

I am particularly drawn to this role due to its alignment with my skills in data analysis, software engineering, and machine learning. My academic background and practical experience have equipped me with a structured, detail-oriented approach to solving complex problems in data-intensive environments."""
    
    def _generate_cover_body(self, job_data: Dict) -> str:
        """Generate body paragraphs for cover letter"""
        responsibilities = job_data.get('key_responsibilities', [])
        skills = job_data.get('required_skills', [])
        
        body = r"""\begin{enumerate}[leftmargin=*, label=\textbf{\arabic*.}]"""
        
        # Point 1: Technical skills
        body += r"""
    \item \textbf{Technical Proficiency:} At Intellect Design Arena, I built Python and SQL-based workflows to process time-sensitive financial datasets, improving reporting accuracy and reducing turnaround time by over 12 hours per week through workflow optimization."""
        
        # Point 2: Data/Analytics focus
        body += r"""
    \item \textbf{Data Analysis and Insights:} I implemented structured data validation and quality checks that improved data accuracy by 20 percent, helping reduce downstream reconciliation issues and ensure consistent reporting outputs."""
        
        # Point 3: Scale/Performance
        body += r"""
    \item \textbf{Handling Scale and Complexity:} As Technical Head at YaanBarpe, I supported backend systems serving 3,000+ monthly active users, focusing on data consistency, system reliability, and smooth operational execution under load."""
        
        # Point 4: Collaboration
        body += r"""
    \item \textbf{Cross-Functional Collaboration:} Through leadership roles and project work, I have worked closely with technical and non-technical teams to meet deadlines while maintaining process discipline, documentation, and accuracy."""
        
        body += r"""
\end{enumerate}"""
        
        # Add paragraph about specific skills match
        if skills:
            body += f"""

My experience with {', '.join(skills[:3])} directly aligns with the technical requirements of this role. I am eager to contribute my analytical and execution-oriented mindset to your team."""
        
        return body
    
    def _generate_cover_closing(self, job_data: Dict) -> str:
        """Generate closing paragraph for cover letter"""
        company = job_data.get('company_name', 'your company')
        
        return f"""I am motivated by the opportunity to contribute to {company}, where precision, innovation, and operational efficiency are critical. I look forward to learning how large-scale operations are managed while contributing my strong analytical skills.

Please find my r\'esum\'e attached. I would welcome the opportunity to further discuss how my background and approach align with this role."""
    
    def compile_latex(self, tex_path: str) -> Optional[str]:
        """
        Compile LaTeX file to PDF
        Returns path to PDF or None if compilation fails
        """
        tex_file = Path(tex_path)
        if not tex_file.exists():
            print(f"❌ LaTeX file not found: {tex_path}")
            return None
        
        output_dir = tex_file.parent
        
        # Try different LaTeX compilers
        compilers = ['xelatex', 'lualatex', 'pdflatex']
        
        for compiler in compilers:
            try:
                result = subprocess.run(
                    [compiler, '-interaction=nonstopmode', '-output-directory', str(output_dir), str(tex_file)],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=str(output_dir)
                )
                
                if result.returncode == 0:
                    pdf_path = tex_file.with_suffix('.pdf')
                    if pdf_path.exists():
                        print(f"✅ Compiled PDF: {pdf_path}")
                        return str(pdf_path)
                
            except FileNotFoundError:
                continue
            except subprocess.TimeoutExpired:
                print(f"⚠️ {compiler} timed out")
                continue
            except Exception as e:
                print(f"⚠️ {compiler} failed: {e}")
                continue
        
        print("❌ Could not compile LaTeX to PDF. Make sure you have xelatex, lualatex, or pdflatex installed.")
        print("   You can install MacTeX (macOS) or TeX Live (Linux/Windows)")
        return None
    
    def optimize_for_job(self, job_description: str, output_dir: str = "optimized_documents", company_name: Optional[str] = None) -> ATSOptimizationResult:
        """
        Main method to optimize resume and cover letter for a job
        
        Args:
            job_description: Full job description text
            output_dir: Directory to save optimized files
        
        Returns:
            ATSOptimizationResult with paths and scores
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print("=" * 60)
        print("🎯 ATS OPTIMIZER")
        print("=" * 60)
        
        # Step 1: Extract keywords from job description
        print("\n📋 Step 1: Analyzing job description...")
        job_data = self.extract_keywords_with_ai(job_description)
        
        print(f"   Company: {job_data.get('company_name', 'Unknown')}")
        print(f"   Position: {job_data.get('position_title', 'Unknown')}")
        print(f"   Keywords found: {len(job_data.get('ats_keywords', []))}")
        
        # Step 2: Calculate baseline ATS score
        print("\n📊 Step 2: Calculating ATS scores...")
        original_resume = self.resume_template_path.read_text()
        baseline_score = self.calculate_ats_score(original_resume, job_data.get('ats_keywords', []))
        print(f"   Baseline ATS score: {baseline_score}/100")
        
        # Step 3: Optimize resume
        print("\n📝 Step 3: Optimizing resume...")
        resume_path = self.optimize_resume(job_data, output_path)
        print(f"   ✅ Resume saved: {resume_path}")
        
        # Step 4: Optimize cover letter
        print("\n📄 Step 4: Optimizing cover letter...")
        cover_letter_path = self.optimize_cover_letter(job_data, output_path)
        print(f"   ✅ Cover letter saved: {cover_letter_path}")
        
        # Step 5: Calculate new ATS score
        optimized_resume = Path(resume_path).read_text()
        new_score = self.calculate_ats_score(optimized_resume, job_data.get('ats_keywords', []))
        print(f"   Optimized ATS score: {new_score}/100")
        print(f"   📈 Improvement: +{new_score - baseline_score} points")
        
        # Step 6: Compile to PDF
        print("\n📑 Step 5: Compiling PDFs...")
        pdf_resume = self.compile_latex(resume_path)
        pdf_cover = self.compile_latex(cover_letter_path)
        
        # Generate report
        self._generate_report(job_data, baseline_score, new_score, output_path)
        
        print("\n" + "=" * 60)
        print("✅ OPTIMIZATION COMPLETE")
        print("=" * 60)
        print(f"\n📁 Output directory: {output_path}")
        print(f"   Resume: {resume_path}")
        print(f"   Cover Letter: {cover_letter_path}")
        if pdf_resume:
            print(f"   Resume PDF: {pdf_resume}")
        if pdf_cover:
            print(f"   Cover Letter PDF: {pdf_cover}")
        
        if company_name:
            job_data['company_name'] = company_name
        
        return ATSOptimizationResult(
            resume_path=resume_path,
            cover_letter_path=cover_letter_path,
            pdf_resume_path=pdf_resume,
            pdf_cover_letter_path=pdf_cover,
            keywords_found=job_data.get('ats_keywords', []),
            keywords_added=job_data.get('required_skills', []),
            ats_score_before=baseline_score,
            ats_score_after=new_score,
            company_name=job_data.get('company_name', 'Unknown'),
            position_title=job_data.get('position_title', 'Unknown')
        )
    
    def _generate_report(self, job_data: Dict, before_score: int, after_score: int, output_dir: Path):
        """Generate optimization report"""
        report = f"""# ATS Optimization Report

## Job Details
- **Company:** {job_data.get('company_name', 'Unknown')}
- **Position:** {job_data.get('position_title', 'Unknown')}
- **Experience Level:** {job_data.get('experience_level', 'Unknown')}

## ATS Score
- **Before Optimization:** {before_score}/100
- **After Optimization:** {after_score}/100
- **Improvement:** +{after_score - before_score} points

## Keywords Identified ({len(job_data.get('ats_keywords', []))} total)

### Required Skills
{chr(10).join('- ' + skill for skill in job_data.get('required_skills', [])[:15])}

### Tools & Technologies
{chr(10).join('- ' + tool for tool in job_data.get('tools_technologies', [])[:10])}

### Soft Skills
{chr(10).join('- ' + skill for skill in job_data.get('soft_skills', []))}

## Recommendations
1. Review the optimized documents for accuracy
2. Ensure all added keywords reflect your actual experience
3. Tailor the cover letter further if you have specific achievements related to this role
4. Research the company culture and add relevant alignment statements

---
Generated by ATS Optimizer on {datetime.now().strftime("%Y-%m-%d %H:%M")}
"""
        
        report_path = output_dir / "optimization_report.md"
        report_path.write_text(report)
        print(f"   📊 Report saved: {report_path}")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='ATS Optimizer - Optimize LaTeX resume and cover letter for job applications'
    )
    parser.add_argument('--job-desc', '-j', type=str, help='Path to job description file')
    parser.add_argument('--output-dir', '-o', type=str, default='optimized_documents',
                        help='Output directory for optimized files')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Interactive mode - paste job description')
    parser.add_argument('--no-pdf', action='store_true',
                        help='Skip PDF compilation')
    
    args = parser.parse_args()
    
    optimizer = ATSOptimizer()
    
    if args.interactive:
        print("📝 Paste the job description below (press Ctrl+D or type 'END' on a new line when done):\n")
        lines = []
        while True:
            try:
                line = input()
                if line.strip() == 'END':
                    break
                lines.append(line)
            except EOFError:
                break
        job_description = '\n'.join(lines)
    elif args.job_desc:
        job_description = Path(args.job_desc).read_text()
    else:
        # Demo mode with sample job description
        print("📝 No job description provided. Using demo mode with sample job description.")
        job_description = """
        Data Science Intern - Summer 2026
        
        We are looking for a Data Science Intern to join our Analytics team. 
        The ideal candidate will have strong Python and SQL skills, experience with 
        machine learning frameworks like TensorFlow or PyTorch, and knowledge of 
        data visualization tools. You will work on real-world problems involving 
        predictive modeling, statistical analysis, and building data pipelines.
        
        Requirements:
        - Proficiency in Python, SQL, and data analysis libraries (pandas, numpy)
        - Experience with machine learning and statistical modeling
        - Knowledge of cloud platforms (AWS, GCP, or Azure)
        - Strong problem-solving and communication skills
        - Currently pursuing a degree in Data Science, Computer Science, or related field
        """
    
    result = optimizer.optimize_for_job(job_description, args.output_dir)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
