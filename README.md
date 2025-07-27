# 🚀 InternMailer

**AI-Powered Academic Outreach Platform**

## ✨ Features
- 🤖 AI-Powered Email Generation
- 📄 Smart Resume Parsing
- 🎯 Targeted Professor Outreach
- 📊 Progress Tracking
- 🔒 Secure & Private

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Gmail account with App Passwords enabled
- (Optional) Ollama with Gemma3 model

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Flamechargerr/InternMailer.git
   cd InternMailer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Copy `.env.template` to `.env`
   - Update with your Gmail credentials

### Running the Application
1. Start the Streamlit UI:
   ```bash
   cd internmailer_ui
   streamlit run app.py
   ```

2. Access the web interface at `http://localhost:8501`

## 📚 Documentation

### Project Structure
- `internmailer_ui/` - Streamlit web interface
- `InternMailer/` - Core application logic
- `data/` - Data files and configurations
- `templates/` - Email templates

### Configuration
Edit `.env` to configure:
- Email settings
- API keys
- Application preferences

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
