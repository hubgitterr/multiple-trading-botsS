# backend/schemas/api_key.py
from pydantic import BaseModel, Field
from typing import Optional
import uuid
from datetime import datetime

# Base properties (excluding sensitive data)
class ApiKeyBase(BaseModel):
    label: Optional[str] = Field(None, example="My Binance Key")
    api_key_public: str = Field(..., example="vmPUZE6mv9SD5VNHk4HlW56...") # Public key only

# Schema for creating a key (requires secret)
class ApiKeyCreate(ApiKeyBase):
    secret_key: str = Field(..., example="NhqPtmdSJYdKjVHjA7...") # Secret needed only on create

# Schema for reading/returning keys (NO secret)
class ApiKey(ApiKeyBase):
    id: uuid.UUID
    user_id: uuid.UUID # Assuming user_id in DB is UUID
    created_at: datetime

    class Config:
        orm_mode = True