# backend/db/crud_trade.py
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from backend.models.trade import Trade # Import the model
# Import schemas later if needed

logger = logging.getLogger(__name__)

def create_trade(db: Session, user_id: str, bot_config_id: UUID, trade_data: Dict[str, Any]) -> Trade:
    """Creates a new trade record in the database."""
    # **IMPORTANT**: Ensure trade_data is validated and contains necessary fields
    logger.info(f"Recording trade for user={user_id}, bot_config={bot_config_id}, order_id={trade_data.get('orderId')}")
    
    # Extract data, converting types as needed
    # Assumes trade_data comes directly from parsed Binance order response
    
    # Get values safely, handling potential None
    price_val = trade_data.get("price")
    quantity_val = trade_data.get("executedQty")
    quote_quantity_val = trade_data.get("cummulativeQuoteQty")
    commission_val = trade_data.get("commission") # May be None if not in fills
    transact_time_val = trade_data.get("transactTime")

    db_trade = Trade(
        user_id=user_id,
        bot_config_id=bot_config_id,
        symbol=trade_data.get("symbol"),
        order_id=str(trade_data.get("orderId")), # Ensure string
        client_order_id=trade_data.get("clientOrderId"),
        side=trade_data.get("side"),
        order_type=trade_data.get("type", "UNKNOWN"), # Add default 'UNKNOWN'
        price=float(price_val) if price_val is not None else 0.0,
        quantity=float(quantity_val) if quantity_val is not None else 0.0,
        quote_quantity=float(quote_quantity_val) if quote_quantity_val is not None else 0.0,
        commission=float(commission_val) if commission_val is not None else 0.0,
        commission_asset=trade_data.get("commissionAsset"),
        timestamp=datetime.fromtimestamp(int(transact_time_val) / 1000) if transact_time_val else datetime.now() # Use variable and ensure int
        # pnl=trade_data.get("pnl") # If calculated elsewhere
    )
    
    # Refinement needed: Parse 'fills' array from Binance order response 
    # to get accurate average price, total commission, and commission asset.
    # Example (conceptual):
    # if 'fills' in trade_data and trade_data['fills']:
    #    total_commission = sum(float(fill.get('commission', 0)) for fill in trade_data['fills'])
    #    commission_asset = trade_data['fills'][0].get('commissionAsset') # Assume same asset for all fills
    #    # Calculate weighted average price from fills if needed
    #    # ...
    #    db_trade.commission = total_commission
    #    db_trade.commission_asset = commission_asset
    #    # db_trade.price = calculated_avg_price

    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    logger.info(f"Trade recorded successfully: id={db_trade.id}")
    return db_trade

def get_trades_by_user(
    db: Session, 
    user_id: str, 
    bot_config_id: Optional[UUID] = None,
    symbol: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[Trade]:
    """Gets trade records for a user, with optional filters."""
    logger.debug(f"Fetching trades for user_id={user_id}, bot_config_id={bot_config_id}, symbol={symbol}")
    query = db.query(Trade).filter(Trade.user_id == user_id)
    
    if bot_config_id:
        query = query.filter(Trade.bot_config_id == bot_config_id)
    if symbol:
        query = query.filter(Trade.symbol == symbol.upper())
    if start_time:
        query = query.filter(Trade.timestamp >= start_time)
    if end_time:
        query = query.filter(Trade.timestamp <= end_time)
        
    return query.order_by(Trade.timestamp.desc()).offset(skip).limit(limit).all()

# Add other query functions if needed (e.g., get_trade_by_order_id)