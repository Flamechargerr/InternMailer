"""
✉️ Cover Letter Agent - Personalized Cover Letter Generation
============================================================
Generates tailored cover letters for each job application.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.agents.base_agent import BaseAgent, AgentContext, AgentResponse
from utils.config import config


# Cover letter templates for different scenarios
TEMPLATES = {
    "standard": {
        "opening": "I am writing to express my strong interest in the {role} position at {company}.",
        "hook_options": [
            "Your company's work on {focus} particularly excites me.",
            "I was drawn to {company} because of {reason}.",
            "The opportunity to contribute to {company}'s {focus} aligns perfectly with my goals.",
        ],
    },
    "referral": {
        "opening": "I was referred to this opportunity by {referrer} and am excited to apply for the {role} position at {company}.",
    },
    "passion": {
        "opening": "As someone passionate about {focus}, I am thrilled to apply for the {role} position at {company}.",
    },
}


class CoverLetterAgent(BaseAgent):
    """
    Specialized agent for generating cover letters.
    
    Capabilities:
    - AI-powered personalization
    - Multiple template styles
    - Company research integration
    - LaTeX PDF generation
    - Tone and length customization
    """
    
    def __init__(self):
        super().__init__("CoverLetter")
        self.output_dir = Path("optimized_documents")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def run(self, context: AgentContext, **kwargs) -> AgentResponse:
        """
        Generate a cover letter for a job.
        
        Kwargs:
            job: Job dict with title, company, description
            template: Template style ('standard', 'passion', 'referral')
            referrer: Name of referrer if template='referral'
            generate_pdf: Whether to generate PDF
            tone: 'formal', 'friendly', 'enthusiastic'
        """
        job = kwargs.get("job")
        template = kwargs.get("template", "standard")
        referrer = kwargs.get("referrer")
        generate_pdf = kwargs.get("generate_pdf", True)
        tone = kwargs.get("tone", "professional")
        
        if not job:
            return AgentResponse(
                success=False,
                agent_name=self.name,
                action_taken="generate_cover_letter",
                message="No job provided",
            )
        
        profile = context.profile
        
        # Generate cover letter
        cover_letter = self._generate_cover_letter(
            profile=profile,
            job=job,
            template=template,
            referrer=referrer,
            tone=tone,
        )
        
        # Generate PDF if requested
        pdf_path = None
        if generate_pdf:
            pdf_path = self._generate_pdf(cover_letter, job, profile)
        
        return AgentResponse(
            success=True,
            agent_name=self.name,
            action_taken="generate_cover_letter",
            result={
                "cover_letter": cover_letter,
                "pdf_path": str(pdf_path) if pdf_path else None,
            },
            message=f"Generated cover letter for {job.get('company', 'company')}",
            data={
                "company": job.get("company"),
                "role": job.get("title"),
                "word_count": len(cover_letter.split()),
            },
        )
    
    def _generate_cover_letter(
        self,
        profile: Dict,
        job: Dict,
        template: str,
        referrer: Optional[str],
        tone: str,
    ) -> str:
        """Generate the cover letter content."""
        company = job.get("company", "your company")
        role = job.get("title", "the position")
        description = job.get("description", "")
        
        # Try AI generation first
        if self.ai_provider:
            return self._ai_generate(profile, job, template, referrer, tone)
        
        # Fallback to template-based generation
        return self._template_generate(profile, job, template, referrer)
    
    def _ai_generate(
        self,
        profile: Dict,
        job: Dict,
        template: str,
        referrer: Optional[str],
        tone: str,
    ) -> str:
        """Generate cover letter using AI."""
        company = job.get("company", "the company")
        role = job.get("title", "the position")
        description = job.get("description", "")[:2000]
        
        # Build profile context
        name = profile.get("name", "Candidate")
        skills = profile.get("skills", [])
        if isinstance(skills, dict):
            skills = [s for cat in skills.values() for s in (cat if isinstance(cat, list) else [])]
        skills_str = ", ".join(skills[:10])
        
        experience = profile.get("experience_highlights", [])
        exp_str = "; ".join(experience[:3])
        
        projects = profile.get("project_highlights", [])
        proj_str = "; ".join(projects[:2])
        
        referral_note = f"I was referred by {referrer}. " if referrer else ""
        
        tone_instructions = {
            "formal": "Use formal, professional language.",
            "friendly": "Use a warm, approachable tone while remaining professional.",
            "enthusiastic": "Show genuine excitement and energy while staying professional.",
            "professional": "Use clear, professional language.",
        }
        
        prompt = f"""Write a compelling cover letter for the following job application.

CANDIDATE:
Name: {name}
Key Skills: {skills_str}
Experience Highlights: {exp_str}
Project Highlights: {proj_str}

JOB:
Company: {company}
Role: {role}
Description: {description}

REQUIREMENTS:
- {tone_instructions.get(tone, tone_instructions['professional'])}
- {referral_note}Keep it to 3-4 paragraphs
- Highlight 2-3 specific achievements that match the job
- Show genuine interest in the company
- End with a clear call to action
- Do NOT make up achievements - only use what's in the profile
- Be specific, not generic

Write the cover letter now (just the body, no header/signature):"""

        try:
            result = self.call_ai(prompt)
            return result.strip()
        except Exception as e:
            self.log("ai_generate", "error", f"AI generation failed: {e}")
            return self._template_generate(profile, job, template, referrer)
    
    def _template_generate(
        self,
        profile: Dict,
        job: Dict,
        template: str,
        referrer: Optional[str],
    ) -> str:
        """Generate cover letter using templates."""
        company = job.get("company", "your company")
        role = job.get("title", "the position")
        
        name = profile.get("name", "Candidate")
        skills = profile.get("skills", [])
        if isinstance(skills, dict):
            skills = [s for cat in skills.values() for s in (cat if isinstance(cat, list) else [])]
        
        experience = profile.get("experience_highlights", [])
        
        # Opening paragraph
        if template == "referral" and referrer:
            opening = TEMPLATES["referral"]["opening"].format(
                referrer=referrer, role=role, company=company
            )
        elif template == "passion":
            focus = skills[0] if skills else "technology"
            opening = TEMPLATES["passion"]["opening"].format(
                focus=focus, role=role, company=company
            )
        else:
            opening = TEMPLATES["standard"]["opening"].format(role=role, company=company)
        
        # Body paragraphs
        body1 = f"With my background in {', '.join(skills[:3]) if skills else 'software development'}, " \
                f"I am confident in my ability to contribute effectively to your team."
        
        if experience:
            body2 = f"In my recent experience, I have: {experience[0]}"
            if len(experience) > 1:
                body2 += f" Additionally, {experience[1]}"
        else:
            body2 = "I am eager to bring my skills and enthusiasm to this role."
        
        # Closing
        closing = f"I would welcome the opportunity to discuss how my background aligns with " \
                  f"{company}'s needs. Thank you for considering my application."
        
        return f"{opening}\n\n{body1}\n\n{body2}\n\n{closing}"
    
    def _generate_pdf(self, content: str, job: Dict, profile: Dict) -> Optional[Path]:
        """Generate PDF version of cover letter."""
        try:
            company = job.get("company", "company").replace(" ", "_")
            timestamp = datetime.now().strftime("%Y%m%d")
            output_name = f"cover_letter_{company}_{timestamp}"
            output_path = self.output_dir / f"{output_name}.pdf"
            
            # Create LaTeX content
            latex_content = self._create_latex(content, job, profile)
            
            # Write LaTeX file
            tex_path = self.output_dir / f"{output_name}.tex"
            tex_path.write_text(latex_content)
            
            # Compile to PDF
            try:
                subprocess.run(
                    ["pdflatex", "-output-directory", str(self.output_dir), str(tex_path)],
                    capture_output=True,
                    timeout=30,
                    check=True,
                )
                
                if output_path.exists():
                    # Cleanup aux files
                    for ext in [".aux", ".log", ".out"]:
                        aux_file = self.output_dir / f"{output_name}{ext}"
                        if aux_file.exists():
                            aux_file.unlink()
                    
                    return output_path
            except subprocess.SubprocessError as e:
                self.log("generate_pdf", "warning", f"LaTeX compilation failed: {e}")
            
        except Exception as e:
            self.log("generate_pdf", "error", f"PDF generation failed: {e}")
        
        return None
    
    def _create_latex(self, content: str, job: Dict, profile: Dict) -> str:
        """Create LaTeX content for cover letter."""
        name = profile.get("name", "Your Name")
        email = profile.get("email", "")
        phone = profile.get("phone", "")
        location = profile.get("location", "")
        linkedin = profile.get("linkedin", "")
        
        company = job.get("company", "Company")
        role = job.get("title", "Position")
        
        # Escape LaTeX special characters
        def escape_latex(text):
            chars = {
                '&': r'\&',
                '%': r'\%',
                '$': r'\$',
                '#': r'\#',
                '_': r'\_',
                '{': r'\{',
                '}': r'\}',
                '~': r'\textasciitilde{}',
                '^': r'\^{}',
            }
            for char, replacement in chars.items():
                text = text.replace(char, replacement)
            return text
        
        content_escaped = escape_latex(content)
        paragraphs = content_escaped.split('\n\n')
        body_latex = '\n\n'.join([f"\\par {p}" for p in paragraphs if p.strip()])
        
        contact_line = " | ".join([x for x in [email, phone, location] if x])
        
        return f"""\\documentclass[11pt,a4paper]{{article}}
\\usepackage[margin=1in]{{geometry}}
\\usepackage{{hyperref}}
\\usepackage{{parskip}}
\\pagestyle{{empty}}

\\begin{{document}}

\\begin{{center}}
{{\\Large \\textbf{{{escape_latex(name)}}}}}\\\\[4pt]
{escape_latex(contact_line)}
\\end{{center}}

\\vspace{{0.5cm}}

\\today

\\vspace{{0.5cm}}

\\textbf{{{escape_latex(company)}}}\\\\
Re: {escape_latex(role)}

\\vspace{{0.3cm}}

Dear Hiring Manager,

{body_latex}

\\vspace{{0.5cm}}

Sincerely,\\\\
{escape_latex(name)}

\\end{{document}}
"""
    
    def generate_for_jobs(self, context: AgentContext, jobs: List[Dict]) -> List[Dict]:
        """Generate cover letters for multiple jobs."""
        results = []
        
        for job in jobs:
            response = self.execute(context, job=job, generate_pdf=False)
            results.append({
                "company": job.get("company"),
                "role": job.get("title"),
                "success": response.success,
                "word_count": response.data.get("word_count"),
            })
        
        return results
