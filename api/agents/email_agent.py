"""
Email Agent
Responsible for email drafting and communication simulation.
"""
from typing import Optional, Dict, Any
import uuid
from datetime import datetime

from api.models.schemas import (
    ExtractedFields,
    UniversityContact,
    OutgoingEmail,
    IncomingEmail
)
from api.tools.tools import AgentTools
from api.services.audit_logger import AuditLogger


class EmailAgent:
    """
    Agent responsible for:
    1. Looking up university contact information
    2. Drafting verification request emails
    3. Sending emails to outbox
    4. Reading university replies
    """
    
    AGENT_NAME = "EmailAgent"
    
    def __init__(
        self,
        tools: AgentTools,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize the email agent.
        
        Args:
            tools: AgentTools instance with all tools
            audit_logger: Optional audit logger
        """
        self.tools = tools
        self.audit = audit_logger or tools.audit
    
    def run(
        self,
        extracted_fields: ExtractedFields,
        university_name: str,
        simulation_scenario: str = "verified"
    ) -> Dict[str, Any]:
        """
        Execute the email workflow.
        
        Args:
            extracted_fields: Certificate information
            university_name: Identified university name
            simulation_scenario: Type of reply to simulate
            
        Returns:
            Dictionary with outgoing_email, incoming_email, and contact info
        """
        self.audit.log_step(
            step="email_agent_start",
            action="Starting email workflow",
            agent=self.AGENT_NAME,
            input_data={
                "university_name": university_name,
                "scenario": simulation_scenario
            }
        )
        
        # Step 1: Lookup university contact
        self.audit.log_step(
            step="email_step_1",
            action="Looking up university contact information",
            agent=self.AGENT_NAME
        )
        
        contact = self.tools.lookup_contact(university_name)
        
        if not contact:
            self.audit.log_step(
                step="email_no_contact",
                action=f"No contact found for university: {university_name}",
                agent=self.AGENT_NAME,
                success=False
            )
            return {
                "contact": None,
                "outgoing_email": None,
                "incoming_email": None,
                "contact_found": False
            }
        
        # Generate reference ID
        reference_id = f"VER-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        
        # Step 2: Draft verification email
        self.audit.log_step(
            step="email_step_2",
            action="Drafting verification request email",
            agent=self.AGENT_NAME
        )
        
        email_content = self.tools.draft_email(
            extracted_fields=extracted_fields,
            recipient=contact,
            reference_id=reference_id
        )
        
        # Step 3: Send to outbox
        self.audit.log_step(
            step="email_step_3",
            action="Storing email in outbox",
            agent=self.AGENT_NAME
        )
        
        outgoing_email = self.tools.send_to_outbox(
            recipient=contact,
            subject=email_content["subject"],
            body=email_content["body"],
            extracted_fields=extracted_fields,
            reference_id=reference_id
        )
        
        # Step 4: Read simulated reply
        self.audit.log_step(
            step="email_step_4",
            action=f"Simulating university reply (scenario: {simulation_scenario})",
            agent=self.AGENT_NAME
        )
        
        incoming_email = self.tools.read_reply(
            reference_id=reference_id,
            university_name=contact.name,
            university_email=contact.email,
            scenario=simulation_scenario
        )
        
        # Log completion
        self.audit.log_step(
            step="email_agent_complete",
            action="Email workflow completed successfully",
            agent=self.AGENT_NAME,
            output_data={
                "reference_id": reference_id,
                "outgoing_email_id": outgoing_email.id,
                "incoming_email_id": incoming_email.id
            }
        )
        
        return {
            "contact": contact,
            "outgoing_email": outgoing_email,
            "incoming_email": incoming_email,
            "reference_id": reference_id,
            "contact_found": True
        }


class EmailAgentResult:
    """Result container for email agent."""
    
    def __init__(
        self,
        contact: Optional[UniversityContact],
        outgoing_email: Optional[OutgoingEmail],
        incoming_email: Optional[IncomingEmail],
        reference_id: Optional[str],
        contact_found: bool
    ):
        self.contact = contact
        self.outgoing_email = outgoing_email
        self.incoming_email = incoming_email
        self.reference_id = reference_id
        self.contact_found = contact_found
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmailAgentResult":
        """Create from dictionary."""
        return cls(
            contact=data.get("contact"),
            outgoing_email=data.get("outgoing_email"),
            incoming_email=data.get("incoming_email"),
            reference_id=data.get("reference_id"),
            contact_found=data.get("contact_found", False)
        )
