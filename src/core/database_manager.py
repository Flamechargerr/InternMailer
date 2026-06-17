"""
Database Manager - Centralized connection pool and context management
Provides thread-safe database connections with automatic connection pooling
"""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Generator, Dict, Any
from datetime import datetime
import json
import os


class DatabaseManager:
    """
    Centralized database manager with connection pooling
    Thread-safe and efficient database operations
    """
    
    _instances: Dict[str, 'DatabaseManager'] = {}
    _lock = threading.Lock()
    
    def __init__(self, db_path: str, pool_size: int = 5):
        """
        Initialize database manager
        
        Args:
            db_path: Path to database file
            pool_size: Maximum number of connections in pool
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self._local = threading.local()
        self._lock = threading.Lock()
        
        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database schema
        self._initialize_schema()
    
    @classmethod
    def get_instance(cls, db_path: str, pool_size: int = 5) -> 'DatabaseManager':
        """Get or create database manager instance for a given path"""
        abs_path = str(Path(db_path).absolute())
        
        with cls._lock:
            if abs_path not in cls._instances:
                cls._instances[abs_path] = cls(abs_path, pool_size)
            return cls._instances[abs_path]
    
    @contextmanager
    def get_connection(self, timeout: Optional[float] = None) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a database connection from the pool
        
        Args:
            timeout: Connection timeout in seconds (default: 30.0)
        
        Usage:
            with db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT * FROM table")
        """
        if timeout is None:
            timeout = 30.0
        
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=timeout
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        # Set busy timeout for query-level timeout handling
        conn.execute(f"PRAGMA busy_timeout = {int(timeout * 1000)}")
        
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def execute(self, query: str, params: tuple = (), timeout: Optional[float] = None) -> sqlite3.Cursor:
        """
        Execute a single query and return cursor
        
        Args:
            query: SQL query to execute
            params: Query parameters
            timeout: Query timeout in seconds (default: 30.0)
        
        Usage:
            cursor = db_manager.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            results = cursor.fetchall()
        """
        with self.get_connection(timeout=timeout) as conn:
            return conn.execute(query, params)
    
    def execute_many(self, query: str, params_list: list, timeout: Optional[float] = None) -> sqlite3.Cursor:
        """
        Execute a query multiple times with different parameters
        
        Args:
            query: SQL query to execute
            params_list: List of parameter tuples
            timeout: Query timeout in seconds (default: 30.0)
        """
        with self.get_connection(timeout=timeout) as conn:
            return conn.executemany(query, params_list)
    
    def fetch_one(self, query: str, params: tuple = (), timeout: Optional[float] = None) -> Optional[sqlite3.Row]:
        """
        Fetch a single row
        
        Args:
            query: SQL query to execute
            params: Query parameters
            timeout: Query timeout in seconds (default: 30.0)
        """
        with self.get_connection(timeout=timeout) as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()
    
    def fetch_all(self, query: str, params: tuple = (), timeout: Optional[float] = None) -> list[sqlite3.Row]:
        """
        Fetch all rows
        
        Args:
            query: SQL query to execute
            params: Query parameters
            timeout: Query timeout in seconds (default: 30.0)
        """
        with self.get_connection(timeout=timeout) as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()
    
    def insert(self, table: str, data: Dict[str, Any], timeout: Optional[float] = None) -> int:
        """
        Insert a row into a table
        
        Args:
            table: Table name (validated for SQL injection prevention)
            data: Dictionary of column names and values
            timeout: Query timeout in seconds (default: 30.0)
        
        Returns:
            Last row ID
        """
        # Validate table name to prevent SQL injection
        from utils.security import sanitize_sql_identifier
        table = sanitize_sql_identifier(table)
        
        # Validate column names
        columns = []
        for col in data.keys():
            sanitize_sql_identifier(col)
            columns.append(col)
        
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['?'] * len(data))
        values = tuple(data.values())
        
        query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
        
        with self.get_connection(timeout=timeout) as conn:
            cursor = conn.execute(query, values)
            return cursor.lastrowid
    
    def update(self, table: str, data: Dict[str, Any], 
               where: str, where_params: tuple = (), timeout: Optional[float] = None) -> int:
        """
        Update rows in a table
        
        Args:
            table: Table name (validated for SQL injection prevention)
            data: Dictionary of column names and values to update
            where: WHERE clause (must use parameterized queries)
            where_params: Parameters for WHERE clause
            timeout: Query timeout in seconds (default: 30.0)
        
        Returns:
            Number of rows affected
        """
        # Validate table name
        from utils.security import sanitize_sql_identifier
        table = sanitize_sql_identifier(table)
        
        # Validate column names
        set_items = []
        for k in data.keys():
            sanitize_sql_identifier(k)
            set_items.append(f"{k} = ?")
        
        set_clause = ', '.join(set_items)
        values = tuple(data.values()) + where_params
        
        # Note: where clause should be pre-validated by caller
        # This method assumes where clause uses parameterized queries
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        
        with self.get_connection(timeout=timeout) as conn:
            cursor = conn.execute(query, values)
            return cursor.rowcount
    
    def delete(self, table: str, where: str, 
               where_params: tuple = (), timeout: Optional[float] = None) -> int:
        """
        Delete rows from a table
        
        Args:
            table: Table name (validated for SQL injection prevention)
            where: WHERE clause (must use parameterized queries)
            where_params: Parameters for WHERE clause
            timeout: Query timeout in seconds (default: 30.0)
        
        Returns:
            Number of rows affected
        """
        # Validate table name
        from utils.security import sanitize_sql_identifier
        table = sanitize_sql_identifier(table)
        
        # Note: where clause should be pre-validated by caller
        # This method assumes where clause uses parameterized queries
        query = f"DELETE FROM {table} WHERE {where}"
        
        with self.get_connection(timeout=timeout) as conn:
            cursor = conn.execute(query, where_params)
            return cursor.rowcount
    
    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """
        result = self.fetch_one(query, (table_name,))
        return result is not None
    
    def get_table_schema(self, table_name: str) -> list[sqlite3.Row]:
        """Get schema information for a table"""
        query = f"PRAGMA table_info({table_name})"
        return self.fetch_all(query)
    
    def column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table"""
        schema = self.get_table_schema(table_name)
        return any(row['name'] == column_name for row in schema)
    
    def add_column(self, table_name: str, column_name: str, 
                  column_type: str = "TEXT", default: Any = None):
        """Add a column to a table if it doesn't exist"""
        if not self.column_exists(table_name, column_name):
            query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            if default is not None:
                query += f" DEFAULT {default}"
            self.execute(query)
    
    def backup(self, backup_path: Optional[str] = None) -> str:
        """
        Create a backup of the database
        
        Returns:
            Path to backup file
        """
        if backup_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = Path(self.db_path).parent / 'backups'
            backup_dir.mkdir(exist_ok=True)
            backup_path = str(backup_dir / f"{Path(self.db_path).stem}_{timestamp}.db")
        
        source = sqlite3.connect(self.db_path)
        backup = sqlite3.connect(backup_path)
        
        with backup:
            source.backup(backup)
        
        backup.close()
        source.close()
        
        return backup_path
    
    def vacuum(self):
        """Optimize database and reduce file size"""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
    
    def analyze(self):
        """Analyze database and update statistics"""
        with self.get_connection() as conn:
            conn.execute("ANALYZE")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {
            'size_bytes': os.path.getsize(self.db_path),
            'size_mb': os.path.getsize(self.db_path) / (1024 * 1024),
            'tables': []
        }
        
        tables = self.fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
        for table in tables:
            table_name = table['name']
            count = self.fetch_one(f"SELECT COUNT(*) as count FROM {table_name}")
            stats['tables'].append({
                'name': table_name,
                'rows': count['count'] if count else 0
            })
        
        return stats
    
    def _initialize_schema(self):
        """Initialize database schema (to be overridden by subclasses)"""
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class EmailTrackingDB(DatabaseManager):
    """Database manager for email tracking"""
    
    def _initialize_schema(self):
        """Initialize email tracking schema"""
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sent_emails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    company TEXT,
                    position TEXT,
                    subject TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    provider_used TEXT,
                    ai_confidence REAL,
                    status TEXT DEFAULT 'sent',
                    followup_sent BOOLEAN DEFAULT 0,
                    replied BOOLEAN DEFAULT 0,
                    opened BOOLEAN DEFAULT 0,
                    clicked BOOLEAN DEFAULT 0,
                    metadata TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS followups_sent (
                    email TEXT PRIMARY KEY,
                    original_sent_date TEXT,
                    followup_sent_date TEXT,
                    attempts INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'sent'
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_sent_emails_email ON sent_emails(email)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_sent_emails_sent_at ON sent_emails(sent_at)
            ''')


class InboxMonitorDB(DatabaseManager):
    """Database manager for inbox monitoring"""
    
    def _initialize_schema(self):
        """Initialize inbox monitor schema"""
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS processed_replies (
                    message_id TEXT PRIMARY KEY,
                    from_email TEXT NOT NULL,
                    to_list TEXT,
                    cc_list TEXT,
                    subject TEXT,
                    body TEXT,
                    category TEXT,
                    confidence REAL,
                    sentiment REAL,
                    received_date TEXT,
                    processed_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    action_taken TEXT DEFAULT 'pending'
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS priority_contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    replied_date TEXT,
                    interest_level TEXT DEFAULT 'medium',
                    calendar_sent BOOLEAN DEFAULT 0,
                    notes TEXT,
                    message_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS review_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    subject TEXT,
                    category TEXT,
                    added_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    reviewed BOOLEAN DEFAULT 0,
                    message_id TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS followup_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    original_subject TEXT,
                    scheduled_date TEXT NOT NULL,
                    sent BOOLEAN DEFAULT 0,
                    sent_date TEXT,
                    message_id TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS unsubscribed (
                    email TEXT PRIMARY KEY,
                    reason TEXT,
                    date TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_processed_replies_from ON processed_replies(from_email)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_processed_replies_category ON processed_replies(category)
            ''')


class DaemonStatusDB(DatabaseManager):
    """Database manager for daemon status"""
    
    def _initialize_schema(self):
        """Initialize daemon status schema"""
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS daemon_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    message TEXT,
                    details TEXT,
                    level TEXT DEFAULT 'INFO'
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    date TEXT PRIMARY KEY,
                    emails_sent INTEGER DEFAULT 0,
                    replies_received INTEGER DEFAULT 0,
                    followups_sent INTEGER DEFAULT 0,
                    actions_taken INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')


class JobDiscoveryDB(DatabaseManager):
    """Database manager for job discovery and applications"""

    def _initialize_schema(self):
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    source_id TEXT,
                    company TEXT,
                    title TEXT,
                    location TEXT,
                    location_type TEXT,
                    url TEXT UNIQUE,
                    apply_url TEXT,
                    description TEXT,
                    employment_type TEXT,
                    posted_at TEXT,
                    season_match BOOLEAN DEFAULT 0,
                    visa_sponsorship BOOLEAN DEFAULT 0,
                    relocation_support BOOLEAN DEFAULT 0,
                    score REAL DEFAULT 0,
                    status TEXT DEFAULT 'new',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS job_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    finished_at TIMESTAMP,
                    total_found INTEGER DEFAULT 0,
                    total_saved INTEGER DEFAULT 0,
                    filters TEXT,
                    status TEXT DEFAULT 'running',
                    notes TEXT
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id INTEGER,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    method TEXT,
                    status TEXT,
                    details TEXT,
                    FOREIGN KEY(job_id) REFERENCES jobs(id)
                )
            ''')

            conn.execute('CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(score)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company)')


def get_email_tracking_db(db_path: str = '/tmp/internmailer_db/email_tracking.db') -> EmailTrackingDB:
    """Get email tracking database manager instance"""
    return EmailTrackingDB.get_instance(db_path)


def get_inbox_monitor_db(db_path: str = '/tmp/internmailer_db/inbox_monitor.db') -> InboxMonitorDB:
    """Get inbox monitor database manager instance"""
    return InboxMonitorDB.get_instance(db_path)


def get_daemon_status_db(db_path: str = '/tmp/internmailer_db/daemon_status.db') -> DaemonStatusDB:
    """Get daemon status database manager instance"""
    return DaemonStatusDB.get_instance(db_path)


def get_job_discovery_db(db_path: str = '/tmp/internmailer_db/job_discovery.db') -> JobDiscoveryDB:
    """Get job discovery database manager instance"""
    return JobDiscoveryDB.get_instance(db_path)
