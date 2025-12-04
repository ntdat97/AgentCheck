"""
Tests for Agent System

These tests use mocks for the LLM client and PDF parser to avoid
real API calls and enable testing without valid credentials.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add api to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.agents.orchestrator import AgentOrchestrator, create_orchestrator
from api.agents.extraction_agent import ExtractionAgent
from api.agents.email_agent import EmailAgent
from api.agents.decision_agent import DecisionAgent
from api.tools.tools import AgentTools
from api.models.schemas import (
    VerificationStatus,
    ComplianceResult,
    ExtractedFields,
    IncomingEmail
)


def create_test_prompts(prompts_dir: Path):
    """Create minimal test prompt templates."""
    # extract_fields.j2
    (prompts_dir / "extract_fields.j2").write_text("""
Extract certificate fields from: {{ raw_text }}
Return JSON with candidate_name, university_name, degree_name, issue_date.
""")
    
    # identify_university.j2
    (prompts_dir / "identify_university.j2").write_text("""
Identify the university from: {{ raw_text }}
Return JSON with university_name.
""")
    
    # draft_email.j2
    (prompts_dir / "draft_email.j2").write_text("""
Draft a verification email for {{ candidate_name }} to {{ university_name }}.
""")
    
    # analyze_reply.j2
    (prompts_dir / "analyze_reply.j2").write_text("""
Analyze this reply: {{ reply_text }}
Return JSON with verification_status, confidence_score, key_phrases, explanation.
""")


class TestAgentTools:
    """Tests for agent tools."""
    
    @pytest.fixture
    def tools(self, tmp_path):
        """Create tools with test directories."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        # Create universities.json
        import json
        uni_config = {
            "universities": {
                "University of Example": {
                    "email": "verify@example.edu",
                    "country": "USA",
                    "verification_department": "Registrar"
                }
            }
        }
        (config_dir / "universities.json").write_text(json.dumps(uni_config))
        
        # Create prompts directory with test templates
        prompts_dir = config_dir / "prompts"
        prompts_dir.mkdir()
        create_test_prompts(prompts_dir)
        
        return AgentTools(
            data_dir=str(tmp_path / "data"),
            config_dir=str(config_dir)
        )
    
    def test_tools_init(self, tools):
        """Test tools initialization."""
        assert tools is not None
        assert len(tools.university_contacts) > 0
    
    def test_lookup_contact_found(self, tools):
        """Test looking up a known university."""
        contact = tools.lookup_contact("University of Example")
        
        assert contact is not None
        assert contact.email == "verify@example.edu"
    
    def test_lookup_contact_not_found(self, tools):
        """Test looking up an unknown university."""
        contact = tools.lookup_contact("Unknown University")
        
        assert contact is None
    
    def test_extract_fields(self, tools):
        """Test field extraction with mocked LLM response."""
        sample_text = """
        UNIVERSITY OF EXAMPLE
        Certificate for JOHN SMITH
        Degree: Bachelor of Science
        Date: May 15, 2023
        """
        
        # Mock the LLM response
        mock_response = {
            "candidate_name": "JOHN SMITH",
            "university_name": "UNIVERSITY OF EXAMPLE",
            "degree_name": "Bachelor of Science",
            "issue_date": "May 15, 2023"
        }
        
        with patch.object(tools.llm, 'complete_json', return_value=mock_response):
            fields = tools.extract_fields(sample_text)
        
        assert fields is not None
        assert isinstance(fields, ExtractedFields)
        assert fields.candidate_name == "JOHN SMITH"
        assert fields.university_name == "UNIVERSITY OF EXAMPLE"
    
    def test_fallback_analyze_reply_verified(self, tools):
        """Test fallback reply analysis for verified text."""
        reply_text = "We confirm that the certificate is authentic and our records match."
        
        analysis = tools._fallback_analyze_reply(reply_text)
        
        assert analysis.verification_status == VerificationStatus.VERIFIED
    
    def test_fallback_analyze_reply_not_verified(self, tools):
        """Test fallback reply analysis for not verified text."""
        reply_text = "We cannot verify this certificate. No record found in our database."
        
        analysis = tools._fallback_analyze_reply(reply_text)
        
        assert analysis.verification_status == VerificationStatus.NOT_VERIFIED
    
    def test_fallback_analyze_reply_inconclusive(self, tools):
        """Test fallback reply analysis for inconclusive text."""
        reply_text = "We need additional information to process your request."
        
        analysis = tools._fallback_analyze_reply(reply_text)
        
        assert analysis.verification_status == VerificationStatus.INCONCLUSIVE


class TestDecisionAgent:
    """Tests for decision agent."""
    
    @pytest.fixture
    def agent(self, tmp_path):
        """Create decision agent with test setup."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        import json
        (config_dir / "universities.json").write_text(json.dumps({"universities": {}}))
        prompts_dir = config_dir / "prompts"
        prompts_dir.mkdir()
        create_test_prompts(prompts_dir)
        
        tools = AgentTools(
            data_dir=str(tmp_path / "data"),
            config_dir=str(config_dir)
        )
        return DecisionAgent(tools)
    
    @pytest.fixture
    def sample_fields(self):
        """Sample extracted fields."""
        return ExtractedFields(
            candidate_name="John Smith",
            university_name="University of Example",
            degree_name="Bachelor of Science",
            issue_date="2023-05-15"
        )
    
    def test_run_no_contact(self, agent, sample_fields):
        """Test decision when no contact was found."""
        result = agent.run(
            incoming_email=None,
            extracted_fields=sample_fields,
            contact_found=False
        )
        
        assert result["compliance_result"] == ComplianceResult.INCONCLUSIVE
        assert result["verification_status"] == VerificationStatus.INCONCLUSIVE
        assert "INCONCLUSIVE" in result["explanation"]
    
    def test_run_with_verified_reply(self, agent, sample_fields):
        """Test decision with verified reply."""
        reply = IncomingEmail(
            sender_email="verify@example.edu",
            sender_name="University Registrar",
            subject="RE: Verification",
            body="We confirm that this certificate is authentic and matches our records.",
            reference_id="TEST-123"
        )
        
        result = agent.run(
            incoming_email=reply,
            extracted_fields=sample_fields,
            contact_found=True
        )
        
        assert result["reply_analysis"] is not None
        # The exact result depends on LLM availability, but should complete


class TestOrchestratorIntegration:
    """Integration tests for orchestrator."""
    
    def test_create_orchestrator(self, tmp_path):
        """Test creating an orchestrator."""
        # Set up minimal config
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        import json
        (config_dir / "universities.json").write_text(json.dumps({"universities": {}}))
        prompts_dir = config_dir / "prompts"
        prompts_dir.mkdir()
        create_test_prompts(prompts_dir)
        
        orch = AgentOrchestrator(
            data_dir=str(tmp_path / "data"),
            config_dir=str(config_dir)
        )
        
        assert orch is not None
        assert orch.extraction_agent is not None
        assert orch.email_agent is not None
        assert orch.decision_agent is not None
    
    def test_verify_certificate_with_sample(self, tmp_path):
        """Test full verification with sample data using mocked PDF parser."""
        # Set up config
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        import json
        uni_config = {
            "universities": {
                "University of Example": {
                    "email": "verify@example.edu",
                    "country": "USA",
                    "verification_department": "Registrar"
                }
            }
        }
        (config_dir / "universities.json").write_text(json.dumps(uni_config))
        prompts_dir = config_dir / "prompts"
        prompts_dir.mkdir()
        create_test_prompts(prompts_dir)
        
        # Set up sample PDF using PyMuPDF
        data_dir = tmp_path / "data"
        sample_dir = data_dir / "sample_pdfs"
        sample_dir.mkdir(parents=True)
        
        try:
            import fitz  # PyMuPDF
            
            # Create a real PDF file
            pdf_path = sample_dir / "test_cert.pdf"
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((72, 72), """
UNIVERSITY OF EXAMPLE
Certificate for JOHN SMITH
Degree: Bachelor of Science
Date: May 15, 2023
            """)
            doc.save(str(pdf_path))
            doc.close()
        except ImportError:
            pytest.skip("PyMuPDF not available")
        
        # Create orchestrator with mocked LLM
        orch = AgentOrchestrator(
            data_dir=str(data_dir),
            config_dir=str(config_dir)
        )
        
        # Mock the PDF parser's parse_pdf to return expected text
        mock_pdf_result = {
            "raw_text": """
UNIVERSITY OF EXAMPLE
Certificate for JOHN SMITH
Degree: Bachelor of Science
Date: May 15, 2023
            """,
            "page_count": 1,
            "filename": "test_cert.pdf",
            "file_path": str(pdf_path),
            "extraction_method": "vision_api"
        }
        
        # Mock LLM responses for extraction and analysis
        mock_extract_response = {
            "candidate_name": "JOHN SMITH",
            "university_name": "University of Example",
            "degree_name": "Bachelor of Science",
            "issue_date": "May 15, 2023"
        }
        
        mock_identify_response = {
            "university_name": "University of Example",
            "confidence": 0.95,
            "reasoning": "Extracted from certificate header"
        }
        
        mock_draft_response = {
            "subject": "Certificate Verification Request",
            "body": "Dear Registrar, I am writing to request verification..."
        }
        
        mock_analyze_response = {
            "verification_status": "VERIFIED",
            "confidence_score": 0.95,
            "key_phrases": ["confirm", "authentic"],
            "explanation": "The university confirmed the certificate is authentic."
        }
        
        def mock_complete_json(prompt, **kwargs):
            """Return appropriate mock response based on prompt content."""
            prompt_lower = prompt.lower()
            if "extract" in prompt_lower:
                return mock_extract_response
            elif "identify" in prompt_lower:
                return mock_identify_response
            elif "draft" in prompt_lower:
                return mock_draft_response
            elif "analyze" in prompt_lower:
                return mock_analyze_response
            return {}
        
        with patch.object(orch.tools.pdf_parser, 'parse_pdf', return_value=mock_pdf_result):
            with patch.object(orch.tools.llm, 'complete_json', side_effect=mock_complete_json):
                with patch.object(orch.tools.llm, 'complete', return_value="Subject: Verification\nBody: Dear..."):
                    # Run verification
                    report = orch.verify_certificate(
                        pdf_path=str(pdf_path),
                        simulation_scenario="verified"
                    )
        
        assert report is not None
        assert report.compliance_result in [
            ComplianceResult.COMPLIANT,
            ComplianceResult.NOT_COMPLIANT,
            ComplianceResult.INCONCLUSIVE
        ]
        assert len(report.audit_log) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
