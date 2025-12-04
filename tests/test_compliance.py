"""
Tests for Compliance Service
"""
import pytest
import sys
from pathlib import Path

# Add api to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.services.compliance import ComplianceService
from api.models.schemas import (
    VerificationStatus,
    ComplianceResult,
    ExtractedFields,
    ReplyAnalysis,
    AuditLogEntry
)


class TestComplianceService:
    """Tests for compliance service functionality."""
    
    @pytest.fixture
    def service(self, tmp_path):
        """Create service with test data directory."""
        return ComplianceService(str(tmp_path))
    
    @pytest.fixture
    def sample_fields(self):
        """Sample extracted fields."""
        return ExtractedFields(
            candidate_name="John Smith",
            university_name="University of Example",
            degree_name="Bachelor of Science",
            issue_date="2023-05-15"
        )
    
    @pytest.fixture
    def sample_analysis_verified(self):
        """Sample verified analysis."""
        return ReplyAnalysis(
            verification_status=VerificationStatus.VERIFIED,
            confidence_score=0.95,
            key_phrases=["confirm", "authentic"],
            explanation="Certificate verified by university"
        )
    
    def test_init(self, service):
        """Test service initialization."""
        assert service is not None
        assert service.reports_dir.exists()
    
    def test_determine_compliance_verified(self, service):
        """Test compliance mapping for verified status."""
        result = service.determine_compliance(VerificationStatus.VERIFIED)
        assert result == ComplianceResult.COMPLIANT
    
    def test_determine_compliance_not_verified(self, service):
        """Test compliance mapping for not verified status."""
        result = service.determine_compliance(VerificationStatus.NOT_VERIFIED)
        assert result == ComplianceResult.NOT_COMPLIANT
    
    def test_determine_compliance_inconclusive(self, service):
        """Test compliance mapping for inconclusive status."""
        result = service.determine_compliance(VerificationStatus.INCONCLUSIVE)
        assert result == ComplianceResult.INCONCLUSIVE
    
    def test_generate_explanation_compliant(self, service, sample_analysis_verified):
        """Test explanation generation for compliant result."""
        explanation = service.generate_decision_explanation(
            verification_status=VerificationStatus.VERIFIED,
            compliance_result=ComplianceResult.COMPLIANT,
            reply_analysis=sample_analysis_verified,
            university_found=True
        )
        
        assert "COMPLIANT" in explanation
        assert len(explanation) > 0
    
    def test_generate_explanation_no_university(self, service):
        """Test explanation when university not found."""
        explanation = service.generate_decision_explanation(
            verification_status=VerificationStatus.INCONCLUSIVE,
            compliance_result=ComplianceResult.INCONCLUSIVE,
            reply_analysis=None,
            university_found=False
        )
        
        assert "INCONCLUSIVE" in explanation
        assert "university" in explanation.lower()
    
    def test_create_report(self, service, sample_fields, sample_analysis_verified):
        """Test creating a compliance report."""
        audit_log = [
            AuditLogEntry(
                step="test_step",
                action="Test action"
            )
        ]
        
        report = service.create_report(
            pdf_filename="test.pdf",
            extracted_fields=sample_fields,
            verification_status=VerificationStatus.VERIFIED,
            audit_log=audit_log,
            processing_time=1.5
        )
        
        assert report is not None
        assert report.pdf_filename == "test.pdf"
        assert report.compliance_result == ComplianceResult.COMPLIANT
        assert report.verification_status == VerificationStatus.VERIFIED
        assert len(report.audit_log) == 1
    
    def test_report_saved_to_file(self, service, sample_fields):
        """Test that report is saved to file."""
        report = service.create_report(
            pdf_filename="test.pdf",
            extracted_fields=sample_fields,
            verification_status=VerificationStatus.VERIFIED,
            audit_log=[]
        )
        
        filepath = service.reports_dir / f"{report.id}.json"
        assert filepath.exists()
    
    def test_get_report(self, service, sample_fields):
        """Test retrieving a report by ID."""
        created = service.create_report(
            pdf_filename="get_test.pdf",
            extracted_fields=sample_fields,
            verification_status=VerificationStatus.VERIFIED,
            audit_log=[]
        )
        
        retrieved = service.get_report(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.pdf_filename == "get_test.pdf"
    
    def test_list_reports(self, service, sample_fields):
        """Test listing reports."""
        # Create a few reports
        for i in range(3):
            service.create_report(
                pdf_filename=f"list_test_{i}.pdf",
                extracted_fields=sample_fields,
                verification_status=VerificationStatus.VERIFIED,
                audit_log=[]
            )
        
        reports = service.list_reports(10)
        assert len(reports) >= 3
    
    def test_export_report_text(self, service, sample_fields, sample_analysis_verified):
        """Test exporting report as text."""
        report = service.create_report(
            pdf_filename="export_test.pdf",
            extracted_fields=sample_fields,
            verification_status=VerificationStatus.VERIFIED,
            audit_log=[],
            reply_analysis=sample_analysis_verified
        )
        
        text = service.export_report_text(report)
        
        assert "COMPLIANCE VERIFICATION REPORT" in text
        assert "export_test.pdf" in text
        assert "COMPLIANT" in text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
