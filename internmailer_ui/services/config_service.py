"""Configuration service for managing app settings and environment variables."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any

class ConfigService:
    """Manages application configuration with file and environment overrides."""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigService, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Load config with defaults and overrides."""
        self._config = {
            'app': {'name': 'InternMailer', 'version': '1.0.0', 'debug': False},
            'api': {'base_url': 'http://localhost:8000', 'timeout': 30},
            'email': {'smtp_server': 'smtp.gmail.com', 'smtp_port': 587}
        }
        
        # Load from config file if exists
        config_path = Path('config.yaml')
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f) or {}
                    self._deep_update(self._config, file_config)
            except Exception:
                pass
        
        # Apply environment variables
        self._load_env_vars()
    
    def _load_env_vars(self):
        """Update config from environment variables."""
        if os.getenv('DEBUG'):
            self._config['app']['debug'] = os.getenv('DEBUG').lower() in ('true', '1', 't')
        if os.getenv('API_BASE_URL'):
            self._config['api']['base_url'] = os.getenv('API_BASE_URL')
    
    def _deep_update(self, original: Dict, update: Dict):
        """Recursively update dictionary."""
        for k, v in update.items():
            if isinstance(v, dict) and k in original and isinstance(original[k], dict):
                self._deep_update(original[k], v)
            else:
                original[k] = v
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot notation."""
        keys = key.split('.')
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

def get_config() -> ConfigService:
    """Get the configuration service instance."""
    return ConfigService()
