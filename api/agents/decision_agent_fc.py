"""
Decision Agent with Function Calling

Enhanced DecisionAgent that uses OpenAI Function Calling to dynamically
decide which tools to call based on the context, rather than following
a fixed sequential pipeline.

This demonstrates modern AI agent patterns while maintaining the 
auditability required for RegTech compliance.
"""
import json
from typing import Optional, Dict, Any, List

from api.models.schemas import (
    ExtractedFields,
    IncomingEmail,
    ReplyAnalysis,
    ComplianceResult,
    VerificationStatus
)
from api.tools.tools import AgentTools
from api.tools.decision_tools import (
    DECISION_AGENT_TOOLS,
    TERMINAL_TOOLS,
    DECISION_AGENT_SYSTEM_PROMPT
)
from api.services.audit_logger import AuditLogger
from api.utils.llm_client import LLMClient


class DecisionAgentWithFunctionCalling:
    """
    Enhanced DecisionAgent using OpenAI Function Calling.
    
    Unlike the original DecisionAgent which follows a fixed pipeline
    (analyze_reply → decide_compliance), this agent uses the LLM to 
    dynamically decide which tools to call based on the context.
    
    Key Features:
    - Dynamic tool selection by LLM
    - Ability to escalate suspicious cases
    - Adaptive path for ambiguous replies
    - Complete audit trail of all tool calls
    - Safety limits (max iterations)
    """
    
    AGENT_NAME = "DecisionAgentFC"
    DEFAULT_MAX_ITERATIONS = 5
    
    def __init__(
        self,
        tools: AgentTools,
        audit_logger: Optional[AuditLogger] = None,
        llm_client: Optional[LLMClient] = None
    ):
        """
        Initialize the function calling decision agent.
        
        Args:
            tools: AgentTools instance with all tools
            audit_logger: Optional audit logger
            llm_client: Optional LLM client (uses tools.llm if not provided)
        """
        self.tools = tools
        self.audit = audit_logger or tools.audit
        self.llm = llm_client or tools.llm
        
        # Track tool calls for this session
        self.tool_calls_made: List[str] = []
        self.escalation_info: Optional[Dict] = None
        self.clarification_info: Optional[Dict] = None
    
    def run(
        self,
        incoming_email: Optional[IncomingEmail],
        extracted_fields: ExtractedFields,
        contact_found: bool = True,
        max_iterations: int = DEFAULT_MAX_ITERATIONS
    ) -> Dict[str, Any]:
        """
        Execute the decision workflow using function calling.
        
        Args:
            incoming_email: Reply from university (None if no contact)
            extracted_fields: Certificate information
            contact_found: Whether university contact was found
            max_iterations: Maximum LLM iterations (safety limit)
            
        Returns:
            Dictionary with decision results, tool calls made, and any escalation info
        """
        # Reset session state
        self.tool_calls_made = []
        self.escalation_info = None
        self.clarification_info = None
        
        self.audit.log_step(
            step="decision_agent_fc_start",
            action="Starting decision workflow with function calling",
            agent=self.AGENT_NAME,
            input_data={
                "has_reply": incoming_email is not None,
                "contact_found": contact_found,
                "max_iterations": max_iterations
            }
        )
        
        # Handle case where no university contact was found
        if not contact_found or incoming_email is None:
            return self._handle_no_contact()
        
        # Build initial messages for the LLM
        messages = self._build_initial_messages(incoming_email, extracted_fields)
        
        # Function calling loop
        final_result = None
        for iteration in range(max_iterations):
            self.audit.log_step(
                step=f"fc_iteration_{iteration + 1}",
                action=f"LLM deciding next action (iteration {iteration + 1}/{max_iterations})",
                agent=self.AGENT_NAME
            )
            
            # Call LLM with tools
            response = self.llm.complete_with_tools(
                messages=messages,
                tools=DECISION_AGENT_TOOLS,
                temperature=0  # Deterministic for compliance
            )
            
            if response is None:
                self.audit.log_step(
                    step="fc_error",
                    action="LLM returned no response",
                    agent=self.AGENT_NAME,
                    success=False
                )
                break
            
            # Check if LLM wants to call a tool
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_call = response.tool_calls[0]
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                self.tool_calls_made.append(tool_name)
                
                # Execute the tool
                tool_result = self._execute_tool(
                    tool_name=tool_name,
                    tool_args=tool_args,
                    incoming_email=incoming_email,
                    extracted_fields=extracted_fields
                )
                
                # Append assistant message and tool result to conversation
                messages = self._append_tool_result(
                    messages=messages,
                    assistant_message=response,
                    tool_call=tool_call,
                    tool_result=tool_result
                )
                
                # Check for terminal tools
                if tool_name in TERMINAL_TOOLS:
                    final_result = tool_result
                    self.audit.log_step(
                        step="fc_terminal_tool",
                        action=f"Terminal tool called: {tool_name}",
                        agent=self.AGENT_NAME,
                        output_data={"tool": tool_name, "iterations_used": iteration + 1}
                    )
                    break
            else:
                # LLM finished without tool call
                self.audit.log_step(
                    step="fc_no_tool_call",
                    action="LLM finished without calling a tool",
                    agent=self.AGENT_NAME
                )
                break
        
        # Build final result
        return self._build_final_result(final_result, incoming_email, extracted_fields)
    
    def _handle_no_contact(self) -> Dict[str, Any]:
        """Handle case where no university contact was found."""
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
                "verification database. Manual verification is required."
            ),
            "function_calling_enabled": True,
            "tool_calls_made": [],
            "escalated_to_human": False,
            "escalation_reason": None,
            "clarification_needed": False,
            "missing_information": None
        }
    
    def _build_initial_messages(
        self,
        incoming_email: IncomingEmail,
        extracted_fields: ExtractedFields
    ) -> List[Dict[str, str]]:
        """Build the initial conversation messages for the LLM."""
        user_message = f"""Please analyze this university verification reply and make a compliance decision.

## Certificate Information
- Candidate Name: {extracted_fields.candidate_name}
- University: {extracted_fields.university_name}
- Degree: {extracted_fields.degree_name}
- Issue Date: {extracted_fields.issue_date}

## University Reply
- From: {incoming_email.sender_email} ({incoming_email.sender_name})
- Subject: {incoming_email.subject}
- Reference ID: {incoming_email.reference_id}

### Reply Content:
{incoming_email.body}

---

Based on this reply, determine the appropriate action. If the reply clearly confirms or denies 
the certificate authenticity, you may directly make a compliance decision. If the reply is 
ambiguous or you notice any red flags, use the appropriate tools to analyze further or escalate."""

        return [
            {"role": "system", "content": DECISION_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    
    def _execute_tool(
        self,
        tool_name: str,
        tool_args: Dict,
        incoming_email: IncomingEmail,
        extracted_fields: ExtractedFields
    ) -> Dict[str, Any]:
        """Execute a tool and return the result."""
        self.audit.log_step(
            step=f"tool_execution_{tool_name}",
            action=f"Executing tool: {tool_name}",
            agent=self.AGENT_NAME,
            tool=tool_name,
            input_data=tool_args
        )
        
        if tool_name == "analyze_reply":
            return self._handle_analyze_reply(incoming_email, extracted_fields, tool_args)
        elif tool_name == "request_clarification":
            return self._handle_request_clarification(tool_args)
        elif tool_name == "escalate_to_human":
            return self._handle_escalate_to_human(tool_args)
        elif tool_name == "decide_compliance":
            return self._handle_decide_compliance(tool_args)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    def _handle_analyze_reply(
        self,
        incoming_email: IncomingEmail,
        extracted_fields: ExtractedFields,
        tool_args: Dict
    ) -> Dict[str, Any]:
        """Handle analyze_reply tool call."""
        # Use existing analyze_reply from tools
        reply_analysis = self.tools.analyze_reply(incoming_email, extracted_fields)
        
        result = {
            "verification_status": reply_analysis.verification_status.value,
            "confidence_score": reply_analysis.confidence_score,
            "key_phrases": reply_analysis.key_phrases,
            "explanation": reply_analysis.explanation,
            "focus_areas_analyzed": tool_args.get("focus_areas", ["all"])
        }
        
        self.audit.log_step(
            step="tool_result_analyze_reply",
            action=f"Reply analysis complete: {reply_analysis.verification_status.value}",
            agent=self.AGENT_NAME,
            tool="analyze_reply",
            output_data=result
        )
        
        return result
    
    def _handle_request_clarification(self, tool_args: Dict) -> Dict[str, Any]:
        """Handle request_clarification tool call."""
        self.clarification_info = {
            "reason": tool_args.get("reason"),
            "missing_information": tool_args.get("missing_information", []),
            "suggested_follow_up": tool_args.get("suggested_follow_up")
        }
        
        result = {
            "status": "clarification_requested",
            **self.clarification_info
        }
        
        self.audit.log_step(
            step="tool_result_request_clarification",
            action="Clarification requested",
            agent=self.AGENT_NAME,
            tool="request_clarification",
            output_data=result
        )
        
        return result
    
    def _handle_escalate_to_human(self, tool_args: Dict) -> Dict[str, Any]:
        """Handle escalate_to_human tool call."""
        self.escalation_info = {
            "reason": tool_args.get("reason"),
            "priority": tool_args.get("priority"),
            "risk_indicators": tool_args.get("risk_indicators", [])
        }
        
        result = {
            "status": "escalated",
            **self.escalation_info
        }
        
        self.audit.log_step(
            step="tool_result_escalate_to_human",
            action=f"Case escalated to human (priority: {self.escalation_info['priority']})",
            agent=self.AGENT_NAME,
            tool="escalate_to_human",
            output_data=result
        )
        
        return result
    
    def _handle_decide_compliance(self, tool_args: Dict) -> Dict[str, Any]:
        """Handle decide_compliance tool call."""
        status_str = tool_args.get("status", "INCONCLUSIVE")
        
        try:
            compliance_result = ComplianceResult(status_str)
        except ValueError:
            compliance_result = ComplianceResult.INCONCLUSIVE
        
        # Map compliance result to verification status
        status_mapping = {
            ComplianceResult.COMPLIANT: VerificationStatus.VERIFIED,
            ComplianceResult.NOT_COMPLIANT: VerificationStatus.NOT_VERIFIED,
            ComplianceResult.INCONCLUSIVE: VerificationStatus.INCONCLUSIVE
        }
        verification_status = status_mapping.get(compliance_result, VerificationStatus.INCONCLUSIVE)
        
        result = {
            "compliance_result": compliance_result.value,
            "verification_status": verification_status.value,
            "confidence_score": tool_args.get("confidence_score", 0.5),
            "explanation": tool_args.get("explanation", ""),
            "evidence_summary": tool_args.get("evidence_summary", "")
        }
        
        self.audit.log_step(
            step="tool_result_decide_compliance",
            action=f"Compliance decision made: {compliance_result.value}",
            agent=self.AGENT_NAME,
            tool="decide_compliance",
            output_data=result
        )
        
        return result
    
    def _append_tool_result(
        self,
        messages: List[Dict],
        assistant_message: Any,
        tool_call: Any,
        tool_result: Dict
    ) -> List[Dict]:
        """Append assistant's tool call and tool result to messages."""
        # Add assistant message with tool call
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": tool_call.id,
                "type": "function",
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments
                }
            }]
        })
        
        # Add tool result
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(tool_result)
        })
        
        return messages
    
    def _build_final_result(
        self,
        final_result: Optional[Dict],
        incoming_email: IncomingEmail,
        extracted_fields: ExtractedFields
    ) -> Dict[str, Any]:
        """Build the final result dictionary."""
        # Handle escalation case
        if self.escalation_info:
            return {
                "reply_analysis": None,
                "compliance_result": ComplianceResult.INCONCLUSIVE,
                "verification_status": VerificationStatus.INCONCLUSIVE,
                "explanation": f"ESCALATED: {self.escalation_info['reason']}",
                "function_calling_enabled": True,
                "tool_calls_made": self.tool_calls_made,
                "escalated_to_human": True,
                "escalation_reason": self.escalation_info["reason"],
                "escalation_priority": self.escalation_info["priority"],
                "risk_indicators": self.escalation_info.get("risk_indicators", []),
                "clarification_needed": False,
                "missing_information": None
            }
        
        # Handle clarification case
        if self.clarification_info and not final_result:
            return {
                "reply_analysis": None,
                "compliance_result": ComplianceResult.INCONCLUSIVE,
                "verification_status": VerificationStatus.INCONCLUSIVE,
                "explanation": f"CLARIFICATION NEEDED: {self.clarification_info['reason']}",
                "function_calling_enabled": True,
                "tool_calls_made": self.tool_calls_made,
                "escalated_to_human": False,
                "escalation_reason": None,
                "clarification_needed": True,
                "missing_information": self.clarification_info.get("missing_information", [])
            }
        
        # Handle normal decision case
        if final_result and "compliance_result" in final_result:
            compliance_result = ComplianceResult(final_result["compliance_result"])
            verification_status = VerificationStatus(final_result["verification_status"])
            
            # Build reply_analysis for compatibility
            reply_analysis = ReplyAnalysis(
                verification_status=verification_status,
                confidence_score=final_result.get("confidence_score", 0.5),
                key_phrases=[],
                explanation=final_result.get("explanation", "")
            )
            
            return {
                "reply_analysis": reply_analysis,
                "compliance_result": compliance_result,
                "verification_status": verification_status,
                "explanation": final_result.get("explanation", ""),
                "function_calling_enabled": True,
                "tool_calls_made": self.tool_calls_made,
                "escalated_to_human": False,
                "escalation_reason": None,
                "clarification_needed": self.clarification_info is not None,
                "missing_information": self.clarification_info.get("missing_information") if self.clarification_info else None
            }
        
        # Fallback if no terminal tool was called
        self.audit.log_step(
            step="fc_fallback",
            action="No terminal tool called - using fallback decision",
            agent=self.AGENT_NAME,
            success=False
        )
        
        return {
            "reply_analysis": None,
            "compliance_result": ComplianceResult.INCONCLUSIVE,
            "verification_status": VerificationStatus.INCONCLUSIVE,
            "explanation": "INCONCLUSIVE: Agent loop ended without making a decision.",
            "function_calling_enabled": True,
            "tool_calls_made": self.tool_calls_made,
            "escalated_to_human": False,
            "escalation_reason": None,
            "clarification_needed": False,
            "missing_information": None
        }


class DecisionAgentFCResult:
    """Result container for function calling decision agent."""
    
    def __init__(
        self,
        reply_analysis: Optional[ReplyAnalysis],
        compliance_result: ComplianceResult,
        verification_status: VerificationStatus,
        explanation: str,
        function_calling_enabled: bool = True,
        tool_calls_made: List[str] = None,
        escalated_to_human: bool = False,
        escalation_reason: Optional[str] = None,
        clarification_needed: bool = False,
        missing_information: Optional[List[str]] = None
    ):
        self.reply_analysis = reply_analysis
        self.compliance_result = compliance_result
        self.verification_status = verification_status
        self.explanation = explanation
        self.function_calling_enabled = function_calling_enabled
        self.tool_calls_made = tool_calls_made or []
        self.escalated_to_human = escalated_to_human
        self.escalation_reason = escalation_reason
        self.clarification_needed = clarification_needed
        self.missing_information = missing_information
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionAgentFCResult":
        """Create from dictionary."""
        return cls(
            reply_analysis=data.get("reply_analysis"),
            compliance_result=data["compliance_result"],
            verification_status=data["verification_status"],
            explanation=data["explanation"],
            function_calling_enabled=data.get("function_calling_enabled", True),
            tool_calls_made=data.get("tool_calls_made", []),
            escalated_to_human=data.get("escalated_to_human", False),
            escalation_reason=data.get("escalation_reason"),
            clarification_needed=data.get("clarification_needed", False),
            missing_information=data.get("missing_information")
        )
