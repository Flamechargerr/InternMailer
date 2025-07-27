"""
Database configuration and connection settings.
"""

import os
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    
    # Database connection settings
    db_type: str = "sqlite"  # sqlite, postgresql
    host: Optional[str] = None
    port: Optional[int] = None
    database: str = "internmailer.db"
    username: Optional[str] = None
    password: Optional[str] = None
    
    # SQLAlchemy settings
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    # Schema settings for tenant separation
    use_schemas: bool = True
    academic_schema: str = "academic"
    corporate_schema: str = "corporate"
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Load configuration from environment variables."""
        return cls(
            db_type=os.getenv("DB_TYPE", "sqlite"),
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", "5432")) if os.getenv("DB_PORT") else None,
            database=os.getenv("DB_NAME", "internmailer.db"),
            username=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            echo=os.getenv("DB_ECHO", "false").lower() == "true",
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),
            use_schemas=os.getenv("DB_USE_SCHEMAS", "true").lower() == "true",
            academic_schema=os.getenv("DB_ACADEMIC_SCHEMA", "academic"),
            corporate_schema=os.getenv("DB_CORPORATE_SCHEMA", "corporate"),
        )


def get_database_url(config: Optional[DatabaseConfig] = None) -> str:
    """
    Generate database URL from configuration.
    
    Args:
        config: Database configuration. If None, loads from environment.
        
    Returns:
        Database URL string.
    """
    if config is None:
        config = DatabaseConfig.from_env()
    
    if config.db_type == "sqlite":
        # SQLite URL
        return f"sqlite:///{config.database}"
    
    elif config.db_type == "postgresql":
        # PostgreSQL URL
        if not all([config.host, config.username, config.password]):
            raise ValueError("PostgreSQL connection requires host, username, and password")
        
        password = quote_plus(config.password)
        port_part = f":{config.port}" if config.port else ""
        
        return f"postgresql://{config.username}:{password}@{config.host}{port_part}/{config.database}"
    
    else:
        raise ValueError(f"Unsupported database type: {config.db_type}")


# Global configuration instance
config = DatabaseConfig.from_env()
DATABASE_URL = get_database_url(config)
