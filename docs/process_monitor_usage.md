# Process Monitor Usage Guide

## Overview

The ProcessMonitor provides timeout detection and stall prevention for long-running processes in the InternMailer system. It tracks process execution time, detects stalls (no progress updates), and enforces timeouts.

## Features

- **Timeout Detection**: Automatically detect when processes exceed their time limits
- **Stall Detection**: Identify processes that stop making progress
- **Progress Tracking**: Monitor progress with checkpoints for recovery
- **Background Monitoring**: Continuous monitoring in a separate thread
- **Process State Tracking**: Track status, elapsed time, and metadata

## Basic Usage

### 1. Using the Global Monitor

```python
from utils.process_monitor import get_process_monitor

# Get the global monitor instance
monitor = get_process_monitor()

# Start monitoring a process
monitor.start_monitoring(
    process_id='job_discovery',
    component='JobDiscovery',
    timeout=300,  # 5 minutes
    expected_duration=60  # Expected to take 1 minute
)

# Update progress during execution
monitor.record_progress('job_discovery', 0.5)

# Check for timeout
timeout_info = monitor.check_timeout('job_discovery')
if timeout_info:
    print(f"Process timed out: {timeout_info}")

# Complete the process
monitor.complete_process('job_discovery')
```

### 2. Using the Decorator

```python
from utils.process_monitor import monitor_process

@monitor_process('email_campaign', 'EmailSystem', timeout=600)
def send_email_campaign(contacts):
    """Send emails to all contacts"""
    for contact in contacts:
        send_email(contact)
    return len(contacts)

# The decorator automatically monitors the function
result = send_email_campaign(my_contacts)
```

### 3. Progress Tracking with Checkpoints

```python
monitor = get_process_monitor()

monitor.start_monitoring('data_processing', 'DataProcessor', timeout=300)

# Process data in batches
for i, batch in enumerate(batches):
    process_batch(batch)
    
    # Update progress with checkpoint for recovery
    progress = (i + 1) / len(batches)
    checkpoint = {
        'batch_number': i + 1,
        'items_processed': (i + 1) * batch_size,
        'last_item_id': batch[-1].id
    }
    monitor.record_progress('data_processing', progress, checkpoint)

monitor.complete_process('data_processing')
```

## Integration Examples

### Job Discovery Integration

```python
from utils.process_monitor import get_process_monitor
from utils.logger import get_logger

class JobDiscoveryEngine:
    def __init__(self):
        self.monitor = get_process_monitor()
        self.logger = get_logger('job_discovery')
    
    def discover_jobs(self, sources):
        """Discover jobs from multiple sources"""
        process_id = 'job_discovery'
        
        # Start monitoring
        self.monitor.start_monitoring(
            process_id=process_id,
            component='JobDiscovery',
            timeout=300,
            expected_duration=60,
            metadata={'source_count': len(sources)}
        )
        
        try:
            all_jobs = []
            
            for i, source in enumerate(sources):
                # Check for timeout
                if self.monitor.check_timeout(process_id):
                    self.logger.error("Job discovery timed out")
                    break
                
                # Fetch jobs from source
                jobs = self.fetch_from_source(source)
                all_jobs.extend(jobs)
                
                # Update progress
                progress = (i + 1) / len(sources)
                checkpoint = {
                    'current_source': source,
                    'sources_completed': i + 1,
                    'jobs_found': len(all_jobs)
                }
                self.monitor.record_progress(process_id, progress, checkpoint)
            
            # Complete successfully
            self.monitor.complete_process(process_id)
            return all_jobs
            
        except Exception as e:
            self.logger.error(f"Job discovery failed: {e}")
            self.monitor.complete_process(process_id, ProcessStatus.FAILED)
            raise
```

### Email Campaign Integration

```python
from utils.process_monitor import get_process_monitor, ProcessStatus
from utils.logger import get_logger

class EmailSystem:
    def __init__(self):
        self.monitor = get_process_monitor()
        self.logger = get_logger('email_system')
    
    def send_campaign(self, contacts, rate_limit=0.1):
        """Send email campaign with monitoring"""
        process_id = 'email_campaign'
        
        # Start monitoring
        self.monitor.start_monitoring(
            process_id=process_id,
            component='EmailSystem',
            timeout=600,  # 10 minutes
            expected_duration=len(contacts) * rate_limit,
            metadata={'total_emails': len(contacts)}
        )
        
        sent_count = 0
        failed_count = 0
        
        try:
            for i, contact in enumerate(contacts):
                # Check for timeout
                if self.monitor.check_timeout(process_id):
                    self.logger.error("Email campaign timed out")
                    break
                
                # Send email
                try:
                    self.send_email(contact)
                    sent_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to send to {contact.email}: {e}")
                    failed_count += 1
                
                # Update progress
                progress = (i + 1) / len(contacts)
                checkpoint = {
                    'emails_sent': sent_count,
                    'emails_failed': failed_count,
                    'current_email': contact.email
                }
                self.monitor.record_progress(process_id, progress, checkpoint)
                
                # Rate limiting
                time.sleep(rate_limit)
            
            # Complete
            self.monitor.complete_process(process_id)
            return {'sent': sent_count, 'failed': failed_count}
            
        except Exception as e:
            self.logger.error(f"Email campaign failed: {e}")
            self.monitor.complete_process(process_id, ProcessStatus.FAILED)
            raise
```

## Monitoring Active Processes

```python
from utils.process_monitor import get_process_monitor

monitor = get_process_monitor()

# Get all active processes
active_processes = monitor.get_active_processes()

for process in active_processes:
    print(f"Process: {process['process_id']}")
    print(f"  Component: {process['component']}")
    print(f"  Progress: {process['progress']:.1%}")
    print(f"  Elapsed: {process['elapsed_seconds']:.1f}s")
    print(f"  Timeout: {process['timeout']}s")
    print(f"  Time since update: {process['time_since_update']:.1f}s")
```

## Configuration

### Stall Threshold

The stall threshold determines how long a process can go without progress updates before being considered stalled:

```python
from utils.process_monitor import ProcessMonitor

# Create monitor with custom stall threshold
monitor = ProcessMonitor(stall_threshold=120)  # 2 minutes
```

### Process Timeouts

Set appropriate timeouts based on expected operation duration:

```python
# Quick operations
monitor.start_monitoring('config_load', 'Config', timeout=10)

# Medium operations
monitor.start_monitoring('job_discovery', 'JobDiscovery', timeout=300)

# Long operations
monitor.start_monitoring('email_campaign', 'EmailSystem', timeout=3600)
```

## Best Practices

1. **Always call `complete_process()`**: Ensure processes are marked as complete or failed
2. **Update progress regularly**: Call `record_progress()` at least every 30-60 seconds
3. **Use checkpoints**: Include recovery information in checkpoints
4. **Check for timeouts**: Periodically check `check_timeout()` in long loops
5. **Set realistic timeouts**: Base timeouts on expected duration + buffer
6. **Use descriptive process IDs**: Make process IDs unique and meaningful
7. **Include metadata**: Add context information in metadata for debugging

## Error Handling

```python
from utils.process_monitor import get_process_monitor, ProcessStatus

monitor = get_process_monitor()

try:
    monitor.start_monitoring('risky_operation', 'Component', timeout=60)
    
    # Perform operation
    result = perform_risky_operation()
    
    # Check if timed out during operation
    if monitor.check_timeout('risky_operation'):
        # Handle timeout
        recover_from_timeout()
    
    monitor.complete_process('risky_operation')
    
except Exception as e:
    # Mark as failed
    monitor.complete_process('risky_operation', ProcessStatus.FAILED)
    raise
```

## Logging

The ProcessMonitor automatically logs:
- Process start/stop events
- Timeout detections
- Stall detections
- Progress updates (at DEBUG level)

Logs are written to `logs/process_monitor.log`.

## Thread Safety

The ProcessMonitor is thread-safe and can be used from multiple threads:

```python
import threading
from utils.process_monitor import get_process_monitor

monitor = get_process_monitor()

def worker(worker_id):
    process_id = f'worker_{worker_id}'
    monitor.start_monitoring(process_id, 'Worker', timeout=60)
    
    # Do work
    for i in range(10):
        time.sleep(0.1)
        monitor.record_progress(process_id, (i + 1) / 10)
    
    monitor.complete_process(process_id)

# Start multiple workers
threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```
