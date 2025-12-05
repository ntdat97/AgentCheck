"""
Tests for Decision Agent with Function Calling

Tests cover:
- Clear verification (single tool call)
- Ambiguous reply (multiple tool calls)
- Suspicious sender (escalation path)
- Max iterations safety
- Audit trail completeness
"""
import pytest
import sys
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass
from typing import Optional, List

# Add api to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.agents.decision_agent_fc import DecisionAgentWithFunctionCalling
from api.tools.tools import AgentTools
from api.tools.decision_tools import DECISION_AGENT_TOOLS, TERMINAL_TOOLS
from api.models.schemas import (
    VerificationStatus,
    ComplianceResult,
    ExtractedFields,
    IncomingEmail
)


def create_test_prompts(prompts_dir: Path):
    """Create minimal test prompt templates."""
    (prompts_dir / "extract_fields.j2").write_text("""
Extract certificate fields from: {{ raw_text }}
Return JSON with candidate_name, university_name, degree_name, issue_date.
""")
    (prompts_dir / "identify_university.j2").write_text("""
Identify the university from: {{ raw_text }}
Return JSON with university_name.
""")
    (prompts_dir / "draft_email.j2").write_text("""
Draft a verification email for {{ candidate_name }} to {{ university_name }}.
""")
    (prompts_dir / "analyze_reply.j2").write_text("""
Analyze this reply: {{ reply_text }}
Return JSON with verification_status, confidence_score, key_phrases, explanation.
""")


# Mock classes for OpenAI response
@dataclass
class MockFunctionCall:
    name: str
    arguments: str

@dataclass
class MockToolCall:
    id: str
    type: str
    function: MockFunctionCall

@dataclass
class MockMessage:
    role: str
    content: Optional[str]
    tool_calls: Optional[List[MockToolCall]]


class TestDecisionAgentFunctionCalling:
    """Tests for DecisionAgentWithFunctionCalling."""
    
    @pytest.fixture
    def tools(self, tmp_path):
        """Create tools with test directories."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        # Create universities.json
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
    
    @pytest.fixture
    def agent(self, tools):
        """Create decision agent with function calling."""
        return DecisionAgentWithFunctionCalling(tools)
    
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
    def verified_reply(self):
        """Sample verified reply email."""
        return IncomingEmail(
            sender_email="verify@example.edu",
            sender_name="University Registrar",
            subject="RE: Verification Request",
            body="We confirm that John Smith graduated with a Bachelor of Science degree on May 15, 2023. Certificate number: CS-2023-1234. This certificate is authentic.",
            reference_id="TEST-123"
        )
    
    @pytest.fixture
    def ambiguous_reply(self):
        """Sample ambiguous reply email."""
        return IncomingEmail(
            sender_email="verify@example.edu",
            sender_name="University Registrar",
            subject="RE: Verification Request",
            body="Please provide additional documentation including the student ID and certificate serial number for our verification process.",
            reference_id="TEST-456"
        )
    
    @pytest.fixture
    def suspicious_reply(self):
        """Sample suspicious reply email."""
        return IncomingEmail(
            sender_email="random.person@gmail.com",
            sender_name="Unknown",
            subject="RE: Verification",
            body="Yes the certificate is valid.",
            reference_id="TEST-789"
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
        assert result["function_calling_enabled"] == True
        assert result["tool_calls_made"] == []
        assert result["escalated_to_human"] == False
    
    def test_clear_verified_single_call(self, agent, sample_fields, verified_reply):
        """Clear verification should result in single decide_compliance call."""
        # Mock LLM to directly call decide_compliance
        mock_response = MockMessage(
            role="assistant",
            content=None,
            tool_calls=[
                MockToolCall(
                    id="call_1",
                    type="function",
                    function=MockFunctionCall(
                        name="decide_compliance",
                        arguments=json.dumps({
                            "status": "COMPLIANT",
                            "confidence_score": 0.95,
                            "explanation": "University explicitly confirmed graduation",
                            "evidence_summary": "Certificate confirmed authentic"
                        })
                    )
                )
            ]
        )
        
        with patch.object(agent.llm, 'complete_with_tools', return_value=mock_response):
            result = agent.run(
                incoming_email=verified_reply,
                extracted_fields=sample_fields,
                contact_found=True
            )
        
        assert result["compliance_result"] == ComplianceResult.COMPLIANT
        assert result["verification_status"] == VerificationStatus.VERIFIED
        assert "decide_compliance" in result["tool_calls_made"]
        assert len(result["tool_calls_made"]) == 1  # Only one tool call
        assert result["function_calling_enabled"] == True
    
    def test_ambiguous_reply_multiple_calls(self, agent, sample_fields, ambiguous_reply):
        """Ambiguous reply should trigger analysis before decision."""
        # Mock LLM to first call analyze_reply, then request_clarification, then decide_compliance
        call_count = [0]
        
        def mock_complete_with_tools(messages, tools, **kwargs):
            call_count[0] += 1
            
            if call_count[0] == 1:
                # First call: analyze_reply
                return MockMessage(
                    role="assistant",
                    content=None,
                    tool_calls=[
                        MockToolCall(
                            id="call_1",
                            type="function",
                            function=MockFunctionCall(
                                name="analyze_reply",
                                arguments=json.dumps({
                                    "focus_areas": ["verification_status", "completeness"]
                                })
                            )
                        )
                    ]
                )
            elif call_count[0] == 2:
                # Second call: request_clarification
                return MockMessage(
                    role="assistant",
                    content=None,
                    tool_calls=[
                        MockToolCall(
                            id="call_2",
                            type="function",
                            function=MockFunctionCall(
                                name="request_clarification",
                                arguments=json.dumps({
                                    "reason": "University requires additional documentation",
                                    "missing_information": ["student_id", "certificate_serial"],
                                    "suggested_follow_up": "Collect missing documents"
                                })
                            )
                        )
                    ]
                )
            else:
                # Third call: decide_compliance
                return MockMessage(
                    role="assistant",
                    content=None,
                    tool_calls=[
                        MockToolCall(
                            id="call_3",
                            type="function",
                            function=MockFunctionCall(
                                name="decide_compliance",
                                arguments=json.dumps({
                                    "status": "INCONCLUSIVE",
                                    "confidence_score": 0.85,
                                    "explanation": "Verification pending - university requires additional documentation"
                                })
                            )
                        )
                    ]
                )
        
        with patch.object(agent.llm, 'complete_with_tools', side_effect=mock_complete_with_tools):
            with patch.object(agent.tools, 'analyze_reply') as mock_analyze:
                mock_analyze.return_value = Mock(
                    verification_status=VerificationStatus.INCONCLUSIVE,
                    confidence_score=0.5,
                    key_phrases=["additional documentation", "verification process"],
                    explanation="University needs more information"
                )
                
                result = agent.run(
                    incoming_email=ambiguous_reply,
                    extracted_fields=sample_fields,
                    contact_found=True
                )
        
        assert result["compliance_result"] == ComplianceResult.INCONCLUSIVE
        assert len(result["tool_calls_made"]) == 3
        assert "analyze_reply" in result["tool_calls_made"]
        assert "request_clarification" in result["tool_calls_made"]
        assert "decide_compliance" in result["tool_calls_made"]
    
    def test_suspicious_reply_escalation(self, agent, sample_fields, suspicious_reply):
        """Suspicious reply should escalate to human."""
        # Mock LLM to analyze then escalate
        call_count = [0]
        
        def mock_complete_with_tools(messages, tools, **kwargs):
            call_count[0] += 1
            
            if call_count[0] == 1:
                return MockMessage(
                    role="assistant",
                    content=None,
                    tool_calls=[
                        MockToolCall(
                            id="call_1",
                            type="function",
                            function=MockFunctionCall(
                                name="analyze_reply",
                                arguments=json.dumps({
                                    "focus_areas": ["sender_legitimacy"]
                                })
                            )
                        )
                    ]
                )
            else:
                return MockMessage(
                    role="assistant",
                    content=None,
                    tool_calls=[
                        MockToolCall(
                            id="call_2",
                            type="function",
                            function=MockFunctionCall(
                                name="escalate_to_human",
                                arguments=json.dumps({
                                    "reason": "Sender email domain does not match university - potential fraud",
                                    "priority": "HIGH",
                                    "risk_indicators": ["domain_mismatch", "external_sender"]
                                })
                            )
                        )
                    ]
                )
        
        with patch.object(agent.llm, 'complete_with_tools', side_effect=mock_complete_with_tools):
            with patch.object(agent.tools, 'analyze_reply') as mock_analyze:
                mock_analyze.return_value = Mock(
                    verification_status=VerificationStatus.INCONCLUSIVE,
                    confidence_score=0.3,
                    key_phrases=[],
                    explanation="Sender domain suspicious"
                )
                
                result = agent.run(
                    incoming_email=suspicious_reply,
                    extracted_fields=sample_fields,
                    contact_found=True
                )
        
        assert result["escalated_to_human"] == True
        assert result["escalation_reason"] == "Sender email domain does not match university - potential fraud"
        assert "escalate_to_human" in result["tool_calls_made"]
        assert result["compliance_result"] == ComplianceResult.INCONCLUSIVE
    
    def test_max_iterations_safety(self, agent, sample_fields, verified_reply):
        """Should not exceed max iterations."""
        # Mock LLM to never call a terminal tool
        mock_response = MockMessage(
            role="assistant",
            content=None,
            tool_calls=[
                MockToolCall(
                    id="call_1",
                    type="function",
                    function=MockFunctionCall(
                        name="analyze_reply",
                        arguments=json.dumps({"focus_areas": ["all"]})
                    )
                )
            ]
        )
        
        with patch.object(agent.llm, 'complete_with_tools', return_value=mock_response):
            with patch.object(agent.tools, 'analyze_reply') as mock_analyze:
                mock_analyze.return_value = Mock(
                    verification_status=VerificationStatus.INCONCLUSIVE,
                    confidence_score=0.5,
                    key_phrases=[],
                    explanation="Analysis"
                )
                
                result = agent.run(
                    incoming_email=verified_reply,
                    extracted_fields=sample_fields,
                    contact_found=True,
                    max_iterations=3
                )
        
        # Should only call analyze_reply 3 times (max iterations)
        assert len(result["tool_calls_made"]) == 3
        assert result["compliance_result"] == ComplianceResult.INCONCLUSIVE
    
    def test_tool_definitions_structure(self):
        """Test that tool definitions are correctly structured."""
        assert len(DECISION_AGENT_TOOLS) == 4
        
        tool_names = [t["function"]["name"] for t in DECISION_AGENT_TOOLS]
        assert "analyze_reply" in tool_names
        assert "request_clarification" in tool_names
        assert "escalate_to_human" in tool_names
        assert "decide_compliance" in tool_names
        
        # Check terminal tools
        assert "decide_compliance" in TERMINAL_TOOLS
        assert "escalate_to_human" in TERMINAL_TOOLS
    
    def test_function_calling_fields_in_result(self, agent, sample_fields, verified_reply):
        """Test that function calling fields are properly populated."""
        mock_response = MockMessage(
            role="assistant",
            content=None,
            tool_calls=[
                MockToolCall(
                    id="call_1",
                    type="function",
                    function=MockFunctionCall(
                        name="decide_compliance",
                        arguments=json.dumps({
                            "status": "COMPLIANT",
                            "confidence_score": 0.9,
                            "explanation": "Verified"
                        })
                    )
                )
            ]
        )
        
        with patch.object(agent.llm, 'complete_with_tools', return_value=mock_response):
            result = agent.run(
                incoming_email=verified_reply,
                extracted_fields=sample_fields,
                contact_found=True
            )
        
        # Check all function calling fields exist
        assert "function_calling_enabled" in result
        assert "tool_calls_made" in result
        assert "escalated_to_human" in result
        assert "escalation_reason" in result
        assert "clarification_needed" in result
        assert "missing_information" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
