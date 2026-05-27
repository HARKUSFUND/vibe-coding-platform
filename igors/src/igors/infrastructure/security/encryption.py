"""AES-256-GCM encryption for sensitive fields."""

import base64
import json
import os
from typing import Any, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from loguru import logger

from ...config.settings import get_settings


class AESCipher:
    """AES-256-GCM encryption for sensitive data (NIR, VIH results, etc.)."""

    def __init__(self, key: Optional[bytes] = None):
        settings = get_settings()
        if key is None:
            key = settings.validate_encryption_key()
        
        if len(key) != 32:
            raise ValueError("Encryption key must be exactly 32 bytes for AES-256")
        
        self.key = key
        self.aesgcm = AESGCM(self.key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string using AES-256-GCM.
        Returns base64-encoded ciphertext with nonce prepended.
        """
        if not plaintext:
            return ""

        try:
            # Generate random 12-byte nonce
            nonce = os.urandom(12)
            
            # Encrypt
            ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
            
            # Combine nonce + ciphertext and encode as base64
            encrypted_data = nonce + ciphertext
            return base64.b64encode(encrypted_data).decode("utf-8")
            
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt a base64-encoded ciphertext.
        Returns original plaintext.
        """
        if not encrypted_data:
            return ""

        try:
            # Decode base64
            data = base64.b64decode(encrypted_data)
            
            # Extract nonce (first 12 bytes) and ciphertext
            nonce = data[:12]
            ciphertext = data[12:]
            
            # Decrypt
            plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode("utf-8")
            
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise

    def encrypt_json(self, data: dict) -> str:
        """Encrypt a dictionary as JSON."""
        json_str = json.dumps(data, ensure_ascii=False)
        return self.encrypt(json_str)

    def decrypt_json(self, encrypted_data: str) -> dict:
        """Decrypt to dictionary."""
        json_str = self.decrypt(encrypted_data)
        return json.loads(json_str)

    @staticmethod
    def generate_key() -> str:
        """Generate a new random 32-byte key (for initial setup)."""
        return base64.b64encode(os.urandom(32)).decode("utf-8")


def encrypt_field(value: str) -> str:
    """Standalone function to encrypt a field value."""
    cipher = AESCipher()
    return cipher.encrypt(value)


def decrypt_field(encrypted_value: str) -> str:
    """Standalone function to decrypt a field value."""
    cipher = AESCipher()
    return cipher.decrypt(encrypted_value)
