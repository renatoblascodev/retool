from __future__ import annotations

import unittest

from app.datasources.secrets import decrypt_auth_config, encrypt_auth_config


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


if __name__ == "__main__":
    unittest.main()
