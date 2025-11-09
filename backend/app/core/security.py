from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from .config import get_settings


class APIKeyEncryptionError(ValueError):
    """Raised when an API key cannot be decrypted."""


def _get_fernet() -> Fernet:
    settings = get_settings()
    return Fernet(settings.derived_encryption_key)


def encrypt_api_key(plain_text: str) -> str:
    """Encrypt a raw API key for persistence."""
    token = _get_fernet().encrypt(plain_text.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_api_key(token: str) -> str:
    """Decrypt a persisted API key token."""
    try:
        decrypted = _get_fernet().decrypt(token.encode("utf-8"))
        return decrypted.decode("utf-8")
    except InvalidToken as exc:  # pragma: no cover - defensive branch
        raise APIKeyEncryptionError("Unable to decrypt provider API key") from exc
