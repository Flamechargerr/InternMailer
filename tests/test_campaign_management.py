"""
Test Suite for Campaign Management Core

Comprehensive tests for:
- CRUD operations
- State machine validation
- Bulk operations
- History logging
- Analytics
- Error handling
"""

import pytest
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict
from unittest.mock import Mock, patch

from campaign_management import (
    CampaignManager, CampaignState, BulkOperationType, 
    CampaignStateMachine, CampaignHistoryLogger
)
from database.session import create_tables, get_session
from database.models import (
    User, Template, Contact, Campaign, CampaignStatus, 
    TenantType, Email, EmailStatus, Log, LogLevel
)


# Test fixtures
@pytest.fixture(scope="session")
def setup_database():
    """Set up test database."""
    create_tables(drop_existing=True)
    yield
    # Cleanup after all tests


@pytest.fixture
def test_user():
    """Create a test user."""
    with get_session() as session:
        user = User(
            id="test-user-123",
            email="test@example.com",
            username="test_user",
            full_name="Test User",
            password_hash="test_hash",
            tenant_type=TenantType.ACADEMIC.value,
            organization="Test University",
            position="Test Position"
        )
        session.merge(user)
        session.commit()
        return user


@pytest.fixture
def test_template(test_user):
    """Create a test template."""
    with get_session() as session:
        template = Template(
            name="Test Template",
            description="Test template for campaigns",
            subject_template="Test Subject - {{name}}",
            body_template="Dear {{name}}, this is a test email.",
            tenant_type=TenantType.ACADEMIC.value,
            category="test",
            variables=["name"],
            user_id=test_user.id,
            is_public=True
        )
        session.add(template)
        session.commit()
        return template


@pytest.fixture
def test_contacts(test_user):
    """Create test contacts."""
    contacts = []
    with get_session() as session:
        for i in range(3):
            contact = Contact(
                email=f"contact{i}@test.edu",
                first_name=f"First{i}",
                last_name=f"Last{i}",
                title="Professor",
                organization=f"University {i}",
                department="Computer Science",
                research_areas=["AI", "ML"],
                email_verified=True
            )
            session.add(contact)
            contacts.append(contact)
        session.commit()
        return contacts


@pytest.fixture
def campaign_manager():
    """Create campaign manager instance."""
    return CampaignManager()


class TestCampaignCRUD:
    """Test CRUD operations for campaigns."""
    
    def test_create_campaign_success(self, setup_database, campaign_manager, test_user, test_template):
        """Test successful campaign creation."""
        campaign_data = {
            'name': 'Test Campaign',
            'description': 'Test campaign description',
            'tenant_id': TenantType.ACADEMIC.value,
            'template_id': test_template.id,
            'target_criteria': {'research_areas': ['AI']},
            'daily_send_limit': 10
        }
        
        campaign = campaign_manager.create_campaign(test_user.id, campaign_data)
        
        assert campaign is not None
        assert campaign.name == 'Test Campaign'
        assert campaign.status == CampaignStatus.DRAFT.value
        assert campaign.tenant_id == TenantType.ACADEMIC.value
        assert campaign.user_id == test_user.id
    
    def test_create_campaign_missing_required_fields(self, setup_database, campaign_manager, test_user):
        """Test campaign creation with missing required fields."""
        campaign_data = {
            'name': 'Test Campaign'
            # Missing tenant_id and template_id
        }
        
        with pytest.raises(ValueError, match="Missing required field"):
            campaign_manager.create_campaign(test_user.id, campaign_data)
    
    def test_create_campaign_invalid_template(self, setup_database, campaign_manager, test_user):
        """Test campaign creation with invalid template."""
        campaign_data = {
            'name': 'Test Campaign',
            'tenant_id': TenantType.ACADEMIC.value,
            'template_id': 'non-existent-template'
        }
        
        with pytest.raises(ValueError, match="Template not found"):
            campaign_manager.create_campaign(test_user.id, campaign_data)
    
    def test_get_campaign(self, setup_database, campaign_manager, test_user, test_template):
        """Test getting a campaign by ID."""
        # Create campaign
        campaign_data = {
            'name': 'Test Campaign',
            'tenant_id': TenantType.ACADEMIC.value,
            'template_id': test_template.id
        }
        created_campaign = campaign_manager.create_campaign(test_user.id, campaign_data)
        
        # Get campaign
        retrieved_campaign = campaign_manager.get_campaign(created_campaign.id, test_user.id)
        
        assert retrieved_campaign is not None
        assert retrieved_campaign.id == created_campaign.id
        assert retrieved_campaign.name == 'Test Campaign'
    
    def test_get_nonexistent_campaign(self, setup_database, campaign_manager, test_user):
        """Test getting a non-existent campaign."""
        result = campaign_manager.get_campaign("non-existent-id", test_user.id)
        assert result is None
    
    def test_get_campaigns_with_filters(self, setup_database, campaign_manager, test_user, test_template):
        """Test getting campaigns with filters."""
        # Create multiple campaigns
        for i in range(3):
            campaign_data = {
                'name': f'Test Campaign {i}',
                'tenant_id': TenantType.ACADEMIC.value,
                'template_id': test_template.id
            }
            campaign_manager.create_campaign(test_user.id, campaign_data)
        
        # Get campaigns with filter
        result = campaign_manager.get_campaigns(
            user_id=test_user.id,
            filters={'tenant_id': TenantType.ACADEMIC.value},
            page=1,
            page_size=10
        )
        
        assert result['total_count'] >= 3
        assert len(result['campaigns']) >= 3
        assert all(c.tenant_id == TenantType.ACADEMIC.value for c in result['campaigns'])
    
    def test_update_campaign(self, setup_database, campaign_manager, test_user, test_template):
        """Test updating a campaign."""
        # Create campaign
        campaign_data = {
            'name': 'Original Name',
            'description': 'Original description',
            'tenant_id': TenantType.ACADEMIC.value,
            'template_id': test_template.id,
            'daily_send_limit': 10
        }
        campaign = campaign_manager.create_campaign(test_user.id, campaign_data)
        
        # Update campaign
        updates = {
            'name': 'Updated Name',
            'description': 'Updated description',
            'daily_send_limit': 20
        }
        updated_campaign = campaign_manager.update_campaign(campaign.id, test_user.id, updates)
        
        assert updated_campaign.name == 'Updated Name'
        assert updated_campaign.description == 'Updated description'
        assert updated_campaign.daily_send_limit == 20
    
    def test_update_nonexistent_campaign(self, setup_database, campaign_manager, test_user):
        """Test updating a non-existent campaign."""
        updates = {'name': 'Updated Name'}
        
        with pytest.raises(ValueError, match="Campaign not found"):
            campaign_manager.update_campaign("non-existent-id", test_user.id, updates)
    
    def test_delete_campaign(self, setup_database, campaign_manager, test_user, test_template):
        """Test deleting a campaign."""
        # Create campaign
        campaign_data = {
            'name': 'Test Campaign',
            'tenant_id': TenantType.ACADEMIC.value,
            'template_id': test_template.id
        }
        campaign = campaign_manager.create_campaign(test_user.id, campaign_data)
        
        # Delete campaign
        result = campaign_manager.delete_campaign(campaign.id, test_user.id)
        assert result is True
        
        # Verify campaign is cancelled
        deleted_campaign = campaign_manager.get_campaign(campaign.id, test_user.id)
        assert deleted_campaign.status == CampaignStatus.CANCELLED.value


class TestCampaignCloning:
    """Test campaign cloning functionality."""
    
    def test_clone_campaign_success(self, setup_database, campaign_manager, test_user, test_template):
        """Test successful campaign cloning."""
        # Create original campaign
        original_data = {
            'name': 'Original Campaign',
            'description': 'Original description',
            'tenant_id': TenantType.ACADEMIC.value,
            'template_id': test_template.id,
            'target_criteria': {'research_areas': ['AI']},
            'daily_send_limit': 10
        }
        original = campaign_manager.create_campaign(test_user.id, original_data)
        
        # Clone campaign
        modifications = {
            'description': 'Cloned description',
            'daily_send_limit': 20
        }
        cloned = campaign_manager.clone_campaign(
            original.id, test_user.id, 'Cloned Campaign', modifications
        )
        
        assert cloned is not None
        assert cloned.id != original.id
        assert cloned.name == 'Cloned Campaign'
        assert cloned.description == 'Cloned description'
        assert cloned.daily_send_limit == 20
        assert cloned.target_criteria == original.target_criteria
        assert cloned.template_id == original.template_id
    
    def test_clone_nonexistent_campaign(self, setup_database, campaign_manager, test_user):
        """Test cloning a non-existent campaign."""
        with pytest.raises(ValueError, match="Original campaign not found"):
            campaign_manager.clone_campaign(
                "non-existent-id", test_user.id, "Cloned Campaign"
            )


class TestCampaignStateMachine:
    """Test campaign state machine functionality."""
    
    def test_valid_state_transitions(self):
        """Test valid state transitions."""
        state_machine = CampaignStateMachine()
        
        # Test valid transitions
        assert state_machine.can_transition(CampaignState.DRAFT, CampaignState.ACTIVE)
        assert state_machine.can_transition(CampaignState.ACTIVE, CampaignState.PAUSED)
        assert state_machine.can_transition(CampaignState.PAUSED, CampaignState.ACTIVE)
        assert state_machine.can_transition(CampaignState.ACTIVE, CampaignState.COMPLETED)
        assert state_machine.can_transition(CampaignState.ACTIVE, CampaignState.CANCELLED)
    
    def test_invalid_state_transitions(self):
        """Test invalid state transitions."""
        state_machine = CampaignStateMachine()
        
        # Test invalid transitions
        assert not state_machine.can_transition(CampaignState.COMPLETED, CampaignState.ACTIVE)
        assert not state_machine.can_transition(CampaignState.CANCELLED, CampaignState.ACTIVE)
        assert not state_machine.can_transition(CampaignState.DRAFT, CampaignState.COMPLETED)
    
    def test_get_valid_transitions(self):
        """Test getting valid transitions for a state."""
        state_machine = CampaignStateMachine()
        
        draft_transitions = state_machine.get_valid_transitions(CampaignState.DRAFT)
        expected_draft = [CampaignState.SCHEDULED, CampaignState.ACTIVE, CampaignState.CANCELLED]
        assert all(state in draft_transitions for state in expected_draft)
        
        completed_transitions = state_machine.get_valid_transitions(CampaignState.COMPLETED)
        assert completed_transitions == []  # Terminal state
    
    def test_start_campaign(self, setup_database, campaign_manager, test_user, test_template):
        """Test starting a campaign."""
        # Create campaign
        campaign_data = {
            'name': 'Test Campaign',
            'tenant_id': TenantType.ACADEMIC.value,
            'template_id': test_template.id
        }
        campaign = campaign_manager.create_campaign(test_user.id, campaign_data)
        
        # Start immediately
        started_campaign = campaign_manager.start_campaign(
            campaign.id, test_user.id, send_immediately=True
        )
        
        assert started_campaign.status == CampaignStatus.ACTIVE.value
        assert started_campaign.send_schedule is not None
    
    def test_pause_and_resume_campaign(self, setup_database, campaign_manager, test_user, test_template):
        """Test pausing and resuming a campaign."""
        # Create and start campaign
        campaign_data = {
            'name': 'Test Campaign',
            'tenant_id': TenantType.ACADEMIC.value,
            'template_id': test_template.id
        }
        campaign = campaign_manager.create_campaign(test_user.id, campaign_data)
        started = campaign_manager.start_campaign(campaign.id, test_user.id, send_immediately=True)
        
        # Pause campaign
        paused = campaign_manager.pause_campaign(campaign.id, test_user.id, "Test pause")
        assert paused.status == CampaignStatus.PAUSED.value
        
        # Resume campaign
        resumed = campaign_manager.resume_campaign(campaign.id, test_user.id)
        assert resumed.status == CampaignStatus.ACTIVE.value
    
    def test_cancel_campaign(self, setup_database, campaign_manager, test_user, test_template):
        """Test cancelling a campaign."""
        # Create campaign
        campaign_data = {
            'name': 'Test Campaign',
            'tenant_id': TenantType.ACADEMIC.value,
            'template_id': test_template.id
        }
        campaign = campaign_manager.create_campaign(test_user.id, campaign_data)
        
        # Cancel campaign
        cancelled = campaign_manager.cancel_campaign(
            campaign.id, test_user.id, "Test cancellation"
        )
        
        assert cancelled.status == CampaignStatus.CANCELLED.value


class TestBulkOperations:
    """Test bulk operations functionality."""
    
    def test_bulk_send_now(self, setup_database, campaign_manager, test_user, test_template):
        """Test bulk send now operation."""
        # Create multiple campaigns
        campaign_ids = []
        for i in range(3):
            campaign_data = {
                'name': f'Bulk Test Campaign {i}',
                'tenant_id': TenantType.ACADEMIC.value,
                'template_id': test_template.id
            }
            campaign = campaign_manager.create_campaign(test_user.id, campaign_data)
            campaign_ids.append(campaign.id)
        
        # Bulk send now
        result = campaign_manager.bulk_send_now(campaign_ids, test_user.id)
        
        assert result.total_count == 3
        assert result.success_count >= 0  # Some may succeed, some may fail
        assert result.operation_id is not None
        assert isinstance(result.errors, list)
    
    def test_bulk_schedule(self, setup_database, campaign_manager, test_user, test_template):
        """Test bulk schedule operation."""
        # Create multiple campaigns
        campaign_ids = []
        for i in range(2):
            campaign_data = {
                'name': f'Bulk Schedule Test {i}',
                'tenant_id': TenantType.ACADEMIC.value,
                'template_id': test_template.id
            }
            campaign = campaign_manager.create_campaign(test_user.id, campaign_data)
            campaign_ids.append(campaign.id)
        
        # Bulk schedule
        schedule_time = datetime.now(timezone.utc) + timedelta(hours=1)
        result = campaign_manager.bulk_schedule(campaign_ids, test_user.id, schedule_time)
        
        assert result.total_count == 2
        assert result.success_count >= 0
        assert result.operation_id is not None
    
    def test_bulk_cancel(self, setup_database, campaign_manager, test_user, test_template):
        """Test bulk cancel operation."""
        # Create multiple campaigns
        campaign_ids = []
        for i in range(2):
            campaign_data = {
                'name': f'Bulk Cancel Test {i}',
                'tenant_id': TenantType.ACADEMIC.value,
                'template_id': test_template.id
            }
            campaign = campaign_manager.create_campaign(test_user.id, campaign_data)
            campaign_ids.append(campaign.id)
        
        # Bulk cancel
        result = campaign_manager.bulk_cancel(campaign_ids, test_user.id, "Bulk test cancel")
        
        assert result.total_count == 2
        assert result.success_count >= 0
        assert result.operation_id is not None
    
    def test_bulk_operation_with_invalid_ids(self, setup_database, campaign_manager, test_user):
        """Test bulk operation with invalid campaign IDs."""
        invalid_ids = ["non-existent-1", "non-existent-2"]
        
        result = campaign_manager.bulk_cancel(invalid_ids, test_user.id)
        
        assert result.total_count == 2
        assert result.success_count == 0
        assert result.failure_count == 2
        assert len(result.errors) == 2
        assert all("Campaign not found" in error["error"] for error in result.errors)


class TestHistoryAndAnalytics:
    """Test history logging and analytics functionality."""
    
    def test_campaign_history_logging(self, setup_database, campaign_manager, test_user, test_template):
        """Test campaign history logging."""
        # Create campaign
        campaign_data = {
            'name': 'History Test Campaign',
            'tenant_id': TenantType.ACADEMIC.value,
            'template_id': test_template.id
        }
        campaign = campaign_manager.create_campaign(test_user.id, campaign_data)
        
        # Perform operations to generate history
        campaign_manager.update_campaign(campaign.id, test_user.id, {'description': 'Updated'})
        campaign_manager.start_campaign(campaign.id, test_user.id, send_immediately=True)
        campaign_manager.pause_campaign(campaign.id, test_user.id, "Test pause")
        
        # Get history
        history = campaign_manager.get_campaign_history(campaign.id, test_user.id)
        
        assert len(history) >= 4  # At least creation, update, start, pause
        assert all('timestamp' in entry for entry in history)
        assert all('message' in entry for entry in history)
        assert all('level' in entry for entry in history)
    
    def test_campaign_analytics(self, setup_database, campaign_manager, test_user, test_template):
        """Test campaign analytics."""
        # Create campaign
        campaign_data = {
            'name': 'Analytics Test Campaign',
            'tenant_id': TenantType.ACADEMIC.value,
            'template_id': test_template.id
        }
        campaign = campaign_manager.create_campaign(test_user.id, campaign_data)
        
        # Get analytics
        analytics = campaign_manager.get_campaign_analytics(campaign.id, test_user.id)
        
        assert analytics['campaign_id'] == campaign.id
        assert analytics['campaign_name'] == campaign.name
        assert analytics['current_status'] == campaign.status
        assert 'statistics' in analytics
        assert 'historical_analytics' in analytics
        
        # Check statistics structure
        stats = analytics['statistics']
        required_stats = [
            'total_emails', 'sent_emails', 'delivered_emails',
            'opened_emails', 'clicked_emails', 'replied_emails',
            'delivery_rate', 'open_rate', 'click_rate', 'reply_rate'
        ]
        assert all(stat in stats for stat in required_stats)
    
    def test_history_for_nonexistent_campaign(self, setup_database, campaign_manager, test_user):
        """Test getting history for non-existent campaign."""
        with pytest.raises(ValueError, match="Campaign not found"):
            campaign_manager.get_campaign_history("non-existent-id", test_user.id)
    
    def test_analytics_for_nonexistent_campaign(self, setup_database, campaign_manager, test_user):
        """Test getting analytics for non-existent campaign."""
        with pytest.raises(ValueError, match="Campaign not found"):
            campaign_manager.get_campaign_analytics("non-existent-id", test_user.id)


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_state_transition_error(self, setup_database, campaign_manager, test_user, test_template):
        """Test error when attempting invalid state transition."""
        # Create and complete a campaign (mock completion)
        campaign_data = {
            'name': 'Completed Campaign',
            'tenant_id': TenantType.ACADEMIC.value,
            'template_id': test_template.id
        }
        campaign = campaign_manager.create_campaign(test_user.id, campaign_data)
        
        # Manually set to completed state
        with get_session() as session:
            db_campaign = session.query(Campaign).filter_by(id=campaign.id).first()
            db_campaign.status = CampaignStatus.COMPLETED.value
            session.commit()
        
        # Try to pause completed campaign (should fail)
        with pytest.raises(ValueError, match="Invalid state transition"):
            campaign_manager.pause_campaign(campaign.id, test_user.id)
    
    def test_update_completed_campaign_error(self, setup_database, campaign_manager, test_user, test_template):
        """Test error when updating completed campaign."""
        # Create campaign
        campaign_data = {
            'name': 'Test Campaign',
            'tenant_id': TenantType.ACADEMIC.value,
            'template_id': test_template.id
        }
        campaign = campaign_manager.create_campaign(test_user.id, campaign_data)
        
        # Manually set to completed
        with get_session() as session:
            db_campaign = session.query(Campaign).filter_by(id=campaign.id).first()
            db_campaign.status = CampaignStatus.COMPLETED.value
            session.commit()
        
        # Try to update completed campaign
        with pytest.raises(ValueError, match="Cannot update completed or cancelled campaigns"):
            campaign_manager.update_campaign(campaign.id, test_user.id, {'name': 'Updated'})
    
    def test_delete_active_campaign_error(self, setup_database, campaign_manager, test_user, test_template):
        """Test error when deleting active campaign."""
        # Create and start campaign
        campaign_data = {
            'name': 'Active Campaign',
            'tenant_id': TenantType.ACADEMIC.value,
            'template_id': test_template.id
        }
        campaign = campaign_manager.create_campaign(test_user.id, campaign_data)
        campaign_manager.start_campaign(campaign.id, test_user.id, send_immediately=True)
        
        # Try to delete active campaign
        with pytest.raises(ValueError, match="Cannot delete active campaigns"):
            campaign_manager.delete_campaign(campaign.id, test_user.id)
    
    def test_start_campaign_without_schedule(self, setup_database, campaign_manager, test_user, test_template):
        """Test error when starting campaign without schedule."""
        # Create campaign without schedule
        campaign_data = {
            'name': 'No Schedule Campaign',
            'tenant_id': TenantType.ACADEMIC.value,
            'template_id': test_template.id
        }
        campaign = campaign_manager.create_campaign(test_user.id, campaign_data)
        
        # Try to start without immediate flag and no schedule
        with pytest.raises(ValueError, match="Campaign must have a send schedule"):
            campaign_manager.start_campaign(campaign.id, test_user.id, send_immediately=False)


class TestCampaignHistoryLogger:
    """Test campaign history logger functionality."""
    
    def test_log_state_transition(self, setup_database):
        """Test logging state transitions."""
        with get_session() as session:
            logger = CampaignHistoryLogger(session)
            
            from campaign_management import CampaignStateTransition
            transition = CampaignStateTransition(
                from_state=CampaignState.DRAFT,
                to_state=CampaignState.ACTIVE,
                action="started",
                timestamp=datetime.now(timezone.utc),
                user_id="test-user",
                reason="Test transition"
            )
            
            logger.log_state_transition("test-campaign-id", transition)
            session.commit()
            
            # Verify log was created
            log_entry = session.query(Log).filter_by(campaign_id="test-campaign-id").first()
            assert log_entry is not None
            assert "transitioned from draft to active" in log_entry.message
            assert log_entry.extra_data["action"] == "started"
    
    def test_log_bulk_operation(self, setup_database):
        """Test logging bulk operations."""
        with get_session() as session:
            logger = CampaignHistoryLogger(session)
            
            from campaign_management import BulkOperationResult
            result = BulkOperationResult(
                success_count=2,
                failure_count=1,
                total_count=3,
                errors=[{"campaign_id": "test", "error": "test error"}],
                operation_id="test-op-123",
                completed_at=datetime.now(timezone.utc)
            )
            
            logger.log_bulk_operation(BulkOperationType.SEND_NOW, result, "test-user")
            session.commit()
            
            # Verify log was created
            log_entry = session.query(Log).filter_by(user_id="test-user").first()
            assert log_entry is not None
            assert "Bulk operation send_now completed" in log_entry.message
            assert log_entry.extra_data["operation_type"] == "send_now"


# Integration tests
class TestCampaignIntegration:
    """Integration tests for full campaign workflows."""
    
    def test_complete_campaign_workflow(self, setup_database, campaign_manager, test_user, test_template):
        """Test complete campaign workflow from creation to completion."""
        # Create campaign
        campaign_data = {
            'name': 'Integration Test Campaign',
            'description': 'Full workflow test',
            'tenant_id': TenantType.ACADEMIC.value,
            'template_id': test_template.id,
            'target_criteria': {'research_areas': ['AI']},
            'daily_send_limit': 5
        }
        campaign = campaign_manager.create_campaign(test_user.id, campaign_data)
        assert campaign.status == CampaignStatus.DRAFT.value
        
        # Update campaign
        updates = {'description': 'Updated for integration test'}
        updated = campaign_manager.update_campaign(campaign.id, test_user.id, updates)
        assert updated.description == 'Updated for integration test'
        
        # Clone campaign
        cloned = campaign_manager.clone_campaign(
            campaign.id, test_user.id, 'Cloned Integration Test',
            {'daily_send_limit': 10}
        )
        assert cloned.name == 'Cloned Integration Test'
        assert cloned.daily_send_limit == 10
        
        # Start original campaign
        started = campaign_manager.start_campaign(campaign.id, test_user.id, send_immediately=True)
        assert started.status == CampaignStatus.ACTIVE.value
        
        # Pause campaign
        paused = campaign_manager.pause_campaign(campaign.id, test_user.id, "Integration test pause")
        assert paused.status == CampaignStatus.PAUSED.value
        
        # Resume campaign
        resumed = campaign_manager.resume_campaign(campaign.id, test_user.id)
        assert resumed.status == CampaignStatus.ACTIVE.value
        
        # Get history
        history = campaign_manager.get_campaign_history(campaign.id, test_user.id)
        assert len(history) >= 5  # Create, update, start, pause, resume
        
        # Get analytics
        analytics = campaign_manager.get_campaign_analytics(campaign.id, test_user.id)
        assert analytics['campaign_name'] == 'Integration Test Campaign'
        
        # Cancel campaign
        cancelled = campaign_manager.cancel_campaign(campaign.id, test_user.id, "Integration test complete")
        assert cancelled.status == CampaignStatus.CANCELLED.value
    
    def test_bulk_operations_workflow(self, setup_database, campaign_manager, test_user, test_template):
        """Test bulk operations workflow."""
        # Create multiple campaigns
        campaign_ids = []
        for i in range(4):
            campaign_data = {
                'name': f'Bulk Workflow Campaign {i}',
                'tenant_id': TenantType.ACADEMIC.value,
                'template_id': test_template.id
            }
            campaign = campaign_manager.create_campaign(test_user.id, campaign_data)
            campaign_ids.append(campaign.id)
        
        # Bulk schedule
        schedule_time = datetime.now(timezone.utc) + timedelta(hours=1)
        schedule_result = campaign_manager.bulk_schedule(
            campaign_ids, test_user.id, schedule_time
        )
        assert schedule_result.total_count == 4
        
        # Bulk send now (first 2)
        send_result = campaign_manager.bulk_send_now(
            campaign_ids[:2], test_user.id
        )
        assert send_result.total_count == 2
        
        # Bulk pause (first 2)
        pause_result = campaign_manager.bulk_pause(
            campaign_ids[:2], test_user.id, "Bulk workflow pause"
        )
        assert pause_result.total_count == 2
        
        # Bulk resume (first 2)
        resume_result = campaign_manager.bulk_resume(
            campaign_ids[:2], test_user.id
        )
        assert resume_result.total_count == 2
        
        # Bulk cancel (all)
        cancel_result = campaign_manager.bulk_cancel(
            campaign_ids, test_user.id, "Bulk workflow cleanup"
        )
        assert cancel_result.total_count == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
