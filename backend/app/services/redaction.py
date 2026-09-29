import re
from typing import Any, List, Pattern, Tuple


class SecretRedactor:
    """Reusable utility for redacting sensitive credentials and tokens in logs & outputs."""

    REDACTION_PATTERNS: List[Tuple[Pattern, str]] = [
        # Authorization header with Bearer: Authorization: Bearer <token>
        (
            re.compile(r"(?i)(authorization\s*:\s*bearer\s+)([^\r\n\s]+)"),
            r"Authorization: Bearer ********",
        ),
        # Authorization header with Basic: Authorization: Basic <token>
        (
            re.compile(r"(?i)(authorization\s*:\s*basic\s+)([^\r\n\s]+)"),
            r"Authorization: Basic ********",
        ),
        # Standalone Bearer token: Bearer <token>
        (
            re.compile(r"(?i)(\bbearer\s+)([a-zA-Z0-9_\-\.]{8,})"),
            r"\1********",
        ),
        # Key-value pairs: password=xxx, passwd=xxx, pwd=xxx, token=xxx, api_key=xxx, secret=xxx, etc.
        (
            re.compile(
                r"(?i)([\"']?(?:password|passwd|pwd|token|api[_-]?key|secret|client[_-]?secret|private[_-]?key|access[_-]?token|refresh[_-]?token)[\"']?\s*[:=]\s*[\"']?)([^\"'\s,;]+)([\"']?)"
            ),
            r"\1********\3",
        ),
        # Private key blocks
        (
            re.compile(
                r"-----BEGIN\s+(?:RSA|OPENSSH|DSA|EC|PGP)?\s*PRIVATE\s+KEY-----[\s\S]*?-----END\s+(?:RSA|OPENSSH|DSA|EC|PGP)?\s*PRIVATE\s+KEY-----"
            ),
            "[REDACTED PRIVATE KEY]",
        ),
    ]

    SENSITIVE_KEY_PATTERNS: List[Pattern] = [
        re.compile(r"(?i)(password|passwd|pwd|token|secret|key|credential|authorization|bearer|cookie|private|jwt)")
    ]

    @classmethod
    def redact(cls, text: str) -> str:
        """Redact sensitive patterns from text."""
        if not text:
            return text

        redacted = text
        for pattern, replacement in cls.REDACTION_PATTERNS:
            redacted = pattern.sub(replacement, redacted)
        return redacted

    @classmethod
    def is_sensitive_key(cls, key: str) -> bool:
        """Check if a dictionary key name suggests sensitive content."""
        if not isinstance(key, str):
            return False
        return any(pattern.search(key) for pattern in cls.SENSITIVE_KEY_PATTERNS)

    @classmethod
    def redact_dict(cls, data: Any) -> Any:
        """Recursively redact sensitive keys and values from dicts/lists for safe metadata storage."""
        if isinstance(data, dict):
            redacted = {}
            for k, v in data.items():
                if cls.is_sensitive_key(str(k)):
                    redacted[k] = "********"
                else:
                    redacted[k] = cls.redact_dict(v)
            return redacted
        elif isinstance(data, list):
            return [cls.redact_dict(item) for item in data]
        elif isinstance(data, str):
            return cls.redact(data)
        return data


secret_redactor = SecretRedactor()
