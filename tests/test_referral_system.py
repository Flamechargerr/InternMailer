"""
CodeRabbit-style Comprehensive Test Suite for Internship Referral System
Verifies InboxMonitor, ReplyClassifier, and AutoActionEngine referral logic.
"""
import unittest
from unittest.mock import MagicMock, patch, ANY
import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inbox_monitor import InboxMonitor
from reply_classifier import ReplyClassifier, ReplyCategory
from auto_action_engine import AutoActionEngine

class TestReferralSystem(unittest.TestCase):
    
    def setUp(self):
        # Setup mocks
        self.mock_imap = MagicMock()
    def setUp(self):
        # Setup mocks
        self.mock_imap = MagicMock()
        self.test_db = os.path.join('test_results', 'test_inbox.db')
        
        # Ensure clean state
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
            
        self.monitor = InboxMonitor(db_path=self.test_db)
        self.classifier = ReplyClassifier()
        self.engine = AutoActionEngine(inbox_db=self.test_db)
        
    def tearDown(self):
        if os.path.exists(self.test_db):
            try:
                os.remove(self.test_db)
            except:
                pass
        
    def test_inbox_monitor_extracts_headers(self):
        """Test extraction of To and CC lists from email headers"""
        print("\n🐰 CodeRabbit: Testing Inbox Header Extraction...")
        
        # Test Case 1: Complex Recipient List
        to_header = "Marc Van Hulle <marc@kuleuven.be>, Hannes <hannes@spinoff.com>"
        cc_header = "Anamay <me@gmail.com>, Another <other@lab.edu>"
        
        to_list = self.monitor._extract_email_list(to_header)
        cc_list = self.monitor._extract_email_list(cc_header)
        
        print(f"   Input To: {to_header}")
        print(f"   Extracted To: {to_list}")
        
        self.assertIn("marc@kuleuven.be", to_list)
        self.assertIn("hannes@spinoff.com", to_list)
        self.assertIn("other@lab.edu", cc_list)
        
    def test_reply_classification_referral(self):
        """Test classification of referral emails"""
        print("\n🐰 CodeRabbit: Testing Referral Classification...")
        
        test_bodies = [
            ("I put you in contact with the CEO of my spinoff.", "referral"),
            ("I am copying my colleague Hannes.", "referral"),
            ("Please contact my PhD student.", "referral"),
            ("Thanks, I'm interested.", "interested"),
            ("Not hiring right now.", "not_interested")
        ]
        
        for body, expected in test_bodies:
            result = self.classifier.classify_reply(body, "Subject")
            classification = result['category'].value
            print(f"   Body: '{body}' -> Classified: {classification.upper()}")
            self.assertEqual(classification, expected)

    @patch('smtplib.SMTP')
    def test_auto_action_reply_all(self, mock_smtp):
        """Test Reply All logic with To/CC handling"""
        print("\n🐰 CodeRabbit: Testing Reply All Logic...")
        
        # Setup
        self.engine.email_address = "me@gmail.com"
        self.engine.password = "fake_pass"
        
        reply_data = {
            'email': 'marc@kuleuven.be',  # From
            'to_list': 'marc@kuleuven.be, hannes@spinoff.com, me@gmail.com', # Original To
            'cc_list': 'admin@kuleuven.be', # Original CC
            'subject': 'Re: Research Inquiry'
        }
        
        # Action
        with patch('builtins.print'): # Suppress print
            success = self.engine.process_referral_reply(reply_data)
        
        self.assertTrue(success)
        
        # Verification
        instance = mock_smtp.return_value.__enter__.return_value
        instance.send_message.assert_called_once()
        
        msg = instance.send_message.call_args[0][0]
        
        print(f"   Sent To: {msg['To']}")
        print(f"   Sent Cc: {msg['Cc']}")
        
        # Logic Verification:
        # To should contain Sender (Marc) + Others in To (Hannes) - Me
        self.assertIn('marc@kuleuven.be', msg['To'])
        self.assertIn('hannes@spinoff.com', msg['To'])
        self.assertNotIn('me@gmail.com', msg['To']) # Should not reply to self
        
        # CC should contain Original CC
        self.assertIn('admin@kuleuven.be', msg['Cc'])

if __name__ == '__main__':
    unittest.main()
