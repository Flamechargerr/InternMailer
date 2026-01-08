"""Environment-based configuration loader."""
import os
from pathlib import Path
from dotenv import load_dotenv

class ConfigLoader:
    def __init__(self, env_file=".env"):
        load_dotenv(env_file)
        self.db_path = os.getenv("DATABASE_PATH", "/tmp/internmailer.db")
        self.gmail_user = os.getenv("GMAIL_USER")
        self.gmail_pass = os.getenv("GMAIL_APP_PASSWORD")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.resume_path = os.getenv("RESUME_PATH")
        
    def validate(self):
        missing = [k for k in ["GMAIL_USER", "GROQ_API_KEY"] if not os.getenv(k)]
        return missing
