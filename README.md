# 🚀 InternMailer

**AI-Powered Academic Outreach Platform**

InternMailer is an intelligent email automation tool designed to help students connect with professors worldwide for research internships. It leverages AI to generate personalized emails, making academic outreach more effective and efficient.

## ✨ Features

- 🤖 **AI-Powered Email Generation**: Uses Ollama/Gemma3 for intelligent, personalized emails
- 📄 **Smart Resume Parsing**: Automatically extracts skills, projects, and experience
- 🎯 **Targeted Outreach**: Filter professors by country, research area, and interests  
- 📊 **Progress Tracking**: Real-time analytics and email delivery status
- 🔒 **Secure & Private**: Uses Gmail SMTP with app passwords
- ⚡ **Rate Limited**: Respects email provider limits and best practices
- 📈 **Template Fallback**: Works even without AI models

## 🚀 Quick Start

### 1. Automatic Setup (Recommended)

```bash
git clone https://github.com/your-username/internmailing.git
cd internmailing
python setup.py
```

The setup script will:
- Install all dependencies
- Configure your Gmail credentials
- Create necessary directories
- Check for required data files
- Verify Ollama installation (optional)

### 2. Manual Setup

#### Prerequisites
- Python 3.8+
- Gmail account with App Passwords enabled
- (Optional) Ollama with Gemma3 model

#### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/internmailing.git
   cd internmailing
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Gmail**
   
   Create a `.env` file in the project root:
   ```env
   GMAIL_USER=your-email@gmail.com
   GMAIL_APP_PASSWORD=your-app-password-here
   ```
   
   **How to get Gmail App Password:**
   - Go to [Google Account Settings](https://myaccount.google.com/apppasswords)
   - Security → App passwords
   - Generate password for "Mail"
   - Use this password (NOT your regular Gmail password)

4. **Prepare Data**
   - Ensure `InternMailer/data/proffesor.csv` contains professor data
   - Upload your resume PDF to the `resumes/` directory

5. **Run the Application**
   ```bash
   cd InternMailer
   streamlit run app.py --server.port=8505
   ```
   
   Or simply double-click `launch.bat` (Windows) or run `./launch.ps1`

## 🎯 Usage Guide

### Step-by-Step Workflow

1. **Upload Resume** 📄
   - Upload your PDF resume
   - The system automatically extracts skills, projects, and experience

2. **Configure Campaign** ⚙️
   - Select target countries (optional)
   - Choose internship season (Winter/Summer/Any)
   - Set funding preference (Paid/Unpaid/Any)

3. **Preview Emails** 👀
   - Generate a sample email to see the output
   - Verify personalization and formatting

4. **Launch Outreach** 🚀
   - Choose between Smart Match or Cold Outreach
   - Monitor real-time progress and logs
   - Track sent emails and delivery status

5. **Monitor Results** 📊
   - View analytics dashboard
   - Check email logs for delivery status
   - Track response rates and follow-ups

### Email Generation Modes

- **AI Mode (Recommended)**: Uses Ollama/Gemma3 for highly personalized emails
- **Template Mode**: Uses Jinja2 templates for consistent, professional emails
- **Hybrid Mode**: AI generation with template fallback

## 🔧 Configuration

### Environment Variables

```env
# Required: Gmail Configuration
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password

# Optional: AI Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:latest

# Optional: Rate Limiting
EMAIL_RATE_LIMIT=50
MIN_DELAY_SECONDS=2

# Optional: Testing
TEST_MODE=false
```

### Data Files Structure

```
InternMailer/data/
├── proffesor.csv          # Professor database
└── list.csv               # Alternative professor list

resumes/
└── your-resume.pdf        # Your resume files

logs/
├── email_log.csv          # Email delivery logs
└── error.log              # Application errors
```

### Professor CSV Format

Your `proffesor.csv` should have these columns:
```csv
University,Name,Email,Homepage,Research Area
MIT,Dr. John Smith,jsmith@mit.edu,https://example.com,Machine Learning
```

## 🤖 AI Setup (Optional but Recommended)

For AI-powered email generation:

1. **Install Ollama**
   - Visit [ollama.ai](https://ollama.ai) and install
   - Or use: `curl -fsSL https://ollama.ai/install.sh | sh`

2. **Download Gemma3 Model**
   ```bash
   ollama pull gemma3
   ```

3. **Start Ollama Server**
   ```bash
   ollama serve
   ```

4. **Verify Installation**
   - The app will show "✅ Ollama server detected!" when running

## 📊 Features Deep Dive

### Smart Resume Parsing
- Extracts skills, projects, experience, and education
- Supports multiple parsing providers (AI + rule-based)
- Fallback mechanisms for robust parsing

### Intelligent Email Generation
- Matches student skills with professor research areas
- Personalizes content based on university and research focus
- Maintains professional tone while being conversational

### Safe Email Delivery
- Rate limiting to respect Gmail limits
- Retry logic with exponential backoff
- Comprehensive error logging and tracking
- Email validation and filtering

### Progress Monitoring
- Real-time delivery status
- Analytics dashboard with key metrics
- Detailed logs for troubleshooting
- Follow-up scheduling

## 🛠️ Troubleshooting

### Common Issues

**1. Gmail Authentication Error**
```
Solution: Ensure you're using an App Password, not your regular Gmail password
Generate at: https://myaccount.google.com/apppasswords
```

**2. Ollama Connection Failed**
```
Solution: Check if Ollama is running
Run: ollama serve
Verify: curl http://localhost:11434
```

**3. No Professors Found**
```
Solution: Check your CSV file format and location
Ensure file is at: InternMailer/data/proffesor.csv
Verify email addresses are valid
```

**4. Resume Parsing Failed**
```
Solution: Check PDF format and file permissions
Try with a different PDF file
Check logs for specific error messages
```

### Debug Mode

Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
streamlit run app.py
```

### Log Files

Check these files for troubleshooting:
- `email_log.csv` - Email delivery status
- `logs/error.log` - Application errors
- Streamlit console output

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Submit a pull request with a clear description

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimers

- **Responsible Use**: Use this tool responsibly and respect email recipients
- **Rate Limits**: Follow Gmail's sending limits (500 emails/day for regular accounts)
- **Privacy**: Your data stays local; no information is sent to external services
- **Academic Purpose**: Intended for legitimate academic research inquiries

## 🆘 Support

- 📧 **Email**: support@internmailer.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-username/internmailing/issues)
- 📖 **Documentation**: Check the `/docs` folder for detailed guides
- 💬 **Discussions**: [GitHub Discussions](https://github.com/your-username/internmailing/discussions)

## 🙏 Acknowledgments

- Built with ❤️ by Anamay Tripathy
- Powered by Streamlit, Ollama, and open-source libraries
- Inspired by the need for better academic outreach tools

---

**InternMailer** - Making academic connections, one email at a time 🚀
