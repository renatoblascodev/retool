from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


def _resolve_fernet_key() -> bytes:
    if settings.datasource_encryption_key:
        return settings.datasource_encryption_key.encode("utf-8")

    # Stable development fallback derived from JWT secret.
    digest = hashlib.sha256(settings.jwt_secret_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _fernet() -> Fernet:
    return Fernet(_resolve_fernet_key())


def _fernet_for_key(raw_key: str) -> Fernet:
    """Return a Fernet instance for an explicit raw key string."""
    return Fernet(raw_key.encode("utf-8"))


def encrypt_auth_config(auth_config: dict[str, Any] | None) -> dict[str, Any]:
    if not auth_config:
        return {}

    raw = json.dumps(auth_config, separators=(",", ":"), ensure_ascii=True)
    token = _fernet().encrypt(raw.encode("utf-8")).decode("utf-8")
    return {
        "_encrypted": True,
        "version": 1,
        "ciphertext": token,
    }


def decrypt_auth_config(stored: dict[str, Any] | None) -> dict[str, Any]:
    if not stored:
        return {}

    if not stored.get("_encrypted"):
        # Backward compatibility with plaintext records.
        return dict(stored)

    ciphertext = stored.get("ciphertext")
    if not isinstance(ciphertext, str) or not ciphertext:
        return {}

    try:
        decoded = _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return {}

    try:
        payload = json.loads(decoded)
    except json.JSONDecodeError:
        return {}

    if not isinstance(payload, dict):
        return {}
    return payload


def rotate_auth_config(
    stored: dict[str, Any] | None,
    old_key: str,
    new_key: str,
) -> dict[str, Any]:
    """Re-encrypt *stored* auth_config from *old_key* to *new_key*.

    Returns the new encrypted blob.  Raises ``InvalidToken`` if *stored*
    cannot be decrypted with *old_key*.
    """
    if not stored or not stored.get("_encrypted"):
        # Plaintext or empty record — encrypt with new key preserving content.
        raw = stored if isinstance(stored, dict) else {}
        raw_json = json.dumps(raw, separators=(",", ":"), ensure_ascii=True)
        token = _fernet_for_key(new_key).encrypt(raw_json.encode("utf-8")).decode("utf-8")
        return {"_encrypted": True, "version": 1, "ciphertext": token}

    ciphertext = stored.get("ciphertext")
    if not isinstance(ciphertext, str) or not ciphertext:
        raise ValueError("Stored auth_config has no ciphertext")

    # Decrypt with old key (raises InvalidToken on failure).
    plaintext = _fernet_for_key(old_key).decrypt(ciphertext.encode("utf-8"))

    # Re-encrypt with new key.
    new_token = _fernet_for_key(new_key).encrypt(plaintext).decode("utf-8")
    return {"_encrypted": True, "version": 1, "ciphertext": new_token}

