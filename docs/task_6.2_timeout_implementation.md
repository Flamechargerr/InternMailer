# Task 6.2: Database and HTTP Timeout Implementation

## Overview

Implemented comprehensive timeout handling and retry logic for database operations and HTTP requests to prevent processing loops and improve system reliability.

## Implementation Summary

### 1. HTTP Client with Retry Logic (`utils/http_client.py`)

Created a robust HTTP client with:

**Features:**
- Configurable timeouts (default: 15 seconds)
- Exponential backoff retry logic (default: 3 retries)
- Connection pooling for efficiency
- Automatic retry on transient errors (timeouts, connection errors, 5xx status codes)
- Rate limiting support (429 status code handling)
- Comprehensive error handling and logging

**Configuration:**
```python
HTTPConfig(
    timeout=15.0,              # Request timeout in seconds
    max_retries=3,             # Maximum retry attempts
    backoff_factor=0.5,        # Exponential backoff multiplier
    retry_statuses=(408, 429, 500, 502, 503, 504),  # Status codes to retry
    pool_connections=10,       # Connection pool size
    pool_maxsize=20,          # Maximum pool size
)
```

**Retry Strategy:**
- Exponential backoff: `delay = backoff_factor * (2 ^ (attempt - 1))`
- Example with backoff_factor=0.5:
  - Attempt 1: 0.5 seconds
  - Attempt 2: 1.0 seconds
  - Attempt 3: 2.0 seconds

**Usage:**
```python
from utils.http_client import get_http_client, HTTPConfig

# Use global client with defaults
client = get_http_client()
response = client.get("https://api.example.com/data")

# Use custom configuration
config = HTTPConfig(timeout=30.0, max_retries=5)
client = get_http_client(config)
data = client.get_json("https://api.example.com/data")
```

### 2. Database Query Timeouts (`core/database_manager.py`)

Enhanced database manager with query-level timeout support:

**Features:**
- Configurable timeout for each database operation
- Default timeout: 30 seconds
- PRAGMA busy_timeout for query-level control
- Timeout parameter propagation through all database methods

**Updated Methods:**
- `get_connection(timeout=None)` - Connection with custom timeout
- `execute(query, params, timeout=None)` - Execute with timeout
- `fetch_one(query, params, timeout=None)` - Fetch single row with timeout
- `fetch_all(query, params, timeout=None)` - Fetch all rows with timeout
- `insert(table, data, timeout=None)` - Insert with timeout
- `update(table, data, where, where_params, timeout=None)` - Update with timeout
- `delete(table, where, where_params, timeout=None)` - Delete with timeout
- `execute_many(query, params_list, timeout=None)` - Batch execute with timeout

**Usage:**
```python
from core.database_manager import get_job_discovery_db

db = get_job_discovery_db()

# Use default timeout (30 seconds)
jobs = db.fetch_all("SELECT * FROM jobs WHERE score >= ?", (0.7,))

# Use custom timeout (5 seconds)
jobs = db.fetch_all(
    "SELECT * FROM jobs WHERE score >= ?",
    (0.7,),
    timeout=5.0
)
```

### 3. Job Discovery Integration

Updated job discovery to use the new HTTP client:

**Changes:**
- `core/job_discovery.py`: Integrated HTTPClient for all API calls
- `core/job_discovery.py`: Updated network connectivity checks
- All HTTP requests now benefit from retry logic and exponential backoff

**Benefits:**
- Automatic retry on transient failures
- Better handling of rate limiting
- Improved reliability for job source APIs
- Connection pooling reduces overhead

## Testing

### HTTP Retry Tests (`tests/test_http_retry.py`)

**Test Coverage:**
- ✅ Default and custom HTTP configuration
- ✅ Successful GET/POST requests
- ✅ Retry on timeout errors
- ✅ Retry on connection errors
- ✅ Retry on server errors (5xx)
- ✅ Max retries exhausted behavior
- ✅ Exponential backoff calculation
- ✅ JSON response handling
- ✅ Error handling (returns empty dict)
- ✅ Context manager support
- ✅ Custom timeout parameters
- ✅ Global client singleton pattern
- ✅ Rate limiting (429) handling
- ✅ No retry on client errors (4xx)

**Results:** 20/20 tests passed ✅

### Database Timeout Tests (`tests/test_database_timeouts.py`)

**Test Coverage:**
- ✅ Default connection timeout (30 seconds)
- ✅ Custom connection timeout
- ✅ Execute with default/custom timeout
- ✅ Fetch operations with timeout
- ✅ Insert/Update/Delete with timeout
- ✅ Execute many with timeout
- ✅ Timeout on locked database
- ✅ Connection pool timeout isolation
- ✅ Job discovery database operations
- ✅ PRAGMA settings validation
- ✅ Timeout parameter validation

**Results:** 16/16 tests passed ✅

## Requirements Validation

### Requirement 6.3: Database Operation Timeouts ✅
- Implemented query-level timeouts for all database operations
- Default timeout: 30 seconds
- Configurable per-operation timeout
- PRAGMA busy_timeout for SQLite timeout handling

### Requirement 6.4: HTTP Retry Logic with Exponential Backoff ✅
- Implemented HTTPClient with configurable retry logic
- Exponential backoff: `delay = backoff_factor * (2 ^ (attempt - 1))`
- Automatic retry on transient errors (timeouts, connection errors, 5xx)
- Rate limiting support (429 status code)

### Requirement 6.6: Connection Pooling and Resource Management ✅
- HTTP connection pooling (default: 10 connections, max: 20)
- Database connection management with context managers
- Proper resource cleanup on errors
- Thread-safe connection handling

## Performance Impact

### HTTP Client
- **Connection Pooling:** Reduces overhead by reusing connections
- **Retry Logic:** Improves reliability without manual intervention
- **Exponential Backoff:** Prevents overwhelming failing services
- **Timeout Control:** Prevents indefinite hangs

### Database Operations
- **Query Timeouts:** Prevents long-running queries from blocking
- **Connection Pooling:** Efficient resource usage
- **WAL Mode:** Better concurrency for SQLite
- **Busy Timeout:** Handles concurrent access gracefully

## Usage Examples

### HTTP Client Example

```python
from utils.http_client import get_http_client, HTTPConfig

# Basic usage with defaults
client = get_http_client()
response = client.get("https://api.example.com/jobs")
if response.status_code == 200:
    jobs = response.json()

# Custom configuration for specific needs
config = HTTPConfig(
    timeout=30.0,        # Longer timeout for slow APIs
    max_retries=5,       # More retries for unreliable APIs
    backoff_factor=1.0,  # Longer backoff between retries
)
client = get_http_client(config)

# Convenient JSON fetching
data = client.get_json("https://api.example.com/data")
# Returns empty dict {} on error
```

### Database Timeout Example

```python
from core.database_manager import get_job_discovery_db

db = get_job_discovery_db()

# Quick query with short timeout
try:
    job = db.fetch_one(
        "SELECT * FROM jobs WHERE id = ?",
        (job_id,),
        timeout=2.0  # 2 second timeout
    )
except sqlite3.OperationalError as e:
    print(f"Query timeout: {e}")

# Long-running query with extended timeout
jobs = db.fetch_all(
    "SELECT * FROM jobs WHERE score >= ? ORDER BY score DESC",
    (0.7,),
    timeout=60.0  # 60 second timeout for complex query
)

# Batch operations with timeout
db.execute_many(
    "INSERT INTO jobs (source, company, title) VALUES (?, ?, ?)",
    job_data_list,
    timeout=30.0
)
```

## Migration Notes

### For Existing Code

The changes are **backward compatible**. Existing code will continue to work with default timeouts:

```python
# Old code - still works with default 30s timeout
db.execute("SELECT * FROM jobs")

# New code - can specify custom timeout
db.execute("SELECT * FROM jobs", timeout=5.0)
```

### For HTTP Requests

Replace direct `requests` usage with the new HTTP client:

```python
# Old code
import requests
response = requests.get(url, timeout=15)

# New code - with retry logic
from utils.http_client import get_http_client
client = get_http_client()
response = client.get(url)  # Automatic retries on failure
```

## Monitoring and Debugging

### HTTP Client Logging

The HTTP client logs retry attempts and errors:

```
DEBUG: Retry attempt 1/3 for GET https://api.example.com/jobs
WARNING: Request returned 503, retrying...
DEBUG: Backing off for 0.50 seconds
ERROR: Request failed after 3 retries
```

### Database Timeout Logging

Database operations log timeout errors:

```python
try:
    result = db.execute(query, params, timeout=5.0)
except sqlite3.OperationalError as e:
    logger.error(f"Database query timeout: {e}")
```

## Future Enhancements

1. **Circuit Breaker Pattern:** Temporarily disable failing endpoints
2. **Metrics Collection:** Track retry rates and timeout frequencies
3. **Adaptive Timeouts:** Adjust timeouts based on historical performance
4. **Request Deduplication:** Prevent duplicate requests during retries
5. **Distributed Tracing:** Track requests across service boundaries

## Conclusion

Task 6.2 successfully implemented:
- ✅ Query timeouts for database operations
- ✅ HTTP retry logic with exponential backoff
- ✅ Connection pooling and resource management
- ✅ Comprehensive test coverage (36/36 tests passing)
- ✅ Backward compatible implementation
- ✅ Production-ready error handling

The implementation significantly improves system reliability by preventing indefinite hangs and automatically recovering from transient failures.
