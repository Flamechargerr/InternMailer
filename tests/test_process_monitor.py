"""
Tests for Process Monitor
Tests timeout detection, stall detection, and process state tracking
"""

import pytest
import time
import threading
from datetime import datetime, timedelta

from utils.process_monitor import (
    ProcessMonitor,
    ProcessStatus,
    ProcessState,
    get_process_monitor,
    monitor_process
)


class TestProcessMonitor:
    """Unit tests for ProcessMonitor"""
    
    def test_start_monitoring(self):
        """Test starting process monitoring"""
        monitor = ProcessMonitor(stall_threshold=30)
        
        monitor.start_monitoring(
            process_id='test_process',
            component='TestComponent',
            timeout=60,
            expected_duration=30,
            metadata={'test': 'data'}
        )
        
        info = monitor.get_process_info('test_process')
        assert info is not None
        assert info['process_id'] == 'test_process'
        assert info['component'] == 'TestComponent'
        assert info['status'] == ProcessStatus.RUNNING.value
        assert info['timeout'] == 60
        assert info['expected_duration'] == 30
        assert info['progress'] == 0.0
        assert info['metadata']['test'] == 'data'
        
        monitor.stop_monitoring()
    
    def test_record_progress(self):
        """Test recording process progress"""
        monitor = ProcessMonitor(stall_threshold=30)
        
        monitor.start_monitoring('test_process', 'TestComponent', timeout=60)
        
        # Record progress
        monitor.record_progress('test_process', 0.5)
        
        info = monitor.get_process_info('test_process')
        assert info['progress'] == 0.5
        
        # Record more progress with checkpoint
        checkpoint = {'step': 'processing', 'items': 50}
        monitor.record_progress('test_process', 0.75, checkpoint=checkpoint)
        
        info = monitor.get_process_info('test_process')
        assert info['progress'] == 0.75
        assert info['checkpoint'] == checkpoint
        
        monitor.stop_monitoring()
    
    def test_progress_bounds(self):
        """Test progress is bounded between 0.0 and 1.0"""
        monitor = ProcessMonitor(stall_threshold=30)
        
        monitor.start_monitoring('test_process', 'TestComponent', timeout=60)
        
        # Test upper bound
        monitor.record_progress('test_process', 1.5)
        info = monitor.get_process_info('test_process')
        assert info['progress'] == 1.0
        
        # Test lower bound
        monitor.record_progress('test_process', -0.5)
        info = monitor.get_process_info('test_process')
        assert info['progress'] == 0.0
        
        monitor.stop_monitoring()
    
    def test_timeout_detection(self):
        """Test timeout detection for long-running processes"""
        monitor = ProcessMonitor(stall_threshold=30)
        
        # Start process with 1 second timeout
        monitor.start_monitoring('test_process', 'TestComponent', timeout=1)
        
        # Wait for timeout
        time.sleep(1.5)
        
        # Check timeout
        timeout_info = monitor.check_timeout('test_process')
        assert timeout_info is not None
        assert timeout_info['process_id'] == 'test_process'
        assert timeout_info['elapsed_seconds'] >= 1.0
        assert timeout_info['timeout_seconds'] == 1
        
        # Verify status changed
        info = monitor.get_process_info('test_process')
        assert info['status'] == ProcessStatus.TIMEOUT.value
        
        monitor.stop_monitoring()
    
    def test_no_timeout_before_limit(self):
        """Test that timeout is not detected before limit"""
        monitor = ProcessMonitor(stall_threshold=30)
        
        # Start process with 10 second timeout
        monitor.start_monitoring('test_process', 'TestComponent', timeout=10)
        
        # Check immediately - should not timeout
        timeout_info = monitor.check_timeout('test_process')
        assert timeout_info is None
        
        info = monitor.get_process_info('test_process')
        assert info['status'] == ProcessStatus.RUNNING.value
        
        monitor.stop_monitoring()
    
    def test_stall_detection(self):
        """Test stall detection when no progress updates"""
        monitor = ProcessMonitor(stall_threshold=1)  # 1 second threshold
        
        monitor.start_monitoring('test_process', 'TestComponent', timeout=60)
        
        # Wait for stall threshold
        time.sleep(1.5)
        
        # Check for stall
        stall_info = monitor.check_stall('test_process')
        assert stall_info is not None
        assert stall_info['process_id'] == 'test_process'
        assert stall_info['seconds_since_update'] >= 1.0
        assert stall_info['stall_threshold'] == 1
        
        # Verify status changed
        info = monitor.get_process_info('test_process')
        assert info['status'] == ProcessStatus.STALLED.value
        
        monitor.stop_monitoring()
    
    def test_no_stall_with_progress_updates(self):
        """Test that stall is not detected with regular progress updates"""
        monitor = ProcessMonitor(stall_threshold=2)
        
        monitor.start_monitoring('test_process', 'TestComponent', timeout=60)
        
        # Update progress regularly
        for i in range(3):
            time.sleep(0.5)
            monitor.record_progress('test_process', i * 0.3)
        
        # Should not be stalled
        stall_info = monitor.check_stall('test_process')
        assert stall_info is None
        
        info = monitor.get_process_info('test_process')
        assert info['status'] == ProcessStatus.RUNNING.value
        
        monitor.stop_monitoring()
    
    def test_complete_process(self):
        """Test completing a process"""
        monitor = ProcessMonitor(stall_threshold=30)
        
        monitor.start_monitoring('test_process', 'TestComponent', timeout=60)
        
        # Complete the process
        monitor.complete_process('test_process', ProcessStatus.COMPLETED)
        
        info = monitor.get_process_info('test_process')
        assert info['status'] == ProcessStatus.COMPLETED.value
        assert info['progress'] == 1.0
        
        monitor.stop_monitoring()
    
    def test_fail_process(self):
        """Test marking a process as failed"""
        monitor = ProcessMonitor(stall_threshold=30)
        
        monitor.start_monitoring('test_process', 'TestComponent', timeout=60)
        monitor.record_progress('test_process', 0.3)
        
        # Fail the process
        monitor.complete_process('test_process', ProcessStatus.FAILED)
        
        info = monitor.get_process_info('test_process')
        assert info['status'] == ProcessStatus.FAILED.value
        assert info['progress'] == 0.3  # Progress preserved
        
        monitor.stop_monitoring()
    
    def test_get_active_processes(self):
        """Test getting list of active processes"""
        monitor = ProcessMonitor(stall_threshold=30)
        
        # Start multiple processes
        monitor.start_monitoring('process1', 'Component1', timeout=60)
        monitor.start_monitoring('process2', 'Component2', timeout=120)
        monitor.start_monitoring('process3', 'Component3', timeout=90)
        
        # Complete one process
        monitor.complete_process('process2', ProcessStatus.COMPLETED)
        
        # Get active processes
        active = monitor.get_active_processes()
        assert len(active) == 2
        
        process_ids = [p['process_id'] for p in active]
        assert 'process1' in process_ids
        assert 'process3' in process_ids
        assert 'process2' not in process_ids
        
        monitor.stop_monitoring()
    
    def test_unknown_process_handling(self):
        """Test handling of unknown process IDs"""
        monitor = ProcessMonitor(stall_threshold=30)
        
        # Try to get info for unknown process
        info = monitor.get_process_info('unknown_process')
        assert info is None
        
        # Try to record progress for unknown process (should not crash)
        monitor.record_progress('unknown_process', 0.5)
        
        # Try to check timeout for unknown process
        timeout_info = monitor.check_timeout('unknown_process')
        assert timeout_info is None
        
        # Try to check stall for unknown process
        stall_info = monitor.check_stall('unknown_process')
        assert stall_info is None
        
        monitor.stop_monitoring()
    
    def test_restart_monitoring(self):
        """Test restarting monitoring for same process ID"""
        monitor = ProcessMonitor(stall_threshold=30)
        
        # Start monitoring
        monitor.start_monitoring('test_process', 'Component1', timeout=60)
        monitor.record_progress('test_process', 0.5)
        
        # Restart monitoring (should reset state)
        monitor.start_monitoring('test_process', 'Component2', timeout=120)
        
        info = monitor.get_process_info('test_process')
        assert info['component'] == 'Component2'
        assert info['timeout'] == 120
        assert info['progress'] == 0.0  # Reset
        
        monitor.stop_monitoring()
    
    def test_checkpoint_recovery(self):
        """Test checkpoint data for recovery"""
        monitor = ProcessMonitor(stall_threshold=30)
        
        monitor.start_monitoring('test_process', 'TestComponent', timeout=60)
        
        # Record progress with checkpoints
        checkpoint1 = {'step': 'fetch', 'items_processed': 100}
        monitor.record_progress('test_process', 0.3, checkpoint=checkpoint1)
        
        checkpoint2 = {'step': 'process', 'items_processed': 200}
        monitor.record_progress('test_process', 0.6, checkpoint=checkpoint2)
        
        # Get latest checkpoint
        info = monitor.get_process_info('test_process')
        assert info['checkpoint'] == checkpoint2
        
        monitor.stop_monitoring()
    
    def test_concurrent_monitoring(self):
        """Test monitoring multiple processes concurrently"""
        monitor = ProcessMonitor(stall_threshold=30)
        
        def simulate_process(process_id: str, duration: float):
            monitor.start_monitoring(process_id, 'TestComponent', timeout=10)
            for i in range(5):
                time.sleep(duration / 5)
                monitor.record_progress(process_id, (i + 1) / 5)
            monitor.complete_process(process_id, ProcessStatus.COMPLETED)
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(
                target=simulate_process,
                args=(f'process_{i}', 0.5)
            )
            thread.start()
            threads.append(thread)
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All processes should be completed
        for i in range(3):
            info = monitor.get_process_info(f'process_{i}')
            if info:  # May be cleaned up already
                assert info['status'] == ProcessStatus.COMPLETED.value
        
        monitor.stop_monitoring()
    
    def test_monitor_process_decorator_success(self):
        """Test monitor_process decorator with successful execution"""
        monitor = get_process_monitor()
        
        @monitor_process('decorated_process', 'TestComponent', timeout=10)
        def successful_function():
            time.sleep(0.1)
            return 'success'
        
        result = successful_function()
        assert result == 'success'
        
        # Process should be completed
        info = monitor.get_process_info('decorated_process')
        if info:  # May be cleaned up
            assert info['status'] == ProcessStatus.COMPLETED.value
    
    def test_monitor_process_decorator_failure(self):
        """Test monitor_process decorator with failed execution"""
        monitor = get_process_monitor()
        
        @monitor_process('failing_process', 'TestComponent', timeout=10)
        def failing_function():
            time.sleep(0.1)
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            failing_function()
        
        # Process should be marked as failed
        info = monitor.get_process_info('failing_process')
        if info:  # May be cleaned up
            assert info['status'] == ProcessStatus.FAILED.value
    
    def test_elapsed_time_tracking(self):
        """Test that elapsed time is tracked correctly"""
        monitor = ProcessMonitor(stall_threshold=30)
        
        monitor.start_monitoring('test_process', 'TestComponent', timeout=60)
        
        # Wait a bit
        time.sleep(0.5)
        
        info = monitor.get_process_info('test_process')
        assert info['elapsed_seconds'] >= 0.5
        assert info['elapsed_seconds'] < 1.0
        
        monitor.stop_monitoring()
    
    def test_time_since_update_tracking(self):
        """Test that time since last update is tracked"""
        monitor = ProcessMonitor(stall_threshold=30)
        
        monitor.start_monitoring('test_process', 'TestComponent', timeout=60)
        
        # Wait and update
        time.sleep(0.3)
        monitor.record_progress('test_process', 0.5)
        
        # Check time since update (should be small)
        info = monitor.get_process_info('test_process')
        assert info['time_since_update'] < 0.1
        
        # Wait again
        time.sleep(0.5)
        
        # Check time since update (should be larger)
        info = monitor.get_process_info('test_process')
        assert info['time_since_update'] >= 0.5
        
        monitor.stop_monitoring()


class TestProcessMonitorIntegration:
    """Integration tests for ProcessMonitor"""
    
    def test_realistic_job_discovery_scenario(self):
        """Test monitoring a realistic job discovery process"""
        monitor = ProcessMonitor(stall_threshold=10)
        
        # Simulate job discovery
        monitor.start_monitoring(
            process_id='job_discovery',
            component='JobDiscovery',
            timeout=300,
            expected_duration=60,
            metadata={'sources': 5}
        )
        
        # Simulate progress through sources
        sources = ['remotive', 'arbeitnow', 'google', 'microsoft', 'amazon']
        for i, source in enumerate(sources):
            time.sleep(0.1)
            progress = (i + 1) / len(sources)
            checkpoint = {
                'current_source': source,
                'sources_completed': i + 1,
                'jobs_found': (i + 1) * 10
            }
            monitor.record_progress('job_discovery', progress, checkpoint)
        
        # Complete
        monitor.complete_process('job_discovery', ProcessStatus.COMPLETED)
        
        info = monitor.get_process_info('job_discovery')
        assert info['status'] == ProcessStatus.COMPLETED.value
        assert info['progress'] == 1.0
        assert info['checkpoint']['jobs_found'] == 50
        
        monitor.stop_monitoring()
    
    def test_realistic_email_campaign_scenario(self):
        """Test monitoring a realistic email campaign"""
        monitor = ProcessMonitor(stall_threshold=30)
        
        # Simulate email campaign
        monitor.start_monitoring(
            process_id='email_campaign',
            component='EmailSystem',
            timeout=600,
            expected_duration=300,
            metadata={'total_emails': 100}
        )
        
        # Simulate sending emails
        total_emails = 100
        for i in range(10):  # Send in batches
            time.sleep(0.1)
            emails_sent = (i + 1) * 10
            progress = emails_sent / total_emails
            checkpoint = {
                'emails_sent': emails_sent,
                'emails_failed': i,  # Some failures
                'current_batch': i + 1
            }
            monitor.record_progress('email_campaign', progress, checkpoint)
        
        # Complete
        monitor.complete_process('email_campaign', ProcessStatus.COMPLETED)
        
        info = monitor.get_process_info('email_campaign')
        assert info['status'] == ProcessStatus.COMPLETED.value
        assert info['checkpoint']['emails_sent'] == 100
        
        monitor.stop_monitoring()
    
    def test_timeout_recovery_scenario(self):
        """Test timeout detection and recovery"""
        monitor = ProcessMonitor(stall_threshold=30)
        
        # Start process with short timeout
        monitor.start_monitoring(
            process_id='slow_process',
            component='SlowComponent',
            timeout=1,
            metadata={'retry_count': 0}
        )
        
        # Simulate slow operation
        time.sleep(1.5)
        
        # Detect timeout
        timeout_info = monitor.check_timeout('slow_process')
        assert timeout_info is not None
        
        # Simulate recovery with retry
        monitor.start_monitoring(
            process_id='slow_process_retry',
            component='SlowComponent',
            timeout=5,
            metadata={'retry_count': 1}
        )
        
        # Complete successfully
        monitor.record_progress('slow_process_retry', 1.0)
        monitor.complete_process('slow_process_retry', ProcessStatus.COMPLETED)
        
        info = monitor.get_process_info('slow_process_retry')
        assert info['status'] == ProcessStatus.COMPLETED.value
        
        monitor.stop_monitoring()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
