"""
Tool Definitions for LangChain Function Calling.
Contains JSON schemas that describe each tool's interface.
"""

# LangChain tool definitions for function calling
TOOL_DEFINITIONS = [
    {
        "name": "parse_pdf",
        "description": "Read a PDF file and extract raw text content",
        "parameters": {
            "type": "object",
            "properties": {
                "pdf_path": {
                    "type": "string",
                    "description": "Path to the PDF file to parse"
                }
            },
            "required": ["pdf_path"]
        }
    },
    {
        "name": "extract_fields",
        "description": "Extract structured fields (name, university, degree, date) from certificate text",
        "parameters": {
            "type": "object",
            "properties": {
                "raw_text": {
                    "type": "string",
                    "description": "Raw text content from the certificate"
                }
            },
            "required": ["raw_text"]
        }
    },
    {
        "name": "identify_university",
        "description": "Determine the official university name from extracted certificate data",
        "parameters": {
            "type": "object",
            "properties": {
                "university_name": {
                    "type": "string",
                    "description": "University name from extracted fields"
                }
            },
            "required": ["university_name"]
        }
    },
    {
        "name": "lookup_contact",
        "description": "Find contact information (email) for a university",
        "parameters": {
            "type": "object",
            "properties": {
                "university_name": {
                    "type": "string",
                    "description": "Name of the university to look up"
                }
            },
            "required": ["university_name"]
        }
    },
    {
        "name": "draft_email",
        "description": "Generate a professional verification request email",
        "parameters": {
            "type": "object",
            "properties": {
                "candidate_name": {"type": "string"},
                "degree_name": {"type": "string"},
                "university_name": {"type": "string"},
                "reference_id": {"type": "string"}
            },
            "required": ["candidate_name", "degree_name", "university_name", "reference_id"]
        }
    },
    {
        "name": "send_to_outbox",
        "description": "Store the verification email in the outbox for sending",
        "parameters": {
            "type": "object",
            "properties": {
                "recipient_email": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"}
            },
            "required": ["recipient_email", "subject", "body"]
        }
    },
    {
        "name": "read_reply",
        "description": "Get the university's reply email for a verification request",
        "parameters": {
            "type": "object",
            "properties": {
                "reference_id": {
                    "type": "string",
                    "description": "The verification reference ID"
                }
            },
            "required": ["reference_id"]
        }
    },
    {
        "name": "analyze_reply",
        "description": "Analyze and interpret the university reply to determine verification status",
        "parameters": {
            "type": "object",
            "properties": {
                "reply_text": {
                    "type": "string",
                    "description": "The body of the university reply email"
                }
            },
            "required": ["reply_text"]
        }
    },
    {
        "name": "decide_compliance",
        "description": "Make the final compliance decision based on verification analysis",
        "parameters": {
            "type": "object",
            "properties": {
                "verification_status": {
                    "type": "string",
                    "enum": ["VERIFIED", "NOT_VERIFIED", "INCONCLUSIVE"]
                },
                "confidence": {
                    "type": "number",
                    "description": "Confidence score from 0 to 1"
                }
            },
            "required": ["verification_status"]
        }
    },
    {
        "name": "log_step",
        "description": "Log an action or observation in the audit trail for compliance tracking",
        "parameters": {
            "type": "object",
            "properties": {
                "step": {
                    "type": "string",
                    "description": "Identifier for this step (e.g., 'validation_check')"
                },
                "action": {
                    "type": "string",
                    "description": "Human-readable description of what happened"
                },
                "details": {
                    "type": "object",
                    "description": "Optional additional details to log"
                },
                "success": {
                    "type": "boolean",
                    "description": "Whether the step was successful"
                }
            },
            "required": ["step", "action"]
        }
    }
]
