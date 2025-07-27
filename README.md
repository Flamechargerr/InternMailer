# InternMailer Winter '25-'26 MVP

🚀 **A comprehensive academic outreach automation tool that helps students connect with professors for research internships through personalized, AI-generated emails.**

## ✨ Features

- **🔍 Smart Professor Discovery**: Scrapes CSRankings for professors in your field
- **🧠 AI-Powered Email Generation**: Creates personalized emails using HuggingFace API with fallback templates
- **📊 Skill Matching**: Matches your skills with professor research areas
- **📧 Gmail Integration**: Automated email sending with CV attachments
- **📈 Campaign Tracking**: Detailed logs and match scoring
- **⏰ Follow-up Scheduling**: Automatic follow-up reminders
- **🎨 Modern UI**: Beautiful Streamlit interface

## 🛡️ Security Features

- **Pinned Dependencies**: All packages use specific versions to prevent supply chain attacks
- **Environment Variables**: Sensitive data stored securely in `.env` files
- **OAuth Authentication**: Secure Gmail integration using OAuth 2.0
- **Comprehensive .gitignore**: Prevents accidental exposure of sensitive files

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Gmail account with OAuth credentials
- HuggingFace API key (optional - has fallback)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Flamechargerr/InternMailer.git
   cd InternMailer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   ```
   Fill in your credentials:
   - `GMAIL_CLIENT_ID`: Your Gmail OAuth client ID
   - `GMAIL_CLIENT_SECRET`: Your Gmail OAuth client secret
   - `HUGGINGFACE_API_KEY`: Your HuggingFace API key (optional)
   - `YOUR_UNIVERSITY`: Your university name
   - `YOUR_DISCIPLINE`: Your field of study
   - `GRAD_YEAR`: Your graduation year

4. **Run the application**
   ```bash
   streamlit run ui/app_fixed.py
   ```

## 📋 Usage

1. **Configure Campaign**: Select country, number of professors, research domains
2. **Upload CV**: Upload your CV in PDF format
3. **Test Configuration**: Use the "Test Configuration" button to verify setup
4. **Launch Campaign**: Click "Launch Campaign" to start sending personalized emails
5. **Monitor Progress**: Track sent emails and responses in the dashboard

## 🧪 Testing

Run the comprehensive test suite:
```bash
python full_flow_test.py
```

This tests:
- Environment setup
- All imports and dependencies
- Project modules
- Scraper functionality
- Email generation
- Gmail authentication
- Streamlit app

## 📁 Project Structure

```
InternMailer/
├── ui/                     # Streamlit user interface
│   ├── app.py             # Main application
│   └── app_fixed.py       # Fixed version with UI improvements
├── scraper/               # Web scraping modules
│   └── csrankings_scraper.py
├── mailer/                # Email generation and sending
│   ├── generate_emails.py
│   └── send_emails.py
├── utils/                 # Utility modules
│   ├── gmail_auth.py      # Gmail authentication
│   ├── cv_summarizer.py   # CV processing
│   ├── skill_matcher.py   # Skill matching logic
│   └── semantic_scholar.py # Paper fetching
├── templates/             # Email templates
├── data/                  # Professor data storage
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

## 🔧 Configuration

### Gmail OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop application)
5. Add your email as a test user
6. Copy client ID and secret to `.env`

### HuggingFace API (Optional)

1. Sign up at [HuggingFace](https://huggingface.co/)
2. Generate an API token
3. Add to `.env` as `HUGGINGFACE_API_KEY`

*Note: The system works without HuggingFace API using fallback templates*

## 📊 Features in Detail

### Smart Matching Algorithm
- Analyzes professor research areas and recent papers
- Matches with your skills and interests
- Provides match scores to prioritize outreach

### Personalized Email Generation
- Uses professor's recent papers and research focus
- Incorporates your CV highlights
- Maintains professional academic tone
- Includes relevant project connections

### Campaign Management
- Tracks all sent emails with timestamps
- Monitors response rates
- Schedules follow-up reminders
- Provides detailed analytics

## 🛠️ Troubleshooting

### Common Issues

1. **Gmail Authentication Failed**
   - Ensure OAuth credentials are correct
   - Check if Gmail API is enabled
   - Verify test user is added

2. **Scraping Issues**
   - Check internet connection
   - Some universities may block scraping
   - Try different countries/regions

3. **Email Generation Failed**
   - HuggingFace API may be down (fallback will activate)
   - Check API key validity
   - Verify CV upload format

### Getting Help

- Check the test report: `test_report.json`
- Run diagnostic test: `python test_app.py`
- Review logs in the Streamlit interface

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python full_flow_test.py`
5. Submit a pull request

## 📄 License

This project is for educational purposes. Please use responsibly and respect professors' time and university policies.

## 🙏 Acknowledgments

- CSRankings for professor data
- Semantic Scholar for paper information
- HuggingFace for AI models
- Google for Gmail API
- Streamlit for the amazing UI framework

---

**⚠️ Important**: Always follow your university's guidelines and respect professors' preferences regarding unsolicited emails. This tool is designed to facilitate meaningful academic connections, not spam.
