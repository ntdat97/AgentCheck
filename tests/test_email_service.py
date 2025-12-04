"""
Tests for Email Service
"""
import pytest
import sys
import json
from pathlib import Path
from datetime import datetime

# Add api to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.services.email_service import EmailService
from api.models.schemas import ExtractedFields, UniversityContact


class TestEmailService:
    """Tests for email service functionality."""
    
    @pytest.fixture
    def service(self, tmp_path):
        """Create service with test data directory."""
        return EmailService(str(tmp_path))
    
    @pytest.fixture
    def sample_contact(self):
        """Sample university contact."""
        return UniversityContact(
            name="University of Example",
            email="verify@example.edu",
            country="USA",
            verification_department="Office of the Registrar"
        )
    
    @pytest.fixture
    def sample_fields(self):
        """Sample extracted fields."""
        return ExtractedFields(
            candidate_name="John Smith",
            university_name="University of Example",
            degree_name="Bachelor of Science",
            issue_date="2023-05-15"
        )
    
    def test_init(self, service):
        """Test service initialization."""
        assert service is not None
        assert service.outbox_dir.exists()
        assert service.inbox_dir.exists()
    
    def test_create_outgoing_email(self, service, sample_contact, sample_fields):
        """Test creating an outgoing email."""
        email = service.create_outgoing_email(
            recipient=sample_contact,
            subject="Test Verification",
            body="Test body content",
            certificate_info=sample_fields
        )
        
        assert email is not None
        assert email.recipient_email == sample_contact.email
        assert email.subject == "Test Verification"
        assert email.body == "Test body content"
        assert email.reference_id.startswith("VER-")
    
    def test_outgoing_email_saved(self, service, sample_contact, sample_fields):
        """Test that outgoing email is saved to file."""
        email = service.create_outgoing_email(
            recipient=sample_contact,
            subject="Test",
            body="Body",
            certificate_info=sample_fields
        )
        
        filepath = service.outbox_dir / f"{email.reference_id}.json"
        assert filepath.exists()
        
        with open(filepath) as f:
            data = json.load(f)
        
        assert data["recipient_email"] == sample_contact.email
    
    def test_get_simulated_reply_verified(self, service):
        """Test getting verified reply."""
        reply = service.get_simulated_reply(
            reference_id="TEST-123",
            university_name="Test University",
            university_email="test@uni.edu",
            scenario="verified"
        )
        
        assert reply is not None
        assert "confirm" in reply.body.lower()
        assert reply.reference_id == "TEST-123"
    
    def test_get_simulated_reply_not_verified(self, service):
        """Test getting not verified reply."""
        reply = service.get_simulated_reply(
            reference_id="TEST-456",
            university_name="Test University",
            university_email="test@uni.edu",
            scenario="not_verified"
        )
        
        assert reply is not None
        assert any(word in reply.body.lower() for word in ["cannot", "no record", "not"])
    
    def test_get_simulated_reply_inconclusive(self, service):
        """Test getting inconclusive reply."""
        reply = service.get_simulated_reply(
            reference_id="TEST-789",
            university_name="Test University",
            university_email="test@uni.edu",
            scenario="inconclusive"
        )
        
        assert reply is not None
        assert any(word in reply.body.lower() for word in ["additional", "information", "require"])
    
    def test_reply_saved_to_inbox(self, service):
        """Test that reply is saved to inbox."""
        reply = service.get_simulated_reply(
            reference_id="SAVE-TEST",
            university_name="Test University",
            university_email="test@uni.edu",
            scenario="verified"
        )
        
        filepath = service.inbox_dir / f"{reply.reference_id}_reply.json"
        assert filepath.exists()
    
    def test_list_outbox(self, service, sample_contact, sample_fields):
        """Test listing outbox emails."""
        # Create a few emails
        for i in range(3):
            service.create_outgoing_email(
                recipient=sample_contact,
                subject=f"Test {i}",
                body=f"Body {i}",
                certificate_info=sample_fields
            )
        
        emails = service.list_outbox()
        assert len(emails) >= 3
    
    def test_get_reply_by_reference(self, service):
        """Test getting reply by reference ID."""
        service.get_simulated_reply(
            reference_id="GET-BY-REF",
            university_name="Test University",
            university_email="test@uni.edu",
            scenario="verified"
        )
        
        reply = service.get_reply_by_reference("GET-BY-REF")
        assert reply is not None
        assert reply.reference_id == "GET-BY-REF"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
