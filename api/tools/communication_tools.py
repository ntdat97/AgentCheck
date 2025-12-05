"""
Communication Tools Mixin
Handles email drafting, sending, and reading replies.
"""
from typing import Dict

from api.models.schemas import (
    ExtractedFields,
    UniversityContact,
    OutgoingEmail,
    IncomingEmail
)


class CommunicationToolsMixin:
    """
    Mixin providing email communication tools.
    Requires self.email_service, self.llm, self.prompt_loader, and self.audit
    to be initialized by the main AgentTools class.
    """
    
    # ==================== Tool 5: Draft Email ====================
    def draft_email(
        self,
        extracted_fields: ExtractedFields,
        recipient: UniversityContact,
        reference_id: str
    ) -> Dict[str, str]:
        """
        Tool: draft_email
        Use LLM to generate a verification request email.
        
        Args:
            extracted_fields: Certificate information
            recipient: University contact
            reference_id: Verification reference ID
            
        Returns:
            Dictionary with 'subject' and 'body'
        """
        self.audit.log_step(
            step="draft_email",
            action="Generating verification request email",
            tool="draft_email",
            input_data={
                "recipient": recipient.name,
                "reference_id": reference_id
            }
        )
        
        try:
            prompt = self.prompt_loader.render(
                "draft_email",
                candidate_name=extracted_fields.candidate_name,
                degree_name=extracted_fields.degree_name,
                issue_date=extracted_fields.issue_date,
                reference_id=reference_id,
                university_name=recipient.name,
                department=recipient.verification_department or "Registrar Office",
                recipient_email=recipient.email
            )
            
            response = self.llm.complete_json(prompt)
            
            email_content = {
                "subject": response.get("subject", f"Verification Request - {reference_id}"),
                "body": response.get("body", "Verification request email body")
            }
            
            self.audit.log_step(
                step="draft_email_complete",
                action="Generated verification email",
                tool="draft_email",
                output_data={"subject": email_content["subject"]}
            )
            
            return email_content
        except Exception as e:
            # Fallback email
            email_content = {
                "subject": f"Certificate Verification Request - {reference_id}",
                "body": f"""Dear {recipient.verification_department or 'Registrar Office'},

I am writing to request verification of the following certificate:

Candidate Name: {extracted_fields.candidate_name}
Degree: {extracted_fields.degree_name}
Issue Date: {extracted_fields.issue_date}
Reference ID: {reference_id}

Please confirm whether this certificate was issued by your institution.

Thank you for your assistance.

Best regards,
Verification Officer"""
            }
            
            self.audit.log_step(
                step="draft_email_fallback",
                action="Used fallback email template",
                tool="draft_email",
                output_data={"subject": email_content["subject"]}
            )
            
            return email_content
    
    # ==================== Tool 6: Send to Outbox ====================
    def send_to_outbox(
        self,
        recipient: UniversityContact,
        subject: str,
        body: str,
        extracted_fields: ExtractedFields,
        reference_id: str
    ) -> OutgoingEmail:
        """
        Tool: send_to_outbox
        Store the email in the simulated outbox.
        
        Args:
            recipient: University contact
            subject: Email subject
            body: Email body
            extracted_fields: Certificate info
            reference_id: Verification reference
            
        Returns:
            OutgoingEmail object
        """
        self.audit.log_step(
            step="send_to_outbox",
            action=f"Sending email to outbox: {recipient.email}",
            tool="send_to_outbox",
            input_data={
                "recipient": recipient.email,
                "subject": subject,
                "reference_id": reference_id
            }
        )
        
        email = self.email_service.create_outgoing_email(
            recipient=recipient,
            subject=subject,
            body=body,
            certificate_info=extracted_fields,
            reference_id=reference_id
        )
        
        self.audit.log_step(
            step="send_to_outbox_complete",
            action="Email stored in outbox",
            tool="send_to_outbox",
            output_data={
                "email_id": email.id,
                "reference_id": email.reference_id
            }
        )
        
        return email
    
    # ==================== Tool 7: Read Reply ====================
    def read_reply(
        self,
        reference_id: str,
        university_name: str,
        university_email: str,
        scenario: str = "verified"
    ) -> IncomingEmail:
        """
        Tool: read_reply
        Get (simulated) university reply email.
        
        Args:
            reference_id: Original verification reference
            university_name: Name of university
            university_email: University email
            scenario: Simulation scenario (verified/not_verified/inconclusive)
            
        Returns:
            IncomingEmail object
        """
        self.audit.log_step(
            step="read_reply",
            action=f"Reading university reply (scenario: {scenario})",
            tool="read_reply",
            input_data={
                "reference_id": reference_id,
                "scenario": scenario
            }
        )
        
        reply = self.email_service.get_simulated_reply(
            reference_id=reference_id,
            university_name=university_name,
            university_email=university_email,
            scenario=scenario
        )
        
        self.audit.log_step(
            step="read_reply_complete",
            action="Received university reply",
            tool="read_reply",
            output_data={
                "email_id": reply.id,
                "sender": reply.sender_email
            }
        )
        
        return reply
