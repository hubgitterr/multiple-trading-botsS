# backend/utils/security.py
import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv
from typing import Optional # Added this import

logger = logging.getLogger(__name__)

# Load environment variables from backend/.env
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# --- Fernet Encryption ---
# IMPORTANT: Generate a strong key ONCE and store it securely in .env
# Generate using: Fernet.generate_key().decode()
# Store this key in backend/.env as FERNET_KEY=your_generated_key
FERNET_KEY = os.getenv("FERNET_KEY")

if not FERNET_KEY:
    logger.critical("FERNET_KEY not found in environment variables! API key encryption/decryption will fail.")
    # raise ValueError("FERNET_KEY must be set for encryption.")
    fernet = None
else:
    try:
         # Ensure the key is bytes
        key_bytes = FERNET_KEY.encode()
        fernet = Fernet(key_bytes)
        logger.info("Fernet encryption initialized.")
    except Exception as e:
         logger.exception(f"Failed to initialize Fernet with key: {e}")
         fernet = None

def encrypt_data(data: str) -> Optional[str]:
    """Encrypts string data using Fernet."""
    if not fernet:
        logger.error("Fernet is not initialized. Cannot encrypt data.")
        return None
    if not isinstance(data, str):
         logger.error("Encryption input must be a string.")
         return None # Or raise error
    try:
        encrypted_bytes = fernet.encrypt(data.encode())
        # Return as URL-safe base64 string for easier storage
        return encrypted_bytes.decode()
    except Exception as e:
        logger.exception(f"Encryption failed: {e}")
        return None

def decrypt_data(encrypted_data: str) -> Optional[str]:
    """Decrypts string data using Fernet."""
    if not fernet:
        logger.error("Fernet is not initialized. Cannot decrypt data.")
        return None
    if not isinstance(encrypted_data, str):
         logger.error("Decryption input must be a string.")
         return None
    try:
        # Ensure data is bytes
        encrypted_bytes = encrypted_data.encode()
        decrypted_bytes = fernet.decrypt(encrypted_bytes)
        return decrypted_bytes.decode()
    except Exception as e:
        # Includes InvalidToken if key is wrong or data tampered/invalid
        logger.error(f"Decryption failed (InvalidToken or other error): {e}")
        return None

# --- Example Usage ---
if __name__ == "__main__":
     # Ensure FERNET_KEY is set in a .env file in the parent dir for this test
     logging.basicConfig(level=logging.INFO)
     if not FERNET_KEY:
          print("Please set FERNET_KEY in backend/.env to run this example.")
          print("Generate one using: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'")
     else:
          original_secret = "my_super_secret_api_key_12345"
          print(f"Original: {original_secret}")

          encrypted = encrypt_data(original_secret)
          print(f"Encrypted: {encrypted}")

          if encrypted:
               decrypted = decrypt_data(encrypted)
               print(f"Decrypted: {decrypted}")
               print(f"Match: {original_secret == decrypted}")

          # Test decryption failure
          print("\nTesting invalid token decryption:")
          decrypt_data("invalid_token_string")
          if encrypted:
               decrypt_data(encrypted[:-5] + "abcde") # Tampered token