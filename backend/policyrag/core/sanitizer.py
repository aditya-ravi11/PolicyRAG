import logging
import re

logger = logging.getLogger(__name__)

# Patterns that indicate prompt injection attempts
INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"ignore\s+(all\s+)?above\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?prior\s+(instructions|context)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a|an)\s+", re.IGNORECASE),
    re.compile(r"new\s+instructions?:", re.IGNORECASE),
    re.compile(r"system\s*:\s*you\s+are", re.IGNORECASE),
    re.compile(r"<\s*/?system\s*>", re.IGNORECASE),
    re.compile(r"```\s*system", re.IGNORECASE),
    re.compile(r"OVERRIDE\s+(PREVIOUS\s+)?INSTRUCTIONS?", re.IGNORECASE),
    re.compile(r"forget\s+(everything|all)\s+(above|previous)", re.IGNORECASE),
]

# Max query length to prevent resource exhaustion
MAX_QUERY_LENGTH = 2000


class PromptInjectionError(Exception):
    """Raised when a prompt injection attempt is detected."""


def sanitize_query(query: str) -> str:
    """
    Sanitize a user query for basic prompt injection patterns.

    Returns the cleaned query or raises PromptInjectionError.
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")

    query = query.strip()

    if len(query) > MAX_QUERY_LENGTH:
        raise ValueError(f"Query exceeds maximum length of {MAX_QUERY_LENGTH} characters")

    for pattern in INJECTION_PATTERNS:
        if pattern.search(query):
            logger.warning(
                f"Prompt injection attempt detected",
                extra={"stage": "sanitization", "pattern": pattern.pattern},
            )
            raise PromptInjectionError(
                "Your query was flagged as a potential prompt injection. "
                "Please rephrase your question about the SEC filings."
            )

    return query
