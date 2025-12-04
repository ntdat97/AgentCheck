"""
Application Constants - FALLBACK DEFAULTS

Some values are ONLY used when environment variables are NOT set.
For actual configuration, use .env file (see .env.example).
"""

# ===========================================
# LLM Provider Fallback Defaults
# ===========================================
DEFAULT_PROVIDER = "groq"

# ===========================================
# Groq Configuration (Free - https://console.groq.com/)
# ===========================================
GROQ_API_BASE_URL = "https://api.groq.com/openai/v1"

# Text models - for reasoning, function calling, and general tasks
GROQ_DEFAULT_MODEL = "openai/gpt-oss-120b"

# Vision models - for scanned PDF OCR
GROQ_DEFAULT_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# ===========================================
# OpenAI Configuration (Requires billing - https://platform.openai.com/)
# ===========================================
# Text models - for reasoning, function calling, and general tasks
OPENAI_DEFAULT_MODEL = "gpt-4o-mini"

# Vision models - for scanned PDF OCR
OPENAI_DEFAULT_VISION_MODEL = "gpt-4o-mini"

# ===========================================
# LLM Parameters
# ===========================================
DEFAULT_TEMPERATURE = 0.1
DEFAULT_MAX_RETRIES = 3
DEFAULT_MAX_TOKENS = 2000

# ===========================================
# Confidence Thresholds
# ===========================================
# Used for reply analysis fallback scoring
CONFIDENCE_SCORE_HIGH = 0.9    # LLM available
CONFIDENCE_SCORE_MEDIUM = 0.7  # Fallback keyword match
CONFIDENCE_SCORE_LOW = 0.5     # LLM unavailable or inconclusive
