# backend/schemas/bot_config.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid
from datetime import datetime

# Base properties shared by all schemas
class BotConfigBase(BaseModel):
    bot_type: str = Field(..., example="MomentumBot")
    name: Optional[str] = Field(None, example="My ETH Momentum Bot")
    symbol: str = Field(..., example="ETHUSDT")
    settings: Dict[str, Any] = Field(default_factory=dict, example={"interval": "1h", "rsi_period": 14})
    is_enabled: bool = True

# Schema for creating a new config (inherits base)
# No ID or user_id needed here, they are set by the backend/DB
class BotConfigCreate(BotConfigBase):
    pass 

# Schema for updating an existing config (all fields optional)
class BotConfigUpdate(BaseModel):
    name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None

# Schema for reading/returning a config (includes DB-generated fields)
# Schema for reading/returning a config (includes DB-generated fields)
class BotConfig(BotConfigBase):
    id: uuid.UUID
    user_id: uuid.UUID # Expect UUID from the database model
    
    model_config = { # Pydantic v2 config
        "from_attributes": True # Enable ORM mode
    }
    created_at: datetime
    updated_at: Optional[datetime] = None

    # class Config: # Removed old Pydantic V1 config
    #     orm_mode = True