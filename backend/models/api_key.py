# backend/models/api_key.py
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from backend.db.session import Base
# from sqlalchemy.orm import relationship # If needed

class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Link to the user who owns this key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    label = Column(String, nullable=True) # User-defined label for the key
    api_key_public = Column(String, nullable=False, unique=True) # The public API key itself
    secret_key_encrypted = Column(String, nullable=False) # Store the encrypted secret key

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Define relationship back to User (optional)
    # owner = relationship("User")

    def __repr__(self):
        return f"<ApiKey(id={self.id}, user_id='{self.user_id}', label='{self.label}', public='{self.api_key_public[:5]}...')>"