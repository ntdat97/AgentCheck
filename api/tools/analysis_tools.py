"""
Analysis Tools Mixin
Handles university identification, contact lookup, reply analysis, and compliance decisions.
"""
from typing import Optional, Dict, Any

from api.models.schemas import (
    ExtractedFields,
    UniversityContact,
    IncomingEmail,
    ReplyAnalysis,
    VerificationStatus,
    ComplianceResult
)
from api.constants import (
    CONFIDENCE_SCORE_MEDIUM,
    CONFIDENCE_SCORE_LOW,
)


class AnalysisToolsMixin:
    """
    Mixin providing analysis and decision-making tools.
    Requires self.university_contacts, self.llm, self.prompt_loader, 
    self.compliance_service, and self.audit to be initialized by the main AgentTools class.
    """
    
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
