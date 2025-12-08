"""
InternMailer - Database Connection Pooling
Thread-safe SQLite connection management
"""

import sqlite3
import threading
from contextlib import contextmanager
from queue import Queue, Empty
from typing import Optional

class DatabasePool:
    """
    Thread-safe connection pool for SQLite databases
    Reuses connections instead of creating new ones
    """
    
    def __init__(self, db_path: str, pool_size: int = 5, timeout: int = 30):
        self.db_path = db_path
        self.pool_size = pool_size
        self.timeout = timeout
        self.pool = Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        
        # Pre-create connections
        for _ in range(pool_size):
            conn = self._create_connection()
            self.pool.put(conn)
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=self.timeout)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for getting database connection from pool
        Automatically returns connection to pool when done
        
        Usage:
            with pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
        """
        conn = None
        try:
            # Get connection from pool (blocks if none available)
            conn = self.pool.get(timeout=self.timeout)
            yield conn
            conn.commit()  # Auto-commit on success
        except Empty:
            # Pool exhausted, create temporary connection
            conn = self._create_connection()
            yield conn
            conn.commit()
            conn.close()  # Don't return temp connection to pool
            conn = None
        except Exception as e:
            if conn:
                conn.rollback()  # Rollback on error
            raise
        finally:
            # Return connection to pool
            if conn and not self.pool.full():
                try:
                    self.pool.put_nowait(conn)
                except:
                    conn.close()
    
    def execute_query(self, query: str, params: tuple = ()):
        """
        Execute a single query and return results
        Convenience method for simple queries
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_many(self, query: str, params_list: list):
        """Execute query with multiple parameter sets"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount
    
    def close_all(self):
        """Close all connections in pool"""
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except:
                pass

# Pool manager for multiple databases
class PoolManager:
    """Manage connection pools for multiple databases"""
    
    def __init__(self):
        self.pools = {}
        self.lock = threading.Lock()
    
    def get_pool(self, db_path: str, pool_size: int = 5) -> DatabasePool:
        """Get or create pool for database"""
        with self.lock:
            if db_path not in self.pools:
                self.pools[db_path] = DatabasePool(db_path, pool_size)
            return self.pools[db_path]
    
    def close_all_pools(self):
        """Close all database pools"""
        with self.lock:
            for pool in self.pools.values():
                pool.close_all()
            self.pools.clear()

# Singleton instance
_pool_manager = None

def get_pool_manager() -> PoolManager:
    """Get singleton pool manager"""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = PoolManager()
    return _pool_manager

# Convenience functions
def get_db_pool(db_path: str) -> DatabasePool:
    """Get connection pool for specific database"""
    manager = get_pool_manager()
    return manager.get_pool(db_path)

# Example usage
if __name__ == '__main__':
    # Get pool for tracking database
    pool = get_db_pool('email_tracking.db')
    
    # Use connection with context manager
    with pool.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM sent_emails")
        result = cursor.fetchone()
        print(f"Total emails sent: {result['count']}")
    
    # Or use convenience method
    results = pool.execute_query("SELECT email FROM sent_emails LIMIT 5")
    for row in results:
        print(f"Email: {row['email']}")
