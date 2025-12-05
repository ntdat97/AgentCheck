"""
Pydantic models for AgentCheck application.
Defines all data structures used throughout the system.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid


class VerificationStatus(str, Enum):
    """Possible verification outcomes from university reply."""
    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    INCONCLUSIVE = "INCONCLUSIVE"


class ComplianceResult(str, Enum):
    """Final compliance decision based on verification."""
    COMPLIANT = "COMPLIANT"
    NOT_COMPLIANT = "NOT_COMPLIANT"
    INCONCLUSIVE = "INCONCLUSIVE"


class TaskStatus(str, Enum):
    """Status of a verification task in the queue."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ExtractedFields(BaseModel):
    """Fields extracted from a certificate PDF."""
    candidate_name: Optional[str] = None
    university_name: Optional[str] = None
    degree_name: Optional[str] = None
    issue_date: Optional[str] = None
    raw_text: Optional[str] = None
    extraction_confidence: float = 0.0


class UniversityContact(BaseModel):
    """Contact information for a university."""
    name: str
    email: str
    country: Optional[str] = None
    verification_department: Optional[str] = None


class OutgoingEmail(BaseModel):
    """Email to be sent to university for verification."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    recipient_email: str
    recipient_name: str
    subject: str
    body: str
    reference_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    certificate_info: ExtractedFields


class IncomingEmail(BaseModel):
    """Simulated reply from university."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_email: str
    sender_name: str
    subject: str
    body: str
    reference_id: str
    received_at: datetime = Field(default_factory=datetime.utcnow)


class ReplyAnalysis(BaseModel):
    """Analysis of university reply."""
    verification_status: VerificationStatus
    confidence_score: float
    key_phrases: List[str]
    explanation: str


class AuditLogEntry(BaseModel):
    """Single entry in the audit log."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    step: str
    action: str
    agent: Optional[str] = None
    tool: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None


class ComplianceReport(BaseModel):
    """Final compliance report with full audit trail."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Certificate Information
    pdf_filename: str
    extracted_fields: ExtractedFields
    
    # University Information
    university_identified: Optional[str] = None
    university_contact: Optional[UniversityContact] = None
    
    # Email Trail
    outgoing_email: Optional[OutgoingEmail] = None
    incoming_email: Optional[IncomingEmail] = None
    
    # Analysis Results
    reply_analysis: Optional[ReplyAnalysis] = None
    
    # Final Decision
    verification_status: VerificationStatus
    compliance_result: ComplianceResult
    decision_explanation: str
    
    # Function Calling Enhancement Fields
    function_calling_enabled: bool = False
    tool_calls_made: List[str] = Field(default_factory=list)
    
    # Escalation Fields
    escalated_to_human: bool = False
    escalation_reason: Optional[str] = None
    escalation_priority: Optional[str] = None
    risk_indicators: List[str] = Field(default_factory=list)
    
    # Clarification Fields
    clarification_needed: bool = False
    missing_information: List[str] = Field(default_factory=list)
    
    # Audit Trail
    audit_log: List[AuditLogEntry] = Field(default_factory=list)
    
    # Metadata
    processing_time_seconds: Optional[float] = None
    agent_version: str = "1.0.0"


class VerificationTask(BaseModel):
    """A verification task in the queue."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pdf_path: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    report_id: Optional[str] = None
    error_message: Optional[str] = None


class VerificationRequest(BaseModel):
    """API request to verify a certificate."""
    pdf_path: Optional[str] = None
    pdf_base64: Optional[str] = None
    simulation_scenario: Optional[str] = "verified"  # verified, not_verified, inconclusive, suspicious, ambiguous


class VerificationResponse(BaseModel):
    """API response for verification request."""
    task_id: str
    status: TaskStatus
    message: str
    report: Optional[ComplianceReport] = None
