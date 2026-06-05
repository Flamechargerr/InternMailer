"""
🧪 Comprehensive Integration Tests for InternMailer
===================================================
End-to-end testing of all major features
"""

import os
import sys
import pytest
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import config
from core.agents.base_agent import AgentContext
from core.agents.orchestrator import get_orchestrator


class TestAgentFramework:
    """Test the AI agent framework"""
    
    def test_agent_context_creation(self):
        """Test AgentContext creation"""
        context = AgentContext.create()
        assert context is not None
        # Profile is a Profile object, not a dict
        assert context.profile is not None
        assert hasattr(context.profile, '__dict__') or isinstance(context.profile, dict)
        assert context.session_id
    
    def test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        orchestrator = get_orchestrator()
        assert orchestrator is not None
        assert orchestrator.name == "Orchestrator"
    
    def test_orchestrator_state_analysis(self):
        """Test state analysis"""
        orchestrator = get_orchestrator()
        context = AgentContext.create()
        state = orchestrator.analyze_state(context)
        
        assert "timestamp" in state
        assert "stats" in state
        assert "priorities" in state
        assert isinstance(state["stats"], dict)


class TestLeadDiscovery:
    """Test lead discovery functionality"""
    
    def test_enhanced_lead_discovery_initialization(self):
        """Test lead discovery module loads"""
        from core.lead_discovery import EnhancedLeadDiscovery
        discovery = EnhancedLeadDiscovery()
        assert discovery is not None
    
    def test_domain_extraction(self):
        """Test domain extraction from URLs"""
        from core.lead_discovery import EnhancedLeadDiscovery
        discovery = EnhancedLeadDiscovery()
        
        assert discovery._extract_domain("https://stripe.com/careers") == "stripe.com"
        assert discovery._extract_domain("https://www.github.com/about") == "github.com"
        assert discovery._extract_domain("not-a-url") is None


class TestGmailAgent:
    """Test Gmail agent functionality"""
    
    def test_gmail_agent_initialization(self):
        """Test Gmail agent loads"""
        from core.gmail_agent import GmailAgent
        agent = GmailAgent()
        assert agent is not None
    
    def test_email_categorization(self):
        """Test email categorization logic"""
        from core.gmail_agent import GmailAgent
        agent = GmailAgent()
        
        # Test interested detection
        email = {"body": "Thank you for your application. We are interested in your profile.", "subject": "Re: Application"}
        result = agent._fallback_classification(email)
        assert result["category"] == "interested"
        
        # Test rejection detection
        email = {"body": "We regret to inform you that we are not moving forward.", "subject": "Application Update"}
        result = agent._fallback_classification(email)
        assert result["category"] == "not_interested"


class TestSchedulerAgent:
    """Test scheduler agent functionality"""
    
    def test_scheduler_agent_initialization(self):
        """Test scheduler agent loads"""
        from core.agents.scheduler import SchedulerAgent
        agent = SchedulerAgent()
        assert agent is not None
    
    def test_meeting_detection(self):
        """Test meeting request detection"""
        from core.agents.scheduler import SchedulerAgent
        from core.agents.base_agent import AgentContext
        
        agent = SchedulerAgent()
        context = AgentContext.create()
        
        email_content = "Can we schedule a call next week to discuss the role?"
        result = agent.execute(context, action="detect_request", email_content=email_content)
        
        # Should detect a meeting request
        assert result.success is True


class TestResumeOptimizer:
    """Test resume optimizer agent"""
    
    def test_resume_optimizer_initialization(self):
        """Test resume optimizer loads"""
        from core.agents.resume_optimizer import ResumeOptimizerAgent
        agent = ResumeOptimizerAgent()
        assert agent is not None
    
    def test_keyword_extraction(self):
        """Test keyword extraction from job description"""
        from core.agents.resume_optimizer import ResumeOptimizerAgent
        agent = ResumeOptimizerAgent()
        
        jd = "Looking for Python developer with Django and React experience. Must know SQL."
        keywords = agent._extract_keywords(jd)
        
        assert "python" in keywords
        assert "django" in keywords or "react" in keywords


class TestCoverLetterAgent:
    """Test cover letter agent"""
    
    def test_cover_letter_agent_initialization(self):
        """Test cover letter agent loads"""
        from core.agents.cover_letter import CoverLetterAgent
        agent = CoverLetterAgent()
        assert agent is not None


class TestEnhancedDaemon:
    """Test enhanced daemon functionality"""
    
    def test_daemon_initialization(self):
        """Test daemon loads"""
        from core.enhanced_daemon import EnhancedAutomationDaemon
        daemon = EnhancedAutomationDaemon()
        assert daemon is not None
        assert hasattr(daemon, 'health_monitor')
        assert hasattr(daemon, 'report_generator')
    
    def test_health_monitor(self):
        """Test health monitoring"""
        from core.enhanced_daemon import HealthMonitor
        monitor = HealthMonitor()
        
        components = {
            "orchestrator": True,
            "email_system": True,
            "inbox_monitor": True,
            "database": True
        }
        
        health = monitor.check_health(components, 3600)
        assert health.status == "healthy"
        assert health.consecutive_failures == 0


class TestJobDiscovery:
    """Test job discovery functionality"""
    
    def test_job_discovery_initialization(self):
        """Test job discovery loads"""
        from core.job_discovery import JobDiscovery
        discovery = JobDiscovery()
        assert discovery is not None
    
    def test_job_scoring(self):
        """Test job scoring"""
        from core.job_discovery import JobDiscovery, JobPosting
        discovery = JobDiscovery()
        
        job = JobPosting(
            source="test",
            source_id="123",
            company="TestCo",
            title="Software Engineering Intern",
            location="Remote",
            location_type="remote",
            url="https://example.com/job",
            apply_url="https://example.com/job",
            description="Python internship for summer 2026",
            employment_type="internship",
        )
        
        score = discovery._score_job(job)
        assert 0 <= score <= 1


class TestEmailSystem:
    """Test email system functionality"""
    
    def test_email_system_initialization(self):
        """Test email system loads"""
        from core.email_system import get_email_system
        # This may fail if not configured, so we just check it doesn't crash
        try:
            system = get_email_system()
            assert system is not None
        except Exception as e:
            # Expected if not configured
            pytest.skip(f"Email system not configured: {e}")


class TestConfiguration:
    """Test configuration system"""
    
    def test_config_loading(self):
        """Test configuration loads"""
        from utils.config import config
        assert config is not None
        assert hasattr(config, 'GMAIL_USER')
        assert hasattr(config, 'MAX_EMAILS_PER_DAY')
    
    def test_config_validation(self):
        """Test configuration validation"""
        from utils.config import config
        issues = config.validate_config()
        # May have issues if not fully configured, but shouldn't crash
        assert isinstance(issues, list)


class TestIntegration:
    """Integration tests across multiple components"""
    
    def test_full_orchestrator_cycle_dry_run(self):
        """Test full orchestrator cycle in dry-run mode"""
        from core.agents.orchestrator import get_orchestrator
        from core.agents.base_agent import AgentContext
        
        orchestrator = get_orchestrator()
        context = AgentContext.create()
        
        response = orchestrator.execute(context, max_actions=3, dry_run=True)
        
        assert response.success is True
        assert response.data["actions_taken"] <= 3
    
    def test_end_to_end_workflow(self):
        """Test end-to-end workflow simulation"""
        # This is a simulation without actually sending emails
        from core.agents.orchestrator import get_orchestrator
        from core.agents.base_agent import AgentContext
        
        orchestrator = get_orchestrator()
        context = AgentContext.create()
        
        # Analyze state
        state = orchestrator.analyze_state(context)
        assert "stats" in state
        assert "priorities" in state
        
        # Execute one action
        if state["priorities"]:
            priority = state["priorities"][0]
            response = orchestrator.execute_action(
                priority.get("type"), 
                context, 
                **priority
            )
            # Response may fail if dependencies aren't configured,
            # but it shouldn't crash
            assert response is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
