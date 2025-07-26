"""
Abstract interface for resume parsing providers.
This module defines the common interface that all parsing implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json

@dataclass
class ResumeData:
    """Structured data class for parsed resume information."""
    skills: List[str]
    projects: List[str]
    courses: List[str]
    experience: List[str]
    summary: str
    domains: Optional[List[str]] = None
    education: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'skills': self.skills,
            'projects': self.projects,
            'courses': self.courses,
            'experience': self.experience,
            'summary': self.summary,
            'domains': self.domains or [],
            'education': self.education or ''
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    def validate(self) -> bool:
        """Validate that essential fields are populated."""
        return bool(self.skills and self.projects and self.summary)


class ResumeParserInterface(ABC):
    """Abstract interface for resume parsing providers."""
    
    @abstractmethod
    def parse(self, text: str) -> ResumeData:
        """
        Parse resume text and return structured data.
        
        Args:
            text: Raw resume text extracted from PDF/DOCX
            
        Returns:
            ResumeData: Structured resume information
            
        Raises:
            ParsingError: If parsing fails
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the name of the parsing provider."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and ready to use."""
        pass
    
    @abstractmethod
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Return performance metrics for monitoring."""
        pass


class ParsingError(Exception):
    """Custom exception for parsing errors."""
    
    def __init__(self, message: str, provider: str = None, original_error: Exception = None):
        self.provider = provider
        self.original_error = original_error
        super().__init__(message)
