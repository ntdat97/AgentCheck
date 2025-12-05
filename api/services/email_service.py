"""
Email Service
Handles drafting, storing, and simulating email communications.
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import random

from api.models.schemas import (
    OutgoingEmail, 
    IncomingEmail, 
    ExtractedFields,
    UniversityContact
)


class EmailService:
    """Service for email operations (simulated)."""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.outbox_dir = self.data_dir / "outbox"
        self.inbox_dir = self.data_dir / "inbox"
        
        # Ensure directories exist
        self.outbox_dir.mkdir(parents=True, exist_ok=True)
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
    
    def create_outgoing_email(
        self,
        recipient: UniversityContact,
        subject: str,
        body: str,
        certificate_info: ExtractedFields,
        reference_id: Optional[str] = None
    ) -> OutgoingEmail:
        """
        Create and store an outgoing verification email.
        
        Args:
            recipient: University contact information
            subject: Email subject line
            body: Email body content
            certificate_info: Extracted certificate fields
            reference_id: Optional reference ID (auto-generated if not provided)
            
        Returns:
            OutgoingEmail object
        """
        if not reference_id:
            reference_id = f"VER-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        email = OutgoingEmail(
            recipient_email=recipient.email,
            recipient_name=recipient.name,
            subject=subject,
            body=body,
            reference_id=reference_id,
            certificate_info=certificate_info
        )
        
        # Store in outbox
        self._save_to_outbox(email)
        
        return email
    
    def _save_to_outbox(self, email: OutgoingEmail) -> None:
        """Save email to outbox directory."""
        filename = f"{email.reference_id}.json"
        filepath = self.outbox_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(email.model_dump(mode='json'), f, indent=2, default=str)
    
    def get_simulated_reply(
        self,
        reference_id: str,
        university_name: str,
        university_email: str,
        scenario: str = "verified"
    ) -> IncomingEmail:
        """
        Generate a simulated university reply.
        
        Args:
            reference_id: Original verification request reference
            university_name: Name of the university
            university_email: University email address
            scenario: One of 'verified', 'not_verified', 'inconclusive', 'suspicious', 'ambiguous'
            
        Returns:
            IncomingEmail object with simulated reply
        """
        replies = self._get_reply_templates()
        
        if scenario not in replies:
            scenario = random.choice(list(replies.keys()))
        
        template = replies[scenario]
        
        # Personalize the reply
        body = template["body"].format(
            university_name=university_name,
            reference_id=reference_id
        )
        
        # Support sender override for suspicious scenarios
        sender_email = template.get("override_sender_email", university_email)
        sender_name = template.get("override_sender_name", f"Registrar Office - {university_name}")
        
        reply = IncomingEmail(
            sender_email=sender_email,
            sender_name=sender_name,
            subject=f"RE: Verification Request - {reference_id}",
            body=body,
            reference_id=reference_id
        )
        
        # Store in inbox
        self._save_to_inbox(reply)
        
        return reply
    
    def _save_to_inbox(self, email: IncomingEmail) -> None:
        """Save received email to inbox directory."""
        filename = f"{email.reference_id}_reply.json"
        filepath = self.inbox_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(email.model_dump(mode='json'), f, indent=2, default=str)
    
    def _get_reply_templates(self) -> dict:
        """Get reply templates for different scenarios."""
        return {
            "verified": {
                "body": """Dear Verification Officer,

Thank you for your verification request (Reference: {reference_id}).

We are pleased to confirm that the certificate in question is authentic and was issued by {university_name}. Our records indicate that the student named in the certificate successfully completed the stated program of study and was awarded the degree as specified.

The details provided in your request match our official records.

If you require any additional documentation or have further questions, please do not hesitate to contact us.

Best regards,
Office of the Registrar
{university_name}

This is an official verification response. Please retain this email for your records."""
            },
            "not_verified": {
                "body": """Dear Verification Officer,

Thank you for your verification request (Reference: {reference_id}).

After a thorough search of our records, we regret to inform you that we cannot verify the authenticity of the certificate in question.

Our investigation found the following issues:
- No matching student record exists in our database
- The certificate format does not match our official templates
- The reference number provided is not in our system

We strongly recommend that you exercise caution regarding this credential. This certificate may be fraudulent.

If you believe there has been an error, please provide additional documentation and we will conduct a further review.

Regards,
Academic Records Office
{university_name}

IMPORTANT: This verification failure should be reported to relevant authorities."""
            },
            "inconclusive": {
                "body": """Dear Verification Officer,

Thank you for your verification request (Reference: {reference_id}).

We have received your request but require additional information to complete the verification process:

1. A clearer copy of the certificate showing the full document
2. The student's date of birth for identity confirmation
3. The exact enrollment dates (start and end)

Our records show multiple possible matches, and we cannot confirm authenticity without these additional details.

Please provide the requested information within 10 business days. After that period, we will close this request and a new submission will be required.

Thank you for your understanding.

Best regards,
Student Records Department
{university_name}

Note: Partial matches were found but require confirmation."""
            },
            "suspicious": {
                "body": """Hello,

Yes, the certificate is valid. I can confirm this personally.

Regards,
John

---
Sent from my iPhone""",
                # Note: This scenario uses a different sender to simulate fraud
                "override_sender_email": "random.person12345@gmail.com",
                "override_sender_name": "John"
            },
            "ambiguous": {
                "body": """Dear Sir/Madam,

RE: Your enquiry (Ref: {reference_id})

We received your request regarding certificate verification. The matter has been forwarded to our records department for review.

Please note that our office has been experiencing some system upgrades recently, and response times may be longer than usual.

If this is urgent, you may want to contact the specific faculty directly, though we cannot guarantee they will be able to assist with verification requests.

We will endeavor to respond when our staff have had an opportunity to review the relevant files.

Thank you for your patience.

Administrative Office
{university_name}"""
            }
        }
    
    def list_outbox(self) -> List[OutgoingEmail]:
        """List all emails in outbox."""
        emails = []
        for filepath in self.outbox_dir.glob("*.json"):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                emails.append(OutgoingEmail(**data))
        return emails
    
    def list_inbox(self) -> List[IncomingEmail]:
        """List all emails in inbox."""
        emails = []
        for filepath in self.inbox_dir.glob("*_reply.json"):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                emails.append(IncomingEmail(**data))
        return emails
    
    def get_reply_by_reference(self, reference_id: str) -> Optional[IncomingEmail]:
        """Get inbox reply by reference ID."""
        filepath = self.inbox_dir / f"{reference_id}_reply.json"
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return IncomingEmail(**data)
        return None
