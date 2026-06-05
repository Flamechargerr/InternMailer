#!/usr/bin/env python3
"""
Test script to identify job persistence issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.job_discovery import JobDiscovery, JobPosting
from core.database_manager import get_job_discovery_db
from utils.config import config
import json

def test_job_persistence():
    """Test job persistence to identify issues"""
    print("Testing job persistence...")
    
    # Create a job discovery instance
    discovery = JobDiscovery()
    
    # Create a test job
    test_job = JobPosting(
        source="test",
        source_id="test-123",
        company="Test Company",
        title="Software Engineer Intern",
        location="Bangalore, India",
        location_type="onsite",
        url="https://test.com/job/123",
        apply_url="https://test.com/job/123",
        description="Summer 2026 internship with visa sponsorship.",
        employment_type="internship",
        score=0.8
    )
    
    print(f"Test job created: {test_job.title} at {test_job.company}")
    
    # Try to save the job
    print("Attempting to save job...")
    saved_count = discovery.save_jobs([test_job])
    print(f"Saved count: {saved_count}")
    
    # Check if job was saved
    db = get_job_discovery_db(config.JOBS_DB_PATH)
    saved_job = db.fetch_one("SELECT * FROM jobs WHERE url = ?", (test_job.url,))
    
    if saved_job:
        print(f"✓ Job successfully saved to database")
        print(f"  ID: {saved_job['id']}")
        print(f"  Company: {saved_job['company']}")
        print(f"  Title: {saved_job['title']}")
        print(f"  Score: {saved_job['score']}")
    else:
        print("✗ Job not found in database")
        
    # Test duplicate URL handling
    print("\nTesting duplicate URL handling...")
    duplicate_job = JobPosting(
        source="test",
        source_id="test-456",
        company="Another Test Company",
        title="Data Scientist Intern",
        location="Remote",
        location_type="remote",
        url="https://test.com/job/123",  # Same URL as above
        apply_url="https://test.com/job/123",
        description="Remote data science internship.",
        employment_type="internship",
        score=0.7
    )
    
    saved_count2 = discovery.save_jobs([duplicate_job])
    print(f"Saved count for duplicate URL: {saved_count2}")
    
    # Test job with empty URL
    print("\nTesting job with empty URL...")
    empty_url_job = JobPosting(
        source="test",
        source_id="test-789",
        company="Empty URL Company",
        title="Backend Engineer Intern",
        location="San Francisco, USA",
        location_type="onsite",
        url="",  # Empty URL
        apply_url="",
        description="Backend engineering internship.",
        employment_type="internship",
        score=0.6
    )
    
    saved_count3 = discovery.save_jobs([empty_url_job])
    print(f"Saved count for empty URL: {saved_count3}")
    
    # Test database connection
    print("\nTesting database connection and schema...")
    try:
        stats = db.get_stats()
        print(f"Database size: {stats['size_mb']:.2f} MB")
        print(f"Tables: {[t['name'] for t in stats['tables']]}")
        
        # Check jobs table schema
        schema = db.get_table_schema("jobs")
        print(f"\nJobs table schema ({len(schema)} columns):")
        for col in schema:
            print(f"  {col['name']}: {col['type']} {'NOT NULL' if col['notnull'] else ''}")
            
    except Exception as e:
        print(f"Error checking database: {e}")
    
    # Clean up test data
    print("\nCleaning up test data...")
    db.delete("jobs", "source = ?", ("test",))
    deleted_count = db.fetch_one("SELECT COUNT(*) as count FROM jobs WHERE source = 'test'")
    print(f"Test jobs remaining: {deleted_count['count'] if deleted_count else 0}")

if __name__ == "__main__":
    test_job_persistence()