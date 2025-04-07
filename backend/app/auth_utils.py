# backend/app/auth_utils.py
import os
import jwt # PyJWT library
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer 
from pydantic import BaseModel, ValidationError
from typing import Optional
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.db import crud_user
import uuid
import uuid # Added for UUID conversion

from sqlalchemy.orm import Session # Added for DB session type hinting
from backend.db.session import get_db # Added for DB session dependency
from backend.db import crud_user # Added for user CRUD operations

logger = logging.getLogger(__name__)

# Load Supabase JWT secret from environment variables (backend/.env)
# IMPORTANT: Get this from your Supabase Project Settings > API > JWT Secret
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET") 
if not SUPABASE_JWT_SECRET:
    logger.critical("SUPABASE_JWT_SECRET not found in environment variables! Authentication will fail.")
    # raise ValueError("SUPABASE_JWT_SECRET must be set") # Or handle more gracefully

ALGORITHM = "HS256" 

# OAuth2 scheme to extract the token from the Authorization header
# The tokenUrl is not strictly needed here as we're just verifying, not issuing tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # "token" is a dummy URL

# Pydantic model for the expected user payload within the JWT
class UserPayload(BaseModel):
    sub: str # Subject (user ID)
    email: Optional[str] = None
    # Add other fields present in your Supabase JWT payload if needed (e.g., role, app_metadata)
    # role: Optional[str] = None 
    exp: int # Expiration time

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserPayload: # Added db dependency
    """
    Dependency function to verify the JWT token and return the user payload.
    Raises HTTPException if the token is invalid or expired.
    """
    if not SUPABASE_JWT_SECRET:
         logger.error("Cannot verify token: SUPABASE_JWT_SECRET is not configured.")
         raise HTTPException(
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             detail="Authentication system configuration error.",
         )
         
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the JWT using the Supabase secret
        payload_dict = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=[ALGORITHM],
            # Supabase includes 'aud' (audience), validate it
            options={"verify_aud": True},
            audience="authenticated" # Default Supabase audience for authenticated users
        )
        
        # Validate payload structure using Pydantic
        user_payload = UserPayload(**payload_dict)

        # --- Start: Check and create user profile if missing ---
        try:
            user_uuid = uuid.UUID(user_payload.sub)
        except ValueError:
            logger.error(f"Invalid UUID format for user ID in token: {user_payload.sub}")
            raise credentials_exception # Re-use existing exception for invalid credentials

        try:
            # Check if user exists in our DB
            # Check if user exists in our DB (synchronous call)
            db_user = crud_user.get_user(db=db, user_id=user_uuid)
            if db_user is None:
                logger.info(f"User profile not found for {user_uuid}. Creating one.")
                try:
                    # Create user if they don't exist
                    # Create user if they don't exist (synchronous call)
                    crud_user.create_user(db=db, user_id=user_uuid, email=user_payload.email)
                    logger.info(f"Successfully created user profile for {user_uuid}.")
                except Exception as create_exc: # Catch potential DB errors during creation
                    logger.error(f"Failed to create user profile for {user_uuid}: {create_exc}")
                    # Decide if this should prevent login. Raising might be too strict,
                    # but indicates a problem initializing the user state.
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to initialize user profile during login."
                    )
            else:
                 logger.debug(f"User profile found for {user_uuid}.")

        except Exception as db_exc: # Catch potential DB errors during get_user
            logger.error(f"Database error checking user {user_uuid}: {db_exc}")
            # If we can't check the DB, it's safer to deny login.
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database error during authentication check.",
            )
        # --- End: Check and create user profile ---

        # Check expiration (already handled by jwt.decode by default, but explicit check is fine)
        # if user_payload.exp < datetime.utcnow().timestamp():
        #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")

        logger.debug(f"Token verified successfully for user: {user_payload.sub}")
        return user_payload

    except jwt.ExpiredSignatureError:
        logger.warning("Token verification failed: Expired signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Token has expired"
        )
    except jwt.PyJWTError as e:
        logger.warning(f"Token verification failed: {e}")
        raise credentials_exception # Generic validation error for other JWT issues
    except ValidationError as e:
         logger.warning(f"Token payload validation failed: {e}")
         raise credentials_exception # Payload structure is wrong

# Optional: Dependency to get just the user ID string
async def get_current_user_id(user: UserPayload = Depends(get_current_user)) -> str:
    return user.sub