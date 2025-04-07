from fastapi import APIRouter, HTTPException, Depends, Body, Response # Added Response
from pydantic import BaseModel, Field # Keep BaseModel for now, might remove later if unused
from typing import Optional, Dict, List
import logging
import uuid
from sqlalchemy.orm import Session
from backend.app.auth_utils import get_current_user, UserPayload
from backend.db.session import get_db
from backend.db import crud_user, crud_api_key # Added crud_api_key
from backend.schemas import user as schemas_user # Renamed alias
from backend.schemas import api_key as schemas_api_key # Added api_key schemas import

# Removed TODOs as auth is being added
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter(
    prefix="/user",     # Prefix for all routes in this router
    tags=["user"],      # Tag for OpenAPI documentation
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)] # Added authentication dependency
)

# --- Pydantic Models for Request/Response ---
# UserSettings is imported from backend.schemas.user
# ApiKey schemas are imported from backend.schemas.api_key
# --- API Endpoints ---

@router.get("/settings", response_model=schemas_user.UserSettings, summary="Get User Settings")
async def get_user_settings(
    db: Session = Depends(get_db), # Added DB dependency
    current_user: UserPayload = Depends(get_current_user)
):
    """
    Retrieves the current authenticated user's settings and preferences
    from the database. If no profile exists yet, returns default settings.
    Requires authentication.
    """
    user_id_str = current_user.sub
    logging.info(f"Attempting to fetch settings for user ID string: {user_id_str}")

    try:
        user_uuid = uuid.UUID(user_id_str)
        logging.info(f"Converted user ID string to UUID: {user_uuid}")
    except ValueError:
        logging.error(f"Invalid user ID format in JWT: {user_id_str}")
        raise HTTPException(status_code=400, detail="Invalid user ID format.")

    db_user = crud_user.get_user(db=db, user_id=user_uuid)

    if db_user:
        logging.info(f"Found user profile in DB for user: {user_uuid}")
        # Assuming preferences are stored on the user model directly
        # If preferences are stored elsewhere, adjust this logic
        user_prefs = getattr(db_user, 'preferences', {}) # Safely get preferences or default to empty dict
        if not isinstance(user_prefs, dict): # Ensure it's a dict
             logging.warning(f"User preferences for {user_uuid} are not a dict: {type(user_prefs)}. Resetting.")
             user_prefs = {}
        return schemas_user.UserSettings(email=db_user.email, preferences=user_prefs)
    else:
        logging.warning(f"No user profile found in DB for user ID: {user_uuid}. Returning default settings.")
        # Return default settings using email from JWT
        return schemas_user.UserSettings(email=current_user.email, preferences={})

@router.put("/settings", response_model=schemas_user.UserSettings, summary="Update User Settings")
async def update_user_settings(
    settings_data: schemas_user.UserSettings, # Use imported schema
    db: Session = Depends(get_db),       # Added DB dependency
    current_user: UserPayload = Depends(get_current_user)
):
    """
    Updates the current authenticated user's settings and preferences (e.g., preferences).
    Requires authentication.
    """
    user_id_str = current_user.sub
    logging.info(f"Attempting to update settings for user ID string: {user_id_str}")

    try:
        user_uuid = uuid.UUID(user_id_str)
        logging.info(f"Converted user ID string to UUID for update: {user_uuid}")
    except ValueError:
        logging.error(f"Invalid user ID format in JWT during update: {user_id_str}")
        raise HTTPException(status_code=400, detail="Invalid user ID format.")

    # Prepare data for update - only allow 'preferences' for now
    update_data = {"preferences": settings_data.preferences}
    logging.info(f"Prepared update data for user {user_uuid}: {update_data}")

    # Call the CRUD function to update the user
    updated_user = crud_user.update_user(db=db, user_id=user_uuid, update_data=update_data)

    if updated_user is None:
        logging.warning(f"User not found during settings update attempt for ID: {user_uuid}")
        raise HTTPException(status_code=404, detail="User not found")

    logging.info(f"Successfully updated settings for user: {user_uuid}")
    
    # Construct the response model from the updated user data
    # Ensure preferences are handled correctly if they might be None or not a dict
    user_prefs = getattr(updated_user, 'preferences', {})
    if not isinstance(user_prefs, dict):
         logging.warning(f"User preferences for {user_uuid} after update are not a dict: {type(user_prefs)}. Resetting in response.")
         user_prefs = {}
         
    return schemas_user.UserSettings(email=updated_user.email, preferences=user_prefs)


@router.get("/api-keys", response_model=List[schemas_api_key.ApiKey], summary="Get User API Keys")
async def get_user_api_keys(
    db: Session = Depends(get_db),
    current_user: UserPayload = Depends(get_current_user)
):
    """
    Retrieves the list of API keys associated with the user's account.
    Secret keys are NOT returned for security.
    Requires authentication.
    """
    user_id_str = current_user.sub
    logging.info(f"Fetching API keys for user ID string: {user_id_str}")

    try:
        user_uuid = uuid.UUID(user_id_str)
        logging.info(f"Converted user ID string to UUID: {user_uuid}")
    except ValueError:
        logging.error(f"Invalid user ID format in JWT: {user_id_str}")
        raise HTTPException(status_code=400, detail="Invalid user ID format.")

    db_api_keys = crud_api_key.get_api_keys_by_user(db=db, user_id=user_uuid)
    logging.info(f"Found {len(db_api_keys)} API keys for user {user_uuid}")
    return db_api_keys

@router.post("/api-keys", response_model=schemas_api_key.ApiKey, status_code=201, summary="Add API Key")
async def add_user_api_key(
    api_key_data: schemas_api_key.ApiKeyCreate,
    db: Session = Depends(get_db),
    current_user: UserPayload = Depends(get_current_user)
):
    """
    Adds a new API key to the user's account.
    The secret key is required but will be stored securely (encrypted) and not returned.
    Requires authentication.
    """
    user_id_str = current_user.sub
    logging.info(f"Attempting to add API key for user ID string: {user_id_str}, Label: {api_key_data.label}")

    try:
        user_uuid = uuid.UUID(user_id_str)
        logging.info(f"Converted user ID string to UUID: {user_uuid}")
    except ValueError:
        logging.error(f"Invalid user ID format in JWT: {user_id_str}")
        raise HTTPException(status_code=400, detail="Invalid user ID format.")

    # Call the CRUD function to create the API key
    db_api_key = crud_api_key.create_api_key(
        db=db,
        user_id=user_uuid,
        label=api_key_data.label,
        api_key_public=api_key_data.api_key_public,
        secret_key=api_key_data.secret_key
    )

    if db_api_key is None:
        logging.error(f"Failed to store API key for user {user_uuid}. Encryption might be misconfigured.")
        raise HTTPException(status_code=400, detail="Failed to store API key. Check encryption setup.")

    logging.info(f"Successfully added API key ID {db_api_key.id} for user {user_uuid}")
    # Pydantic response_model handles serialization (excluding secret_key)
    return db_api_key

@router.delete("/api-keys/{api_key_public}", status_code=204, summary="Delete API Key")
async def delete_user_api_key(
    api_key_public: str,
    db: Session = Depends(get_db),
    current_user: UserPayload = Depends(get_current_user)
):
    """
    Deletes a specific API key associated with the user's account, identified by its public key.
    Requires authentication.
    """
    user_id_str = current_user.sub
    logging.info(f"Attempting to delete API key {api_key_public} for user ID string: {user_id_str}")

    try:
        user_uuid = uuid.UUID(user_id_str)
        logging.info(f"Converted user ID string to UUID: {user_uuid}")
    except ValueError:
        logging.error(f"Invalid user ID format in JWT: {user_id_str}")
        raise HTTPException(status_code=400, detail="Invalid user ID format.")

    # Call the CRUD function to delete the API key
    deleted = crud_api_key.delete_api_key(
        db=db,
        user_id=user_uuid,
        api_key_public=api_key_public
    )

    if not deleted:
        logging.warning(f"API key {api_key_public} not found or deletion failed for user {user_uuid}")
        raise HTTPException(status_code=404, detail="API key not found or deletion failed")

    logging.info(f"Successfully deleted API key {api_key_public} for user {user_uuid}")
    # Return No Content response
    return Response(status_code=204)