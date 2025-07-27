# InternMailer UI

[![CI](https://github.com/internmailer/internmailer-ui/workflows/CI/badge.svg)](https://github.com/internmailer/internmailer-ui/actions)
[![codecov](https://codecov.io/gh/internmailer/internmailer-ui/branch/main/graph/badge.svg)](https://codecov.io/gh/internmailer/internmailer-ui)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/dependency%20management-poetry-blue.svg)](https://python-poetry.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern, responsive web interface for the InternMailer email management system, built with Streamlit.

## 🚀 Features

- **📧 Campaign Management**: Create, edit, and manage email campaigns with an intuitive interface
- **📊 Analytics Dashboard**: Real-time analytics and reporting with interactive charts
- **👥 Contact Management**: Import, organize, and segment your email contacts
- **🎨 Custom Theming**: Modern UI with customizable themes and responsive design
- **🔐 Secure Authentication**: Built-in user management and secure API integration
- **📱 Mobile Responsive**: Works seamlessly across desktop, tablet, and mobile devices

## 📋 Prerequisites

- Python 3.9 or higher
- Poetry (recommended) or pip for dependency management
- Access to InternMailer API backend

## 🛠️ Installation

### Using Poetry (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/internmailer/internmailer-ui.git
   cd internmailer-ui
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Activate the virtual environment**
   ```bash
   poetry shell
   ```

### Using pip

1. **Clone the repository**
   ```bash
   git clone https://github.com/internmailer/internmailer-ui.git
   cd internmailer-ui
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Quick Start

1. **Configure API settings**
   
   Create a `.streamlit/secrets.toml` file:
   ```toml
   api_url = "http://localhost:8000"
   api_key = "your-api-key-here"
   ```

2. **Run the application**
   ```bash
   streamlit run app.py
   ```

3. **Open in browser**
   
   Navigate to `http://localhost:8501` to access the application.

## 📁 Project Structure

```
internmailer_ui/
├── 📄 app.py                  # Main application entry point
├── 📁 pages/                  # Streamlit page modules
│   ├── 🏠 home.py            # Dashboard/home page
│   ├── 📊 analytics.py       # Analytics and reporting
│   └── ⚙️ settings.py        # Application settings
├── 📁 components/             # Reusable UI components
│   ├── 📊 charts.py          # Chart components
│   ├── 📝 forms.py           # Form components
│   └── 🧩 widgets.py         # Custom widgets
├── 📁 services/               # Business logic and API integration
│   ├── 📧 email_service.py   # Email campaign operations
│   ├── 👤 user_service.py    # User management
│   └── 📈 analytics_service.py # Analytics data processing
├── 📁 assets/                 # Static assets (images, CSS, etc.)
├── 📁 .streamlit/             # Streamlit configuration
│   └── config.toml           # App theming and settings
├── 📁 .github/                # GitHub Actions workflows
│   └── workflows/
│       └── ci.yml            # Continuous integration
├── 📄 requirements.txt        # Python dependencies (pip)
├── 📄 pyproject.toml         # Poetry configuration
└── 📄 README.md              # This file
```

## ⚙️ Configuration

### Environment Variables

Configure the application using environment variables or Streamlit secrets:

```bash
# API Configuration
INTERNMAILER_API_URL=http://localhost:8000
INTERNMAILER_API_KEY=your-api-key

# Database (if applicable)
DATABASE_URL=postgresql://user:pass@localhost/internmailer

# Security
SECRET_KEY=your-secret-key
```

### Streamlit Configuration

Customize the application appearance and behavior by editing `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

## 🧪 Development

### Running Tests

```bash
# Using Poetry
poetry run pytest

# Using pip
pytest
```

### Code Formatting

```bash
# Format code with Black
poetry run black .

# Sort imports with isort
poetry run isort .

# Type checking with mypy
poetry run mypy .

# Linting with flake8
poetry run flake8 .
```

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
poetry run pre-commit install
```

## 📊 Available Pages

### 🏠 Dashboard
- Overview of key metrics and KPIs
- Recent campaign activity
- Quick action buttons for common tasks

### 📊 Analytics
- Campaign performance metrics
- Interactive charts and visualizations
- Engagement trends and insights
- Exportable reports

### ⚙️ Settings
- API configuration
- User preferences
- Theme customization
- Notification settings

## 🔧 API Integration

The application integrates with the InternMailer API backend. Ensure your API server is running and accessible.

### API Endpoints Used

- `GET /campaigns` - Retrieve email campaigns
- `POST /campaigns` - Create new campaigns
- `GET /analytics/metrics` - Get performance metrics
- `GET /users/{id}/contacts` - Retrieve user contacts
- `POST /auth/login` - User authentication

## 🐳 Docker Deployment

Build and run using Docker:

```bash
# Build the image
docker build -t internmailer-ui .

# Run the container
docker run -p 8501:8501 internmailer-ui
```

## 🚀 Production Deployment

### Using Streamlit Cloud

1. Push your code to a GitHub repository
2. Connect your repository to [Streamlit Cloud](https://streamlit.io/cloud)
3. Configure your secrets in the Streamlit Cloud dashboard
4. Deploy with one click

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read our [Contributing Guidelines](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md).

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) for the amazing web framework
- [Plotly](https://plotly.com/) for interactive visualizations
- [Poetry](https://python-poetry.org/) for dependency management
- The open-source community for inspiration and contributions

## 📞 Support

- 📧 Email: support@internmailer.com
- 🐛 Issues: [GitHub Issues](https://github.com/internmailer/internmailer-ui/issues)
- 📖 Documentation: [Project Wiki](https://github.com/internmailer/internmailer-ui/wiki)
- 💬 Discussions: [GitHub Discussions](https://github.com/internmailer/internmailer-ui/discussions)

---

Made with ❤️ by the InternMailer Team
