"""
Tests for Database Timeout Handling
===================================

Tests validate:
- Query-level timeout configuration
- Connection timeout handling
- Timeout parameter propagation
- Database operations with custom timeouts

Validates Requirements: 6.3, 6.6
"""

import pytest
import sqlite3
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from core.database_manager import DatabaseManager, get_job_discovery_db


class TestDatabaseTimeouts:
    """Test database timeout handling"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.test_db_path = "test_timeout.db"
        self.db = DatabaseManager(self.test_db_path)
        
        # Create test table
        with self.db.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    value INTEGER
                )
            """)
    
    def teardown_method(self):
        """Cleanup after tests"""
        # Remove test database
        Path(self.test_db_path).unlink(missing_ok=True)
    
    def test_default_connection_timeout(self):
        """Test default connection timeout is set"""
        with self.db.get_connection() as conn:
            # Verify connection was created
            assert conn is not None
            
            # Check that busy_timeout pragma is set
            cursor = conn.execute("PRAGMA busy_timeout")
            timeout = cursor.fetchone()[0]
            # Default timeout is 30 seconds = 30000 milliseconds
            assert timeout == 30000
    
    def test_custom_connection_timeout(self):
        """Test custom connection timeout"""
        custom_timeout = 10.0
        
        with self.db.get_connection(timeout=custom_timeout) as conn:
            assert conn is not None
            
            # Check that busy_timeout pragma is set to custom value
            cursor = conn.execute("PRAGMA busy_timeout")
            timeout = cursor.fetchone()[0]
            # Custom timeout is 10 seconds = 10000 milliseconds
            assert timeout == 10000
    
    def test_execute_with_default_timeout(self):
        """Test execute method uses default timeout"""
        # Insert test data
        self.db.execute(
            "INSERT INTO test_table (name, value) VALUES (?, ?)",
            ("test", 42)
        )
        
        # Verify data was inserted
        result = self.db.fetch_one("SELECT * FROM test_table WHERE name = ?", ("test",))
        assert result is not None
        assert result["name"] == "test"
        assert result["value"] == 42
    
    def test_execute_with_custom_timeout(self):
        """Test execute method with custom timeout"""
        # Insert test data with custom timeout
        self.db.execute(
            "INSERT INTO test_table (name, value) VALUES (?, ?)",
            ("test", 42),
            timeout=5.0
        )
        
        # Verify data was inserted
        result = self.db.fetch_one("SELECT * FROM test_table WHERE name = ?", ("test",))
        assert result is not None
    
    def test_fetch_one_with_timeout(self):
        """Test fetch_one with custom timeout"""
        # Insert test data
        self.db.insert("test_table", {"name": "test", "value": 42})
        
        # Fetch with custom timeout
        result = self.db.fetch_one(
            "SELECT * FROM test_table WHERE name = ?",
            ("test",),
            timeout=5.0
        )
        
        assert result is not None
        assert result["name"] == "test"
    
    def test_fetch_all_with_timeout(self):
        """Test fetch_all with custom timeout"""
        # Insert multiple rows
        for i in range(5):
            self.db.insert("test_table", {"name": f"test{i}", "value": i})
        
        # Fetch all with custom timeout
        results = self.db.fetch_all(
            "SELECT * FROM test_table ORDER BY value",
            timeout=5.0
        )
        
        assert len(results) == 5
        assert results[0]["name"] == "test0"
        assert results[4]["name"] == "test4"
    
    def test_insert_with_timeout(self):
        """Test insert with custom timeout"""
        row_id = self.db.insert(
            "test_table",
            {"name": "test", "value": 42},
            timeout=5.0
        )
        
        assert row_id > 0
        
        # Verify insertion
        result = self.db.fetch_one("SELECT * FROM test_table WHERE id = ?", (row_id,))
        assert result is not None
    
    def test_update_with_timeout(self):
        """Test update with custom timeout"""
        # Insert test data
        row_id = self.db.insert("test_table", {"name": "test", "value": 42})
        
        # Update with custom timeout
        rows_affected = self.db.update(
            "test_table",
            {"value": 100},
            "id = ?",
            (row_id,),
            timeout=5.0
        )
        
        assert rows_affected == 1
        
        # Verify update
        result = self.db.fetch_one("SELECT * FROM test_table WHERE id = ?", (row_id,))
        assert result["value"] == 100
    
    def test_delete_with_timeout(self):
        """Test delete with custom timeout"""
        # Insert test data
        row_id = self.db.insert("test_table", {"name": "test", "value": 42})
        
        # Delete with custom timeout
        rows_affected = self.db.delete(
            "test_table",
            "id = ?",
            (row_id,),
            timeout=5.0
        )
        
        assert rows_affected == 1
        
        # Verify deletion
        result = self.db.fetch_one("SELECT * FROM test_table WHERE id = ?", (row_id,))
        assert result is None
    
    def test_execute_many_with_timeout(self):
        """Test execute_many with custom timeout"""
        data = [
            ("test1", 1),
            ("test2", 2),
            ("test3", 3),
        ]
        
        self.db.execute_many(
            "INSERT INTO test_table (name, value) VALUES (?, ?)",
            data,
            timeout=5.0
        )
        
        # Verify all rows were inserted
        results = self.db.fetch_all("SELECT * FROM test_table ORDER BY value")
        assert len(results) == 3
    
    def test_timeout_on_locked_database(self):
        """Test timeout behavior when database is locked"""
        # Create a lock by starting a transaction in another thread
        lock_acquired = threading.Event()
        lock_released = threading.Event()
        
        def lock_database():
            conn = sqlite3.connect(self.test_db_path)
            conn.execute("BEGIN EXCLUSIVE")
            lock_acquired.set()
            lock_released.wait(timeout=5.0)
            conn.rollback()
            conn.close()
        
        # Start locking thread
        lock_thread = threading.Thread(target=lock_database)
        lock_thread.start()
        
        # Wait for lock to be acquired
        lock_acquired.wait(timeout=2.0)
        
        try:
            # Try to access database with short timeout
            start_time = time.time()
            with pytest.raises(sqlite3.OperationalError):
                self.db.execute(
                    "INSERT INTO test_table (name, value) VALUES (?, ?)",
                    ("test", 42),
                    timeout=0.5  # Very short timeout
                )
            duration = time.time() - start_time
            
            # Verify timeout occurred quickly
            assert duration < 2.0
        finally:
            # Release lock
            lock_released.set()
            lock_thread.join(timeout=2.0)
    
    def test_connection_pool_timeout_isolation(self):
        """Test that timeout settings don't affect other connections"""
        # Create connection with short timeout
        with self.db.get_connection(timeout=1.0) as conn1:
            cursor = conn1.execute("PRAGMA busy_timeout")
            timeout1 = cursor.fetchone()[0]
            assert timeout1 == 1000
        
        # Create connection with long timeout
        with self.db.get_connection(timeout=60.0) as conn2:
            cursor = conn2.execute("PRAGMA busy_timeout")
            timeout2 = cursor.fetchone()[0]
            assert timeout2 == 60000
        
        # Create connection with default timeout
        with self.db.get_connection() as conn3:
            cursor = conn3.execute("PRAGMA busy_timeout")
            timeout3 = cursor.fetchone()[0]
            assert timeout3 == 30000


class TestJobDiscoveryDBTimeouts:
    """Test timeout handling in job discovery database"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.test_db_path = "test_job_discovery.db"
        # Remove existing test database
        Path(self.test_db_path).unlink(missing_ok=True)
        # Create new database with schema
        from core.database_manager import JobDiscoveryDB
        self.db = JobDiscoveryDB(self.test_db_path)
    
    def teardown_method(self):
        """Cleanup after tests"""
        Path(self.test_db_path).unlink(missing_ok=True)
    
    def test_job_insertion_with_timeout(self):
        """Test job insertion with custom timeout"""
        job_data = {
            "source": "test",
            "source_id": "test123",
            "company": "Test Company",
            "title": "Software Engineer Intern",
            "location": "Remote",
            "location_type": "remote",
            "url": "https://example.com/job/123",
            "apply_url": "https://example.com/apply/123",
            "description": "Test job description",
            "employment_type": "internship",
            "score": 0.8,
            "status": "new",
        }
        
        # Insert with custom timeout
        job_id = self.db.insert("jobs", job_data, timeout=5.0)
        
        assert job_id > 0
        
        # Verify insertion
        result = self.db.fetch_one("SELECT * FROM jobs WHERE id = ?", (job_id,))
        assert result is not None
        assert result["company"] == "Test Company"
    
    def test_job_query_with_timeout(self):
        """Test job queries with custom timeout"""
        # Insert test jobs
        for i in range(5):
            self.db.insert("jobs", {
                "source": "test",
                "source_id": f"test{i}",
                "company": f"Company {i}",
                "title": "Software Engineer Intern",
                "location": "Remote",
                "location_type": "remote",
                "url": f"https://example.com/job/{i}",
                "apply_url": f"https://example.com/apply/{i}",
                "description": "Test job description",
                "employment_type": "internship",
                "score": 0.8,
                "status": "new",
            })
        
        # Query with custom timeout
        results = self.db.fetch_all(
            "SELECT * FROM jobs WHERE score >= ?",
            (0.7,),
            timeout=5.0
        )
        
        assert len(results) == 5


class TestDatabaseTimeoutConfiguration:
    """Test database timeout configuration"""
    
    def test_pragma_settings_applied(self):
        """Test that PRAGMA settings are applied correctly"""
        test_db_path = "test_pragma.db"
        db = DatabaseManager(test_db_path)
        
        try:
            with db.get_connection() as conn:
                # Check foreign keys
                cursor = conn.execute("PRAGMA foreign_keys")
                assert cursor.fetchone()[0] == 1
                
                # Check journal mode
                cursor = conn.execute("PRAGMA journal_mode")
                assert cursor.fetchone()[0] == "wal"
                
                # Check synchronous mode
                cursor = conn.execute("PRAGMA synchronous")
                assert cursor.fetchone()[0] in (1, 2)  # NORMAL or FULL
        finally:
            Path(test_db_path).unlink(missing_ok=True)
    
    def test_timeout_parameter_validation(self):
        """Test timeout parameter validation"""
        test_db_path = "test_validation.db"
        db = DatabaseManager(test_db_path)
        
        try:
            # Test with None (should use default)
            with db.get_connection(timeout=None) as conn:
                cursor = conn.execute("PRAGMA busy_timeout")
                timeout = cursor.fetchone()[0]
                assert timeout == 30000
            
            # Test with zero (should work)
            with db.get_connection(timeout=0.0) as conn:
                cursor = conn.execute("PRAGMA busy_timeout")
                timeout = cursor.fetchone()[0]
                assert timeout == 0
            
            # Test with large value
            with db.get_connection(timeout=300.0) as conn:
                cursor = conn.execute("PRAGMA busy_timeout")
                timeout = cursor.fetchone()[0]
                assert timeout == 300000
        finally:
            Path(test_db_path).unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
