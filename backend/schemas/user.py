# backend/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
import uuid
from datetime import datetime

# Base properties
class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com")
    # Add other base fields if they exist in your model (e.g., name)
    # name: Optional[str] = None

# Properties received via API on creation (if you have a create endpoint)
# class UserCreate(UserBase):
#    pass # No extra fields needed if ID comes from Supabase Auth

# Properties to return to client (Read schema)
class User(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    # Include preferences if stored directly on the user model
    # preferences: Optional[Dict[str, Any]] = None 

    class Config:
        orm_mode = True # Enable reading data from ORM models
        from_attributes = True # Use from_attributes instead of orm_mode for Pydantic v2

# Schema specifically for user settings (if stored separately or partially)
# This might be more appropriate for the /settings endpoint response
class UserSettings(BaseModel):
     email: EmailStr # Include email for reference
     preferences: Optional[Dict[str, Any]] = Field(None, example={"theme": "dark", "notifications": True})
     # Add other settings fields here
     
     class Config:
         orm_mode = True # If fetching preferences from User model directly
         from_attributes = True # Use from_attributes instead of orm_mode for Pydantic v2