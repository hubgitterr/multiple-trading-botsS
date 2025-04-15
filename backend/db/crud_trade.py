# backend/db/crud_trade.py
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import UUID
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from backend.models.trade import Trade # Import the model
from backend.db.session import SessionLocal # Import SessionLocal if needed elsewhere or for consistency
# Import schemas later if needed

logger = logging.getLogger(__name__)

def create_trade(db: Session, user_id: str, bot_config_id: UUID, trade_data: Dict[str, Any]) -> Trade:
    """Creates a new trade record in the database."""
    # **IMPORTANT**: Ensure trade_data is validated and contains necessary fields
    retrieved_order_id = trade_data.get('orderId') # Explicitly get the value
    # Removed diagnostic log line

    # Extract data, converting types as needed
    # Assumes trade_data comes directly from parsed Binance order response

    # Get values safely, handling potential None
    price_val = trade_data.get("price")
    quantity_val = trade_data.get("executedQty") # Use executedQty as per base_bot
    quote_quantity_val = trade_data.get("cummulativeQuoteQty") # Use cummulativeQuoteQty as per base_bot
    commission_val = trade_data.get("commission") # May be None if not in fills
    transact_time_val = trade_data.get("transactTime")

    # Process order_id before passing to the model
    order_id_for_db = str(retrieved_order_id) if retrieved_order_id is not None else None # Convert to string OR keep None if it was None

    db_trade = Trade(
        user_id=user_id,
        bot_config_id=bot_config_id,
        symbol=trade_data.get("symbol"),
        order_id=order_id_for_db, # Use the processed value
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
    """Retrieves trades for a user, optionally filtered."""
    query = db.query(Trade).filter(Trade.user_id == user_id)
    if bot_config_id:
        query = query.filter(Trade.bot_config_id == bot_config_id)
    if symbol:
        query = query.filter(Trade.symbol == symbol)
    if start_time:
        query = query.filter(Trade.timestamp >= start_time)
    if end_time:
        query = query.filter(Trade.timestamp <= end_time)

    return query.order_by(Trade.timestamp.desc()).offset(skip).limit(limit).all()

def get_trade_by_order_id(db: Session, order_id: str) -> Optional[Trade]:
    """Retrieves a specific trade by its exchange order ID."""
    return db.query(Trade).filter(Trade.order_id == order_id).first()

# Add other query functions if needed (e.g., get_trade_by_order_id)