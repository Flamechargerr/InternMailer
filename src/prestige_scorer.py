"""
Prestige Scoring Algorithm for InternMailer
Assigns prestige tiers and scores to companies and research institutions
"""

import json
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class PrestigeData:
    tier: str
    score: float
    category: str  # 'tech', 'finance', 'consulting', 'research'
    reasoning: str

class PrestigeScorer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Tier 1 Companies (Score: 0.9-1.0)
        self.tier1_companies = {
            # Big Tech
            'google': PrestigeData('Tier 1', 1.0, 'tech', 'Global tech leader, top AI research'),
            'microsoft': PrestigeData('Tier 1', 0.98, 'tech', 'Cloud leader, strong AI division'),
            'amazon': PrestigeData('Tier 1', 0.97, 'tech', 'E-commerce giant, AWS leader'),
            'meta': PrestigeData('Tier 1', 0.96, 'tech', 'Social media leader, VR/AR pioneer'),
            'apple': PrestigeData('Tier 1', 0.95, 'tech', 'Consumer tech leader, premium brand'),
            'nvidia': PrestigeData('Tier 1', 0.99, 'tech', 'AI hardware leader, GPU pioneer'),
            'openai': PrestigeData('Tier 1', 1.0, 'tech', 'Leading AI research company'),
            'deepmind': PrestigeData('Tier 1', 1.0, 'tech', 'Premier AI research lab'),
            'anthropic': PrestigeData('Tier 1', 0.98, 'tech', 'Leading AI safety research'),
            
            # Finance
            'goldman sachs': PrestigeData('Tier 1', 0.95, 'finance', 'Top investment bank'),
            'jane street': PrestigeData('Tier 1', 0.97, 'finance', 'Elite quantitative trading'),
            'citadel': PrestigeData('Tier 1', 0.96, 'finance', 'Top hedge fund'),
            'two sigma': PrestigeData('Tier 1', 0.95, 'finance', 'Quantitative investment firm'),
            
            # Consulting
            'mckinsey': PrestigeData('Tier 1', 0.94, 'consulting', 'Top management consulting'),
            'bain': PrestigeData('Tier 1', 0.93, 'consulting', 'Elite strategy consulting'),
            'bcg': PrestigeData('Tier 1', 0.93, 'consulting', 'Boston Consulting Group'),
        }
        
        # Tier 2 Companies (Score: 0.7-0.89)
        self.tier2_companies = {
            'adobe': PrestigeData('Tier 2', 0.85, 'tech', 'Creative software leader'),
            'uber': PrestigeData('Tier 2', 0.82, 'tech', 'Ride-sharing pioneer'),
            'airbnb': PrestigeData('Tier 2', 0.83, 'tech', 'Travel platform leader'),
            'spotify': PrestigeData('Tier 2', 0.81, 'tech', 'Music streaming leader'),
            'netflix': PrestigeData('Tier 2', 0.84, 'tech', 'Streaming entertainment leader'),
            'salesforce': PrestigeData('Tier 2', 0.82, 'tech', 'CRM platform leader'),
            'palantir': PrestigeData('Tier 2', 0.86, 'tech', 'Data analytics platform'),
            'databricks': PrestigeData('Tier 2', 0.85, 'tech', 'Data lakehouse platform'),
            'snowflake': PrestigeData('Tier 2', 0.84, 'tech', 'Cloud data platform'),
            'stripe': PrestigeData('Tier 2', 0.87, 'tech', 'Payment processing leader'),
            'flipkart': PrestigeData('Tier 2', 0.78, 'tech', 'Leading Indian e-commerce'),
            'zomato': PrestigeData('Tier 2', 0.75, 'tech', 'Food delivery platform'),
            'paytm': PrestigeData('Tier 2', 0.74, 'tech', 'Digital payments platform'),
            'sap': PrestigeData('Tier 2', 0.79, 'tech', 'Enterprise software leader'),
            'oracle': PrestigeData('Tier 2', 0.78, 'tech', 'Database and cloud services'),
            'ibm': PrestigeData('Tier 2', 0.77, 'tech', 'Enterprise technology services'),
            'jp morgan': PrestigeData('Tier 2', 0.88, 'finance', 'Major investment bank'),
            'morgan stanley': PrestigeData('Tier 2', 0.87, 'finance', 'Investment banking'),
            'deloitte': PrestigeData('Tier 2', 0.82, 'consulting', 'Big 4 consulting'),
            'pwc': PrestigeData('Tier 2', 0.81, 'consulting', 'Professional services'),
            'ey': PrestigeData('Tier 2', 0.80, 'consulting', 'Ernst & Young'),
            'kpmg': PrestigeData('Tier 2', 0.79, 'consulting', 'Big 4 consulting'),
        }
        
        # Tier 3 Companies (Score: 0.5-0.69)
        self.tier3_companies = {
            'tcs': PrestigeData('Tier 3', 0.68, 'tech', 'Large IT services company'),
            'infosys': PrestigeData('Tier 3', 0.67, 'tech', 'IT services and consulting'),
            'wipro': PrestigeData('Tier 3', 0.65, 'tech', 'IT services provider'),
            'hcl': PrestigeData('Tier 3', 0.64, 'tech', 'Technology services'),
            'cognizant': PrestigeData('Tier 3', 0.66, 'tech', 'IT services and consulting'),
            'accenture': PrestigeData('Tier 3', 0.69, 'consulting', 'Technology consulting'),
            'capgemini': PrestigeData('Tier 3', 'tech', 0.63, 'IT consulting services'),
            'reliance': PrestigeData('Tier 3', 0.62, 'tech', 'Diversified conglomerate'),
            'airtel': PrestigeData('Tier 3', 0.61, 'tech', 'Telecommunications'),
            'jio': PrestigeData('Tier 3', 0.63, 'tech', 'Digital services platform'),
        }
        
        # Research Universities (Score: 0.85-1.0)
        self.research_institutions = {
            'mit': PrestigeData('Tier 1', 1.0, 'research', 'Top engineering and CS research'),
            'stanford': PrestigeData('Tier 1', 1.0, 'research', 'Silicon Valley research leader'),
            'cmu': PrestigeData('Tier 1', 0.98, 'research', 'Top CS and AI research'),
            'uc berkeley': PrestigeData('Tier 1', 0.97, 'research', 'Leading public research university'),
            'caltech': PrestigeData('Tier 1', 0.96, 'research', 'Elite science and engineering'),
            'eth zurich': PrestigeData('Tier 1', 0.95, 'research', 'Top European tech university'),
            'university of toronto': PrestigeData('Tier 1', 0.94, 'research', 'Leading AI research'),
            'oxford': PrestigeData('Tier 1', 0.93, 'research', 'Premier UK university'),
            'cambridge': PrestigeData('Tier 1', 0.93, 'research', 'Top UK research institution'),
            
            # Indian Institutions
            'iit bombay': PrestigeData('Tier 1', 0.92, 'research', 'Premier Indian engineering'),
            'iit delhi': PrestigeData('Tier 1', 0.91, 'research', 'Top Indian technical institute'),
            'iit madras': PrestigeData('Tier 1', 0.90, 'research', 'Leading Indian IIT'),
            'iit kanpur': PrestigeData('Tier 1', 0.89, 'research', 'Premier engineering institute'),
            'iit kharagpur': PrestigeData('Tier 1', 0.88, 'research', 'Oldest IIT'),
            'iisc bangalore': PrestigeData('Tier 1', 0.94, 'research', 'Top Indian research institute'),
            'tifr': PrestigeData('Tier 1', 0.93, 'research', 'Fundamental research institute'),
        }
        
        # Combine all databases
        self.all_organizations = {
            **self.tier1_companies,
            **self.tier2_companies, 
            **self.tier3_companies,
            **self.research_institutions
        }
    
    def normalize_company_name(self, company_name: str) -> str:
        """Normalize company name for matching"""
        if not company_name:
            return ""
        
        # Convert to lowercase and remove common suffixes
        normalized = company_name.lower().strip()
        
        # Remove common company suffixes
        suffixes = [
            ' inc', ' inc.', ' corp', ' corp.', ' ltd', ' ltd.', 
            ' llc', ' llp', ' pvt ltd', ' private limited',
            ' technologies', ' technology', ' tech', ' systems',
            ' solutions', ' services', ' consulting', ' group',
            ' company', ' co.', ' co'
        ]
        
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()
        
        # Handle special cases
        special_cases = {
            'google llc': 'google',
            'alphabet': 'google',
            'meta platforms': 'meta',
            'facebook': 'meta',
            'amazon web services': 'amazon',
            'aws': 'amazon',
            'microsoft corporation': 'microsoft',
            'apple inc': 'apple',
            'nvidia corporation': 'nvidia',
            'goldman sachs group': 'goldman sachs',
            'jp morgan chase': 'jp morgan',
            'jpmorgan': 'jp morgan',
            'morgan stanley': 'morgan stanley',
            'tata consultancy services': 'tcs',
            'hcl technologies': 'hcl',
            'massachusetts institute of technology': 'mit',
            'stanford university': 'stanford',
            'carnegie mellon university': 'cmu',
            'university of california berkeley': 'uc berkeley',
            'california institute of technology': 'caltech',
            'indian institute of technology bombay': 'iit bombay',
            'indian institute of science': 'iisc bangalore',
        }
        
        return special_cases.get(normalized, normalized)
    
    def get_prestige_score(self, company_name: str) -> Tuple[str, float, str]:
        """
        Get prestige tier, score, and reasoning for a company
        
        Returns:
            Tuple of (tier, score, reasoning)
        """
        if not company_name:
            return "Unknown", 0.0, "No company name provided"
        
        normalized_name = self.normalize_company_name(company_name)
        
        if normalized_name in self.all_organizations:
            org_data = self.all_organizations[normalized_name]
            return org_data.tier, org_data.score, org_data.reasoning
        
        # Fuzzy matching for partial matches
        for org_name, org_data in self.all_organizations.items():
            if normalized_name in org_name or org_name in normalized_name:
                return org_data.tier, org_data.score, f"Partial match: {org_data.reasoning}"
        
        # Default scoring for unknown companies
        return "Unknown", 0.3, "Unknown company - requires manual review"
    
    def rank_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Rank opportunities by prestige score, match score, and recency
        
        Args:
            opportunities: List of job opportunities with company names
            
        Returns:
            Sorted list of opportunities with prestige data added
        """
        ranked_opportunities = []
        
        for opp in opportunities:
            company_name = opp.get('company', '')
            tier, score, reasoning = self.get_prestige_score(company_name)
            
            # Add prestige data to opportunity
            opp_with_prestige = opp.copy()
            opp_with_prestige.update({
                'prestige_tier': tier,
                'prestige_score': score,
                'prestige_reasoning': reasoning
            })
            
            ranked_opportunities.append(opp_with_prestige)
        
        # Sort by: Prestige Score (desc) -> Match Score (desc) -> Posted Date (desc)
        ranked_opportunities.sort(key=lambda x: (
            x.get('prestige_score', 0.0),
            x.get('match_score', 0.0),
            x.get('posted_date', '')
        ), reverse=True)
        
        return ranked_opportunities
    
    def filter_by_prestige(self, opportunities: List[Dict], min_tier: str = "Tier 3") -> List[Dict]:
        """
        Filter opportunities by minimum prestige tier
        
        Args:
            opportunities: List of opportunities
            min_tier: Minimum tier to include ("Tier 1", "Tier 2", "Tier 3")
            
        Returns:
            Filtered list of opportunities
        """
        tier_hierarchy = {"Tier 1": 3, "Tier 2": 2, "Tier 3": 1, "Unknown": 0}
        min_level = tier_hierarchy.get(min_tier, 0)
        
        filtered = []
        for opp in opportunities:
            tier = opp.get('prestige_tier', 'Unknown')
            if tier_hierarchy.get(tier, 0) >= min_level:
                filtered.append(opp)
        
        return filtered
    
    def get_tier_distribution(self, opportunities: List[Dict]) -> Dict[str, int]:
        """Get distribution of opportunities by prestige tier"""
        distribution = {"Tier 1": 0, "Tier 2": 0, "Tier 3": 0, "Unknown": 0}
        
        for opp in opportunities:
            tier = opp.get('prestige_tier', 'Unknown')
            distribution[tier] = distribution.get(tier, 0) + 1
        
        return distribution

if __name__ == "__main__":
    # Test the prestige scorer
    scorer = PrestigeScorer()
    
    test_companies = [
        "Google", "Microsoft", "Amazon", "TCS", "Infosys", 
        "MIT", "Stanford", "IIT Bombay", "Unknown Company"
    ]
    
    print("Prestige Scoring Test:")
    print("-" * 50)
    
    for company in test_companies:
        tier, score, reasoning = scorer.get_prestige_score(company)
        print(f"{company:15} | {tier:8} | {score:4.2f} | {reasoning}")