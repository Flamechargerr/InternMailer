# Professor Parsing System: Workers and Extraction Techniques

## Overview
The professor parsing system uses a sophisticated multi-layered approach with parallel workers and advanced extraction techniques to gather and process professor data from various sources.

## 1. Multi-Worker Architecture

### Enhanced Professor Scraper (`src/enhanced_professor_scraper.py`)
- **Max Workers**: 800 concurrent workers for ultra-high performance
- **Connection Pooling**: 200 pool connections, 800 max pool size
- **Threading**: Uses `ThreadPoolExecutor` for parallel processing
- **Session Management**: Optimized HTTP session with retry strategies

### Key Worker Features:
```python
# Ultra-optimized session setup
adapter = HTTPAdapter(
    max_retries=retry_strategy,
    pool_connections=200,  # Massive connection pool
    pool_maxsize=800,     # Match max_workers for optimal performance
    pool_block=False      # Non-blocking pool
)
```

## 2. Data Extraction Techniques

### CSV Parsing Strategy
- **Targeted Files**: Focuses on CSRankings CSV files (`csrankings-*.csv`)
- **Column Detection**: Automatically identifies professor-relevant columns
- **Data Normalization**: Standardizes column names across different sources

### Email Extraction Methods (Multiple Strategies)

#### Strategy 1: Mailto Links (Most Reliable)
```python
mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
for link in mailto_links:
    email = link['href'].replace('mailto:', '').split('?')[0].strip()
```

#### Strategy 2: Enhanced CSS Selectors
```python
email_selectors = [
    '[href*="@"]',  # Any link containing @
    '.email', '.contact-email', '.faculty-email', '.prof-email',
    '#email', '#contact-email', '#faculty-email', '#prof-email',
    '[class*="email"]', '[id*="email"]', '[class*="contact"]',
    '.contact-info', '.contact', '.profile-contact', '.personal-info',
    '.faculty-info', '.staff-info', '.researcher-info'
]
```

#### Strategy 3: Advanced Text Parsing
- **Regex Patterns**: Multiple email regex patterns for different formats
- **Obfuscated Email Detection**: Handles JavaScript-obfuscated emails
- **Text Mining**: Extracts emails from plain text content

#### Strategy 4: JavaScript Email Extraction
```python
def _extract_js_email(self, html_source: str) -> str:
    # Extracts emails from JavaScript variables
    js_patterns = [
        r'var\s+email\s*=\s*["\']([^"\']+@[^"\']+)["\']',
        r'email\s*:\s*["\']([^"\']+@[^"\']+)["\']',
        r'contact\s*:\s*["\']([^"\']+@[^"\']+)["\']'
    ]
```

## 3. Targeted Scraping System (`targeted_professor_scraper.py`)

### File Prioritization Algorithm
```python
def get_csv_files_by_priority(self):
    # High Priority: Files with professor keywords
    if any(keyword in file.lower() for keyword in ['professor', 'scraped', 'enriched', 'discovered']):
        csv_files.insert(0, file_path)
    # Medium Priority: CSRankings files
    elif any(keyword in file.lower() for keyword in ['csrankings']):
        csv_files.append(file_path)
    # Low Priority: Other CSV files
    else:
        csv_files.append(file_path)
```

### Caching Mechanism
- **JSON Cache**: `targeted_scraping_cache.json` tracks processed files
- **Skip Logic**: Automatically skips already processed CSV files
- **Progress Tracking**: Maintains scraping progress across sessions

## 4. Data Quality Assurance

### Deduplication Process
```python
def remove_duplicates(self, professors):
    # Remove duplicates based on email and name
    seen_emails = set()
    seen_names = set()
    unique_professors = []
    
    for prof in professors:
        email = prof.get('email', '').lower().strip()
        name = prof.get('name', '').lower().strip()
        
        if email and email not in seen_emails:
            seen_emails.add(email)
            unique_professors.append(prof)
        elif name and name not in seen_names:
            seen_names.add(name)
            unique_professors.append(prof)
```

### Validation Checks
- **Email Format Validation**: Ensures proper email structure
- **Data Completeness**: Checks for required fields (name, affiliation, email)
- **Source Tracking**: Records which file each professor came from

## 5. Contact Tracking System

### Professor Tracker (`src/professor_tracker.py`)
- **Already Emailed Tracking**: Prevents duplicate emails
- **Cooldown Periods**: Respects time-based restrictions
- **Status Management**: Tracks email delivery and engagement

### Duplicate Prevention Service (`src/email_engine.py`)
```python
def is_duplicate(self, recipient: str, campaign_id: str, subject: str) -> bool:
    # Hash-based duplicate detection
    duplicate_hash = self.generate_hash(recipient, campaign_id, subject)
    
    # Check database for existing emails
    existing = self.db_session.query(Email).filter(
        Email.campaign_id == campaign_id,
        Email.contact_id.in_(...),
        Email.status.in_([EmailStatus.SENT.value, EmailStatus.DELIVERED.value])
    ).first()
```

## 6. Performance Optimizations

### Parallel Processing
- **Concurrent Scraping**: 800 workers process multiple professors simultaneously
- **Connection Reuse**: Optimized HTTP session with connection pooling
- **Timeout Management**: Ultra-fast timeouts (8 seconds) for maximum throughput

### Memory Management
- **Batch Processing**: Processes professors in manageable batches
- **Cache Management**: Efficient JSON-based caching system
- **Resource Cleanup**: Proper session and connection cleanup

## 7. Error Handling and Resilience

### Retry Strategies
```python
retry_strategy = Retry(
    total=1,  # Single retry for maximum speed
    backoff_factor=0.3,  # Ultra-fast backoff
    status_forcelist=[429, 500, 502, 503, 504],
)
```

### Graceful Degradation
- **Fallback Parsers**: Multiple extraction strategies ensure data capture
- **Error Logging**: Comprehensive error tracking and reporting
- **Partial Success Handling**: Continues processing even if some extractions fail

## 8. Integration Points

### Database Integration
- **SQLAlchemy Models**: Structured data storage
- **Email Tracking**: Complete email lifecycle management
- **Campaign Management**: Organized outreach campaigns

### File System Integration
- **CSV Processing**: Handles multiple CSV formats and structures
- **Cache Persistence**: Maintains progress across sessions
- **Output Generation**: Creates timestamped result files

## Summary
The professor parsing system combines:
- **800 concurrent workers** for maximum throughput
- **Multiple extraction strategies** for comprehensive data capture
- **Intelligent caching** to avoid redundant processing
- **Advanced deduplication** for data quality
- **Contact tracking** to prevent duplicate emails
- **Performance optimizations** for large-scale processing

This creates a robust, scalable system capable of processing thousands of professors efficiently while maintaining data quality and preventing duplicate outreach. 