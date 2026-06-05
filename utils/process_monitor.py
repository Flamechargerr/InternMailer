"""
Process Monitor - Timeout detection and stall prevention
Tracks long-running processes and detects stalls
"""

import time
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Callable, Any
from enum import Enum

from utils.logger import get_logger


class ProcessStatus(Enum):
    """Process execution status"""
    RUNNING = "running"
    COMPLETED = "completed"
    STALLED = "stalled"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ProcessState:
    """State information for a monitored process"""
    process_id: str
    component: str
    start_time: datetime
    last_update: datetime
    expected_duration: int  # seconds
    timeout: int  # seconds
    progress: float = 0.0  # 0.0-1.0
    status: ProcessStatus = ProcessStatus.RUNNING
    checkpoint: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProcessMonitor:
    """
    Monitor long-running processes for timeouts and stalls
    
    Usage:
        monitor = ProcessMonitor()
        
        # Start monitoring a process
        monitor.start_monitoring('job_discovery', 'JobDiscovery', timeout=300)
        
        # Update progress
        monitor.record_progress('job_discovery', 0.5)
        
        # Check for timeout
        if monitor.check_timeout('job_discovery'):
            print("Process timed out!")
        
        # Complete process
        monitor.complete_process('job_discovery')
    """
    
    def __init__(self, stall_threshold: int = 60):
        """
        Initialize process monitor
        
        Args:
            stall_threshold: Seconds without progress update to consider stalled
        """
        self.stall_threshold = stall_threshold
        self._processes: Dict[str, ProcessState] = {}
        self._lock = threading.Lock()
        self.logger = get_logger('process_monitor')
        
        # Start background monitoring thread
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def start_monitoring(
        self,
        process_id: str,
        component: str,
        timeout: int,
        expected_duration: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Start monitoring a process
        
        Args:
            process_id: Unique identifier for the process
            component: Component name (e.g., 'JobDiscovery', 'EmailSystem')
            timeout: Maximum allowed duration in seconds
            expected_duration: Expected duration in seconds (defaults to timeout)
            metadata: Additional metadata about the process
        """
        with self._lock:
            now = datetime.now()
            
            if process_id in self._processes:
                self.logger.warning(
                    f"Process {process_id} already being monitored, restarting"
                )
            
            self._processes[process_id] = ProcessState(
                process_id=process_id,
                component=component,
                start_time=now,
                last_update=now,
                expected_duration=expected_duration or timeout,
                timeout=timeout,
                progress=0.0,
                status=ProcessStatus.RUNNING,
                checkpoint=None,
                metadata=metadata or {}
            )
            
            self.logger.info(
                f"Started monitoring process {process_id} "
                f"(component={component}, timeout={timeout}s)"
            )
    
    def record_progress(
        self,
        process_id: str,
        progress: float,
        checkpoint: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record progress for a monitored process
        
        Args:
            process_id: Process identifier
            progress: Progress value between 0.0 and 1.0
            checkpoint: Optional checkpoint data for recovery
        """
        with self._lock:
            if process_id not in self._processes:
                self.logger.warning(
                    f"Attempted to record progress for unknown process {process_id}"
                )
                return
            
            process = self._processes[process_id]
            process.progress = max(0.0, min(1.0, progress))
            process.last_update = datetime.now()
            
            if checkpoint:
                process.checkpoint = checkpoint
            
            self.logger.debug(
                f"Process {process_id} progress: {progress:.1%}"
            )
    
    def check_timeout(self, process_id: str) -> Optional[Dict[str, Any]]:
        """
        Check if a process has timed out
        
        Args:
            process_id: Process identifier
            
        Returns:
            Timeout information if timed out, None otherwise
        """
        with self._lock:
            if process_id not in self._processes:
                return None
            
            process = self._processes[process_id]
            elapsed = (datetime.now() - process.start_time).total_seconds()
            
            if elapsed > process.timeout:
                process.status = ProcessStatus.TIMEOUT
                
                timeout_info = {
                    'process_id': process_id,
                    'component': process.component,
                    'elapsed_seconds': elapsed,
                    'timeout_seconds': process.timeout,
                    'progress': process.progress,
                    'checkpoint': process.checkpoint
                }
                
                self.logger.warning(
                    f"Process {process_id} timed out after {elapsed:.1f}s "
                    f"(timeout={process.timeout}s, progress={process.progress:.1%})"
                )
                
                return timeout_info
            
            return None
    
    def check_stall(self, process_id: str) -> Optional[Dict[str, Any]]:
        """
        Check if a process has stalled (no progress updates)
        
        Args:
            process_id: Process identifier
            
        Returns:
            Stall information if stalled, None otherwise
        """
        with self._lock:
            if process_id not in self._processes:
                return None
            
            process = self._processes[process_id]
            
            if process.status != ProcessStatus.RUNNING:
                return None
            
            time_since_update = (datetime.now() - process.last_update).total_seconds()
            
            if time_since_update > self.stall_threshold:
                process.status = ProcessStatus.STALLED
                
                stall_info = {
                    'process_id': process_id,
                    'component': process.component,
                    'seconds_since_update': time_since_update,
                    'stall_threshold': self.stall_threshold,
                    'progress': process.progress,
                    'checkpoint': process.checkpoint
                }
                
                self.logger.warning(
                    f"Process {process_id} appears stalled "
                    f"(no update for {time_since_update:.1f}s, threshold={self.stall_threshold}s)"
                )
                
                return stall_info
            
            return None
    
    def complete_process(
        self,
        process_id: str,
        status: ProcessStatus = ProcessStatus.COMPLETED
    ) -> None:
        """
        Mark a process as completed
        
        Args:
            process_id: Process identifier
            status: Final status (COMPLETED or FAILED)
        """
        with self._lock:
            if process_id not in self._processes:
                self.logger.warning(
                    f"Attempted to complete unknown process {process_id}"
                )
                return
            
            process = self._processes[process_id]
            process.status = status
            process.progress = 1.0 if status == ProcessStatus.COMPLETED else process.progress
            
            elapsed = (datetime.now() - process.start_time).total_seconds()
            
            self.logger.info(
                f"Process {process_id} {status.value} after {elapsed:.1f}s "
                f"(expected={process.expected_duration}s)"
            )
            
            # Remove from active monitoring after a delay
            # Keep for a short time for status queries
            threading.Timer(60.0, self._cleanup_process, args=[process_id]).start()
    
    def get_active_processes(self) -> list[Dict[str, Any]]:
        """
        Get information about all active processes
        
        Returns:
            List of process information dictionaries
        """
        with self._lock:
            active = []
            
            for process_id, process in self._processes.items():
                if process.status == ProcessStatus.RUNNING:
                    elapsed = (datetime.now() - process.start_time).total_seconds()
                    time_since_update = (datetime.now() - process.last_update).total_seconds()
                    
                    active.append({
                        'process_id': process_id,
                        'component': process.component,
                        'status': process.status.value,
                        'progress': process.progress,
                        'elapsed_seconds': elapsed,
                        'expected_duration': process.expected_duration,
                        'timeout': process.timeout,
                        'time_since_update': time_since_update,
                        'metadata': process.metadata
                    })
            
            return active
    
    def get_process_info(self, process_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific process
        
        Args:
            process_id: Process identifier
            
        Returns:
            Process information dictionary or None if not found
        """
        with self._lock:
            if process_id not in self._processes:
                return None
            
            process = self._processes[process_id]
            elapsed = (datetime.now() - process.start_time).total_seconds()
            time_since_update = (datetime.now() - process.last_update).total_seconds()
            
            return {
                'process_id': process_id,
                'component': process.component,
                'status': process.status.value,
                'progress': process.progress,
                'elapsed_seconds': elapsed,
                'expected_duration': process.expected_duration,
                'timeout': process.timeout,
                'time_since_update': time_since_update,
                'start_time': process.start_time.isoformat(),
                'last_update': process.last_update.isoformat(),
                'checkpoint': process.checkpoint,
                'metadata': process.metadata
            }
    
    def _monitor_loop(self) -> None:
        """Background monitoring loop to detect timeouts and stalls"""
        while self._monitoring:
            try:
                with self._lock:
                    process_ids = list(self._processes.keys())
                
                for process_id in process_ids:
                    # Check for timeout
                    timeout_info = self.check_timeout(process_id)
                    if timeout_info:
                        self.logger.error(
                            f"TIMEOUT DETECTED: {timeout_info}"
                        )
                    
                    # Check for stall
                    stall_info = self.check_stall(process_id)
                    if stall_info:
                        self.logger.warning(
                            f"STALL DETECTED: {stall_info}"
                        )
                
                # Sleep before next check
                time.sleep(10)
                
            except Exception as e:
                self.logger.error(
                    f"Error in monitoring loop: {str(e)}",
                    exc_info=True
                )
                time.sleep(10)
    
    def _cleanup_process(self, process_id: str) -> None:
        """Remove a completed process from monitoring"""
        with self._lock:
            if process_id in self._processes:
                del self._processes[process_id]
                self.logger.debug(f"Cleaned up process {process_id}")
    
    def stop_monitoring(self) -> None:
        """Stop the background monitoring thread"""
        self._monitoring = False
        if self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)
        self.logger.info("Process monitoring stopped")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_monitoring()


# Global process monitor instance
_global_monitor: Optional[ProcessMonitor] = None
_monitor_lock = threading.Lock()


def get_process_monitor(stall_threshold: int = 60) -> ProcessMonitor:
    """
    Get the global process monitor instance
    
    Args:
        stall_threshold: Seconds without progress to consider stalled
        
    Returns:
        ProcessMonitor instance
    """
    global _global_monitor
    
    with _monitor_lock:
        if _global_monitor is None:
            _global_monitor = ProcessMonitor(stall_threshold=stall_threshold)
        return _global_monitor


def monitor_process(
    process_id: str,
    component: str,
    timeout: int,
    expected_duration: Optional[int] = None
):
    """
    Decorator to automatically monitor a function execution
    
    Usage:
        @monitor_process('job_discovery', 'JobDiscovery', timeout=300)
        def discover_jobs():
            # Long-running operation
            pass
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            monitor = get_process_monitor()
            
            # Start monitoring
            monitor.start_monitoring(
                process_id=process_id,
                component=component,
                timeout=timeout,
                expected_duration=expected_duration,
                metadata={'function': func.__name__}
            )
            
            try:
                result = func(*args, **kwargs)
                monitor.complete_process(process_id, ProcessStatus.COMPLETED)
                return result
            except Exception as e:
                monitor.complete_process(process_id, ProcessStatus.FAILED)
                raise
        
        return wrapper
    return decorator
