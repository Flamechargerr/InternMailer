"""
Database session management and connection handling.
"""

from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, Engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool

from .config import DATABASE_URL, config


# Create the declarative base
Base = declarative_base()

# Create engine
def create_database_engine() -> Engine:
    """Create and configure the database engine."""
    
    engine_kwargs = {
        "echo": config.echo,
    }
    
    if config.db_type == "sqlite":
        # SQLite specific configuration
        engine_kwargs.update({
            "poolclass": StaticPool,
            "connect_args": {
                "check_same_thread": False,
                "timeout": 20,
            }
        })
    else:
        # PostgreSQL configuration
        engine_kwargs.update({
            "pool_size": config.pool_size,
            "max_overflow": config.max_overflow,
            "pool_timeout": config.pool_timeout,
            "pool_recycle": config.pool_recycle,
        })
    
    engine = create_engine(DATABASE_URL, **engine_kwargs)
    
    # Enable foreign key constraints for SQLite
    if config.db_type == "sqlite":
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    
    return engine


# Create engine and session factory
engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Get a database session with automatic cleanup.
    
    Yields:
        Database session.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session_sync() -> Session:
    """
    Get a synchronous database session.
    
    Note: Remember to close the session manually.
    
    Returns:
        Database session.
    """
    return SessionLocal()


def create_tables(drop_existing: bool = False) -> None:
    """
    Create all database tables.
    
    Args:
        drop_existing: Whether to drop existing tables first.
    """
    # Import all models to ensure they're registered
    from .models import *
    
    if drop_existing:
        Base.metadata.drop_all(bind=engine)
    
    Base.metadata.create_all(bind=engine)
    
    # Create schemas for PostgreSQL if needed
    if config.db_type == "postgresql" and config.use_schemas:
        with get_session() as session:
            # Create academic schema
            session.execute(f"CREATE SCHEMA IF NOT EXISTS {config.academic_schema}")
            # Create corporate schema
            session.execute(f"CREATE SCHEMA IF NOT EXISTS {config.corporate_schema}")


def get_tenant_schema(tenant_type: str) -> Optional[str]:
    """
    Get the schema name for a given tenant type.
    
    Args:
        tenant_type: Either 'academic' or 'corporate'.
        
    Returns:
        Schema name or None if not using schemas.
    """
    if not config.use_schemas or config.db_type == "sqlite":
        return None
    
    if tenant_type == "academic":
        return config.academic_schema
    elif tenant_type == "corporate":
        return config.corporate_schema
    else:
        raise ValueError(f"Invalid tenant type: {tenant_type}")


def close_connections():
    """Close all database connections."""
    engine.dispose()
