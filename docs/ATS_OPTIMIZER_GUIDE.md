# 🎯 ATS Optimizer - User Guide

## Overview

The ATS Optimizer is an AI-powered tool that automatically customizes your LaTeX resume and cover letter based on job descriptions to maximize your ATS (Applicant Tracking System) score.

## Features

- **AI Keyword Extraction**: Analyzes job descriptions to extract relevant keywords
- **Automatic LaTeX Modification**: Updates your resume/cover letter with ATS-optimized content
- **PDF Compilation**: Compiles optimized LaTeX files to PDF (requires LaTeX installation)
- **ATS Score Tracking**: Shows before/after ATS compatibility scores
- **Fallback Mode**: Works without AI APIs using keyword pattern matching

## Installation

### Prerequisites

1. **Python 3.8+** (already included in InternMailer)
2. **LaTeX Distribution** (optional, for PDF compilation):
   - **macOS**: Install [MacTeX](https://www.tug.org/mactex/)
   - **Linux**: `sudo apt-get install texlive-full`
   - **Windows**: Install [MiKTeX](https://miktex.org/)

### Setup

The ATS Optimizer is included in InternMailer. No additional installation needed.

## Usage

### Method 1: Interactive Mode (Recommended)

Paste a job description directly:

```bash
python ats_optimizer.py --interactive
```

Then paste the job description and type `END` on a new line when done.

### Method 2: From File

Save the job description to a file:

```bash
python ats_optimizer.py --job-desc path/to/job_description.txt
```

### Method 3: Demo Mode

Test with a sample job description:

```bash
python ats_optimizer.py
```

### Command Line Options

```bash
python ats_optimizer.py [OPTIONS]

Options:
  -h, --help            Show help message
  -j, --job-desc PATH   Path to job description file
  -o, --output-dir DIR  Output directory (default: optimized_documents)
  -i, --interactive     Interactive mode
  --no-pdf              Skip PDF compilation
```

## Output

The optimizer creates an `optimized_documents/` directory containing:

1. **`resume_<company>.tex`** - Optimized LaTeX resume
2. **`cover_letter_<company>.tex`** - Optimized LaTeX cover letter
3. **`resume_<company>.pdf`** - Compiled resume (if LaTeX installed)
4. **`cover_letter_<company>.pdf`** - Compiled cover letter (if LaTeX installed)
5. **`optimization_report.md`** - Detailed report with keywords and scores

## How It Works

### 1. Job Description Analysis

The optimizer extracts:
- Company name
- Position title
- Required skills
- Preferred skills
- Tools & technologies
- Soft skills
- Industry keywords

### 2. Resume Optimization

Updates these sections with job-specific keywords:
- **Summary**: Highlights relevant skills
- **Coursework**: Adds relevant courses
- **Experience**: Emphasizes matching technologies
- **Projects**: Showcases relevant work
- **Skills**: Prioritizes job-required technologies

### 3. Cover Letter Optimization

Generates customized:
- Opening paragraph mentioning company and position
- Body paragraphs highlighting relevant experience
- Closing with company-specific motivation

### 4. ATS Scoring

Calculates compatibility score (0-100) based on:
- Keyword match percentage
- Industry terminology presence
- Required skills coverage

## AI Provider Configuration

The optimizer uses AI for better keyword extraction. Configure these environment variables in your `.env` file:

```bash
# Primary: Groq (fast, free tier)
GROQ_API_KEY=your_groq_key

# Fallback: OpenRouter (free models available)
OPENROUTER_API_KEY=your_openrouter_key

# Fallback: GitHub Models
GITHUB_TOKEN=your_github_token
```

**Without AI APIs**: The tool falls back to pattern matching (less accurate but still functional).

## Example Workflow

1. **Find a job posting** you're interested in

2. **Copy the job description** to a file:
   ```bash
   echo "Job description text..." > job.txt
   ```

3. **Run the optimizer**:
   ```bash
   python ats_optimizer.py --job-desc job.txt
   ```

4. **Review the output**:
   - Check `optimization_report.md` for keyword analysis
   - Review the `.tex` files for accuracy
   - Make manual adjustments if needed

5. **Compile to PDF** (if not auto-compiled):
   ```bash
   cd optimized_documents
   xelatex resume_company.tex
   xelatex cover_letter_company.tex
   ```

6. **Use for application**:
   - Attach the optimized PDF resume
   - Use the cover letter PDF or copy text to email

## Tips for Best Results

1. **Review Before Sending**: Always review AI-generated content for accuracy
2. **Customize Further**: Add specific achievements related to the role
3. **Be Honest**: Only include keywords for skills you actually have
4. **Research Company**: Add company-specific alignment statements
5. **Keep Originals**: The optimizer creates new files, preserving your originals

## Troubleshooting

### "No AI provider available"
- The tool will use fallback keyword extraction
- Set up GROQ_API_KEY or OPENROUTER_API_KEY for better results

### "Could not compile LaTeX to PDF"
- Install a LaTeX distribution (MacTeX, MiKTeX, or TeX Live)
- Or use the `.tex` files with Overleaf or another LaTeX editor

### Low ATS Score After Optimization
- The job may require skills you haven't listed
- Manually add relevant projects or coursework
- Consider learning the missing skills

## Integration with Email System

To automatically attach optimized resumes to emails:

1. Run the optimizer before sending emails
2. The optimized files are saved in `optimized_documents/`
3. Reference these files when configuring email attachments

## Sample Output

```
============================================================
🎯 ATS OPTIMIZER
============================================================

📋 Step 1: Analyzing job description...
   Company: Google
   Position: Data Science Intern
   Keywords found: 24

📊 Step 2: Calculating ATS scores...
   Baseline ATS score: 45/100

📝 Step 3: Optimizing resume...
   ✅ Resume saved: optimized_documents/resume_google.tex

📄 Step 4: Optimizing cover letter...
   ✅ Cover letter saved: optimized_documents/cover_letter_google.tex
   Optimized ATS score: 78/100
   📈 Improvement: +33 points

📑 Step 5: Compiling PDFs...
   ✅ Compiled PDF: optimized_documents/resume_google.pdf
   ✅ Compiled PDF: optimized_documents/cover_letter_google.pdf
   📊 Report saved: optimized_documents/optimization_report.md

============================================================
✅ OPTIMIZATION COMPLETE
============================================================
```

## Customization

### Modifying Templates

Edit the templates in `templates/ats/`:
- `resume_template.tex` - Resume structure
- `cover_letter_template.tex` - Cover letter structure

### Adding Your Experience

Update these methods in `ats_optimizer.py`:
- `_generate_experience()` - Your work experience
- `_generate_projects()` - Your projects
- `_generate_skills()` - Your skills

## Support

For issues or questions:
1. Check the optimization report for details
2. Review the generated `.tex` files
3. Ensure your LaTeX templates are valid
4. Verify AI API keys are set correctly
