"""
Compliance Service
Handles compliance decision logic and report generation.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from api.models.schemas import (
    ComplianceReport,
    ComplianceResult,
    VerificationStatus,
    ExtractedFields,
    UniversityContact,
    OutgoingEmail,
    IncomingEmail,
    ReplyAnalysis,
    AuditLogEntry
)


class ComplianceService:
    """Service for compliance decisions and report generation."""
    
    # Mapping from verification status to compliance result
    STATUS_TO_COMPLIANCE = {
        VerificationStatus.VERIFIED: ComplianceResult.COMPLIANT,
        VerificationStatus.NOT_VERIFIED: ComplianceResult.NOT_COMPLIANT,
        VerificationStatus.INCONCLUSIVE: ComplianceResult.INCONCLUSIVE
    }
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.reports_dir = self.data_dir / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def determine_compliance(
        self,
        verification_status: VerificationStatus
    ) -> ComplianceResult:
        """
        Map verification status to compliance result.
        
        Args:
            verification_status: The verification outcome
            
        Returns:
            Corresponding compliance result
        """
        return self.STATUS_TO_COMPLIANCE.get(
            verification_status,
            ComplianceResult.INCONCLUSIVE
        )
    
    def generate_decision_explanation(
        self,
        verification_status: VerificationStatus,
        compliance_result: ComplianceResult,
        reply_analysis: Optional[ReplyAnalysis] = None,
        university_found: bool = True
    ) -> str:
        """
        Generate human-readable explanation for the compliance decision.
        
        Args:
            verification_status: The verification outcome
            compliance_result: The compliance result
            reply_analysis: Analysis of the university reply
            university_found: Whether university was found in database
            
        Returns:
            Human-readable explanation string
        """
        if not university_found:
            return (
                "INCONCLUSIVE: The issuing university could not be identified in our "
                "verification database. Manual verification is required. The certificate "
                "authenticity cannot be confirmed through automated means."
            )
        
        explanations = {
            ComplianceResult.COMPLIANT: (
                f"COMPLIANT: The certificate has been verified as authentic by the issuing "
                f"university. {reply_analysis.explanation if reply_analysis else ''} "
                f"Confidence score: {reply_analysis.confidence_score:.0%}" if reply_analysis else ""
            ),
            ComplianceResult.NOT_COMPLIANT: (
                f"NOT COMPLIANT: The university was unable to verify the certificate. "
                f"{reply_analysis.explanation if reply_analysis else ''} "
                f"This credential should be treated as potentially fraudulent. "
                f"Further investigation is recommended."
            ),
            ComplianceResult.INCONCLUSIVE: (
                f"INCONCLUSIVE: The verification process could not reach a definitive "
                f"conclusion. {reply_analysis.explanation if reply_analysis else ''} "
                f"Additional information may be required from the university or applicant."
            )
        }
        
        base_explanation = explanations.get(
            compliance_result,
            "Unable to determine compliance status."
        )
        
        return base_explanation.strip()
    
    def create_report(
        self,
        pdf_filename: str,
        extracted_fields: ExtractedFields,
        verification_status: VerificationStatus,
        audit_log: List[AuditLogEntry],
        university_contact: Optional[UniversityContact] = None,
        outgoing_email: Optional[OutgoingEmail] = None,
        incoming_email: Optional[IncomingEmail] = None,
        reply_analysis: Optional[ReplyAnalysis] = None,
        processing_time: Optional[float] = None
    ) -> ComplianceReport:
        """
        Create a comprehensive compliance report.
        
        Args:
            pdf_filename: Name of the processed PDF
            extracted_fields: Fields extracted from certificate
            verification_status: Final verification status
            audit_log: Complete audit trail
            university_contact: University contact info (if found)
            outgoing_email: Verification request email (if sent)
            incoming_email: University reply (if received)
            reply_analysis: Analysis of reply (if performed)
            processing_time: Time taken to process
            
        Returns:
            Complete ComplianceReport object
        """
        compliance_result = self.determine_compliance(verification_status)
        
        decision_explanation = self.generate_decision_explanation(
            verification_status=verification_status,
            compliance_result=compliance_result,
            reply_analysis=reply_analysis,
            university_found=university_contact is not None
        )
        
        report = ComplianceReport(
            pdf_filename=pdf_filename,
            extracted_fields=extracted_fields,
            university_identified=extracted_fields.university_name,
            university_contact=university_contact,
            outgoing_email=outgoing_email,
            incoming_email=incoming_email,
            reply_analysis=reply_analysis,
            verification_status=verification_status,
            compliance_result=compliance_result,
            decision_explanation=decision_explanation,
            audit_log=audit_log,
            processing_time_seconds=processing_time
        )
        
        # Save report
        self._save_report(report)
        
        return report
    
    def _save_report(self, report: ComplianceReport) -> None:
        """Save report to file."""
        filename = f"{report.id}.json"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report.model_dump(mode='json'), f, indent=2, default=str)
    
    def get_report(self, report_id: str) -> Optional[ComplianceReport]:
        """Load a report by ID."""
        filepath = self.reports_dir / f"{report_id}.json"
        
        if not filepath.exists():
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return ComplianceReport(**data)
    
    def list_reports(self, limit: int = 50) -> List[dict]:
        """List recent compliance reports."""
        reports = []
        
        for filepath in sorted(
            self.reports_dir.glob("*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:limit]:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                reports.append({
                    "id": data.get("id"),
                    "created_at": data.get("created_at"),
                    "pdf_filename": data.get("pdf_filename"),
                    "compliance_result": data.get("compliance_result"),
                    "university_identified": data.get("university_identified")
                })
        
        return reports
    
    def export_report_text(self, report: ComplianceReport) -> str:
        """Export report as human-readable text."""
        lines = [
            "=" * 70,
            "COMPLIANCE VERIFICATION REPORT",
            "=" * 70,
            "",
            f"Report ID: {report.id}",
            f"Generated: {report.created_at}",
            f"Processing Time: {report.processing_time_seconds:.2f}s" if report.processing_time_seconds else "",
            "",
            "-" * 70,
            "FINAL DECISION",
            "-" * 70,
            f"Compliance Result: {report.compliance_result.value}",
            f"Verification Status: {report.verification_status.value}",
            "",
            "Explanation:",
            report.decision_explanation,
            "",
            "-" * 70,
            "CERTIFICATE INFORMATION",
            "-" * 70,
            f"File: {report.pdf_filename}",
            f"Candidate: {report.extracted_fields.candidate_name}",
            f"University: {report.extracted_fields.university_name}",
            f"Degree: {report.extracted_fields.degree_name}",
            f"Issue Date: {report.extracted_fields.issue_date}",
            "",
        ]
        
        if report.university_contact:
            lines.extend([
                "-" * 70,
                "UNIVERSITY CONTACT",
                "-" * 70,
                f"Name: {report.university_contact.name}",
                f"Email: {report.university_contact.email}",
                f"Department: {report.university_contact.verification_department}",
                "",
            ])
        
        if report.outgoing_email:
            lines.extend([
                "-" * 70,
                "OUTGOING VERIFICATION REQUEST",
                "-" * 70,
                f"To: {report.outgoing_email.recipient_email}",
                f"Subject: {report.outgoing_email.subject}",
                f"Reference: {report.outgoing_email.reference_id}",
                "",
                "Body:",
                report.outgoing_email.body,
                "",
            ])
        
        if report.incoming_email:
            lines.extend([
                "-" * 70,
                "UNIVERSITY REPLY",
                "-" * 70,
                f"From: {report.incoming_email.sender_email}",
                f"Subject: {report.incoming_email.subject}",
                "",
                "Body:",
                report.incoming_email.body,
                "",
            ])
        
        if report.reply_analysis:
            lines.extend([
                "-" * 70,
                "AI ANALYSIS OF REPLY",
                "-" * 70,
                f"Status: {report.reply_analysis.verification_status.value}",
                f"Confidence: {report.reply_analysis.confidence_score:.0%}",
                f"Key Phrases: {', '.join(report.reply_analysis.key_phrases)}",
                f"Explanation: {report.reply_analysis.explanation}",
                "",
            ])
        
        lines.extend([
            "-" * 70,
            "AUDIT TRAIL",
            "-" * 70,
        ])
        
        for entry in report.audit_log:
            status = "✓" if entry.success else "✗"
            lines.append(f"{status} [{entry.timestamp}] {entry.step}: {entry.action}")
        
        lines.extend([
            "",
            "=" * 70,
            "END OF REPORT",
            "=" * 70,
        ])
        
        return "\n".join(lines)
