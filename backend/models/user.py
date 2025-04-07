# backend/models/user.py
import uuid
from sqlalchemy import Column, String, DateTime, JSON # Add JSON if storing preferences here
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship # If defining relationships
from backend.db.session import Base

class User(Base):
    __tablename__ = "users"

    # Use the Supabase Auth user ID as the primary key
    id = Column(UUID(as_uuid=True), primary_key=True, index=True) 
    
    email = Column(String, unique=True, index=True, nullable=False)
    # Add other user profile fields if needed, e.g.:
    # name = Column(String, nullable=True)
    # preferences = Column(JSON, nullable=True) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) # Auto-updates on modification

    # Define relationship to BotConfig (optional but recommended)
    # Assumes BotConfig model has a 'user_id' ForeignKey and 'owner' relationship defined
    # bot_configs = relationship("BotConfig", back_populates="owner") 

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"