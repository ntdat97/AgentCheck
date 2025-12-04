"""
Decision Agent
Responsible for analyzing replies and making compliance decisions.
"""
from typing import Optional, Dict, Any

from api.models.schemas import (
    ExtractedFields,
    IncomingEmail,
    ReplyAnalysis,
    ComplianceResult,
    VerificationStatus
)
from api.tools.tools import AgentTools
from api.services.audit_logger import AuditLogger


class DecisionAgent:
    """
    Agent responsible for:
    1. Analyzing university replies using LLM
    2. Determining verification status
    3. Making final compliance decision
    4. Generating explanations
    """
    
    AGENT_NAME = "DecisionAgent"
    
    def __init__(
        self,
        tools: AgentTools,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize the decision agent.
        
        Args:
            tools: AgentTools instance with all tools
            audit_logger: Optional audit logger
        """
        self.tools = tools
        self.audit = audit_logger or tools.audit
    
    def run(
        self,
        incoming_email: Optional[IncomingEmail],
        extracted_fields: ExtractedFields,
        contact_found: bool = True
    ) -> Dict[str, Any]:
        """
        Execute the decision workflow.
        
        Args:
            incoming_email: Reply from university (None if no contact)
            extracted_fields: Certificate information
            contact_found: Whether university contact was found
            
        Returns:
            Dictionary with reply_analysis, compliance_result, and explanation
        """
        self.audit.log_step(
            step="decision_agent_start",
            action="Starting decision workflow",
            agent=self.AGENT_NAME,
            input_data={
                "has_reply": incoming_email is not None,
                "contact_found": contact_found
            }
        )
        
        # Handle case where no university contact was found
        if not contact_found or incoming_email is None:
            self.audit.log_step(
                step="decision_no_contact",
                action="No university contact - marking as inconclusive",
                agent=self.AGENT_NAME
            )
            
            return {
                "reply_analysis": None,
                "compliance_result": ComplianceResult.INCONCLUSIVE,
                "verification_status": VerificationStatus.INCONCLUSIVE,
                "explanation": (
                    "INCONCLUSIVE: The issuing university could not be identified in our "
                    "verification database. Manual verification is required. The certificate "
                    "authenticity cannot be confirmed through automated means."
                )
            }
        
        # Step 1: Analyze the university reply
        self.audit.log_step(
            step="decision_step_1",
            action="Analyzing university reply with LLM",
            agent=self.AGENT_NAME
        )
        
        reply_analysis = self.tools.analyze_reply(
            reply=incoming_email,
            extracted_fields=extracted_fields
        )
        
        # Step 2: Make compliance decision
        self.audit.log_step(
            step="decision_step_2",
            action="Determining compliance result",
            agent=self.AGENT_NAME
        )
        
        compliance_result, explanation = self.tools.decide_compliance(reply_analysis)
        
        # Log completion
        self.audit.log_step(
            step="decision_agent_complete",
            action=f"Decision workflow completed: {compliance_result.value}",
            agent=self.AGENT_NAME,
            output_data={
                "verification_status": reply_analysis.verification_status.value,
                "compliance_result": compliance_result.value,
                "confidence": reply_analysis.confidence_score
            }
        )
        
        return {
            "reply_analysis": reply_analysis,
            "compliance_result": compliance_result,
            "verification_status": reply_analysis.verification_status,
            "explanation": explanation
        }


class DecisionAgentResult:
    """Result container for decision agent."""
    
    def __init__(
        self,
        reply_analysis: Optional[ReplyAnalysis],
        compliance_result: ComplianceResult,
        verification_status: VerificationStatus,
        explanation: str
    ):
        self.reply_analysis = reply_analysis
        self.compliance_result = compliance_result
        self.verification_status = verification_status
        self.explanation = explanation
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionAgentResult":
        """Create from dictionary."""
        return cls(
            reply_analysis=data.get("reply_analysis"),
            compliance_result=data["compliance_result"],
            verification_status=data["verification_status"],
            explanation=data["explanation"]
        )
