"""
Agent Tools
Defines all tools available to the AI agents for the verification workflow.
"""
import json
from typing import Optional, Dict, Any
from pathlib import Path

from api.models.schemas import (
    ExtractedFields,
    UniversityContact,
    OutgoingEmail,
    IncomingEmail,
    ReplyAnalysis,
    VerificationStatus,
    ComplianceResult
)
from api.services.pdf_parser import PDFParser
from api.services.email_service import EmailService
from api.services.audit_logger import AuditLogger
from api.services.compliance import ComplianceService
from api.utils.llm_client import LLMClient
from api.utils.prompt_loader import PromptLoader
from api.constants import (
    CONFIDENCE_SCORE_HIGH,
    CONFIDENCE_SCORE_MEDIUM,
    CONFIDENCE_SCORE_LOW,
)


class AgentTools:
    """
    Collection of tools for AI agents to use during verification workflow.
    Each tool is a discrete action the agent can take.
    """
    
    def __init__(
        self,
        data_dir: str = "./data",
        config_dir: str = "./config",
        llm_client: Optional[LLMClient] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize tools with required services.
        
        Args:
            data_dir: Directory for data storage
            config_dir: Directory for configuration files
            llm_client: LLM client for AI operations
            audit_logger: Logger for audit trail
        """
        self.data_dir = Path(data_dir)
        self.config_dir = Path(config_dir)
        
        # Initialize LLM first (needed by PDF parser for Vision OCR)
        self.llm = llm_client or LLMClient()
        
        # Initialize services
        self.pdf_parser = PDFParser(data_dir, llm_client=self.llm)
        self.email_service = EmailService(data_dir)
        self.compliance_service = ComplianceService(data_dir)
        self.prompt_loader = PromptLoader(str(self.config_dir / "prompts"))
        
        self.audit = audit_logger or AuditLogger(data_dir)
        
        # Load university contacts
        self.university_contacts = self._load_university_contacts()
    
    def _load_university_contacts(self) -> Dict[str, UniversityContact]:
        """Load university contact information from config."""
        config_path = self.config_dir / "universities.json"
        
        if not config_path.exists():
            return {}
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        contacts = {}
        for name, info in data.get("universities", {}).items():
            contacts[name.lower()] = UniversityContact(
                name=name,
                email=info["email"],
                country=info.get("country"),
                verification_department=info.get("verification_department")
            )
        
        return contacts
    
    # ==================== Tool 1: Parse PDF ====================
    def parse_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Tool: parse_pdf
        Read a PDF file and extract raw text content.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with raw_text and metadata
        """
        self.audit.log_step(
            step="parse_pdf",
            action=f"Parsing PDF file: {pdf_path}",
            tool="parse_pdf",
            input_data={"pdf_path": pdf_path}
        )
        
        try:
            result = self.pdf_parser.parse_pdf(pdf_path)
            
            self.audit.log_step(
                step="parse_pdf_complete",
                action="Successfully extracted text from PDF",
                tool="parse_pdf",
                output_data={
                    "page_count": result.get("page_count"),
                    "text_length": len(result.get("raw_text", ""))
                }
            )
            
            return result
        except Exception as e:
            self.audit.log_step(
                step="parse_pdf_error",
                action=f"Failed to parse PDF: {str(e)}",
                tool="parse_pdf",
                success=False,
                error_message=str(e)
            )
            raise
    
    # ==================== Tool 2: Extract Fields ====================
    def extract_fields(self, raw_text: str) -> ExtractedFields:
        """
        Tool: extract_fields
        Use LLM to extract structured fields from certificate text.
        
        Args:
            raw_text: Raw text from PDF
            
        Returns:
            ExtractedFields with candidate_name, university_name, etc.
        """
        self.audit.log_step(
            step="extract_fields",
            action="Extracting structured fields from certificate text",
            tool="extract_fields",
            input_data={"text_length": len(raw_text)}
        )
        
        try:
            prompt = self.prompt_loader.render(
                "extract_fields",
                certificate_text=raw_text
            )
            
            response = self.llm.complete_json(prompt)
            
            fields = ExtractedFields(
                candidate_name=response.get("candidate_name"),
                university_name=response.get("university_name"),
                degree_name=response.get("degree_name"),
                issue_date=response.get("issue_date"),
                raw_text=raw_text,
                extraction_confidence=CONFIDENCE_SCORE_HIGH if self.llm.is_available() else CONFIDENCE_SCORE_LOW
            )
            
            self.audit.log_step(
                step="extract_fields_complete",
                action="Successfully extracted certificate fields",
                tool="extract_fields",
                output_data={
                    "candidate_name": fields.candidate_name,
                    "university_name": fields.university_name,
                    "degree_name": fields.degree_name,
                    "issue_date": fields.issue_date
                }
            )
            
            return fields
        except Exception as e:
            self.audit.log_step(
                step="extract_fields_error",
                action=f"Failed to extract fields: {str(e)}",
                tool="extract_fields",
                success=False,
                error_message=str(e)
            )
            raise
    
    # ==================== Tool 3: Identify University ====================
    def identify_university(self, extracted_fields: ExtractedFields) -> str:
        """
        Tool: identify_university
        Determine the official university name from extracted data.
        
        Args:
            extracted_fields: Fields extracted from certificate
            
        Returns:
            Normalized university name
        """
        self.audit.log_step(
            step="identify_university",
            action="Identifying issuing university",
            tool="identify_university",
            input_data={"raw_university": extracted_fields.university_name}
        )
        
        # First try direct match
        if extracted_fields.university_name:
            uni_lower = extracted_fields.university_name.lower().strip()
            
            # Check exact match
            if uni_lower in self.university_contacts:
                university_name = self.university_contacts[uni_lower].name
                self.audit.log_step(
                    step="identify_university_complete",
                    action=f"Identified university: {university_name}",
                    tool="identify_university",
                    output_data={"university_name": university_name, "match_type": "exact"}
                )
                return university_name
            
            # Check partial match
            for key, contact in self.university_contacts.items():
                if key in uni_lower or uni_lower in key:
                    self.audit.log_step(
                        step="identify_university_complete",
                        action=f"Identified university: {contact.name}",
                        tool="identify_university",
                        output_data={"university_name": contact.name, "match_type": "partial"}
                    )
                    return contact.name
        
        # Use LLM to identify if no direct match
        try:
            prompt = self.prompt_loader.render(
                "identify_university",
                extracted_text=extracted_fields.raw_text or str(extracted_fields)
            )
            
            response = self.llm.complete_json(prompt)
            university_name = response.get("university_name") or extracted_fields.university_name or "Unknown"
            
            self.audit.log_step(
                step="identify_university_complete",
                action=f"Identified university: {university_name}",
                tool="identify_university",
                output_data={
                    "university_name": university_name,
                    "match_type": "llm" if response.get("university_name") else "fallback",
                    "confidence": response.get("confidence")
                }
            )
            
            return university_name
        except:
            fallback = extracted_fields.university_name or "Unknown"
            self.audit.log_step(
                step="identify_university_complete",
                action=f"Identified university (fallback): {fallback}",
                tool="identify_university",
                output_data={"university_name": fallback, "match_type": "fallback"}
            )
            return fallback
    
    # ==================== Tool 4: Lookup Contact ====================
    def lookup_contact(self, university_name: str) -> Optional[UniversityContact]:
        """
        Tool: lookup_contact
        Find contact information for a university.
        
        Args:
            university_name: Name of the university
            
        Returns:
            UniversityContact if found, None otherwise
        """
        # Handle None or empty university name
        if not university_name:
            self.audit.log_step(
                step="lookup_contact_not_found",
                action="No university name provided",
                tool="lookup_contact",
                output_data={"university_name": None},
                success=False
            )
            return None
        
        self.audit.log_step(
            step="lookup_contact",
            action=f"Looking up contact for: {university_name}",
            tool="lookup_contact",
            input_data={"university_name": university_name}
        )
        
        uni_lower = university_name.lower().strip()
        
        # Direct match
        if uni_lower in self.university_contacts:
            contact = self.university_contacts[uni_lower]
            self.audit.log_step(
                step="lookup_contact_complete",
                action=f"Found contact: {contact.email}",
                tool="lookup_contact",
                output_data={"email": contact.email, "department": contact.verification_department}
            )
            return contact
        
        # Partial match
        for key, contact in self.university_contacts.items():
            if key in uni_lower or uni_lower in key:
                self.audit.log_step(
                    step="lookup_contact_complete",
                    action=f"Found contact (partial match): {contact.email}",
                    tool="lookup_contact",
                    output_data={"email": contact.email, "department": contact.verification_department}
                )
                return contact
        
        self.audit.log_step(
            step="lookup_contact_not_found",
            action="No contact found in database",
            tool="lookup_contact",
            output_data={"university_name": university_name},
            success=False
        )
        
        return None
    
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
    
    # ==================== Tool 8: Analyze Reply ====================
    def analyze_reply(
        self,
        reply: IncomingEmail,
        extracted_fields: ExtractedFields
    ) -> ReplyAnalysis:
        """
        Tool: analyze_reply
        Use LLM to interpret the university reply.
        
        Args:
            reply: Incoming email from university
            extracted_fields: Original certificate fields
            
        Returns:
            ReplyAnalysis with verification status
        """
        self.audit.log_step(
            step="analyze_reply",
            action="Analyzing university reply with LLM",
            tool="analyze_reply",
            input_data={
                "reply_id": reply.id,
                "reply_length": len(reply.body)
            }
        )
        
        try:
            prompt = self.prompt_loader.render(
                "analyze_reply",
                candidate_name=extracted_fields.candidate_name,
                degree_name=extracted_fields.degree_name,
                university_name=extracted_fields.university_name,
                reference_id=reply.reference_id,
                reply_text=reply.body
            )
            
            response = self.llm.complete_json(prompt)
            
            # Parse verification status
            status_str = response.get("verification_status", "INCONCLUSIVE").upper()
            try:
                verification_status = VerificationStatus(status_str)
            except ValueError:
                verification_status = VerificationStatus.INCONCLUSIVE
            
            analysis = ReplyAnalysis(
                verification_status=verification_status,
                confidence_score=float(response.get("confidence_score", 0.5)),
                key_phrases=response.get("key_phrases", []),
                explanation=response.get("explanation", "Analysis completed")
            )
            
            self.audit.log_step(
                step="analyze_reply_complete",
                action=f"Reply analysis: {analysis.verification_status.value}",
                tool="analyze_reply",
                output_data={
                    "verification_status": analysis.verification_status.value,
                    "confidence": analysis.confidence_score,
                    "key_phrases": analysis.key_phrases
                }
            )
            
            return analysis
        except Exception as e:
            self.audit.log_step(
                step="analyze_reply_error",
                action=f"Reply analysis failed: {str(e)}",
                tool="analyze_reply",
                success=False,
                error_message=str(e)
            )
            
            # Fallback: simple keyword analysis
            return self._fallback_analyze_reply(reply.body)
    
    def _fallback_analyze_reply(self, reply_text: str) -> ReplyAnalysis:
        """Simple keyword-based reply analysis as fallback."""
        reply_lower = reply_text.lower()
        
        verified_keywords = ["confirm", "authentic", "verified", "valid", "records match"]
        not_verified_keywords = ["cannot verify", "no record", "fraudulent", "deny", "not found"]
        inconclusive_keywords = ["need more", "additional information", "unclear", "contact us"]
        
        verified_count = sum(1 for kw in verified_keywords if kw in reply_lower)
        not_verified_count = sum(1 for kw in not_verified_keywords if kw in reply_lower)
        inconclusive_count = sum(1 for kw in inconclusive_keywords if kw in reply_lower)
        
        if verified_count > not_verified_count and verified_count > inconclusive_count:
            status = VerificationStatus.VERIFIED
            confidence = CONFIDENCE_SCORE_MEDIUM
        elif not_verified_count > verified_count and not_verified_count > inconclusive_count:
            status = VerificationStatus.NOT_VERIFIED
            confidence = CONFIDENCE_SCORE_MEDIUM
        else:
            status = VerificationStatus.INCONCLUSIVE
            confidence = CONFIDENCE_SCORE_LOW
        
        return ReplyAnalysis(
            verification_status=status,
            confidence_score=confidence,
            key_phrases=[],
            explanation="Fallback keyword-based analysis"
        )
    
    # ==================== Tool 9: Decide Compliance ====================
    def decide_compliance(
        self,
        reply_analysis: ReplyAnalysis
    ) -> tuple[ComplianceResult, str]:
        """
        Tool: decide_compliance
        Make final compliance decision based on analysis.
        
        Args:
            reply_analysis: Analysis of university reply
            
        Returns:
            Tuple of (ComplianceResult, explanation)
        """
        self.audit.log_step(
            step="decide_compliance",
            action="Making final compliance decision",
            tool="decide_compliance",
            input_data={
                "verification_status": reply_analysis.verification_status.value,
                "confidence": reply_analysis.confidence_score
            }
        )
        
        compliance = self.compliance_service.determine_compliance(
            reply_analysis.verification_status
        )
        
        explanation = self.compliance_service.generate_decision_explanation(
            verification_status=reply_analysis.verification_status,
            compliance_result=compliance,
            reply_analysis=reply_analysis,
            university_found=True
        )
        
        self.audit.log_step(
            step="decide_compliance_complete",
            action=f"Compliance decision: {compliance.value}",
            tool="decide_compliance",
            output_data={
                "compliance_result": compliance.value,
                "explanation_preview": explanation[:100]
            }
        )
        
        return compliance, explanation
    
    # ==================== Tool 10: Log Step ====================
    def log_step(
        self,
        step: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True
    ) -> Dict[str, Any]:
        """
        Tool: log_step
        Log a step in the audit trail for compliance tracking.
        
        This tool allows agents to explicitly record actions, decisions,
        and observations during the verification workflow.
        
        Args:
            step: Identifier for this step (e.g., "validation_check")
            action: Human-readable description of what happened
            details: Optional additional details to log
            success: Whether the step was successful
            
        Returns:
            Dictionary confirming the logged entry
        """
        entry = self.audit.log_step(
            step=step,
            action=action,
            tool="log_step",
            input_data=details or {},
            success=success
        )
        
        return {
            "logged": True,
            "step": step,
            "action": action,
            "timestamp": entry.timestamp.isoformat() if hasattr(entry, 'timestamp') else None
        }


# LangChain tool definitions for function calling
TOOL_DEFINITIONS = [
    {
        "name": "parse_pdf",
        "description": "Read a PDF file and extract raw text content",
        "parameters": {
            "type": "object",
            "properties": {
                "pdf_path": {
                    "type": "string",
                    "description": "Path to the PDF file to parse"
                }
            },
            "required": ["pdf_path"]
        }
    },
    {
        "name": "extract_fields",
        "description": "Extract structured fields (name, university, degree, date) from certificate text",
        "parameters": {
            "type": "object",
            "properties": {
                "raw_text": {
                    "type": "string",
                    "description": "Raw text content from the certificate"
                }
            },
            "required": ["raw_text"]
        }
    },
    {
        "name": "identify_university",
        "description": "Determine the official university name from extracted certificate data",
        "parameters": {
            "type": "object",
            "properties": {
                "university_name": {
                    "type": "string",
                    "description": "University name from extracted fields"
                }
            },
            "required": ["university_name"]
        }
    },
    {
        "name": "lookup_contact",
        "description": "Find contact information (email) for a university",
        "parameters": {
            "type": "object",
            "properties": {
                "university_name": {
                    "type": "string",
                    "description": "Name of the university to look up"
                }
            },
            "required": ["university_name"]
        }
    },
    {
        "name": "draft_email",
        "description": "Generate a professional verification request email",
        "parameters": {
            "type": "object",
            "properties": {
                "candidate_name": {"type": "string"},
                "degree_name": {"type": "string"},
                "university_name": {"type": "string"},
                "reference_id": {"type": "string"}
            },
            "required": ["candidate_name", "degree_name", "university_name", "reference_id"]
        }
    },
    {
        "name": "send_to_outbox",
        "description": "Store the verification email in the outbox for sending",
        "parameters": {
            "type": "object",
            "properties": {
                "recipient_email": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"}
            },
            "required": ["recipient_email", "subject", "body"]
        }
    },
    {
        "name": "read_reply",
        "description": "Get the university's reply email for a verification request",
        "parameters": {
            "type": "object",
            "properties": {
                "reference_id": {
                    "type": "string",
                    "description": "The verification reference ID"
                }
            },
            "required": ["reference_id"]
        }
    },
    {
        "name": "analyze_reply",
        "description": "Analyze and interpret the university reply to determine verification status",
        "parameters": {
            "type": "object",
            "properties": {
                "reply_text": {
                    "type": "string",
                    "description": "The body of the university reply email"
                }
            },
            "required": ["reply_text"]
        }
    },
    {
        "name": "decide_compliance",
        "description": "Make the final compliance decision based on verification analysis",
        "parameters": {
            "type": "object",
            "properties": {
                "verification_status": {
                    "type": "string",
                    "enum": ["VERIFIED", "NOT_VERIFIED", "INCONCLUSIVE"]
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence score from 0 to 1"
                }
            },
            "required": ["verification_status"]
        }
    },
    {
        "name": "log_step",
        "description": "Log an action or observation in the audit trail for compliance tracking",
        "parameters": {
            "type": "object",
            "properties": {
                "step": {
                    "type": "string",
                    "description": "Identifier for this step (e.g., 'validation_check')"
                },
                "action": {
                    "type": "string",
                    "description": "Human-readable description of what happened"
                },
                "details": {
                    "type": "object",
                    "description": "Optional additional details to log"
                },
                "success": {
                    "type": "boolean",
                    "description": "Whether the step was successful"
                }
            },
            "required": ["step", "action"]
        }
    }
]
