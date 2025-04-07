# backend/db/crud_user.py
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, Dict, Any
import logging

from backend.models.user import User # Import the User model
# Import Pydantic schemas later if needed
# from backend.schemas import UserCreate 

logger = logging.getLogger(__name__)

def get_user(db: Session, user_id: UUID) -> Optional[User]:
    """Gets a user by their ID (UUID)."""
    logger.debug(f"Fetching user by id={user_id}")
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Gets a user by their email address."""
    logger.debug(f"Fetching user by email={email}")
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user_id: UUID, email: str, extra_data: Optional[Dict[str, Any]] = None) -> User:
    """
    Creates a new user profile entry in the public users table.
    Typically called after successful Supabase signup.
    """
    # **IMPORTANT**: Ensure data is validated before this step
    logger.info(f"Creating user profile for id={user_id}, email={email}")
    
    # Check if user already exists (e.g., if called multiple times)
    db_user = get_user(db, user_id=user_id)
    if db_user:
        logger.warning(f"User profile already exists for id={user_id}. Returning existing user.")
        return db_user

    create_data = {"id": user_id, "email": email}
    if extra_data:
         # Only add keys that are valid columns in the User model
         valid_keys = {key for key in extra_data if hasattr(User, key)}
         create_data.update({key: extra_data[key] for key in valid_keys})
         
    db_user = User(**create_data)
    
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
        logger.info(f"User profile created successfully: id={db_user.id}")
        return db_user
    except Exception as e:
        logger.exception(f"Error creating user profile for id={user_id}: {e}")
        db.rollback() # Rollback transaction on error
        raise # Re-raise the exception to be handled by API layer

def update_user(db: Session, user_id: UUID, update_data: Dict[str, Any]) -> Optional[User]:
    """Updates a user's profile data (e.g., preferences)."""
    logger.info(f"Updating user profile for id={user_id}")
    db_user = get_user(db, user_id=user_id)
    if not db_user:
        logger.warning(f"User id={user_id} not found during update.")
        return None

    update_values = update_data.copy()
    # Only allow updating specific fields (e.g., 'preferences', 'name' if added)
    allowed_keys = {'preferences', 'name'} # Add other updatable fields here
    
    updated = False
    for key, value in update_values.items():
        if key in allowed_keys and hasattr(db_user, key):
            setattr(db_user, key, value)
            updated = True
        else:
            logger.warning(f"Attempted to update disallowed or non-existent field '{key}' on User.")

    if not updated:
         logger.info(f"No valid fields provided for update for user id={user_id}.")
         # Return the user object without committing if no changes were made
         # Or return None/raise error depending on desired behavior
         return db_user

    try:
        db.commit()
        db.refresh(db_user)
        logger.info(f"User profile updated successfully: id={db_user.id}")
        return db_user
    except Exception as e:
        logger.exception(f"Error updating user profile for id={user_id}: {e}")
        db.rollback()
        raise # Re-raise the exception