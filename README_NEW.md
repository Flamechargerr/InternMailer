# InternMailer - AI-Powered Email Campaign Manager

InternMailer is a sophisticated email campaign management system that leverages AI to help you create, manage, and track email campaigns with ease. The application features a modern, responsive web interface built with Streamlit.

## 🚀 Features

- **User Authentication**: Secure login and user management
- **Campaign Management**: Create, schedule, and track email campaigns
- **Analytics Dashboard**: Monitor campaign performance with detailed metrics
- **AI-Powered**: Leverage AI for email content generation and optimization
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Monitoring**: Track email delivery and engagement in real-time

## 🛠 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Flamechargerr/InternMailer.git
   cd InternMailer
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file in the project root with the following variables:
   ```env
   # App Settings
   DEBUG=True
   SECRET_KEY=your-secret-key
   
   # Email Settings
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   
   # API Settings
   API_BASE_URL=http://localhost:8000
   ```

## 🚦 Running the Application

1. **Start the Streamlit UI**
   ```bash
   streamlit run internmailer_ui/app_new.py
   ```

2. **Access the application**
   Open your browser and navigate to: `http://localhost:8501`

## 📂 Project Structure

```
internmailer_ui/
├── app_new.py           # Main application entry point
├── components/          # Reusable UI components
│   └── ui_utils.py      # UI utility functions
├── pages/               # Application pages
│   ├── home_new.py      # Dashboard/home page
│   ├── login.py         # User authentication
│   ├── analytics.py     # Analytics dashboard
│   ├── campaign_builder.py  # Campaign creation
│   └── settings.py      # Application settings
└── services/            # Business logic and API clients
    ├── config_service.py    # Configuration management
    ├── state_service.py     # Application state management
    ├── campaign_service.py  # Campaign operations
    ├── email_service.py     # Email sending
    └── analytics_service.py # Analytics processing
```

## 🤝 Contributing

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature`
3. Make your changes and commit: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

For questions or support, please contact: support@internmailer.com
