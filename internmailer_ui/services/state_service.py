"""
State Service for InternMailer UI

Manages application state and persistence.
"""

import streamlit as st
from typing import Any, Dict, Optional, List, Union
import json
import os
from pathlib import Path
from datetime import datetime

class StateService:
    """Manages application state with persistence."""
    
    def __init__(self, persist_path: Optional[str] = None):
        """Initialize the state service.
        
        Args:
            persist_path: Path to persist state (optional)
        """
        self.persist_path = persist_path or str(Path.home() / '.internmailer' / 'state.json')
        self._ensure_persist_dir()
        
        # Initialize session state if not exists
        if 'app_state' not in st.session_state:
            st.session_state.app_state = {}
        
        # Load persisted state if exists
        self._load_persisted_state()
    
    def _ensure_persist_dir(self) -> None:
        """Ensure the persistence directory exists."""
        os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)
    
    def _load_persisted_state(self) -> None:
        """Load state from persistent storage."""
        try:
            if os.path.exists(self.persist_path):
                with open(self.persist_path, 'r') as f:
                    persisted = json.load(f)
                    st.session_state.app_state.update(persisted)
        except Exception as e:
            print(f"Warning: Could not load persisted state: {e}")
    
    def _persist_state(self) -> None:
        """Save state to persistent storage."""
        try:
            with open(self.persist_path, 'w') as f:
                json.dump(st.session_state.app_state, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not persist state: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a state value.
        
        Args:
            key: Dot-notation key (e.g., 'user.preferences.theme')
            default: Default value if key not found
            
        Returns:
            The stored value or default if not found
        """
        keys = key.split('.')
        value = st.session_state.app_state
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any, persist: bool = False) -> None:
        """Set a state value.
        
        Args:
            key: Dot-notation key
            value: Value to store
            persist: Whether to persist to disk
        """
        keys = key.split('.')
        current = st.session_state.app_state
        
        # Navigate to the parent dict
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # Set the value
        current[keys[-1]] = value
        
        # Persist if requested
        if persist:
            self._persist_state()
    
    def update(self, data: Dict[str, Any], persist: bool = False) -> None:
        """Update multiple state values.
        
        Args:
            data: Dictionary of key-value pairs to update
            persist: Whether to persist to disk
        """
        for key, value in data.items():
            self.set(key, value, persist=False)
        
        if persist:
            self._persist_state()
    
    def delete(self, key: str, persist: bool = False) -> None:
        """Delete a state value.
        
        Args:
            key: Dot-notation key to delete
            persist: Whether to persist to disk
        """
        keys = key.split('.')
        current = st.session_state.app_state
        
        try:
            for k in keys[:-1]:
                current = current[k]
            
            if keys[-1] in current:
                del current[keys[-1]]
                
                if persist:
                    self._persist_state()
        except (KeyError, TypeError):
            pass
    
    def clear(self, persist: bool = True) -> None:
        """Clear all state.
        
        Args:
            persist: Whether to persist the cleared state
        """
        st.session_state.app_state = {}
        
        if persist:
            self._persist_state()

# Global instance for easy access
state = StateService()
