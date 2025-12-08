"""
Extraction Agent
Responsible for PDF parsing and field extraction.
"""
from typing import Optional, Dict, Any
from api.models.schemas import ExtractedFields
from api.tools.tools import AgentTools
from api.services.audit_logger import AuditLogger


class ExtractionAgent:
    """
    Agent responsible for:
    1. Parsing PDF certificates
    2. Extracting structured fields
    3. Identifying the issuing university
    """
    
    AGENT_NAME = "ExtractionAgent"
    
    def __init__(
        self,
        tools: AgentTools,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize the extraction agent.
        
        Args:
            tools: AgentTools instance with all tools
            audit_logger: Optional audit logger
        """
        self.tools = tools
        self.audit = audit_logger or tools.audit
    
    def run(self, pdf_path: str) -> Dict[str, Any]:
        """
        Execute the extraction workflow.
        
        Args:
            pdf_path: Path to the PDF certificate
            
        Returns:
            Dictionary with extracted_fields and university_name
        """
        self.audit.log_step(
            step="extraction_agent_start",
            action="Starting extraction workflow",
            agent=self.AGENT_NAME,
            input_data={"pdf_path": pdf_path}
        )
        
        # Step 1: Parse PDF
        self.audit.log_step(
            step="extraction_step_1",
            action="Parsing PDF document",
            agent=self.AGENT_NAME
        )
        
        pdf_content = self.tools.parse_pdf(pdf_path)
        raw_text = pdf_content.get("raw_text", "")
        
        # Get document quality from Vision API (if available)
        vision_quality = pdf_content.get("document_quality", {})
        vision_confidence = vision_quality.get("confidence", 1.0)
        vision_issues = vision_quality.get("issues", [])
        
        if not raw_text:
            self.audit.log_step(
                step="extraction_error",
                action="No text extracted from PDF",
                agent=self.AGENT_NAME,
                success=False,
                error_message="PDF appears to be empty or unreadable"
            )
            raise ValueError("No text could be extracted from the PDF")
        
        # Step 2: Extract fields using LLM
        self.audit.log_step(
            step="extraction_step_2",
            action="Extracting structured fields from text",
            agent=self.AGENT_NAME
        )
        
        extracted_fields = self.tools.extract_fields(raw_text)
        
        # Merge Vision API quality with LLM extraction confidence
        # Use the MINIMUM confidence (most conservative approach for compliance)
        final_confidence = min(vision_confidence, extracted_fields.extraction_confidence)
        
        # Combine issues from both Vision and LLM extraction
        combined_issues = list(set(vision_issues + extracted_fields.extraction_issues))
        
        # Update extracted_fields with merged quality info
        extracted_fields.extraction_confidence = final_confidence
        extracted_fields.extraction_issues = combined_issues
        
        # Log if Vision detected damage
        if vision_quality.get("is_damaged", False):
            self.audit.log_step(
                step="vision_damage_detected",
                action=f"Vision API detected document damage: {vision_issues}",
                agent=self.AGENT_NAME,
                output_data={
                    "vision_confidence": vision_confidence,
                    "vision_issues": vision_issues
                }
            )
        
        # Step 3: Identify university
        self.audit.log_step(
            step="extraction_step_3",
            action="Identifying issuing university",
            agent=self.AGENT_NAME
        )
        
        university_name = self.tools.identify_university(extracted_fields)
        
        # Log completion
        self.audit.log_step(
            step="extraction_agent_complete",
            action="Extraction workflow completed successfully",
            agent=self.AGENT_NAME,
            output_data={
                "candidate_name": extracted_fields.candidate_name,
                "university_name": university_name,
                "degree_name": extracted_fields.degree_name,
                "issue_date": extracted_fields.issue_date,
                "extraction_confidence": final_confidence,
                "extraction_issues": combined_issues
            }
        )
        
        return {
            "extracted_fields": extracted_fields,
            "university_name": university_name,
            "pdf_metadata": {
                "filename": pdf_content.get("filename"),
                "page_count": pdf_content.get("page_count")
            }
        }


class ExtractionAgentResult:
    """Result container for extraction agent."""
    
    def __init__(
        self,
        extracted_fields: ExtractedFields,
        university_name: str,
        pdf_metadata: Dict[str, Any]
    ):
        self.extracted_fields = extracted_fields
        self.university_name = university_name
        self.pdf_metadata = pdf_metadata
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractionAgentResult":
        """Create from dictionary."""
        return cls(
            extracted_fields=data["extracted_fields"],
            university_name=data["university_name"],
            pdf_metadata=data.get("pdf_metadata", {})
        )
