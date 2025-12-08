#!/usr/bin/env python3
"""
Performance Optimization Module for InternMailer

Optimizes system performance for production deployment:
- Database query optimization
- Caching mechanisms
- Concurrent processing
- Memory management
- API rate limiting
"""

import asyncio
import aiohttp
import sqlite3
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from typing import List, Dict, Any
import logging
from datetime import datetime, timedelta

class PerformanceOptimizer:
    def __init__(self, db_path: str = 'data/internmailer.db'):
        self.db_path = db_path
        self.cache = {}
        self.rate_limits = {
            'linkedin': {'calls': 0, 'reset_time': time.time()},
            'google_jobs': {'calls': 0, 'reset_time': time.time()},
            'glassdoor': {'calls': 0, 'reset_time': time.time()}
        }
        self.max_workers = 10
        
    def optimize_database(self):
        """Optimize database performance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create indexes for faster queries
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_applications_company ON applications(company)',
            'CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status)',
            'CREATE INDEX IF NOT EXISTS idx_applications_date ON applications(applied_date)',
            'CREATE INDEX IF NOT EXISTS idx_contacts_company ON contacts(company)',
            'CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email)',
            'CREATE INDEX IF NOT EXISTS idx_materials_job_title ON materials(job_title)'
        ]
        
        for index in indexes:
            cursor.execute(index)
            
        # Analyze tables for query optimization
        cursor.execute('ANALYZE')
        
        conn.commit()
        conn.close()
        
        logging.info("Database optimization completed")
        
    @lru_cache(maxsize=1000)
    def cached_prestige_score(self, company: str) -> float:
        """Cache prestige scores to avoid recalculation"""
        # This would call the actual prestige scoring function
        from src.prestige_scorer import PrestigeScorer
        scorer = PrestigeScorer()
        return scorer.calculate_score(company)
        
    def check_rate_limit(self, source: str) -> bool:
        """Check if API rate limit allows request"""
        current_time = time.time()
        rate_info = self.rate_limits.get(source, {'calls': 0, 'reset_time': current_time})
        
        # Reset counter every hour
        if current_time - rate_info['reset_time'] > 3600:
            rate_info['calls'] = 0
            rate_info['reset_time'] = current_time
            
        # Different limits per source
        limits = {
            'linkedin': 100,
            'google_jobs': 200,
            'glassdoor': 150
        }
        
        if rate_info['calls'] < limits.get(source, 100):
            rate_info['calls'] += 1
            return True
        return False
        
    async def async_job_scraping(self, sources: List[str]) -> List[Dict[str, Any]]:
        """Asynchronous job scraping for better performance"""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for source in sources:
                if self.check_rate_limit(source):
                    task = self.scrape_source_async(session, source)
                    tasks.append(task)
                    
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and flatten results
            jobs = []
            for result in results:
                if isinstance(result, list):
                    jobs.extend(result)
                elif not isinstance(result, Exception):
                    jobs.append(result)
                    
            return jobs
            
    async def scrape_source_async(self, session: aiohttp.ClientSession, source: str) -> List[Dict[str, Any]]:
        """Async scraping for individual source"""
        # Placeholder for actual async scraping implementation
        await asyncio.sleep(0.1)  # Simulate API call
        return []
        
    def parallel_resume_processing(self, job_descriptions: List[str], resume_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process multiple resume tailoring tasks in parallel"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            
            for job_desc in job_descriptions:
                future = executor.submit(self.process_single_resume, job_desc, resume_data)
                futures.append(future)
                
            results = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception as e:
                    logging.error(f"Resume processing failed: {e}")
                    
            return results
            
    def process_single_resume(self, job_description: str, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process single resume tailoring task"""
        from src.resume_tailor import ResumeTailor
        tailor = ResumeTailor()
        return tailor.tailor_resume(resume_data, job_description)
        
    def optimize_memory_usage(self):
        """Optimize memory usage"""
        # Clear caches periodically
        if len(self.cache) > 10000:
            # Keep only recent entries
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.cache = {k: v for k, v in self.cache.items() 
                         if v.get('timestamp', datetime.min) > cutoff_time}
            
        # Clear LRU cache
        self.cached_prestige_score.cache_clear()
        
        logging.info("Memory optimization completed")
        
    def batch_database_operations(self, operations: List[Dict[str, Any]]):
        """Batch database operations for better performance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Group operations by type
            inserts = [op for op in operations if op['type'] == 'insert']
            updates = [op for op in operations if op['type'] == 'update']
            
            # Batch inserts
            if inserts:
                for insert in inserts:
                    cursor.execute(insert['query'], insert['params'])
                    
            # Batch updates
            if updates:
                for update in updates:
                    cursor.execute(update['query'], update['params'])
                    
            conn.commit()
            logging.info(f"Batched {len(operations)} database operations")
            
        except Exception as e:
            conn.rollback()
            logging.error(f"Batch operation failed: {e}")
            raise
        finally:
            conn.close()
            
    def performance_monitoring(self) -> Dict[str, Any]:
        """Monitor system performance metrics"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        metrics = {
            'cpu_percent': process.cpu_percent(),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'cache_size': len(self.cache),
            'rate_limits': self.rate_limits,
            'timestamp': datetime.now().isoformat()
        }
        
        # Log performance metrics
        logging.info(f"Performance metrics: {json.dumps(metrics, indent=2)}")
        
        return metrics
        
    def run_optimization_suite(self):
        """Run complete optimization suite"""
        logging.info("Starting performance optimization suite")
        
        # Database optimization
        self.optimize_database()
        
        # Memory optimization
        self.optimize_memory_usage()
        
        # Performance monitoring
        metrics = self.performance_monitoring()
        
        logging.info("Performance optimization suite completed")
        return metrics

if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/performance.log'),
            logging.StreamHandler()
        ]
    )
    
    # Run optimization
    optimizer = PerformanceOptimizer()
    metrics = optimizer.run_optimization_suite()
    
    print("\n=== Performance Optimization Complete ===")
    print(f"CPU Usage: {metrics['cpu_percent']:.2f}%")
    print(f"Memory Usage: {metrics['memory_mb']:.2f} MB")
    print(f"Cache Size: {metrics['cache_size']} entries")
    print("\nSystem optimized for production deployment!")