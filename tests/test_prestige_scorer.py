"""
Unit tests for PrestigeScorer module
"""

import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from prestige_scorer import PrestigeScorer

class TestPrestigeScorer(unittest.TestCase):
    def setUp(self):
        self.scorer = PrestigeScorer()
    
    def test_normalize_company_name(self):
        """Test company name normalization"""
        # Test basic normalization
        self.assertEqual(self.scorer.normalize_company_name("Google Inc."), "google")
        self.assertEqual(self.scorer.normalize_company_name("Microsoft Corporation"), "microsoft")
        
        # Test special cases
        self.assertEqual(self.scorer.normalize_company_name("Meta Platforms"), "meta")
        self.assertEqual(self.scorer.normalize_company_name("Facebook"), "meta")
        self.assertEqual(self.scorer.normalize_company_name("Alphabet"), "google")
        
        # Test empty/None input
        self.assertEqual(self.scorer.normalize_company_name(""), "")
        self.assertEqual(self.scorer.normalize_company_name(None), "")
    
    def test_get_prestige_score_tier1(self):
        """Test prestige scoring for Tier 1 companies"""
        tier, score, reasoning = self.scorer.get_prestige_score("Google")
        self.assertEqual(tier, "Tier 1")
        self.assertEqual(score, 1.0)
        self.assertIn("tech leader", reasoning.lower())
        
        tier, score, reasoning = self.scorer.get_prestige_score("Microsoft")
        self.assertEqual(tier, "Tier 1")
        self.assertGreaterEqual(score, 0.9)
    
    def test_get_prestige_score_tier2(self):
        """Test prestige scoring for Tier 2 companies"""
        tier, score, reasoning = self.scorer.get_prestige_score("Adobe")
        self.assertEqual(tier, "Tier 2")
        self.assertGreaterEqual(score, 0.7)
        self.assertLess(score, 0.9)
    
    def test_get_prestige_score_tier3(self):
        """Test prestige scoring for Tier 3 companies"""
        tier, score, reasoning = self.scorer.get_prestige_score("TCS")
        self.assertEqual(tier, "Tier 3")
        self.assertGreaterEqual(score, 0.5)
        self.assertLess(score, 0.7)
    
    def test_get_prestige_score_unknown(self):
        """Test prestige scoring for unknown companies"""
        tier, score, reasoning = self.scorer.get_prestige_score("Unknown Startup XYZ")
        self.assertEqual(tier, "Unknown")
        self.assertEqual(score, 0.3)
        self.assertIn("unknown", reasoning.lower())
    
    def test_rank_opportunities(self):
        """Test opportunity ranking"""
        opportunities = [
            {"company": "TCS", "match_score": 0.8, "posted_date": "2024-12-01"},
            {"company": "Google", "match_score": 0.7, "posted_date": "2024-12-02"},
            {"company": "Adobe", "match_score": 0.9, "posted_date": "2024-12-03"}
        ]
        
        ranked = self.scorer.rank_opportunities(opportunities)
        
        # Google should be first (highest prestige)
        self.assertEqual(ranked[0]["company"], "Google")
        # Adobe should be second (Tier 2 with high match)
        self.assertEqual(ranked[1]["company"], "Adobe")
        # TCS should be last (Tier 3)
        self.assertEqual(ranked[2]["company"], "TCS")
        
        # Check that prestige data was added
        for opp in ranked:
            self.assertIn("prestige_tier", opp)
            self.assertIn("prestige_score", opp)
    
    def test_filter_by_prestige(self):
        """Test filtering by prestige tier"""
        opportunities = [
            {"company": "Google", "prestige_tier": "Tier 1"},
            {"company": "Adobe", "prestige_tier": "Tier 2"},
            {"company": "TCS", "prestige_tier": "Tier 3"},
            {"company": "Unknown", "prestige_tier": "Unknown"}
        ]
        
        # Filter for Tier 1 only
        tier1_only = self.scorer.filter_by_prestige(opportunities, "Tier 1")
        self.assertEqual(len(tier1_only), 1)
        self.assertEqual(tier1_only[0]["company"], "Google")
        
        # Filter for Tier 2 and above
        tier2_plus = self.scorer.filter_by_prestige(opportunities, "Tier 2")
        self.assertEqual(len(tier2_plus), 2)
        companies = [opp["company"] for opp in tier2_plus]
        self.assertIn("Google", companies)
        self.assertIn("Adobe", companies)
        
        # Filter for Tier 3 and above (all known companies)
        tier3_plus = self.scorer.filter_by_prestige(opportunities, "Tier 3")
        self.assertEqual(len(tier3_plus), 3)
    
    def test_get_tier_distribution(self):
        """Test tier distribution calculation"""
        opportunities = [
            {"prestige_tier": "Tier 1"},
            {"prestige_tier": "Tier 1"},
            {"prestige_tier": "Tier 2"},
            {"prestige_tier": "Tier 3"},
            {"prestige_tier": "Unknown"}
        ]
        
        distribution = self.scorer.get_tier_distribution(opportunities)
        
        self.assertEqual(distribution["Tier 1"], 2)
        self.assertEqual(distribution["Tier 2"], 1)
        self.assertEqual(distribution["Tier 3"], 1)
        self.assertEqual(distribution["Unknown"], 1)

if __name__ == '__main__':
    unittest.main()