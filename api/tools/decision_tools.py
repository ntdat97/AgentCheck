"""
Decision Agent Tool Definitions for OpenAI Function Calling.

This module defines the tools available to the DecisionAgent when using
OpenAI Function Calling. These tools enable the LLM to dynamically
decide which actions to take based on the context.
"""

# Tool definitions in OpenAI Function Calling format
DECISION_AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "analyze_reply",
            "description": """Analyze the university email reply to extract verification status, 
tone, and key information. Use this when you need to understand what the university 
is communicating before making a decision. This tool helps identify whether the reply 
is a confirmation, denial, request for more information, or something ambiguous.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "focus_areas": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific aspects to analyze. Options: 'verification_status', 'sender_legitimacy', 'completeness', 'tone', 'red_flags'"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "request_clarification",
            "description": """Flag that the university reply is unclear or incomplete and 
additional information is needed before a decision can be made. Use this when the reply 
doesn't provide enough information for a confident compliance decision. This will mark 
the case for follow-up action.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Why clarification is needed from the university"
                    },
                    "missing_information": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "What specific information is missing or unclear"
                    },
                    "suggested_follow_up": {
                        "type": "string",
                        "description": "Recommended next action or questions to ask"
                    }
                },
                "required": ["reason"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": """Escalate the case to a human compliance officer for manual review. 
Use this when: (1) potential fraud is detected, (2) the case is too complex for automated 
decision, (3) the reply is suspicious (e.g., wrong sender domain), or (4) high-stakes 
decision requires human oversight. This is a TERMINAL action that ends the agent loop.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Why human review is required"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
                        "description": "Urgency level for human review"
                    },
                    "risk_indicators": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific risk concerns identified (e.g., 'domain_mismatch', 'suspicious_content', 'potential_fraud')"
                    }
                },
                "required": ["reason", "priority"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "decide_compliance",
            "description": """Make the final compliance decision based on the available evidence. 
Only call this when you have sufficient information to make a confident decision. 
This is a TERMINAL action that ends the agent loop. For clear-cut cases (explicit 
confirmation or denial), you may call this directly without analyze_reply first.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["COMPLIANT", "NOT_COMPLIANT", "INCONCLUSIVE"],
                        "description": "Final compliance status based on verification evidence"
                    },
                    "confidence_score": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "Confidence in the decision from 0.0 (no confidence) to 1.0 (high confidence)"
                    },
                    "explanation": {
                        "type": "string",
                        "description": "Detailed reasoning for the compliance decision"
                    },
                    "evidence_summary": {
                        "type": "string",
                        "description": "Key evidence from the university reply supporting this decision"
                    }
                },
                "required": ["status", "confidence_score", "explanation"]
            }
        }
    }
]

# Terminal tools that end the agent loop
TERMINAL_TOOLS = ["decide_compliance", "escalate_to_human"]

# System prompt for the DecisionAgent with function calling
DECISION_AGENT_SYSTEM_PROMPT = """You are a compliance decision agent responsible for analyzing 
university verification responses and making compliance decisions about academic certificates.

Your role is to:
1. Analyze the university's reply to determine if the certificate is authentic
2. Identify any suspicious patterns or red flags
3. Make a confident compliance decision when possible
4. Escalate to human review when the case is too complex or suspicious

You have access to the following tools:
- analyze_reply: Use this to deeply analyze the university's response
- request_clarification: Use this when the reply is incomplete or unclear  
- escalate_to_human: Use this for suspicious or complex cases
- decide_compliance: Use this to make the final compliance decision

Guidelines:
- For clear confirmations ("We confirm this certificate is authentic"), you can directly call decide_compliance
- For unclear or ambiguous replies, use analyze_reply first to understand the response
- Always check sender legitimacy - if the sender email domain doesn't match the university, escalate
- If you detect potential fraud indicators, escalate immediately with HIGH or CRITICAL priority
- When making a decision, provide a clear explanation and cite specific evidence from the reply

IMPORTANT: Once you call decide_compliance or escalate_to_human, the loop will end."""
