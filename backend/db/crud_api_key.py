# backend/db/crud_api_key.py
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import UUID
from typing import List, Optional
import logging

from backend.models.api_key import ApiKey # Import the model
from backend.utils.security import encrypt_data, decrypt_data # Import encryption utils

logger = logging.getLogger(__name__)

def create_api_key(db: Session, user_id: UUID, label: Optional[str], api_key_public: str, secret_key: str) -> Optional[ApiKey]:
    """Creates and stores a new API key, encrypting the secret."""
    logger.info(f"Storing API key for user={user_id}, label={label}")

    # Encrypt the secret key
    encrypted_secret = encrypt_data(secret_key)
    if not encrypted_secret:
        logger.error("Failed to encrypt secret key. Cannot store API key.")
        return None # Or raise an exception

    db_api_key = ApiKey(
        user_id=user_id,
        label=label,
        api_key_public=api_key_public,
        secret_key_encrypted=encrypted_secret
    )
    db.add(db_api_key)
    try:
        db.commit()
        db.refresh(db_api_key)
        logger.info(f"API key stored successfully: id={db_api_key.id}")
        return db_api_key
    except Exception as e:
        # Handle potential unique constraint violation on api_key_public
        logger.exception(f"Error storing API key for user={user_id}: {e}")
        db.rollback()
        raise # Re-raise

def get_api_keys_by_user(db: Session, user_id: UUID) -> List[ApiKey]:
    """Gets all API keys for a user (excluding encrypted secrets)."""
    logger.debug(f"Fetching API keys for user_id={user_id}")
    # Intentionally does not load secret_key_encrypted by default if using deferred loading,
    # but explicitly excluding it in a schema is safer for API responses.
    return db.query(ApiKey).filter(ApiKey.user_id == user_id).all()

def get_api_key_by_public_key(db: Session, user_id: UUID, api_key_public: str) -> Optional[ApiKey]:
    """Gets a specific API key by its public part, ensuring user ownership."""
    logger.debug(f"Fetching API key for user_id={user_id}, public_key={api_key_public[:5]}...")
    return db.query(ApiKey).filter(ApiKey.user_id == user_id, ApiKey.api_key_public == api_key_public).first()

def get_decrypted_secret_key(db: Session, user_id: UUID, api_key_public: str) -> Optional[str]:
    """
    Retrieves and decrypts the secret key for a specific API key.
    USE WITH CAUTION - only for internal backend processes like bot initialization.
    """
    logger.warning(f"Attempting to retrieve DECRYPTED secret key for user={user_id}, public_key={api_key_public[:5]}...")
    db_api_key = get_api_key_by_public_key(db, user_id=user_id, api_key_public=api_key_public)

    if not db_api_key:
        logger.error("API key not found for decryption.")
        return None

    decrypted_secret = decrypt_data(db_api_key.secret_key_encrypted)
    if not decrypted_secret:
         logger.error(f"Failed to decrypt secret key for api_key_id={db_api_key.id}")
         # This could indicate a wrong FERNET_KEY or corrupted data
         return None

    logger.info(f"Secret key decrypted successfully for api_key_id={db_api_key.id}")
    return decrypted_secret

def delete_api_key(db: Session, user_id: UUID, api_key_public: str) -> bool:
    """Deletes an API key record."""
    logger.info(f"Deleting API key for user={user_id}, public_key={api_key_public[:5]}...")
    db_api_key = get_api_key_by_public_key(db, user_id=user_id, api_key_public=api_key_public)
    if not db_api_key:
        logger.warning("API key not found for deletion.")
        return False

    db.delete(db_api_key)
    db.commit()
    logger.info(f"API key deleted successfully: id={db_api_key.id}")
    return True