"""
User service for InternMailer UI

Handles user management and authentication.
"""

import requests
import streamlit as st
from typing import Dict, Any, Optional, List


class UserService:
    """Service for managing user operations."""
    
    def __init__(self, api_url: str = "http://localhost:8000", api_key: str = None):
        """
        Initialize the user service.
        
        Args:
            api_url: Base URL for the API
            api_key: API authentication key
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
    
    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user.
        
        Args:
            username: User's username or email
            password: User's password
            
        Returns:
            User data and token if successful, None otherwise
        """
        try:
            response = self.session.post(
                f"{self.api_url}/auth/login",
                json={"username": username, "password": password}
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            st.error(f"Authentication failed: {e}")
            return None
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile information.
        
        Args:
            user_id: ID of the user
            
        Returns:
            User profile data or None if failed
        """
        try:
            response = self.session.get(f"{self.api_url}/users/{user_id}")
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            st.error(f"Failed to fetch user profile: {e}")
            return None
    
    def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """
        Update user profile.
        
        Args:
            user_id: ID of the user
            profile_data: Updated profile data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.put(
                f"{self.api_url}/users/{user_id}",
                json=profile_data
            )
            response.raise_for_status()
            return True
        
        except requests.RequestException as e:
            st.error(f"Failed to update profile: {e}")
            return False
    
    def get_user_contacts(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get user's contacts.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of contacts to return
            
        Returns:
            List of contact dictionaries
        """
        try:
            params = {"limit": limit}
            response = self.session.get(
                f"{self.api_url}/users/{user_id}/contacts",
                params=params
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            st.error(f"Failed to fetch contacts: {e}")
            return []
    
    def add_contact(self, user_id: str, contact_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add a new contact.
        
        Args:
            user_id: ID of the user
            contact_data: Contact information
            
        Returns:
            Created contact data or None if failed
        """
        try:
            response = self.session.post(
                f"{self.api_url}/users/{user_id}/contacts",
                json=contact_data
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            st.error(f"Failed to add contact: {e}")
            return None
    
    def import_contacts(self, user_id: str, contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Import multiple contacts.
        
        Args:
            user_id: ID of the user
            contacts: List of contact data dictionaries
            
        Returns:
            Import results summary
        """
        try:
            response = self.session.post(
                f"{self.api_url}/users/{user_id}/contacts/import",
                json={"contacts": contacts}
            )
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            st.error(f"Failed to import contacts: {e}")
            return {"success": 0, "failed": len(contacts), "errors": [str(e)]}
    
    def get_user_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user settings.
        
        Args:
            user_id: ID of the user
            
        Returns:
            User settings or None if failed
        """
        try:
            response = self.session.get(f"{self.api_url}/users/{user_id}/settings")
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            st.error(f"Failed to fetch settings: {e}")
            return None
    
    def update_user_settings(self, user_id: str, settings: Dict[str, Any]) -> bool:
        """
        Update user settings.
        
        Args:
            user_id: ID of the user
            settings: Updated settings data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.session.put(
                f"{self.api_url}/users/{user_id}/settings",
                json=settings
            )
            response.raise_for_status()
            return True
        
        except requests.RequestException as e:
            st.error(f"Failed to update settings: {e}")
            return False


# Global service instance
@st.cache_resource
def get_user_service() -> UserService:
    """Get a cached user service instance."""
    api_url = st.secrets.get("api_url", "http://localhost:8000")
    api_key = st.secrets.get("api_key")
    return UserService(api_url, api_key)


# Session management functions
def login_user(username: str, password: str) -> bool:
    """
    Log in a user and store session data.
    
    Args:
        username: User's username or email
        password: User's password
        
    Returns:
        True if login successful, False otherwise
    """
    service = get_user_service()
    auth_data = service.authenticate(username, password)
    
    if auth_data:
        st.session_state.user_authenticated = True
        st.session_state.user_data = auth_data.get("user", {})
        st.session_state.access_token = auth_data.get("access_token")
        return True
    
    return False


def logout_user():
    """Log out the current user."""
    for key in ["user_authenticated", "user_data", "access_token"]:
        if key in st.session_state:
            del st.session_state[key]


def is_authenticated() -> bool:
    """Check if user is authenticated."""
    return st.session_state.get("user_authenticated", False)


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current user data."""
    if is_authenticated():
        return st.session_state.get("user_data")
    return None


def require_authentication():
    """Require user authentication, redirect to login if not authenticated."""
    if not is_authenticated():
        st.error("Please log in to access this page.")
        st.stop()
