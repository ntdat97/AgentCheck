"""
Agent Orchestrator
Coordinates all agents to execute the full verification workflow.
"""
import time
import uuid
from typing import Optional, Dict, Any
from pathlib import Path

from api.models.schemas import (
    ComplianceReport,
    VerificationStatus,
    ComplianceResult,
    AuditLogEntry,
    ExtractedFields
)
from api.tools.tools import AgentTools
from api.services.audit_logger import AuditLogger
from api.services.compliance import ComplianceService
from api.agents.extraction_agent import ExtractionAgent
from api.agents.email_agent import EmailAgent
from api.agents.decision_agent import DecisionAgent
from api.agents.decision_agent_fc import DecisionAgentWithFunctionCalling
from api.utils.llm_client import LLMClient


class AgentOrchestrator:
    """
    Main orchestrator that coordinates the multi-agent workflow.
    
    Workflow:
    1. ExtractionAgent: Parse PDF and extract fields
    2. EmailAgent: Lookup contact, draft email, simulate reply
    3. DecisionAgent: Analyze reply and make compliance decision
    4. Generate final report with audit trail
    """
    
    def __init__(
        self,
        data_dir: str = "./data",
        config_dir: str = "./config",
        llm_client: Optional[LLMClient] = None,
        use_function_calling: bool = True  # Default to function calling for AI-driven interpretation
    ):
        """
        Initialize the orchestrator.
        
        Args:
            data_dir: Directory for data storage
            config_dir: Directory for configuration
            llm_client: Optional LLM client (created if not provided)
        """
        self.data_dir = Path(data_dir)
        self.config_dir = Path(config_dir)
        
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize shared components
        self.audit_logger = AuditLogger(str(self.data_dir))
        self.llm_client = llm_client or LLMClient()
        
        # Initialize tools (shared by all agents)
        self.tools = AgentTools(
            data_dir=str(self.data_dir),
            config_dir=str(self.config_dir),
            llm_client=self.llm_client,
            audit_logger=self.audit_logger
        )
        
        # Initialize agents
        self.extraction_agent = ExtractionAgent(self.tools, self.audit_logger)
        self.email_agent = EmailAgent(self.tools, self.audit_logger)
        
        # Use function calling agent if enabled
        self.use_function_calling = use_function_calling
        if use_function_calling:
            self.decision_agent = DecisionAgentWithFunctionCalling(
                self.tools, self.audit_logger, self.llm_client
            )
        else:
            self.decision_agent = DecisionAgent(self.tools, self.audit_logger)
        
        # Compliance service for report generation
        self.compliance_service = ComplianceService(str(self.data_dir))
    
    def verify_certificate(
        self,
        pdf_path: str,
        simulation_scenario: str = "verified"
    ) -> ComplianceReport:
        """
        Execute the full verification workflow.
        
        Args:
            pdf_path: Path to the certificate PDF
            simulation_scenario: Type of reply to simulate
                - "verified": University confirms certificate
                - "not_verified": University denies certificate
                - "inconclusive": University needs more info
                
        Returns:
            Complete ComplianceReport with audit trail
        """
        start_time = time.time()
        session_id = str(uuid.uuid4())
        
        # Start audit session
        self.audit_logger.start_session(session_id)
        
        self.audit_logger.log_step(
            step="orchestrator_start",
            action="Starting certificate verification workflow",
            agent="Orchestrator",
            input_data={
                "pdf_path": pdf_path,
                "simulation_scenario": simulation_scenario
            }
        )
        
        try:
            # ==================== Phase 1: Extraction ====================
            self.audit_logger.log_step(
                step="phase_1_extraction",
                action="Delegating to ExtractionAgent",
                agent="Orchestrator"
            )
            
            extraction_result = self.extraction_agent.run(pdf_path)
            extracted_fields = extraction_result["extracted_fields"]
            university_name = extraction_result["university_name"]
            
            # ==================== Phase 2: Email ====================
            self.audit_logger.log_step(
                step="phase_2_email",
                action="Delegating to EmailAgent",
                agent="Orchestrator"
            )
            
            email_result = self.email_agent.run(
                extracted_fields=extracted_fields,
                university_name=university_name,
                simulation_scenario=simulation_scenario
            )
            
            # ==================== Phase 3: Decision ====================
            self.audit_logger.log_step(
                step="phase_3_decision",
                action="Delegating to DecisionAgent",
                agent="Orchestrator"
            )
            
            decision_result = self.decision_agent.run(
                incoming_email=email_result.get("incoming_email"),
                extracted_fields=extracted_fields,
                contact_found=email_result.get("contact_found", False)
            )
            
            # ==================== Phase 4: Report Generation ====================
            self.audit_logger.log_step(
                step="phase_4_report",
                action="Generating compliance report",
                agent="Orchestrator"
            )
            
            processing_time = time.time() - start_time
            
            # Get audit logs
            audit_logs = self.audit_logger.end_session(
                success=True,
                final_result={
                    "compliance_result": decision_result["compliance_result"].value,
                    "verification_status": decision_result["verification_status"].value
                }
            )
            
            # Create report
            report = self.compliance_service.create_report(
                pdf_filename=Path(pdf_path).name,
                extracted_fields=extracted_fields,
                verification_status=decision_result["verification_status"],
                audit_log=audit_logs,
                university_contact=email_result.get("contact"),
                outgoing_email=email_result.get("outgoing_email"),
                incoming_email=email_result.get("incoming_email"),
                reply_analysis=decision_result.get("reply_analysis"),
                processing_time=processing_time,
                # Function calling enhancement fields
                function_calling_enabled=decision_result.get("function_calling_enabled", False),
                tool_calls_made=decision_result.get("tool_calls_made", []),
                escalated_to_human=decision_result.get("escalated_to_human", False),
                escalation_reason=decision_result.get("escalation_reason"),
                escalation_priority=decision_result.get("escalation_priority"),
                risk_indicators=decision_result.get("risk_indicators", []),
                clarification_needed=decision_result.get("clarification_needed", False),
                missing_information=decision_result.get("missing_information", [])
            )
            
            return report
            
        except Exception as e:
            # Log error and end session
            self.audit_logger.log_step(
                step="orchestrator_error",
                action=f"Workflow failed: {str(e)}",
                agent="Orchestrator",
                success=False,
                error_message=str(e)
            )
            
            audit_logs = self.audit_logger.end_session(
                success=False,
                final_result={"error": str(e)}
            )
            
            # Create error extracted_fields if not available
            error_fields = extracted_fields if 'extracted_fields' in locals() and extracted_fields else ExtractedFields(
                candidate_name="Unknown",
                university_name="Unknown",
                degree_name="Unknown",
                issue_date=None,
                raw_text="",
                extraction_confidence=0.0
            )
            
            # Create error report
            report = ComplianceReport(
                pdf_filename=Path(pdf_path).name,
                extracted_fields=error_fields,
                verification_status=VerificationStatus.INCONCLUSIVE,
                compliance_result=ComplianceResult.INCONCLUSIVE,
                decision_explanation=f"Workflow failed with error: {str(e)}",
                audit_log=audit_logs,
                processing_time_seconds=time.time() - start_time
            )
            
            self.compliance_service._save_report(report)
            
            raise
    
    def get_report(self, report_id: str) -> Optional[ComplianceReport]:
        """Get a report by ID."""
        return self.compliance_service.get_report(report_id)
    
    def list_reports(self, limit: int = 50) -> list:
        """List recent reports."""
        return self.compliance_service.list_reports(limit)
    
    def export_report_text(self, report: ComplianceReport) -> str:
        """Export report as human-readable text."""
        return self.compliance_service.export_report_text(report)


def create_orchestrator(
    data_dir: str = "./data",
    config_dir: str = "./config"
) -> AgentOrchestrator:
    """Factory function to create orchestrator with default settings."""
    return AgentOrchestrator(
        data_dir=data_dir,
        config_dir=config_dir
    )
