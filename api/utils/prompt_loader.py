"""
Prompt Loader Utility
Loads and renders Jinja2 prompt templates.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False


class PromptLoader:
    """
    Loads prompt templates from files and renders them with variables.
    Uses Jinja2 for template rendering.
    """
    
    def __init__(self, prompts_dir: Optional[str] = None):
        """
        Initialize prompt loader.
        
        Args:
            prompts_dir: Directory containing prompt templates
        """
        if prompts_dir:
            self.prompts_dir = Path(prompts_dir)
        else:
            # Default to config/prompts relative to project root
            self.prompts_dir = Path(__file__).parent.parent.parent / "config" / "prompts"
        
        self._cache: Dict[str, str] = {}
        
        if JINJA2_AVAILABLE and self.prompts_dir.exists():
            self.env = Environment(
                loader=FileSystemLoader(str(self.prompts_dir)),
                autoescape=select_autoescape(['html', 'xml']),
                trim_blocks=True,
                lstrip_blocks=True
            )
        else:
            self.env = None
    
    def load_template(self, template_name: str) -> str:
        """
        Load a template file content.
        
        Args:
            template_name: Name of template file (with or without .j2 extension)
            
        Returns:
            Template content as string
        """
        if not template_name.endswith('.j2'):
            template_name = f"{template_name}.j2"
        
        # Check cache
        if template_name in self._cache:
            return self._cache[template_name]
        
        template_path = self.prompts_dir / template_name
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self._cache[template_name] = content
        return content
    
    def render(self, template_name: str, **variables) -> str:
        """
        Render a template with provided variables.
        
        Args:
            template_name: Name of template file
            **variables: Variables to substitute in template
            
        Returns:
            Rendered template string
        """
        if not template_name.endswith('.j2'):
            template_name = f"{template_name}.j2"
        
        if self.env:
            template = self.env.get_template(template_name)
            return template.render(**variables)
        else:
            # Fallback: simple string replacement
            content = self.load_template(template_name)
            for key, value in variables.items():
                content = content.replace(f"{{{{ {key} }}}}", str(value))
            return content
    
    def list_templates(self) -> list:
        """List available prompt templates."""
        if not self.prompts_dir.exists():
            return []
        
        return [f.name for f in self.prompts_dir.glob("*.j2")]


# Pre-defined prompt templates as fallback
FALLBACK_PROMPTS = {
    "extract_fields": """
Extract the following fields from the certificate text:
- candidate_name: Full name of the person
- university_name: Name of the issuing institution
- degree_name: Name of the degree/qualification
- issue_date: Date issued (YYYY-MM-DD format)

Certificate Text:
{certificate_text}

Return as JSON with those exact keys. Use null for missing fields.
""",
    "draft_email": """
Draft a professional verification email for:
- Candidate: {candidate_name}
- Degree: {degree_name}
- University: {university_name}
- Reference: {reference_id}

Return JSON with "subject" and "body" keys.
""",
    "analyze_reply": """
Analyze this university verification reply:

{reply_text}

Determine:
1. verification_status: VERIFIED, NOT_VERIFIED, or INCONCLUSIVE
2. confidence_score: 0.0-1.0
3. key_phrases: Important phrases from reply
4. explanation: Why you reached this conclusion

Return as JSON.
""",
    "identify_university": """
From this certificate text, identify the issuing university:

{extracted_text}

Return JSON with:
- university_name: Official name
- confidence: 0.0-1.0
- reasoning: Why you identified this
"""
}


def get_prompt_loader() -> PromptLoader:
    """Factory function to get prompt loader."""
    return PromptLoader()
