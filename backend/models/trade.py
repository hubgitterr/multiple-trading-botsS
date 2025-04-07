# backend/models/trade.py
import uuid
from sqlalchemy import Column, String, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from backend.db.session import Base

class Trade(Base):
    __tablename__ = "trades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to link back to the specific bot configuration
    bot_config_id = Column(UUID(as_uuid=True), ForeignKey("bot_configs.id"), nullable=False, index=True)
    
    # Store user_id denormalized here for easier querying, or rely on join via bot_config
    user_id = Column(String, nullable=False, index=True) # Match user_id type in bot_configs

    symbol = Column(String, nullable=False, index=True)
    order_id = Column(String, unique=True, nullable=False, index=True) # Exchange's order ID
    client_order_id = Column(String, nullable=True, index=True) # Optional client order ID from exchange response
    
    side = Column(String, nullable=False) # 'BUY' or 'SELL'
    order_type = Column(String, nullable=False) # 'MARKET', 'LIMIT', etc.
    
    price = Column(Float, nullable=False) # Execution price per unit
    quantity = Column(Float, nullable=False) # Executed quantity in base asset
    quote_quantity = Column(Float, nullable=False) # Executed quantity in quote asset (cost/proceeds before commission)
    
    commission = Column(Float, nullable=True)
    commission_asset = Column(String, nullable=True)
    
    # Timestamp from the exchange execution time if available, otherwise record time
    timestamp = Column(DateTime(timezone=True), nullable=False, default=func.now()) 

    # Optional: Add PnL if calculated at time of trade (e.g., for closing trades)
    # pnl = Column(Float, nullable=True)

    # Define relationship back to BotConfig (optional)
    # bot_config = relationship("BotConfig") # Add back_populates if needed

    def __repr__(self):
        return f"<Trade(id={self.id}, order_id='{self.order_id}', symbol='{self.symbol}', side='{self.side}')>"