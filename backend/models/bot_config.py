# backend/models/bot_config.py
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID # Use UUID for primary key
from sqlalchemy.sql import func # For default timestamps
from backend.db.session import Base # Import Base from session

class BotConfig(Base):
    __tablename__ = "bot_configs"

    # Use UUID for primary key, generated by database or python
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) 
    
    # Assuming a 'users' table exists with a UUID primary key named 'id'
    # If users table doesn't exist yet or uses a different key, adjust/remove ForeignKey
    # user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True) 
    user_id = Column(String, nullable=False, index=True) # Placeholder if no users table/FK yet

    bot_type = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True) # Optional user-defined name
    symbol = Column(String, nullable=False, index=True)
    settings = Column(JSON, nullable=False, default={}) # Store strategy settings as JSON
    is_enabled = Column(Boolean, default=True, nullable=False)
    # api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=True, index=True) # Temporarily removed due to DB issue
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Define relationship if users table model exists (e.g., User)
    # owner = relationship("User", back_populates="bot_configs")

    def __repr__(self):
        return f"<BotConfig(id={self.id}, user='{self.user_id}', type='{self.bot_type}', symbol='{self.symbol}')>"