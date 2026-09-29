import re
from typing import List, Pattern, Tuple


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

    @classmethod
    def redact(cls, text: str) -> str:
        """Redact sensitive patterns from text."""
        if not text:
            return text

        redacted = text
        for pattern, replacement in cls.REDACTION_PATTERNS:
            redacted = pattern.sub(replacement, redacted)
        return redacted


secret_redactor = SecretRedactor()
