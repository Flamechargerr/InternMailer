# InternMailer

InternMailer is a modular, AI-powered academic outreach tool designed to help students secure research internships by automating personalized outreach emails to professors worldwide. It leverages resume parsing, semantic research matching, and automated email workflows for efficient, targeted outreach.

## Features
- **Resume Parser:** Extracts skills, domains, and experience from PDF resumes.
- **Professor Scraper:** Parses CSRankings CSVs and scrapes professor homepages for research areas and contact info.
- **Semantic Research Matcher:** Uses sentence-transformers to match your profile with professors' research.
- **Email Generator:** Crafts personalized, professional emails (with GPT-4 fallback if available).
- **Gmail Sender:** Authenticates and sends emails with resume attachments, logging status and handling failures.
- **Follow-up Scheduler:** Tracks outreach and schedules follow-ups if no reply.
- **Streamlit UI:** User-friendly interface for uploading resumes, launching outreach, and viewing analytics.

## Folder Structure
```
InternMailer/
├── data/                # CSRankings CSV files
├── resumes/             # Resume PDFs
├── templates/           # Email templates
├── src/
│   ├── resume_parser.py
│   ├── professor_scraper.py
│   ├── semantic_matcher.py
│   ├── email_generator.py
│   ├── gmail_sender.py
│   ├── followup_scheduler.py
│   └── main.py
├── app.py               # Streamlit frontend
├── .env                 # Email credentials and API keys
├── requirements.txt
└── README.md
```

## Setup Instructions
1. **Clone the repository**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Add your resume:** Place your PDF in `resumes/`.
4. **Download CSRankings CSVs:** Place them in `data/`.
5. **Configure secrets:** Create a `.env` file with your Gmail credentials and (optionally) OpenAI API key.
6. **Run the app:**
   ```bash
   streamlit run app.py
   ```

## Security
- All secrets are read from `.env` and masked in logs.
- API calls are secured.

## Testing
- Unit tests are included for core modules.

## License
MIT 