"""
Integration tests for InternMailer system
Tests end-to-end workflows and component interactions
"""

import unittest
import tempfile
import os
import sys
import json
from unittest.mock import Mock, patch
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from prestige_scorer import PrestigeScorer
from application_tracker import ApplicationTracker, ApplicationStatus
from email_notifier import EmailNotifier

class TestInternMailerIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test environment with temporary database"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Initialize components with test database
        self.prestige_scorer = PrestigeScorer()
        self.application_tracker = ApplicationTracker(self.temp_db.name)
        self.email_notifier = EmailNotifier()
        
        # Sample job data for testing
        self.sample_jobs = [
            {
                'job_title': 'Machine Learning Intern',
                'company': 'Google',
                'location': 'Mountain View, CA',
                'duration': 'Summer 2026 (12 weeks)',
                'job_type': 'Internship',
                'apply_link': 'https://careers.google.com/jobs/123',
                'description': 'Work on cutting-edge ML projects with our research team.',
                'eligibility': 'Undergraduate students in Computer Science, Data Science, or related fields',
                'posted_date': '2024-12-01',
                'deadline': '2025-02-15',
                'source': 'Google Careers'
            },
            {
                'job_title': 'Data Science Intern',
                'company': 'Adobe',
                'location': 'San Jose, CA',
                'duration': 'Summer 2026 (10 weeks)',
                'job_type': 'Internship',
                'apply_link': 'https://adobe.com/careers/jobs/456',
                'description': 'Analyze user behavior data and build predictive models.',
                'eligibility': 'Students pursuing Bachelor degree in Data Science',
                'posted_date': '2024-12-02',
                'deadline': '2025-03-01',
                'source': 'Adobe Careers'
            },
            {
                'job_title': 'Software Engineering Intern',
                'company': 'TCS',
                'location': 'Bangalore, India',
                'duration': 'Summer 2026 (8 weeks)',
                'job_type': 'Internship',
                'apply_link': 'https://tcs.com/careers/789',
                'description': 'Develop web applications using modern frameworks.',
                'eligibility': 'BTech students in Computer Science',
                'posted_date': '2024-12-03',
                'deadline': '2025-01-31',
                'source': 'TCS Careers'
            }
        ]
    
    def tearDown(self):
        """Clean up test environment"""
        os.unlink(self.temp_db.name)
    
    def test_prestige_scoring_integration(self):
        """Test prestige scoring integration with job ranking"""
        # Score and rank the sample jobs
        ranked_jobs = self.prestige_scorer.rank_opportunities(self.sample_jobs)
        
        # Verify all jobs have prestige data
        for job in ranked_jobs:
            self.assertIn('prestige_tier', job)
            self.assertIn('prestige_score', job)
            self.assertIn('prestige_reasoning', job)
        
        # Verify ranking order (Google should be first, TCS last)
        self.assertEqual(ranked_jobs[0]['company'], 'Google')
        self.assertEqual(ranked_jobs[-1]['company'], 'TCS')
        
        # Verify prestige tiers
        google_job = next(job for job in ranked_jobs if job['company'] == 'Google')
        adobe_job = next(job for job in ranked_jobs if job['company'] == 'Adobe')
        tcs_job = next(job for job in ranked_jobs if job['company'] == 'TCS')
        
        self.assertEqual(google_job['prestige_tier'], 'Tier 1')
        self.assertEqual(adobe_job['prestige_tier'], 'Tier 2')
        self.assertEqual(tcs_job['prestige_tier'], 'Tier 3')
    
    def test_application_tracking_workflow(self):
        """Test application tracking and status management workflow"""
        # Create a test application in the database
        import sqlite3
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id TEXT PRIMARY KEY,
                job_title TEXT,
                company TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        cursor.execute("""
            INSERT INTO applications (id, job_title, company, status, created_at, updated_at)
            VALUES ('test_app_1', 'ML Intern', 'Google', 'not_applied', ?, ?)
        """, ('2024-12-04T10:00:00', '2024-12-04T10:00:00'))
        conn.commit()
        conn.close()
        
        # Test status progression
        # 1. Initial status
        status = self.application_tracker.get_application_status('test_app_1')
        self.assertEqual(status, ApplicationStatus.NOT_APPLIED)
        
        # 2. Update to applied
        success = self.application_tracker.update_application_status(
            'test_app_1', ApplicationStatus.APPLIED, 'Application submitted via portal', 'manual'
        )
        self.assertTrue(success)
        
        # 3. Update to under review
        success = self.application_tracker.update_application_status(
            'test_app_1', ApplicationStatus.UNDER_REVIEW, 'Received confirmation email', 'email_parser'
        )
        self.assertTrue(success)
        
        # 4. Verify current status
        current_status = self.application_tracker.get_application_status('test_app_1')
        self.assertEqual(current_status, ApplicationStatus.UNDER_REVIEW)
        
        # 5. Check status history
        history = self.application_tracker.get_status_history('test_app_1')
        self.assertGreaterEqual(len(history), 2)
        self.assertEqual(history[0]['status'], 'under_review')  # Most recent first
        self.assertEqual(history[1]['status'], 'applied')
    
    @patch.object(EmailNotifier, '_send_email')
    def test_email_notification_workflow(self, mock_send_email):
        """Test email notification workflow"""
        mock_send_email.return_value = True
        
        # Create sample daily report
        daily_report = {
            'date': '2024-12-04',
            'summary': {
                'total_found': 3,
                'shortlisted': 3,
                'auto_applied': 0,
                'manual_required': 3,
                'tiers': {'Tier 1': 1, 'Tier 2': 1, 'Tier 3': 1}
            },
            'opportunities_ranked': [
                {
                    'job_title': 'Machine Learning Intern',
                    'company': 'Google',
                    'location': 'Mountain View, CA',
                    'apply_link': 'https://careers.google.com/jobs/123',
                    'contact_email': 'recruiter@google.com',
                    'match_score': 0.95,
                    'prestige_tier': 'Tier 1',
                    'prestige_score': 1.0
                }
            ],
            'application_logs': [],
            'materials': []
        }
        
        # Test email sending
        success = self.email_notifier.send_daily_report(daily_report)
        self.assertTrue(success)
        mock_send_email.assert_called_once()
    
    def test_error_handling_and_recovery(self):
        """Test system behavior with invalid data and error conditions"""
        # Test with invalid job data
        invalid_job = {
            'company': '',  # Empty company name
            'job_title': None,  # None job title
            'location': 'Unknown'
        }
        
        # Prestige scoring should handle invalid data gracefully
        tier, score, reasoning = self.prestige_scorer.get_prestige_score('')
        self.assertEqual(tier, 'Unknown')
        self.assertEqual(score, 0.0)
        
        # Test with None input
        tier, score, reasoning = self.prestige_scorer.get_prestige_score(None)
        self.assertEqual(tier, 'Unknown')
        self.assertEqual(score, 0.0)
    
    def test_data_consistency_across_components(self):
        """Test data consistency when passed between different components"""
        # Start with original job data
        original_job = self.sample_jobs[0].copy()
        
        # Add prestige scoring
        tier, score, reasoning = self.prestige_scorer.get_prestige_score(original_job['company'])
        original_job.update({
            'prestige_tier': tier,
            'prestige_score': score,
            'prestige_reasoning': reasoning
        })
        
        # Verify data consistency
        self.assertEqual(original_job['company'], 'Google')
        self.assertEqual(original_job['job_title'], 'Machine Learning Intern')
        self.assertEqual(original_job['prestige_tier'], 'Tier 1')
        self.assertEqual(original_job['prestige_score'], 1.0)
    
    def test_performance_with_large_dataset(self):
        """Test system performance with larger number of applications"""
        # Create 50 test applications
        large_dataset = []
        companies = ['Google', 'Microsoft', 'Amazon', 'Adobe', 'TCS'] * 10
        
        for i, company in enumerate(companies):
            job = {
                'job_title': f'Intern Position {i+1}',
                'company': company,
                'location': 'Various',
                'apply_link': f'https://{company.lower()}.com/jobs/{i+1}',
                'description': f'Internship opportunity {i+1}',
                'source': f'{company} Careers'
            }
            large_dataset.append(job)
        
        # Test prestige scoring performance
        import time
        start_time = time.time()
        scored_jobs = self.prestige_scorer.rank_opportunities(large_dataset)
        scoring_time = time.time() - start_time
        
        # Should complete within reasonable time (< 5 seconds)
        self.assertLess(scoring_time, 5.0)
        self.assertEqual(len(scored_jobs), 50)
        
        # Verify all jobs have prestige data
        for job in scored_jobs:
            self.assertIn('prestige_tier', job)
            self.assertIn('prestige_score', job)

if __name__ == '__main__':
    # Run integration tests
    unittest.main(verbosity=2)