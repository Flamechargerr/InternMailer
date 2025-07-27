"""
Campaign Management Core Demo

This script demonstrates the comprehensive campaign management functionality including:
- Creating campaigns with validation
- CRUD operations
- Campaign cloning
- State machine transitions
- Bulk operations
- History logging and analytics
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any
import json

from campaign_management import CampaignManager, CampaignState, BulkOperationType
from database.session import create_tables, get_session
from database.models import User, Template, Contact, TenantType


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CampaignDemo:
    """Demonstration class for campaign management functionality."""
    
    def __init__(self):
        self.campaign_manager = CampaignManager()
        self.demo_user_id = "demo-user-123"
        self.demo_template_id = None
        self.created_campaign_ids = []
    
    def setup_demo_data(self):
        """Set up demo users, templates, and contacts."""
        logger.info("Setting up demo data...")
        
        with get_session() as session:
            # Create demo user
            demo_user = User(
                id=self.demo_user_id,
                email="demo@example.com",
                username="demo_user",
                full_name="Demo User",
                password_hash="demo_hash",
                tenant_type=TenantType.ACADEMIC.value,
                organization="Demo University",
                position="Research Assistant"
            )
            session.merge(demo_user)  # Use merge to handle existing user
            
            # Create demo template
            demo_template = Template(
                name="Research Inquiry Template",
                description="Template for reaching out to professors for research opportunities",
                subject_template="Research Opportunity Inquiry - {{student_name}}",
                body_template="""Dear Professor {{professor_name}},

I hope this email finds you well. My name is {{student_name}}, and I am a {{student_year}} studying {{student_major}} at {{student_university}}.

I am very interested in your research in {{research_area}}, particularly your work on {{specific_research_topic}}. I would love to explore opportunities to contribute to your research as an undergraduate researcher.

My qualifications include:
- {{relevant_experience}}
- Skills: {{relevant_skills}}
- Relevant coursework: {{relevant_coursework}}

I have attached my resume for your review. Would you be available for a brief meeting to discuss potential research opportunities?

Thank you for your time and consideration.

Best regards,
{{student_name}}
{{student_email}}""",
                tenant_type=TenantType.ACADEMIC.value,
                category="research_inquiry",
                variables=["student_name", "professor_name", "research_area", "specific_research_topic"],
                user_id=self.demo_user_id,
                is_public=True
            )
            session.add(demo_template)
            session.flush()
            self.demo_template_id = demo_template.id
            
            # Create demo contacts
            demo_contacts = [
                Contact(
                    email="prof.anderson@university.edu",
                    first_name="John",
                    last_name="Anderson",
                    title="Professor",
                    organization="Stanford University",
                    department="Computer Science",
                    research_areas=["Machine Learning", "AI"],
                    email_verified=True
                ),
                Contact(
                    email="dr.chen@tech.edu",
                    first_name="Lisa",
                    last_name="Chen",
                    title="Associate Professor",
                    organization="MIT",
                    department="EECS",
                    research_areas=["Computer Vision", "Robotics"],
                    email_verified=True
                ),
                Contact(
                    email="prof.williams@research.edu",
                    first_name="Michael",
                    last_name="Williams",
                    title="Professor",
                    organization="Carnegie Mellon",
                    department="Machine Learning",
                    research_areas=["NLP", "Deep Learning"],
                    email_verified=True
                )
            ]
            
            for contact in demo_contacts:
                session.merge(contact)
            
            session.commit()
            logger.info("Demo data setup completed")
    
    def demo_campaign_creation(self):
        """Demonstrate campaign creation with validation."""
        logger.info("\n" + "="*60)
        logger.info("DEMO: Campaign Creation")
        logger.info("="*60)
        
        # Valid campaign creation
        campaign_data = {
            'name': 'ML Research Outreach 2024',
            'description': 'Outreach to machine learning professors for research opportunities',
            'tenant_id': TenantType.ACADEMIC.value,
            'template_id': self.demo_template_id,
            'target_criteria': {
                'research_areas': ['Machine Learning', 'AI', 'Computer Vision'],
                'universities': ['Stanford', 'MIT', 'Carnegie Mellon'],
                'min_h_index': 20
            },
            'contact_filters': {
                'email_verified': True,
                'department': ['Computer Science', 'EECS', 'Machine Learning']
            },
            'daily_send_limit': 25,
            'time_between_emails': 600,
            'followup_delay_days': 10,
            'max_followups': 1
        }
        
        try:
            campaign = self.campaign_manager.create_campaign(
                user_id=self.demo_user_id,
                campaign_data=campaign_data
            )
            self.created_campaign_ids.append(campaign.id)
            
            logger.info(f"✓ Campaign created successfully!")
            logger.info(f"  ID: {campaign.id}")
            logger.info(f"  Name: {campaign.name}")
            logger.info(f"  Status: {campaign.status}")
            logger.info(f"  Tenant: {campaign.tenant_id}")
            
            return campaign
            
        except Exception as e:
            logger.error(f"✗ Campaign creation failed: {e}")
            return None
    
    def demo_campaign_crud(self):
        """Demonstrate CRUD operations."""
        logger.info("\n" + "="*60)
        logger.info("DEMO: CRUD Operations")
        logger.info("="*60)
        
        # Create campaign
        campaign_data = {
            'name': 'CV Research Campaign',
            'description': 'Computer Vision research opportunities',
            'tenant_id': TenantType.ACADEMIC.value,
            'template_id': self.demo_template_id,
            'target_criteria': {'research_areas': ['Computer Vision']},
            'daily_send_limit': 10
        }
        
        # Create
        campaign = self.campaign_manager.create_campaign(self.demo_user_id, campaign_data)
        self.created_campaign_ids.append(campaign.id)
        logger.info(f"✓ Created campaign: {campaign.name}")
        
        # Read
        retrieved = self.campaign_manager.get_campaign(campaign.id, self.demo_user_id)
        logger.info(f"✓ Retrieved campaign: {retrieved.name if retrieved else 'Not found'}")
        
        # Update
        updates = {
            'description': 'Updated: Advanced Computer Vision research focus',
            'daily_send_limit': 15,
            'target_criteria': {
                'research_areas': ['Computer Vision', 'Image Processing'],
                'min_publications': 50
            }
        }
        updated = self.campaign_manager.update_campaign(campaign.id, self.demo_user_id, updates)
        logger.info(f"✓ Updated campaign description: {updated.description}")
        logger.info(f"✓ Updated daily limit: {updated.daily_send_limit}")
        
        # List campaigns with filters
        result = self.campaign_manager.get_campaigns(
            user_id=self.demo_user_id,
            filters={'tenant_id': TenantType.ACADEMIC.value},
            page=1,
            page_size=10
        )
        logger.info(f"✓ Listed campaigns: {len(result['campaigns'])} found, {result['total_count']} total")
        
        return campaign
    
    def demo_campaign_cloning(self):
        """Demonstrate campaign cloning."""
        logger.info("\n" + "="*60)
        logger.info("DEMO: Campaign Cloning")
        logger.info("="*60)
        
        if not self.created_campaign_ids:
            logger.warning("No campaigns available for cloning")
            return None
        
        original_id = self.created_campaign_ids[0]
        
        # Clone with modifications
        modifications = {
            'description': 'Cloned campaign with different target criteria',
            'target_criteria': {
                'research_areas': ['Natural Language Processing', 'AI'],
                'universities': ['Berkeley', 'CMU', 'Stanford']
            },
            'daily_send_limit': 20
        }
        
        try:
            cloned = self.campaign_manager.clone_campaign(
                campaign_id=original_id,
                user_id=self.demo_user_id,
                new_name='NLP Research Campaign (Cloned)',
                modifications=modifications
            )
            self.created_campaign_ids.append(cloned.id)
            
            logger.info(f"✓ Campaign cloned successfully!")
            logger.info(f"  Original ID: {original_id}")
            logger.info(f"  Cloned ID: {cloned.id}")
            logger.info(f"  Cloned Name: {cloned.name}")
            logger.info(f"  Modified criteria: {cloned.target_criteria}")
            
            return cloned
            
        except Exception as e:
            logger.error(f"✗ Campaign cloning failed: {e}")
            return None
    
    def demo_state_machine(self):
        """Demonstrate campaign state machine."""
        logger.info("\n" + "="*60)
        logger.info("DEMO: Campaign State Machine")
        logger.info("="*60)
        
        if not self.created_campaign_ids:
            logger.warning("No campaigns available for state transitions")
            return
        
        campaign_id = self.created_campaign_ids[0]
        
        try:
            # Get initial state
            campaign = self.campaign_manager.get_campaign(campaign_id, self.demo_user_id)
            logger.info(f"Initial state: {campaign.status}")
            
            # Schedule campaign
            future_time = datetime.now(timezone.utc) + timedelta(hours=1)
            updates = {'send_schedule': future_time}
            self.campaign_manager.update_campaign(campaign_id, self.demo_user_id, updates)
            
            # Start campaign (scheduled)
            started = self.campaign_manager.start_campaign(
                campaign_id=campaign_id,
                user_id=self.demo_user_id,
                send_immediately=False
            )
            logger.info(f"✓ Campaign scheduled: {started.status}")
            
            # Start immediately (override schedule)
            active = self.campaign_manager.start_campaign(
                campaign_id=campaign_id,
                user_id=self.demo_user_id,
                send_immediately=True
            )
            logger.info(f"✓ Campaign activated: {active.status}")
            
            # Pause campaign
            paused = self.campaign_manager.pause_campaign(
                campaign_id=campaign_id,
                user_id=self.demo_user_id,
                reason="Demo pause for testing"
            )
            logger.info(f"✓ Campaign paused: {paused.status}")
            
            # Resume campaign
            resumed = self.campaign_manager.resume_campaign(
                campaign_id=campaign_id,
                user_id=self.demo_user_id
            )
            logger.info(f"✓ Campaign resumed: {resumed.status}")
            
            # Show valid transitions
            current_state = CampaignState(resumed.status)
            valid_transitions = self.campaign_manager.state_machine.get_valid_transitions(current_state)
            logger.info(f"Valid transitions from {current_state.value}: {[s.value for s in valid_transitions]}")
            
        except Exception as e:
            logger.error(f"✗ State transition failed: {e}")
    
    def demo_bulk_operations(self):
        """Demonstrate bulk operations."""
        logger.info("\n" + "="*60)
        logger.info("DEMO: Bulk Operations")
        logger.info("="*60)
        
        # Create additional campaigns for bulk operations
        bulk_campaigns = []
        for i in range(3):
            campaign_data = {
                'name': f'Bulk Test Campaign {i+1}',
                'description': f'Campaign {i+1} for bulk operations demo',
                'tenant_id': TenantType.ACADEMIC.value,
                'template_id': self.demo_template_id,
                'target_criteria': {'research_areas': ['AI']},
                'daily_send_limit': 5
            }
            
            campaign = self.campaign_manager.create_campaign(self.demo_user_id, campaign_data)
            bulk_campaigns.append(campaign.id)
            self.created_campaign_ids.append(campaign.id)
        
        logger.info(f"Created {len(bulk_campaigns)} campaigns for bulk operations")
        
        try:
            # Bulk schedule
            schedule_time = datetime.now(timezone.utc) + timedelta(hours=2)
            result = self.campaign_manager.bulk_schedule(
                campaign_ids=bulk_campaigns,
                user_id=self.demo_user_id,
                schedule_time=schedule_time
            )
            logger.info(f"✓ Bulk schedule: {result.success_count}/{result.total_count} successful")
            
            # Bulk send now
            result = self.campaign_manager.bulk_send_now(
                campaign_ids=bulk_campaigns[:2],  # Send first 2 immediately
                user_id=self.demo_user_id
            )
            logger.info(f"✓ Bulk send now: {result.success_count}/{result.total_count} successful")
            
            # Bulk pause
            result = self.campaign_manager.bulk_pause(
                campaign_ids=bulk_campaigns[:2],
                user_id=self.demo_user_id,
                reason="Bulk demo pause"
            )
            logger.info(f"✓ Bulk pause: {result.success_count}/{result.total_count} successful")
            
            # Bulk resume
            result = self.campaign_manager.bulk_resume(
                campaign_ids=bulk_campaigns[:2],
                user_id=self.demo_user_id
            )
            logger.info(f"✓ Bulk resume: {result.success_count}/{result.total_count} successful")
            
            # Bulk cancel (last campaign)
            result = self.campaign_manager.bulk_cancel(
                campaign_ids=[bulk_campaigns[-1]],
                user_id=self.demo_user_id,
                reason="Bulk demo cancellation"
            )
            logger.info(f"✓ Bulk cancel: {result.success_count}/{result.total_count} successful")
            
            # Show any errors
            if result.errors:
                logger.info(f"Errors encountered: {result.errors}")
            
        except Exception as e:
            logger.error(f"✗ Bulk operations failed: {e}")
    
    def demo_history_and_analytics(self):
        """Demonstrate history logging and analytics."""
        logger.info("\n" + "="*60)
        logger.info("DEMO: History and Analytics")
        logger.info("="*60)
        
        if not self.created_campaign_ids:
            logger.warning("No campaigns available for history/analytics")
            return
        
        campaign_id = self.created_campaign_ids[0]
        
        try:
            # Get campaign history
            history = self.campaign_manager.get_campaign_history(campaign_id, self.demo_user_id)
            logger.info(f"✓ Campaign history retrieved: {len(history)} entries")
            
            # Show recent history entries
            for i, entry in enumerate(history[:5]):  # Show first 5
                timestamp = entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f"  {i+1}. [{timestamp}] {entry['level']}: {entry['message']}")
            
            # Get campaign analytics
            analytics = self.campaign_manager.get_campaign_analytics(campaign_id, self.demo_user_id)
            logger.info(f"✓ Campaign analytics retrieved")
            logger.info(f"  Campaign: {analytics['campaign_name']}")
            logger.info(f"  Status: {analytics['current_status']}")
            
            stats = analytics['statistics']
            logger.info(f"  Statistics:")
            logger.info(f"    Total emails: {stats['total_emails']}")
            logger.info(f"    Sent emails: {stats['sent_emails']}")
            logger.info(f"    Delivered emails: {stats['delivered_emails']}")
            logger.info(f"    Delivery rate: {stats['delivery_rate']:.2%}")
            logger.info(f"    Open rate: {stats['open_rate']:.2%}")
            logger.info(f"    Reply rate: {stats['reply_rate']:.2%}")
            
            logger.info(f"  Historical analytics: {len(analytics['historical_analytics'])} periods")
            
        except Exception as e:
            logger.error(f"✗ History/analytics retrieval failed: {e}")
    
    def demo_error_handling(self):
        """Demonstrate error handling and validation."""
        logger.info("\n" + "="*60)
        logger.info("DEMO: Error Handling")
        logger.info("="*60)
        
        # Test invalid campaign creation
        invalid_data = {
            'name': '',  # Empty name
            'tenant_id': 'invalid_tenant',  # Invalid tenant
            'template_id': 'non-existent-template'  # Non-existent template
        }
        
        try:
            self.campaign_manager.create_campaign(self.demo_user_id, invalid_data)
            logger.error("✗ Should have failed with validation error")
        except ValueError as e:
            logger.info(f"✓ Caught validation error: {e}")
        except Exception as e:
            logger.info(f"✓ Caught other error: {e}")
        
        # Test invalid state transition
        if self.created_campaign_ids:
            campaign_id = self.created_campaign_ids[0]
            
            # Try to transition to completed (should fail from current state)
            try:
                campaign = self.campaign_manager.get_campaign(campaign_id, self.demo_user_id)
                if campaign:
                    # Manually try invalid transition
                    current_state = CampaignState(campaign.status)
                    if not self.campaign_manager.state_machine.can_transition(current_state, CampaignState.COMPLETED):
                        logger.info(f"✓ Invalid transition detected: {current_state.value} -> {CampaignState.COMPLETED.value}")
            except Exception as e:
                logger.info(f"✓ Caught transition error: {e}")
        
        # Test non-existent campaign operations
        try:
            result = self.campaign_manager.get_campaign("non-existent-id", self.demo_user_id)
            if result is None:
                logger.info("✓ Non-existent campaign returned None (expected)")
        except Exception as e:
            logger.info(f"✓ Caught non-existent campaign error: {e}")
    
    def cleanup_demo_data(self):
        """Clean up demo data."""
        logger.info("\n" + "="*60)
        logger.info("DEMO: Cleanup")
        logger.info("="*60)
        
        # Cancel all created campaigns
        if self.created_campaign_ids:
            try:
                for campaign_id in self.created_campaign_ids:
                    try:
                        self.campaign_manager.cancel_campaign(
                            campaign_id=campaign_id,
                            user_id=self.demo_user_id,
                            reason="Demo cleanup"
                        )
                        logger.info(f"✓ Cancelled campaign: {campaign_id}")
                    except Exception as e:
                        logger.warning(f"Could not cancel campaign {campaign_id}: {e}")
                
                logger.info(f"Cleanup completed for {len(self.created_campaign_ids)} campaigns")
            except Exception as e:
                logger.error(f"Cleanup failed: {e}")
    
    def run_full_demo(self):
        """Run the complete demo."""
        logger.info("🚀 Starting Campaign Management Core Demo")
        logger.info("=" * 80)
        
        try:
            # Setup
            self.setup_demo_data()
            
            # Run demos
            self.demo_campaign_creation()
            self.demo_campaign_crud()
            self.demo_campaign_cloning()
            self.demo_state_machine()
            self.demo_bulk_operations()
            self.demo_history_and_analytics()
            self.demo_error_handling()
            
            # Cleanup
            self.cleanup_demo_data()
            
            logger.info("\n" + "🎉 Campaign Management Core Demo Completed Successfully!")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            raise


def main():
    """Main function to run the demo."""
    try:
        # Create database tables if they don't exist
        logger.info("Initializing database...")
        create_tables(drop_existing=False)
        
        # Run demo
        demo = CampaignDemo()
        demo.run_full_demo()
        
    except Exception as e:
        logger.error(f"Demo execution failed: {e}")
        raise


if __name__ == "__main__":
    main()
