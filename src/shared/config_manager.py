"""
Centralized Configuration Management
Handles all configuration validation and setup for the InternMailer application
"""

import os
import streamlit as st
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

class ConfigManager:
    """Centralized configuration management"""
    
    def __init__(self):
        self.config = self._load_config()
        self.issues = self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        return {
            'gmail_user': os.getenv('GMAIL_USER'),
            'gmail_password': os.getenv('GMAIL_APP_PASSWORD'),
            'azure_api_key': os.getenv('AZURE_OPENAI_API_KEY'),
            'azure_endpoint': os.getenv('AZURE_OPENAI_ENDPOINT'),
            'professor_csv_path': self._find_professor_csv(),
            'resume_dir': 'resumes',
            'data_dir': 'data'
        }
    
    def _find_professor_csv(self) -> str:
        """Find professor CSV file in various possible locations"""
        possible_paths = [
            'data/proffesor.csv',
            '../data/proffesor.csv',
            'InternMailer/data/proffesor.csv',
            os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'proffesor.csv'),
            'professors_final.csv'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    
    def _validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check Gmail credentials
        if not self.config['gmail_user']:
            issues.append("GMAIL_USER environment variable not set")
        if not self.config['gmail_password']:
            issues.append("GMAIL_APP_PASSWORD environment variable not set")
        
        # Check professor data
        if not self.config['professor_csv_path']:
            issues.append("Professor CSV file not found. Expected locations: data/proffesor.csv, professors_final.csv")
        
        # Ensure resume directory exists
        if not os.path.exists(self.config['resume_dir']):
            os.makedirs(self.config['resume_dir'], exist_ok=True)
        
        # Ensure data directory exists
        if not os.path.exists(self.config['data_dir']):
            os.makedirs(self.config['data_dir'], exist_ok=True)
        
        return issues
    
    def is_valid(self) -> bool:
        """Check if configuration is valid"""
        return len(self.issues) == 0
    
    def get_config(self, key: str) -> Any:
        """Get configuration value by key"""
        return self.config.get(key)
    
    def get_issues(self) -> List[str]:
        """Get list of configuration issues"""
        return self.issues
    
    def show_status_sidebar(self):
        """Show configuration status in Streamlit sidebar"""
        if self.is_valid():
            st.sidebar.success("✅ Configuration OK")
        else:
            st.sidebar.error("⚠️ Configuration Issues")
            for issue in self.issues:
                st.sidebar.warning(f"• {issue}")
            
            with st.sidebar.expander("Setup Instructions"):
                st.markdown("""
                **Required Setup:**
                1. Create a `.env` file in the project root
                2. Add your Gmail credentials:
                   ```
                   GMAIL_USER=your-email@gmail.com
                   GMAIL_APP_PASSWORD=your-app-password
                   ```
                3. Generate Gmail App Password:
                   - Go to Google Account settings
                   - Security → App passwords
                   - Generate password for "Mail"
                4. Ensure professor CSV exists in data/ folder
                """)

# Global config instance
config_manager = ConfigManager()
