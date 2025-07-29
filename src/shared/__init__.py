"""
Shared module for InternMailer application
Contains centralized configuration, UI components, and managers
"""

from .config_manager import config_manager
from .professor_manager import professor_manager
from .ui_components import ui_components

__all__ = ['config_manager', 'professor_manager', 'ui_components']
