"""
Database management utilities for InternMailer.

This module provides utilities for database initialization, migration management,
and data seeding operations.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timezone

# Add the parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.exc import IntegrityError, OperationalError

from .session import get_session, create_tables, Base, engine
from .models import (
    User, Campaign, Contact, Template, Email, FollowUp, Log, Analytics,
    TenantType, CampaignStatus, EmailStatus, LogLevel
)
from .config import config


class DatabaseManager:
    """Database management utility class."""
    
    def __init__(self):
        self.session = None
    
    def init_database(self, drop_existing: bool = False) -> None:
        """
        Initialize the database with all tables.
        
        Args:
            drop_existing: Whether to drop existing tables first.
        """
        print("Initializing database...")
        try:
            create_tables(drop_existing=drop_existing)
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            raise
    
    def seed_initial_data(self) -> None:
        """Seed the database with initial data."""
        print("Seeding initial data...")
        
        try:
            with get_session() as session:
                # Create a default admin user for testing
                admin_user = User(
                    email="admin@internmailer.com",
                    username="admin",
                    full_name="Admin User",
                    password_hash="$2b$12$dummy_hash",  # In real app, use proper hashing
                    is_active=True,
                    is_verified=True,
                    tenant_type=TenantType.ACADEMIC.value,
                    organization="InternMailer",
                    position="Administrator",
                    monthly_email_limit=1000
                )
                session.add(admin_user)
                session.flush()  # Get the ID
                
                # Create default email templates
                academic_template = Template(
                    name="Academic Research Inquiry",
                    description="Standard template for contacting professors",
                    subject_template="Research Opportunity Inquiry - {{student_name}}",
                    body_template="""Dear Professor {{professor_name}},

I hope this email finds you well. My name is {{student_name}}, and I am a {{student_level}} student at {{student_university}} studying {{student_major}}.

I have been following your research work in {{research_area}}, particularly your recent work on {{specific_research}}. I am very interested in the intersection of {{student_interests}} and {{professor_research_area}}.

{{personalized_paragraph}}

I would be grateful for the opportunity to discuss potential research opportunities in your lab. I have attached my CV for your review.

Thank you for your time and consideration.

Best regards,
{{student_name}}
{{student_email}}""",
                    tenant_type=TenantType.ACADEMIC.value,
                    category="research_inquiry",
                    variables=[
                        "student_name", "professor_name", "student_level", 
                        "student_university", "student_major", "research_area",
                        "specific_research", "student_interests", 
                        "professor_research_area", "personalized_paragraph",
                        "student_email"
                    ],
                    user_id=admin_user.id,
                    is_system=True,
                    is_public=True
                )
                session.add(academic_template)
                
                corporate_template = Template(
                    name="Corporate Internship Inquiry",
                    description="Standard template for contacting companies",
                    subject_template="Internship Application - {{student_name}}",
                    body_template="""Dear {{contact_name}},

I hope this email finds you well. My name is {{student_name}}, and I am a {{student_level}} student at {{student_university}} majoring in {{student_major}}.

I am writing to express my strong interest in internship opportunities at {{company_name}}. Your company's work in {{company_focus}} aligns perfectly with my career interests and academic background.

{{personalized_paragraph}}

I would welcome the opportunity to contribute to your team while gaining valuable industry experience. Please find my resume attached for your consideration.

Thank you for your time and consideration.

Best regards,
{{student_name}}
{{student_email}}""",
                    tenant_type=TenantType.CORPORATE.value,
                    category="internship_inquiry",
                    variables=[
                        "student_name", "contact_name", "student_level",
                        "student_university", "student_major", "company_name",
                        "company_focus", "personalized_paragraph", "student_email"
                    ],
                    user_id=admin_user.id,
                    is_system=True,
                    is_public=True
                )
                session.add(corporate_template)
                
                # Create sample contacts
                academic_contact = Contact(
                    email="professor@university.edu",
                    first_name="John",
                    last_name="Smith",
                    title="Professor",
                    organization="MIT",
                    department="Computer Science",
                    position="Professor of Computer Science",
                    research_areas=["Machine Learning", "Natural Language Processing"],
                    publications_count=150,
                    h_index=45.0,
                    university_ranking=1,
                    data_source="csrankings",
                    confidence_score=0.95,
                    email_verified=True
                )
                session.add(academic_contact)
                
                corporate_contact = Contact(
                    email="hr@techcompany.com",
                    first_name="Jane",
                    last_name="Doe",
                    title="HR Manager",
                    organization="TechCorp",
                    department="Human Resources",
                    position="Senior HR Manager",
                    company_size="large",
                    industry="Technology",
                    company_stage="public",
                    data_source="manual",
                    confidence_score=0.9,
                    email_verified=True
                )
                session.add(corporate_contact)
                
                # Create a sample campaign
                sample_campaign = Campaign(
                    name="MIT CS Professors Outreach",
                    description="Reaching out to MIT Computer Science professors for research opportunities",
                    tenant_id=TenantType.ACADEMIC.value,
                    status=CampaignStatus.DRAFT.value,
                    template_id=academic_template.id,
                    target_criteria={
                        "universities": ["MIT"],
                        "research_areas": ["Machine Learning", "AI"],
                        "min_h_index": 20
                    },
                    daily_send_limit=10,
                    enable_followups=True,
                    followup_delay_days=7,
                    max_followups=2,
                    user_id=admin_user.id
                )
                session.add(sample_campaign)
                
                print("✅ Initial data seeded successfully")
                
        except IntegrityError as e:
            print(f"⚠️  Some initial data already exists: {e}")
        except Exception as e:
            print(f"❌ Error seeding initial data: {e}")
            raise
    
    def create_sample_analytics(self) -> None:
        """Create sample analytics data for testing."""
        print("Creating sample analytics data...")
        
        try:
            with get_session() as session:
                # Get a sample campaign
                campaign = session.query(Campaign).first()
                if not campaign:
                    print("⚠️  No campaigns found. Please seed initial data first.")
                    return
                
                # Create analytics entry
                analytics = Analytics(
                    campaign_id=campaign.id,
                    metric_type="daily",
                    date_period=datetime.now(timezone.utc),
                    emails_sent=50,
                    emails_delivered=48,
                    emails_bounced=2,
                    emails_opened=15,
                    unique_opens=12,
                    emails_clicked=5,
                    unique_clicks=4,
                    replies_received=3,
                    delivery_rate=0.96,
                    open_rate=0.31,
                    click_rate=0.10,
                    reply_rate=0.06,
                    bounce_rate=0.04,
                    tenant_type=campaign.tenant_id
                )
                session.add(analytics)
                
                print("✅ Sample analytics data created")
                
        except Exception as e:
            print(f"❌ Error creating sample analytics: {e}")
            raise
    
    def create_test_user(self, tenant_type: str = "academic") -> User:
        """
        Create a test user for development.
        
        Args:
            tenant_type: Type of tenant (academic or corporate).
            
        Returns:
            Created user instance.
        """
        try:
            with get_session() as session:
                user = User(
                    email=f"test_{tenant_type}@example.com",
                    username=f"test_{tenant_type}",
                    full_name=f"Test {tenant_type.title()} User",
                    password_hash="$2b$12$dummy_hash",
                    is_active=True,
                    is_verified=True,
                    tenant_type=tenant_type,
                    organization=f"Test {tenant_type.title()} Org",
                    position="Test User"
                )
                session.add(user)
                session.flush()
                
                print(f"✅ Test {tenant_type} user created: {user.email}")
                return user
                
        except IntegrityError:
            print(f"⚠️  Test {tenant_type} user already exists")
        except Exception as e:
            print(f"❌ Error creating test user: {e}")
            raise
    
    def cleanup_test_data(self) -> None:
        """Clean up test data from the database."""
        print("Cleaning up test data...")
        
        try:
            with get_session() as session:
                # Delete test users and related data
                test_users = session.query(User).filter(
                    User.email.like("test_%@example.com")
                ).all()
                
                for user in test_users:
                    session.delete(user)
                
                print("✅ Test data cleaned up")
                
        except Exception as e:
            print(f"❌ Error cleaning up test data: {e}")
            raise
    
    def show_statistics(self) -> None:
        """Show database statistics."""
        try:
            with get_session() as session:
                stats = {
                    "Users": session.query(User).count(),
                    "Campaigns": session.query(Campaign).count(),
                    "Contacts": session.query(Contact).count(),
                    "Templates": session.query(Template).count(),
                    "Emails": session.query(Email).count(),
                    "FollowUps": session.query(FollowUp).count(),
                    "Logs": session.query(Log).count(),
                    "Analytics": session.query(Analytics).count(),
                }
                
                print("\n📊 Database Statistics:")
                print("-" * 30)
                for table, count in stats.items():
                    print(f"{table:<12}: {count:>6}")
                print("-" * 30)
                
                # Show tenant distribution
                academic_campaigns = session.query(Campaign).filter(
                    Campaign.tenant_id == TenantType.ACADEMIC.value
                ).count()
                corporate_campaigns = session.query(Campaign).filter(
                    Campaign.tenant_id == TenantType.CORPORATE.value
                ).count()
                
                print(f"\n🎓 Academic Campaigns: {academic_campaigns}")
                print(f"🏢 Corporate Campaigns: {corporate_campaigns}")
                
        except Exception as e:
            print(f"❌ Error retrieving statistics: {e}")


def main():
    """Main CLI interface for database management."""
    parser = argparse.ArgumentParser(description="InternMailer Database Management")
    parser.add_argument(
        "command",
        choices=[
            "init", "seed", "analytics", "test-user", 
            "cleanup", "stats", "reset"
        ],
        help="Database management command"
    )
    parser.add_argument(
        "--tenant-type",
        choices=["academic", "corporate"],
        default="academic",
        help="Tenant type for test user creation"
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop existing tables before initialization"
    )
    
    args = parser.parse_args()
    db_manager = DatabaseManager()
    
    try:
        if args.command == "init":
            db_manager.init_database(drop_existing=args.drop)
        elif args.command == "seed":
            db_manager.seed_initial_data()
        elif args.command == "analytics":
            db_manager.create_sample_analytics()
        elif args.command == "test-user":
            db_manager.create_test_user(args.tenant_type)
        elif args.command == "cleanup":
            db_manager.cleanup_test_data()
        elif args.command == "stats":
            db_manager.show_statistics()
        elif args.command == "reset":
            print("⚠️  This will destroy all data. Are you sure? (y/N): ", end="")
            if input().lower() == 'y':
                db_manager.init_database(drop_existing=True)
                db_manager.seed_initial_data()
                print("✅ Database reset completed")
            else:
                print("Operation cancelled")
                
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
