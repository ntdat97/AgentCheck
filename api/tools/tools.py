"""
Agent Tools
Defines all tools available to the AI agents for the verification workflow.

This module uses a mixin pattern to organize tools by domain:
- DocumentToolsMixin: PDF parsing and field extraction
- CommunicationToolsMixin: Email drafting and sending
- AnalysisToolsMixin: University identification, reply analysis, compliance
- BaseToolsMixin: Shared utilities (logging)
"""
import json
from typing import Optional, Dict
from pathlib import Path

from api.models.schemas import UniversityContact
from api.services.pdf_parser import PDFParser
from api.services.email_service import EmailService
from api.services.audit_logger import AuditLogger
from api.services.compliance import ComplianceService
from api.utils.llm_client import LLMClient
from api.utils.prompt_loader import PromptLoader

# Import mixins
from api.tools.base import BaseToolsMixin
from api.tools.document_tools import DocumentToolsMixin
from api.tools.communication_tools import CommunicationToolsMixin
from api.tools.analysis_tools import AnalysisToolsMixin

# Re-export TOOL_DEFINITIONS for backward compatibility
from api.tools.definitions import TOOL_DEFINITIONS


class AgentTools(
    DocumentToolsMixin,
    CommunicationToolsMixin,
    AnalysisToolsMixin,
    BaseToolsMixin
):
    """
    Collection of tools for AI agents to use during verification workflow.
    Each tool is a discrete action the agent can take.
    
    This class inherits from domain-specific mixins that provide the actual
    tool implementations. It handles initialization of shared services that
    the mixins depend on.
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
