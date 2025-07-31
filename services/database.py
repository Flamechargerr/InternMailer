"""
Database Service - Comprehensive database operations with async support.

This module provides database operations for contacts, campaigns, and other
entities with both production and mock implementations.
"""

import asyncio
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

try:
    from sqlalchemy import create_engine, select, func
    from sqlalchemy.orm import sessionmaker, Session
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

from .base import BaseService, ServiceConfig, with_error_handling, ServiceError


@dataclass
class Contact:
    """Contact data structure."""
    id: Optional[str] = None
    email: str = ""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization: Optional[str] = None
    position: Optional[str] = None
    research_areas: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Campaign:
    """Campaign data structure."""
    id: Optional[str] = None
    name: str = ""
    description: Optional[str] = None
    status: str = "draft"
    template_id: Optional[str] = None
    user_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Statistics
    total_contacts: int = 0
    emails_sent: int = 0
    emails_delivered: int = 0
    emails_opened: int = 0
    emails_clicked: int = 0


@dataclass
class QueryFilters:
    """Query filters for database operations."""
    limit: Optional[int] = None
    offset: Optional[int] = None
    sort_by: Optional[str] = None
    sort_order: str = "asc"  # asc or desc
    filters: Optional[Dict[str, Any]] = None


class DatabaseService(BaseService):
    """Production database service with SQLAlchemy support."""
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self._engine = None
        self._session_factory = None
        self._async_engine = None
        self._async_session_factory = None
        
    async def _initialize_impl(self) -> None:
        """Initialize database service."""
        if not SQLALCHEMY_AVAILABLE:
            raise ServiceError(
                "SQLAlchemy not available. Install with: pip install sqlalchemy",
                error_code="SQLALCHEMY_MISSING"
            )
        
        if not self.config.database_url:
            raise ServiceError(
                "Database URL not configured",
                error_code="DATABASE_URL_MISSING"
            )
        
        await self._setup_database_connections()
        
    async def _cleanup_impl(self) -> None:
        """Cleanup database service resources."""
        if self._async_engine:
            await self._async_engine.dispose()
        if self._engine:
            self._engine.dispose()
    
    async def _health_check_impl(self) -> Dict[str, Any]:
        """Health check for database service."""
        try:
            # Try to execute a simple query
            if self._async_engine:
                async with self._async_session_factory() as session:
                    result = await session.execute(select(func.now()))
                    db_time = result.scalar()
            else:
                with self._session_factory() as session:
                    result = session.execute(select(func.now()))
                    db_time = result.scalar()
            
            return {
                "database_url": self.config.database_url.split("@")[-1],  # Hide credentials
                "connection_pool_size": self.config.database_pool_size,
                "database_time": db_time.isoformat() if db_time else None
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "connection_failed"
            }
    
    async def _setup_database_connections(self):
        """Setup database connections."""
        # Setup async engine if supported
        if self.config.database_url.startswith(('postgresql+asyncpg', 'sqlite+aiosqlite')):
            self._async_engine = create_async_engine(
                self.config.database_url,
                pool_size=self.config.database_pool_size,
                max_overflow=self.config.database_max_overflow,
                echo=self.config.debug
            )
            self._async_session_factory = async_sessionmaker(
                self._async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
        
        # Setup sync engine for fallback
        sync_url = self.config.database_url
        if sync_url.startswith('postgresql+asyncpg'):
            sync_url = sync_url.replace('postgresql+asyncpg', 'postgresql+psycopg2')
        elif sync_url.startswith('sqlite+aiosqlite'):
            sync_url = sync_url.replace('sqlite+aiosqlite', 'sqlite')
        
        self._engine = create_engine(
            sync_url,
            pool_size=self.config.database_pool_size,
            max_overflow=self.config.database_max_overflow,
            echo=self.config.debug
        )
        self._session_factory = sessionmaker(self._engine)
    
    @with_error_handling
    async def list_contacts(self, filters: Optional[QueryFilters] = None) -> List[Contact]:
        """List contacts with optional filtering."""
        async with self._ensure_initialized():
            # This is a simplified implementation
            # In production, you'd use your actual ORM models
            if filters is None:
                filters = QueryFilters()
            
            contacts = []
            # Implement actual database query here
            # For now, return empty list as this requires ORM models
            
            return contacts
    
    @with_error_handling
    async def get_contact(self, contact_id: str) -> Optional[Contact]:
        """Get a contact by ID."""
        async with self._ensure_initialized():
            # Implement actual database query here
            return None
    
    @with_error_handling
    async def create_contact(self, contact_data: Dict[str, Any]) -> Contact:
        """Create a new contact."""
        async with self._ensure_initialized():
            contact = Contact(**contact_data)
            contact.id = f"contact_{int(time.time() * 1000000)}"
            contact.created_at = datetime.now(timezone.utc)
            contact.updated_at = contact.created_at
            
            # Implement actual database insert here
            
            return contact
    
    @with_error_handling
    async def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> Optional[Contact]:
        """Update a contact."""
        async with self._ensure_initialized():
            # Implement actual database update here
            return None
    
    @with_error_handling
    async def delete_contact(self, contact_id: str) -> bool:
        """Delete a contact."""
        async with self._ensure_initialized():
            # Implement actual database delete here
            return False
    
    @with_error_handling
    async def list_campaigns(self, filters: Optional[QueryFilters] = None) -> List[Campaign]:
        """List campaigns with optional filtering."""
        async with self._ensure_initialized():
            if filters is None:
                filters = QueryFilters()
            
            campaigns = []
            # Implement actual database query here
            
            return campaigns
    
    @with_error_handling
    async def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get a campaign by ID."""
        async with self._ensure_initialized():
            # Implement actual database query here
            return None
    
    @with_error_handling
    async def create_campaign(self, campaign_data: Dict[str, Any]) -> Campaign:
        """Create a new campaign."""
        async with self._ensure_initialized():
            campaign = Campaign(**campaign_data)
            campaign.id = f"campaign_{int(time.time() * 1000000)}"
            campaign.created_at = datetime.now(timezone.utc)
            campaign.updated_at = campaign.created_at
            
            # Implement actual database insert here
            
            return campaign
    
    @with_error_handling
    async def update_campaign(self, campaign_id: str, updates: Dict[str, Any]) -> Optional[Campaign]:
        """Update a campaign."""
        async with self._ensure_initialized():
            # Implement actual database update here
            return None
    
    @with_error_handling
    async def execute_raw_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a raw SQL query."""
        async with self._ensure_initialized():
            # Implement raw query execution
            # This should be used carefully and with proper sanitization
            return []


class MockDatabaseService(BaseService):
    """Mock database service for development and testing."""
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self._contacts = {}
        self._campaigns = {}
        self._next_contact_id = 1
        self._next_campaign_id = 1
        
    async def _initialize_impl(self) -> None:
        """Initialize mock database service."""
        # Create some sample data
        await self._create_sample_data()
        self.logger.info("Mock database service initialized with sample data")
    
    async def _cleanup_impl(self) -> None:
        """Cleanup mock database service."""
        self._contacts.clear()
        self._campaigns.clear()
    
    async def _health_check_impl(self) -> Dict[str, Any]:
        """Health check for mock database service."""
        return {
            "provider": "mock",
            "contacts_count": len(self._contacts),
            "campaigns_count": len(self._campaigns),
            "memory_usage_mb": len(str(self._contacts)) + len(str(self._campaigns)) / 1024 / 1024
        }
    
    async def _create_sample_data(self):
        """Create sample data for testing."""
        # Avoid recursion by directly manipulating _contacts and _campaigns
        sample_contacts = [
            {
                "email": "john.smith@mit.edu",
                "first_name": "John",
                "last_name": "Smith", 
                "organization": "MIT",
                "position": "Professor",
                "research_areas": ["Machine Learning", "Computer Vision"],
                "tags": ["academic", "ml"]
            },
            {
                "email": "jane.doe@stanford.edu",
                "first_name": "Jane",
                "last_name": "Doe",
                "organization": "Stanford University",
                "position": "Associate Professor",
                "research_areas": ["Natural Language Processing", "AI"],
                "tags": ["academic", "nlp"]
            },
            {
                "email": "bob.wilson@google.com",
                "first_name": "Bob",
                "last_name": "Wilson",
                "organization": "Google",
                "position": "Senior Engineer",
                "research_areas": ["Software Engineering", "Distributed Systems"],
                "tags": ["industry", "engineering"]
            }
        ]
        
        for contact_data in sample_contacts:
            contact = Contact(**contact_data)
            contact.id = f"contact_{self._next_contact_id}"
            self._next_contact_id += 1
            self._contacts[contact.id] = contact

        # Directly create campaigns
        sample_campaigns = [
            {
                "name": "ML Professors Outreach",
                "description": "Outreach to machine learning professors",
                "status": "active",
                "total_contacts": 50,
                "emails_sent": 45,
                "emails_delivered": 43,
                "emails_opened": 12,
                "emails_clicked": 3
            },
            {
                "name": "Industry Internships",
                "description": "Reach out to industry contacts for internships",
                "status": "draft",
                "total_contacts": 25,
                "emails_sent": 0,
                "emails_delivered": 0,
                "emails_opened": 0,
                "emails_clicked": 0
            }
        ]
        
        for campaign_data in sample_campaigns:
            campaign = Campaign(**campaign_data)
            campaign.id = f"campaign_{self._next_campaign_id}"
            self._next_campaign_id += 1
            self._campaigns[campaign.id] = campaign
    
    @with_error_handling
    async def list_contacts(self, filters: Optional[QueryFilters] = None) -> List[Contact]:
        """List contacts with optional filtering."""
        async with self._ensure_initialized():
            # Simulate some processing delay
            await asyncio.sleep(random.uniform(0.01, 0.05))
            
            contacts = list(self._contacts.values())
            
            if filters and filters.filters:
                # Apply basic filtering
                if "organization" in filters.filters:
                    org_filter = filters.filters["organization"].lower()
                    contacts = [c for c in contacts if org_filter in (c.organization or "").lower()]
                
                if "tags" in filters.filters:
                    tag_filter = filters.filters["tags"]
                    if isinstance(tag_filter, str):
                        tag_filter = [tag_filter]
                    contacts = [c for c in contacts if any(tag in (c.tags or []) for tag in tag_filter)]
            
            # Apply sorting
            if filters and filters.sort_by:
                reverse = filters.sort_order == "desc"
                try:
                    contacts.sort(key=lambda x: getattr(x, filters.sort_by, "") or "", reverse=reverse)
                except TypeError:
                    # Handle cases where we can't sort (e.g., mixed types, None values)
                    contacts.sort(key=lambda x: str(getattr(x, filters.sort_by, "") or ""), reverse=reverse)
            
            # Apply pagination
            if filters and filters.offset:
                contacts = contacts[filters.offset:]
            if filters and filters.limit:
                contacts = contacts[:filters.limit]
            
            return contacts
    
    @with_error_handling
    async def get_contact(self, contact_id: str) -> Optional[Contact]:
        """Get a contact by ID."""
        async with self._ensure_initialized():
            await asyncio.sleep(random.uniform(0.005, 0.02))
            return self._contacts.get(contact_id)
    
    @with_error_handling
    async def create_contact(self, contact_data: Dict[str, Any]) -> Contact:
        """Create a new contact."""
        async with self._ensure_initialized():
            await asyncio.sleep(random.uniform(0.01, 0.03))
            
            contact = Contact(**contact_data)
            contact.id = f"contact_{self._next_contact_id}"
            self._next_contact_id += 1
            contact.created_at = datetime.now(timezone.utc)
            contact.updated_at = contact.created_at
            
            self._contacts[contact.id] = contact
            
            self.logger.info("Mock contact created", contact_id=contact.id, email=contact.email)
            
            return contact
    
    @with_error_handling
    async def update_contact(self, contact_id: str, updates: Dict[str, Any]) -> Optional[Contact]:
        """Update a contact."""
        async with self._ensure_initialized():
            await asyncio.sleep(random.uniform(0.01, 0.03))
            
            contact = self._contacts.get(contact_id)
            if not contact:
                return None
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(contact, key):
                    setattr(contact, key, value)
            
            contact.updated_at = datetime.now(timezone.utc)
            
            self.logger.info("Mock contact updated", contact_id=contact_id)
            
            return contact
    
    @with_error_handling
    async def delete_contact(self, contact_id: str) -> bool:
        """Delete a contact."""
        async with self._ensure_initialized():
            await asyncio.sleep(random.uniform(0.005, 0.02))
            
            if contact_id in self._contacts:
                del self._contacts[contact_id]
                self.logger.info("Mock contact deleted", contact_id=contact_id)
                return True
            
            return False
    
    @with_error_handling
    async def list_campaigns(self, filters: Optional[QueryFilters] = None) -> List[Campaign]:
        """List campaigns with optional filtering."""
        async with self._ensure_initialized():
            await asyncio.sleep(random.uniform(0.01, 0.05))
            
            campaigns = list(self._campaigns.values())
            
            if filters and filters.filters:
                # Apply basic filtering
                if "status" in filters.filters:
                    status_filter = filters.filters["status"]
                    campaigns = [c for c in campaigns if c.status == status_filter]
            
            # Apply sorting
            if filters and filters.sort_by:
                reverse = filters.sort_order == "desc"
                try:
                    campaigns.sort(key=lambda x: getattr(x, filters.sort_by, "") or "", reverse=reverse)
                except TypeError:
                    # Handle cases where we can't sort (e.g., mixed types, None values)
                    campaigns.sort(key=lambda x: str(getattr(x, filters.sort_by, "") or ""), reverse=reverse)
            
            # Apply pagination
            if filters and filters.offset:
                campaigns = campaigns[filters.offset:]
            if filters and filters.limit:
                campaigns = campaigns[:filters.limit]
            
            return campaigns
    
    @with_error_handling
    async def get_campaign(self, campaign_id: str) -> Optional[Campaign]:
        """Get a campaign by ID."""
        async with self._ensure_initialized():
            await asyncio.sleep(random.uniform(0.005, 0.02))
            return self._campaigns.get(campaign_id)
    
    @with_error_handling
    async def create_campaign(self, campaign_data: Dict[str, Any]) -> Campaign:
        """Create a new campaign."""
        async with self._ensure_initialized():
            await asyncio.sleep(random.uniform(0.01, 0.03))
            
            campaign = Campaign(**campaign_data)
            campaign.id = f"campaign_{self._next_campaign_id}"
            self._next_campaign_id += 1
            campaign.created_at = datetime.now(timezone.utc)
            campaign.updated_at = campaign.created_at
            
            self._campaigns[campaign.id] = campaign
            
            self.logger.info("Mock campaign created", campaign_id=campaign.id, name=campaign.name)
            
            return campaign
    
    @with_error_handling
    async def update_campaign(self, campaign_id: str, updates: Dict[str, Any]) -> Optional[Campaign]:
        """Update a campaign."""
        async with self._ensure_initialized():
            await asyncio.sleep(random.uniform(0.01, 0.03))
            
            campaign = self._campaigns.get(campaign_id)
            if not campaign:
                return None
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(campaign, key):
                    setattr(campaign, key, value)
            
            campaign.updated_at = datetime.now(timezone.utc)
            
            self.logger.info("Mock campaign updated", campaign_id=campaign_id)
            
            return campaign
    
    @with_error_handling
    async def execute_raw_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a mock raw query."""
        async with self._ensure_initialized():
            await asyncio.sleep(random.uniform(0.02, 0.1))
            
            # Return mock data based on query type
            if "SELECT" in query.upper():
                return [{"mock_result": True, "query": query}]
            else:
                return [{"affected_rows": 1}]
    
    def get_all_data(self) -> Dict[str, Any]:
        """Get all mock data for inspection (mock only)."""
        return {
            "contacts": self._contacts,
            "campaigns": self._campaigns
        }
    
    def clear_all_data(self):
        """Clear all mock data (mock only)."""
        self._contacts.clear()
        self._campaigns.clear()
        self._next_contact_id = 1
        self._next_campaign_id = 1
