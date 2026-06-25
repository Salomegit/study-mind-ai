# backend/services/input_guard.py

import re
import logging

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────

MAX_QUESTION_LENGTH = 1000  # characters

# Common prompt injection patterns — not foolproof but catches obvious attacks
# Keep this list focused on clear attack patterns, not legitimate academic words
INJECTION_PATTERNS = [
    r"ignore\s+(previous|above|all|prior)\s+instructions?",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+(a\s+)?(different|new|another|unrestricted)",
    r"disregard\s+(your|all|previous|prior)\s+(instructions?|rules?|guidelines?)",
    r"forget\s+(everything|all|your|previous)",
    r"new\s+instructions?\s*:",
    r"system\s*:\s*you",
    r"override\s+(your\s+)?(instructions?|rules?|guidelines?|safety)",
    r"do\s+not\s+follow\s+your",
    r"pretend\s+(you\s+are|to\s+be)",
    r"simulate\s+(being|a\s+different)",
    r"jailbreak",
    r"dan\s+mode",          # "DAN" jailbreak variant
    r"developer\s+mode",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

# Sensitive output patterns to redact from Gemini responses
# Catches accidentally leaked PII in source documents
SENSITIVE_OUTPUT_PATTERNS = [
    # Credit card numbers (basic pattern)
    (re.compile(r'\b(?:\d[ -]?){13,16}\b'), '[REDACTED-CARD]'),
    # Kenya National ID format (7-8 digits)
    (re.compile(r'\bID\s*[:\-]?\s*\d{7,8}\b', re.IGNORECASE), '[REDACTED-ID]'),
    # Email addresses — only redact if they look like real PII in context
    # Commented out by default as emails often appear legitimately in academic docs
    # (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), '[REDACTED-EMAIL]'),
]


# ── Input validation ───────────────────────────────────────────────────────

class InputValidationError(ValueError):
    """Raised when user input fails security validation."""
    pass


def validate_question(question: str) -> str:
    """
    Validate and sanitise a user question before it reaches the LLM.

    Steps:
    1. Strip leading/trailing whitespace
    2. Enforce length limit
    3. Check for obvious injection patterns
    4. Collapse excessive whitespace (makes injection harder to hide)

    Returns the cleaned question string.
    Raises InputValidationError if the question is rejected.

    NOTE: This is defence-in-depth, not a complete solution.
    The primary protection is the structured prompt in prompts.py.
    """
    if not question or not question.strip():
        raise InputValidationError("Question cannot be empty.")

    cleaned = question.strip()

    # Length check — long inputs increase attack surface and token cost
    if len(cleaned) > MAX_QUESTION_LENGTH:
        raise InputValidationError(
            f"Question is too long ({len(cleaned)} characters). "
            f"Maximum is {MAX_QUESTION_LENGTH} characters."
        )

    # Collapse multiple spaces/newlines — obfuscation like "i g n o r e" won't
    # pass but "ignore  previous" might without this
    normalised = re.sub(r'\s+', ' ', cleaned)

    # Injection pattern check
    for pattern in COMPILED_PATTERNS:
        if pattern.search(normalised):
            logger.warning(
                "Potential prompt injection detected in question: %s",
                cleaned[:100]  # log only first 100 chars
            )
            raise InputValidationError(
                "Your question contains patterns that cannot be processed. "
                "Please rephrase and try again."
            )

    return cleaned


def validate_collection_name(name: str) -> str:
    """
    Validate collection name before it reaches ChromaDB.
    Length check on top of the sanitise_collection_name normalisation.
    """
    if not name or not name.strip():
        raise InputValidationError("Subject name cannot be empty.")

    if len(name.strip()) > 200:
        raise InputValidationError("Subject name is too long (max 200 characters).")

    return name.strip()


# ── Output post-processing ─────────────────────────────────────────────────

def sanitise_output(text: str) -> str:
    """
    Scan Gemini's response for sensitive patterns and redact them.
    Defence-in-depth: catches PII that may have been in source documents.
    """
    for pattern, replacement in SENSITIVE_OUTPUT_PATTERNS:
        text = pattern.sub(replacement, text)
    return text