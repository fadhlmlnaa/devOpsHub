import base64
import logging
from typing import Optional
from cryptography.fernet import Fernet
from app.core.config import settings

logger = logging.getLogger(__name__)


class SecretEncryptionService:
    """Service to encrypt and decrypt sensitive credentials (passwords, private keys)

    at rest using Fernet symmetric encryption.
    """

    def __init__(self, key: Optional[str] = None):
        raw_key = key or settings.CREDENTIAL_ENCRYPTION_KEY
        # Ensure key is 32-byte urlsafe base64
        try:
            self._fernet = Fernet(raw_key.encode() if isinstance(raw_key, str) else raw_key)
        except Exception:
            # Fallback for padded 32-byte key
            padded_key = base64.urlsafe_b64encode(raw_key.encode().ljust(32, b"0")[:32])
            self._fernet = Fernet(padded_key)

    def encrypt(self, plain_text: Optional[str]) -> Optional[str]:
        """Encrypts a plaintext secret. Returns URL-safe base64 string or None."""
        if plain_text is None or plain_text == "":
            return None
        return self._fernet.encrypt(plain_text.encode("utf-8")).decode("utf-8")

    def decrypt(self, cipher_text: Optional[str]) -> Optional[str]:
        """Decrypts a ciphertext secret back to plaintext. Returns None if input is None."""
        if cipher_text is None or cipher_text == "":
            return None
        try:
            return self._fernet.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
        except Exception as e:
            logger.error("Failed to decrypt secret credential: %s", type(e).__name__)
            raise ValueError("Failed to decrypt credential secret.") from e


# Singleton instance
secret_encryption_service = SecretEncryptionService()
