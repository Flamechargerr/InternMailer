"""
Test script for InternMailer database setup.

This script tests the database models, connections, and basic operations
to ensure everything is working correctly.
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent))

from database.management import DatabaseManager
from database import get_session
from database.models import User, Campaign, Contact, Template, TenantType


def test_database_connection():
    """Test basic database connection."""
    print("🔌 Testing database connection...")
    try:
        with get_session() as session:
            # Simple query to test connection
            result = session.execute("SELECT 1").scalar()
            assert result == 1
            print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    return True


def test_model_creation():
    """Test creating and querying models."""
    print("📊 Testing model creation...")
    try:
        with get_session() as session:
            # Test creating a user
            user = User(
                email="test@example.com",
                username="testuser",
                full_name="Test User",
                password_hash="dummy_hash",
                tenant_type=TenantType.ACADEMIC.value
            )
            session.add(user)
            session.flush()  # Get the ID without committing
            
            # Test creating a template
            template = Template(
                name="Test Template",
                subject_template="Test Subject",
                body_template="Test Body",
                tenant_type=TenantType.ACADEMIC.value,
                user_id=user.id
            )
            session.add(template)
            session.flush()
            
            # Test creating a campaign
            campaign = Campaign(
                name="Test Campaign",
                tenant_id=TenantType.ACADEMIC.value,
                template_id=template.id,
                user_id=user.id
            )
            session.add(campaign)
            session.flush()
            
            # Test creating a contact
            contact = Contact(
                email="professor@university.edu",
                first_name="Test",
                last_name="Professor",
                organization="Test University",
                research_areas=["AI", "ML"]
            )
            session.add(contact)
            session.flush()
            
            # Verify relationships work
            assert user.campaigns[0].id == campaign.id
            assert campaign.template.id == template.id
            
            print("✅ Model creation and relationships working")
            
    except Exception as e:
        print(f"❌ Model creation failed: {e}")
        return False
    return True


def test_tenant_separation():
    """Test tenant separation functionality."""
    print("🏢 Testing tenant separation...")
    try:
        with get_session() as session:
            # Count academic campaigns
            academic_count = session.query(Campaign).filter(
                Campaign.tenant_id == TenantType.ACADEMIC.value
            ).count()
            
            # Count corporate campaigns  
            corporate_count = session.query(Campaign).filter(
                Campaign.tenant_id == TenantType.CORPORATE.value
            ).count()
            
            print(f"Academic campaigns: {academic_count}")
            print(f"Corporate campaigns: {corporate_count}")
            print("✅ Tenant separation queries working")
            
    except Exception as e:
        print(f"❌ Tenant separation test failed: {e}")
        return False
    return True


def test_json_fields():
    """Test JSON field functionality."""
    print("📝 Testing JSON fields...")
    try:
        with get_session() as session:
            # Test JSON fields in contacts
            contact = session.query(Contact).filter(
                Contact.research_areas.isnot(None)
            ).first()
            
            if contact and contact.research_areas:
                print(f"Contact research areas: {contact.research_areas}")
                assert isinstance(contact.research_areas, list)
            
            # Test JSON fields in campaigns
            campaign = session.query(Campaign).first()
            if campaign:
                campaign.target_criteria = {
                    "universities": ["MIT", "Stanford"],
                    "min_h_index": 20
                }
                session.flush()
                
                # Verify JSON was stored correctly
                retrieved = session.query(Campaign).filter(
                    Campaign.id == campaign.id
                ).first()
                assert retrieved.target_criteria["min_h_index"] == 20
                
            print("✅ JSON fields working correctly")
            
    except Exception as e:
        print(f"❌ JSON fields test failed: {e}")
        return False
    return True


def run_all_tests():
    """Run all database tests."""
    print("🚀 Starting InternMailer Database Tests")
    print("=" * 50)
    
    # Initialize database first
    db_manager = DatabaseManager()
    print("📋 Initializing test database...")
    db_manager.init_database(drop_existing=True)
    db_manager.seed_initial_data()
    
    tests = [
        test_database_connection,
        test_model_creation, 
        test_tenant_separation,
        test_json_fields,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        print("\n" + "-" * 30)
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📈 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Database setup is working correctly.")
        return True
    else:
        print("💥 Some tests failed. Please check the database setup.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
