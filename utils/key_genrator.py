# verify_and_generate_key.py
import base64
import os


def verify_key(key_str):
    """Verify that a base64-encoded key is valid 256-bit."""
    try:
        key_str = key_str.split('#')[0].strip()
        key_bytes = base64.b64decode(key_str)
        if len(key_bytes) == 32:
            return True, "Key is valid 256-bit"
        return False, f"Invalid key length: {len(key_bytes)} bytes (need 32)"
    except Exception as e:
        return False, f"Invalid key format: {str(e)}"


def generate_new_key():
    """Generate a new 256-bit (32 bytes) random key, base64-encoded."""
    key_bytes = os.urandom(32)
    key_b64 = base64.b64encode(key_bytes).decode('utf-8')
    return key_b64


if __name__ == "__main__":
    # Generate a fresh key for use in .env
    new_key = generate_new_key()
    is_valid, message = verify_key(new_key)
    print(f"Generated key status: {message}")
    print("Add this to your .env file:")
    print(f"ENCRYPTION_KEY={new_key}")