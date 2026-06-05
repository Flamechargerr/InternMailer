"""
Backup Scheduler - Automated database backups
Schedules and manages automatic backups
"""

import os
import shutil
import gzip
import schedule
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Callable
import json

from core.database_manager import (
    get_email_tracking_db,
    get_inbox_monitor_db,
    get_daemon_status_db
)
from utils.logger import get_logger


class BackupScheduler:
    """
    Automated backup scheduler for databases and important files
    """
    
    def __init__(
        self,
        backup_dir: str = 'backups',
        retention_days: int = 30,
        compression: bool = True
    ):
        """
        Initialize backup scheduler
        
        Args:
            backup_dir: Directory to store backups
            retention_days: How long to keep backups
            compression: Whether to compress backups
        """
        self.backup_dir = Path(backup_dir)
        self.retention_days = retention_days
        self.compression = compression
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger('backup_scheduler')
        
        # Database paths to backup
        self.databases = [
            ('email_tracking', '/tmp/internmailer_db/email_tracking.db'),
            ('inbox_monitor', '/tmp/internmailer_db/inbox_monitor.db'),
            ('daemon_status', '/tmp/internmailer_db/daemon_status.db'),
            ('data_contacts', 'data/verified_professors.db')
        ]
        
        # File paths to backup
        self.files = [
            ('data', 'data'),
            ('campaign_results', '/tmp/internmailer_db'),
            ('logs', 'logs')
        ]
    
    def create_backup(self, name: Optional[str] = None) -> str:
        """
        Create a backup of all databases and files
        
        Args:
            name: Optional backup name (auto-generated if None)
            
        Returns:
            Path to backup directory
        """
        if not name:
            name = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        backup_path = self.backup_dir / f"backup_{name}"
        backup_path.mkdir(exist_ok=True)
        
        self.logger.info(f"Creating backup: {name}")
        
        # Backup databases
        db_dir = backup_path / 'databases'
        db_dir.mkdir(exist_ok=True)
        
        for db_name, db_path in self.databases:
            if Path(db_path).exists():
                dest = db_dir / f"{db_name}.db"
                if self.compression:
                    dest = dest.with_suffix('.db.gz')
                    self._compress_file(db_path, dest)
                else:
                    shutil.copy2(db_path, dest)
                self.logger.info(f"Backed up: {db_name}")
        
        # Backup files
        for file_name, file_path in self.files:
            if Path(file_path).exists():
                dest = backup_path / file_name
                if self.compression:
                    dest = dest.with_suffix(f'.{file_name}.tar.gz')
                    self._compress_directory(file_path, dest)
                else:
                    shutil.copytree(file_path, dest, dirs_exist_ok=True)
                self.logger.info(f"Backed up: {file_name}")
        
        # Create backup metadata
        metadata = {
            'name': name,
            'timestamp': datetime.now().isoformat(),
            'databases': len(self.databases),
            'files': len(self.files),
            'compression': self.compression
        }
        
        with open(backup_path / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.logger.info(f"Backup created: {backup_path}")
        
        return str(backup_path)
    
    def restore_backup(self, backup_name: str) -> bool:
        """
        Restore from a backup
        
        Args:
            backup_name: Name of backup to restore
            
        Returns:
            True if successful
        """
        backup_path = self.backup_dir / f"backup_{backup_name}"
        
        if not backup_path.exists():
            self.logger.error(f"Backup not found: {backup_name}")
            return False
        
        self.logger.warning(f"Restoring backup: {backup_name}")
        
        try:
            # Restore databases
            db_dir = backup_path / 'databases'
            if db_dir.exists():
                for db_name, db_path in self.databases:
                    src = db_dir / f"{db_name}.db"
                    if self.compression:
                        src = src.with_suffix('.db.gz')
                        if src.exists():
                            self._decompress_file(src, db_path)
                    else:
                        if src.exists():
                            shutil.copy2(src, db_path)
            
            self.logger.info(f"Backup restored: {backup_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore backup: {e}", exc_info=True)
            return False
    
    def _compress_file(self, src_path: str, dest_path: str):
        """Compress a file using gzip"""
        with open(src_path, 'rb') as f_in:
            with gzip.open(dest_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def _compress_directory(self, src_path: str, dest_path: str):
        """Compress a directory using tar and gzip"""
        import tarfile
        with tarfile.open(dest_path, 'w:gz') as tar:
            tar.add(src_path, arcname=Path(src_path).name)
    
    def _decompress_file(self, src_path: str, dest_path: str):
        """Decompress a file using gzip"""
        with gzip.open(src_path, 'rb') as f_in:
            with open(dest_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def _decompress_directory(self, src_path: str, dest_path: str):
        """Decompress a directory using tar and gzip"""
        import tarfile
        with tarfile.open(src_path, 'r:gz') as tar:
            tar.extractall(path=Path(dest_path).parent)
    
    def cleanup_old_backups(self):
        """Remove backups older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        removed_count = 0
        
        for backup_dir in self.backup_dir.glob('backup_*'):
            # Check modification time
            mtime = datetime.fromtimestamp(backup_dir.stat().st_mtime)
            
            if mtime < cutoff_date:
                try:
                    shutil.rmtree(backup_dir)
                    removed_count += 1
                    self.logger.info(f"Removed old backup: {backup_dir.name}")
                except Exception as e:
                    self.logger.error(f"Failed to remove {backup_dir.name}: {e}")
        
        if removed_count > 0:
            self.logger.info(f"Removed {removed_count} old backups")
    
    def list_backups(self) -> List[dict]:
        """List all available backups"""
        backups = []
        
        for backup_dir in sorted(self.backup_dir.glob('backup_*'), reverse=True):
            metadata_file = backup_dir / 'metadata.json'
            
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)
                
                # Get size
                total_size = sum(
                    f.stat().st_size for f in backup_dir.rglob('*') if f.is_file()
                )
                
                backups.append({
                    'name': backup_dir.name.replace('backup_', ''),
                    'path': str(backup_dir),
                    'timestamp': metadata.get('timestamp'),
                    'size_mb': round(total_size / (1024 * 1024), 2),
                    'databases': metadata.get('databases', 0),
                    'files': metadata.get('files', 0)
                })
        
        return backups
    
    def run_automated_backups(
        self,
        interval_hours: int = 24,
        cleanup: bool = True
    ):
        """
        Run automated backups on schedule
        
        Args:
            interval_hours: Hours between backups
            cleanup: Whether to cleanup old backups
        """
        def backup_job():
            try:
                self.create_backup()
                if cleanup:
                    self.cleanup_old_backups()
            except Exception as e:
                self.logger.error(f"Automated backup failed: {e}", exc_info=True)
        
        # Schedule backup
        schedule.every(interval_hours).hours.do(backup_job)
        
        self.logger.info(f"Scheduled automated backups every {interval_hours} hours")
        
        # Run immediately first time
        backup_job()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    def get_backup_stats(self) -> dict:
        """Get backup statistics"""
        backups = self.list_backups()
        
        total_size = sum(b['size_mb'] for b in backups)
        total_count = len(backups)
        
        return {
            'total_backups': total_count,
            'total_size_mb': round(total_size, 2),
            'backup_dir': str(self.backup_dir),
            'retention_days': self.retention_days,
            'compression': self.compression
        }
