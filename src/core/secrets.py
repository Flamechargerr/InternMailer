"""Secure secrets management."""
import os
from pathlib import Path
from typing import Optional

class Secrets:
    @staticmethod
    def get(key: str, default: Optional[str] = None) -> Optional[str]:
        return os.getenv(key, default)
    
    @staticmethod
    def require(key: str) -> str:
        val = os.getenv(key)
        if not val:
            raise ValueError(f"Required environment variable {key} not set")
        return val
    
    @staticmethod
    def load_env(path: str = ".env"):
        try:
            from dotenv import load_dotenv
            load_dotenv(path)
        except ImportError:
            pass
    
    @staticmethod
    def mask(value: str, visible: int = 4) -> str:
        if len(value) <= visible * 2:
            return "*" * len(value)
        return value[:visible] + "*" * (len(value) - visible * 2) + value[-visible:]
