"""
InternMailer - Configuration Manager
Load and manage settings from config.yaml
"""

import yaml
import os
from typing import Any, Dict

class ConfigManager:
    """
    Centralized configuration management
    Loads settings from config.yaml with environment variable support
    """
    
    def __init__(self, config_path='config.yaml'):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        if not os.path.exists(self.config_path):
            print(f"⚠️ Config file not found: {self.config_path}")
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Replace environment variable references
            config = self._resolve_env_vars(config)
            return config
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return self._get_default_config()
    
    def _resolve_env_vars(self, config: Any) -> Any:
        """Recursively resolve environment variable references"""
        if isinstance(config, dict):
            return {k: self._resolve_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._resolve_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith('$'):
            # Environment variable reference
            env_var = config[1:]
            return os.getenv(env_var, config)
        return config
    
    def _get_default_config(self) -> Dict:
        """Fallback default configuration"""
        return {
            'email': {'smtp_server': 'smtp.gmail.com', 'smtp_port': 587},
            'campaign': {'daily_limit': 500, 'warmup_enabled': False},
            'logging': {'level': 'INFO', 'format': 'json'}
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        Example: config.get('email.smtp_port') returns 587
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """Set configuration value (runtime only, doesn't save to file)"""
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def reload(self):
        """Reload configuration from file"""
        self.config = self._load_config()

# Singleton instance
_config_instance = None

def get_config():
    """Get singleton config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance

# Example usage
if __name__ == '__main__':
    config = get_config()
    
    print("📝 Configuration Loaded:")
    print(f"Daily Limit: {config.get('campaign.daily_limit')}")
    print(f"SMTP Server: {config.get('email.smtp_server')}")
    print(f"Turbo Mode: {config.get('campaign.turbo_mode')}")
    print(f"Paper-First: {config.get('personalization.paper_first_strategy')}")
