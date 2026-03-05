# utils/encryption_utils.py
import os
from cryptography.fernet import Fernet, InvalidToken


class EncryptionUtils:
    def __init__(self, key):
        if not key:
            raise ValueError("Encryption key cannot be None or empty")
        if isinstance(key, str):
            key_bytes = key.encode()
        else:
            key_bytes = key
        self.cipher = Fernet(key_bytes)

    def encrypt(self, data):
        """Encrypt string data. Returns a string for database storage."""
        if not data:
            return ""
        if isinstance(data, str):
            data = data.encode()
        encrypted = self.cipher.encrypt(data)
        return encrypted.decode('utf-8')  # Return string for DB storage

    def decrypt(self, encrypted_data):
        """Decrypt data. Logs warning on failure instead of silently passing through."""
        if not encrypted_data:
            return ""
        try:
            if isinstance(encrypted_data, str):
                encrypted_data = encrypted_data.encode()
            return self.cipher.decrypt(encrypted_data).decode()
        except InvalidToken:
            import logging
            logging.getLogger(__name__).warning(
                "Decryption failed for data (length=%d). Data may not be encrypted.",
                len(encrypted_data)
            )
            raw = encrypted_data if isinstance(encrypted_data, str) else encrypted_data.decode(errors='replace')
            return f"[DECRYPTION_FAILED] {raw[:100]}..."
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")

    def migrate_data(self, data):
        """Migrate unencrypted data to encrypted format."""
        try:
            self.decrypt(data)
            return data  # Already encrypted
        except (ValueError, InvalidToken):
            return self.encrypt(data)