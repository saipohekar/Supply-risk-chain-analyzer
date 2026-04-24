"""
Configuration management for Supply Chain Risk Analyzer.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root OR parent directory
_here = Path(__file__).parent.parent
load_dotenv(_here / ".env")
load_dotenv(_here.parent / ".env")  # also try parent workspace .env

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
# Back-compat: README/docs may reference GEMINI_API_KEY; runtime uses Groq SDK.
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "") or GEMINI_API_KEY
TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")

# Groq model settings
GROQ_MODEL = "llama-3.3-70b-versatile"

# Tavily search settings
TAVILY_MAX_RESULTS = 8
TAVILY_SEARCH_DEPTH = "advanced"  # "basic" or "advanced"

# Analysis settings
MAX_RISK_FACTORS = 8
MAX_MITIGATION_STRATEGIES = 6

def validate_config() -> tuple[bool, list[str]]:
    """Validate that all required API keys are present."""
    errors = []
    warnings = []
    if not GROQ_API_KEY or "your_" in GROQ_API_KEY:
        errors.append("GROQ_API_KEY (or GEMINI_API_KEY fallback) is not set or is a placeholder.")
    if not TAVILY_API_KEY or "your_" in TAVILY_API_KEY:
        warnings.append("TAVILY_API_KEY not set — will use built-in mock intelligence data.")
    return len(errors) == 0, errors + warnings

