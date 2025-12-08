"""
LLM Client Utility
Wrapper for OpenAI/Groq API with retry logic and error handling.
"""
import os
import json
from typing import Optional, Dict, Any, List
from pathlib import Path

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from dotenv import load_dotenv

# Import constants from central config
from api.constants import (
    DEFAULT_PROVIDER,
    GROQ_API_BASE_URL,
    GROQ_DEFAULT_MODEL,
    GROQ_DEFAULT_VISION_MODEL,
    OPENAI_DEFAULT_MODEL,
    OPENAI_DEFAULT_VISION_MODEL,
    DEFAULT_TEMPERATURE,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_TOKENS,
)

# Load environment variables
load_dotenv()


class LLMClient:
    """
    Wrapper for LLM API calls.
    Supports OpenAI and Groq (OpenAI-compatible) models.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        vision_model: Optional[str] = None,
        temperature: float = DEFAULT_TEMPERATURE,
        max_retries: int = DEFAULT_MAX_RETRIES,
        provider: Optional[str] = None
    ):
        """
        Initialize LLM client.
        
        Args:
            api_key: API key (defaults to env var based on provider)
            model: Model to use for text (defaults to env var)
            vision_model: Model to use for vision/OCR (defaults to env var)
            temperature: Sampling temperature
            max_retries: Number of retries on failure
            provider: 'openai' or 'groq' (defaults to LLM_PROVIDER env var)
        """
        self.provider = provider or os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER).lower()
        
        # Set API key and base URL based on provider
        if self.provider == "groq":
            self.api_key = api_key or os.getenv("GROQ_API_KEY")
            self.base_url = GROQ_API_BASE_URL
            self.model = model or os.getenv("GROQ_MODEL", GROQ_DEFAULT_MODEL)
            self.vision_model = vision_model or os.getenv("GROQ_VISION_MODEL", GROQ_DEFAULT_VISION_MODEL)
        else:  # openai
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            self.base_url = None  # Use default OpenAI URL
            self.model = model or os.getenv("OPENAI_MODEL", OPENAI_DEFAULT_MODEL)
            self.vision_model = vision_model or os.getenv("OPENAI_VISION_MODEL", OPENAI_DEFAULT_VISION_MODEL)
        
        self.temperature = temperature
        self.max_retries = max_retries
        
        if OPENAI_AVAILABLE and self.api_key:
            if self.base_url:
                self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            else:
                self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
    
    def is_available(self) -> bool:
        """Check if LLM client is properly configured."""
        return self.client is not None

    def _is_new_model_format(self) -> bool:
        """Check if the model uses new API format (max_completion_tokens instead of max_tokens)."""
        # Models like gpt-5-*, o1-*, o3-* use the new format
        new_format_prefixes = ("gpt-5", "o1", "o3")
        return self.model and any(self.model.startswith(prefix) for prefix in new_format_prefixes)

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 2000,
        response_format: Optional[Dict] = None
    ) -> str:
        """
        Get a completion from the LLM.
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            temperature: Override default temperature
            max_tokens: Maximum tokens in response
            response_format: Optional response format (e.g., {"type": "json_object"})
            
        Returns:
            LLM response text
        """
        if not self.is_available():
            return self._mock_response(prompt)
        
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature or self.temperature,
        }

        # Use appropriate token parameter based on model
        if self._is_new_model_format():
            kwargs["max_completion_tokens"] = max_tokens
        else:
            kwargs["max_tokens"] = max_tokens
        
        if response_format:
            kwargs["response_format"] = response_format
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(**kwargs)
                return response.choices[0].message.content
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"LLM call failed after {self.max_retries} attempts: {e}")
                continue
        
        return ""
    
    def complete_with_tools(
        self,
        messages: List[Dict],
        tools: List[Dict],
        tool_choice: str = "auto",
        temperature: Optional[float] = None
    ) -> Any:
        """
        Call LLM with function calling capability.
        
        Args:
            messages: Conversation history
            tools: Tool definitions in OpenAI format
            tool_choice: "auto", "none", or {"type": "function", "function": {"name": "..."}}
            temperature: Override default temperature
            
        Returns:
            ChatCompletionMessage with potential tool_calls attribute
        """
        if not self.is_available():
            return self._mock_tool_response(messages, tools)
        
        kwargs = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": tool_choice,
            "temperature": temperature or self.temperature,
        }
        
        # Use appropriate token parameter based on model
        if self._is_new_model_format():
            kwargs["max_completion_tokens"] = DEFAULT_MAX_TOKENS
        else:
            kwargs["max_tokens"] = DEFAULT_MAX_TOKENS
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(**kwargs)
                return response.choices[0].message
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise RuntimeError(f"LLM tool call failed after {self.max_retries} attempts: {e}")
                continue
        
        return None
    
    def _mock_tool_response(self, messages: List[Dict], tools: List[Dict]) -> Any:
        """
        Provide mock tool response when LLM is not available.
        Returns a mock object that simulates OpenAI's ChatCompletionMessage.
        """
        from dataclasses import dataclass
        from typing import Optional, List as TypingList
        
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
            tool_calls: Optional[TypingList[MockToolCall]]
        
        # Analyze the last user message to determine appropriate mock response
        last_user_msg = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "").lower()
                break
        
        # Default to decide_compliance tool for simplicity
        import json
        return MockMessage(
            role="assistant",
            content=None,
            tool_calls=[
                MockToolCall(
                    id="mock_call_1",
                    type="function",
                    function=MockFunctionCall(
                        name="decide_compliance",
                        arguments=json.dumps({
                            "status": "COMPLIANT",
                            "confidence_score": 0.85,
                            "explanation": "Mock response - LLM not configured",
                            "evidence_summary": "Mock evidence"
                        })
                    )
                )
            ]
        )
    
    def complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Get a JSON response from the LLM.
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            temperature: Override default temperature
            
        Returns:
            Parsed JSON response
        """
        response = self.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            return self._extract_json(response)
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text that might have extra content."""
        # Try to find JSON block
        import re
        
        # Look for JSON in code blocks
        code_block = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if code_block:
            try:
                return json.loads(code_block.group(1))
            except:
                pass
        
        # Try to find raw JSON object
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        # Return empty dict if nothing found
        return {}
    
    def extract_text_from_image(self, base64_image: str) -> Optional[str]:
        """
        Extract text from an image using Vision API.
        Used for OCR on scanned PDF certificates.
        
        Supports:
        - OpenAI: gpt-4o, gpt-4o-mini, gpt-4-vision-preview
        - Groq: llama-3.2-11b-vision-preview, llama-3.2-90b-vision-preview
        
        Args:
            base64_image: Base64 encoded image data
            
        Returns:
            Extracted text or None if failed
        """
        if not self.is_available():
            return None
        
        # Get vision-capable model for the provider
        vision_model = self._get_vision_model()
        if not vision_model:
            print(f"No vision model available for provider: {self.provider}")
            return None
        
        try:
            response = self.client.chat.completions.create(
                model=vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """Analyze this certificate image and extract ALL text content.

## Your Task:
1. Extract every piece of visible text exactly as it appears - names, dates, degree titles, university name, signatures, seals, etc.
2. CRITICALLY: Check for visual quality issues and document damage

## Quality Issues to Look For:
- Text that is crossed out, struck through, or has lines drawn through it
- Text that has been altered, erased, or written over
- Blurry, faded, or low resolution text
- Visible corrections, whiteout, or tampering
- Watermarks or overlays that obscure text
- Any signs of document manipulation

## Output Format (JSON):
Return a JSON object with:
```json
{
  "extracted_text": "all visible text content preserving layout",
  "document_quality": {
    "confidence": 0.0 to 1.0,
    "is_damaged": true or false,
    "issues": ["list of specific issues found"]
  }
}
```

Confidence scoring:
- 1.0: Perfect, clear document with no issues
- 0.7-0.9: Minor issues (slight blur, small marks) but fully readable
- 0.4-0.6: Significant issues affecting some text readability
- 0.0-0.3: Major damage, crossed-out text, or alterations detected

IMPORTANT: If you see ANY text that appears crossed out, struck through, or altered, you MUST report it in issues and set is_damaged to true with low confidence."""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=DEFAULT_MAX_TOKENS,
                temperature=0.1
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Vision API error ({self.provider}/{vision_model}): {e}")
            return None
    
    def _get_vision_model(self) -> Optional[str]:
        """
        Get the vision-capable model for the current provider.
        
        Returns:
            Vision model name from env vars (GROQ_VISION_MODEL or OPENAI_VISION_MODEL)
        """
        return self.vision_model
    
    def supports_vision(self) -> bool:
        """Check if the current provider supports vision API."""
        return self.vision_model is not None
    
    def _mock_response(self, prompt: str) -> str:
        """
        Provide mock responses when LLM is not available.
        Useful for testing without API key.
        """
        prompt_lower = prompt.lower()
        
        # Mock field extraction
        if "extract" in prompt_lower and "certificate" in prompt_lower:
            return json.dumps({
                "candidate_name": "John Smith",
                "university_name": "University of Example",
                "degree_name": "Bachelor of Science in Computer Science",
                "issue_date": "2023-05-15"
            })
        
        # Mock email drafting
        if "draft" in prompt_lower and "email" in prompt_lower:
            return json.dumps({
                "subject": "Verification Request - Certificate Authenticity",
                "body": "Dear Registrar,\n\nI am writing to request verification of a certificate...\n\nBest regards"
            })
        
        # Mock reply analysis
        if "analyze" in prompt_lower and "reply" in prompt_lower:
            return json.dumps({
                "verification_status": "VERIFIED",
                "confidence_score": 0.95,
                "key_phrases": ["confirm", "authentic", "records match"],
                "explanation": "The university confirmed the certificate is authentic."
            })
        
        # Mock university identification
        if "identify" in prompt_lower and "university" in prompt_lower:
            return json.dumps({
                "university_name": "University of Example",
                "confidence": 0.9,
                "reasoning": "Name extracted from certificate header"
            })
        
        # Default mock response
        return json.dumps({"status": "mock_response", "message": "LLM not configured"})


def get_llm_client() -> LLMClient:
    """Factory function to get configured LLM client."""
    return LLMClient()
