from __future__ import annotations

import unittest

from cryptography.fernet import Fernet, InvalidToken

from app.datasources.secrets import (
    decrypt_auth_config,
    encrypt_auth_config,
    rotate_auth_config,
)


class DataSourceSecretsTests(unittest.TestCase):
    def test_encrypt_and_decrypt_round_trip(self) -> None:
        original = {"token": "top-secret", "region": "us"}
        encrypted = encrypt_auth_config(original)

        self.assertTrue(encrypted.get("_encrypted"))
        self.assertNotEqual(encrypted.get("ciphertext"), "top-secret")

        decrypted = decrypt_auth_config(encrypted)
        self.assertEqual(decrypted, original)

    def test_decrypt_legacy_plaintext_payload(self) -> None:
        legacy = {"username": "dev", "password": "pw"}
        self.assertEqual(decrypt_auth_config(legacy), legacy)


class RotateAuthConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.old_key = Fernet.generate_key().decode("utf-8")
        self.new_key = Fernet.generate_key().decode("utf-8")

    def _encrypt_with(self, payload: dict, key: str) -> dict:
        import base64, json
        from cryptography.fernet import Fernet as F
        raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
        token = F(key.encode()).encrypt(raw.encode()).decode()
        return {"_encrypted": True, "version": 1, "ciphertext": token}

    def _decrypt_with(self, stored: dict, key: str) -> dict:
        import json
        from cryptography.fernet import Fernet as F
        plaintext = F(key.encode()).decrypt(stored["ciphertext"].encode()).decode()
        return json.loads(plaintext)

    def test_rotate_re_encrypts_with_new_key(self) -> None:
        original = {"token": "secret-bearer"}
        stored = self._encrypt_with(original, self.old_key)

        rotated = rotate_auth_config(stored, self.old_key, self.new_key)

        # Must be decryptable with new key.
        decrypted = self._decrypt_with(rotated, self.new_key)
        self.assertEqual(decrypted, original)

    def test_rotate_old_key_cannot_decrypt_new_blob(self) -> None:
        stored = self._encrypt_with({"pw": "x"}, self.old_key)
        rotated = rotate_auth_config(stored, self.old_key, self.new_key)

        with self.assertRaises(InvalidToken):
            Fernet(self.old_key.encode()).decrypt(rotated["ciphertext"].encode())

    def test_rotate_raises_invalid_token_on_wrong_old_key(self) -> None:
        stored = self._encrypt_with({"token": "t"}, self.old_key)
        wrong_key = Fernet.generate_key().decode("utf-8")

        with self.assertRaises(InvalidToken):
            rotate_auth_config(stored, wrong_key, self.new_key)

    def test_rotate_empty_stored_encrypts_with_new_key(self) -> None:
        """Empty auth_config (no credentials) is wrapped and encrypted."""
        rotated = rotate_auth_config({}, self.old_key, self.new_key)

        self.assertTrue(rotated.get("_encrypted"))
        decrypted = self._decrypt_with(rotated, self.new_key)
        self.assertEqual(decrypted, {})

    def test_rotate_plaintext_legacy_record(self) -> None:
        """Plaintext legacy record is re-encrypted with the new key."""
        legacy = {"username": "admin", "password": "pw"}
        rotated = rotate_auth_config(legacy, self.old_key, self.new_key)

        self.assertTrue(rotated.get("_encrypted"))
        decrypted = self._decrypt_with(rotated, self.new_key)
        self.assertEqual(decrypted, legacy)

    def test_rotate_preserves_structure_version(self) -> None:
        stored = self._encrypt_with({"token": "t"}, self.old_key)
        rotated = rotate_auth_config(stored, self.old_key, self.new_key)

        self.assertEqual(rotated.get("version"), 1)
        self.assertIn("ciphertext", rotated)


if __name__ == "__main__":
    unittest.main()

