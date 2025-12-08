"""
Document Tools Mixin
Handles PDF parsing and field extraction from certificates.
"""
from typing import Dict, Any

from api.models.schemas import ExtractedFields
from api.constants import CONFIDENCE_SCORE_HIGH, CONFIDENCE_SCORE_LOW


class DocumentToolsMixin:
    """
    Mixin providing document processing tools.
    Requires self.pdf_parser, self.llm, self.prompt_loader, and self.audit
    to be initialized by the main AgentTools class.
    """
    
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
            
            # Parse confidence from LLM response (fallback to static values if not provided)
            extraction_confidence = response.get("extraction_confidence")
            if extraction_confidence is None:
                extraction_confidence = CONFIDENCE_SCORE_HIGH if self.llm.is_available() else CONFIDENCE_SCORE_LOW
            
            # Parse extraction issues from LLM response
            extraction_issues = response.get("extraction_issues", [])
            if not isinstance(extraction_issues, list):
                extraction_issues = []
            
            fields = ExtractedFields(
                candidate_name=response.get("candidate_name"),
                university_name=response.get("university_name"),
                degree_name=response.get("degree_name"),
                issue_date=response.get("issue_date"),
                raw_text=raw_text,
                extraction_confidence=extraction_confidence,
                extraction_issues=extraction_issues
            )
            
            # Log warning for low confidence extractions
            if extraction_confidence < 0.6:
                self.audit.log_step(
                    step="extract_fields_low_confidence",
                    action=f"Low extraction confidence: {extraction_confidence:.2f}. Issues: {extraction_issues}",
                    tool="extract_fields",
                    output_data={
                        "confidence": extraction_confidence,
                        "issues": extraction_issues,
                        "is_damaged": response.get("is_damaged", False)
                    }
                )
            
            self.audit.log_step(
                step="extract_fields_complete",
                action="Successfully extracted certificate fields",
                tool="extract_fields",
                output_data={
                    "candidate_name": fields.candidate_name,
                    "university_name": fields.university_name,
                    "degree_name": fields.degree_name,
                    "issue_date": fields.issue_date,
                    "extraction_confidence": extraction_confidence,
                    "extraction_issues": extraction_issues
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
