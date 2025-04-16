from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

# --- Schemas moved from engine.py for better organization ---

class KLine(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

class Trade(BaseModel):
    entry_timestamp: int
    exit_timestamp: Optional[int] = None
    entry_price: float
    exit_price: Optional[float] = None
    quantity: float
    pnl: Optional[float] = None
    side: str # 'BUY' or 'SELL' for the entry trade, or 'CLOSE' for final mark-to-market
    avg_entry_price: Optional[float] = None # Added for DCA/Grid avg price tracking

# Renamed original BacktestResult to avoid conflict with DB model schema
class BacktestOutput(BaseModel):
    metrics: Dict[str, Any]
    trades: List[Trade]
    equity_curve: List[Dict[str, Any]] # List of {'timestamp': int, 'equity': float}

# --- New schema for the backtest request ---

class BacktestRequest(BaseModel):
    start_date: str # Expecting "YYYY-MM-DD" string from frontend
    end_date: str   # Expecting "YYYY-MM-DD" string from frontend
    interval: str   # e.g., '1h', '4h', '1d'
    initial_capital: float

    # No Config class needed for a simple request body schema unless using ORM features


# --- Schemas for Persistent Backtest Results (Database) ---

class BacktestResultBase(BaseModel):
    # Fields from BacktestRequest (or derived)
    start_date: datetime
    end_date: datetime
    interval: str
    initial_capital: float

    # Fields derived from BacktestOutput metrics
    total_profit: Optional[float] = None
    total_profit_pct: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    win_rate: Optional[float] = None
    total_trades: Optional[int] = None
    # Add other metrics corresponding to the model

    # Optional JSON fields if storing raw output
    # metrics_json: Optional[Dict[str, Any]] = None
    # trades_json: Optional[List[Trade]] = None
    # equity_curve_json: Optional[List[Dict[str, Any]]] = None

class BacktestResultCreate(BacktestResultBase):
    bot_config_id: uuid.UUID
    # Potentially accept the raw metrics dict to populate fields in CRUD
    raw_metrics: Optional[Dict[str, Any]] = Field(None, exclude=True) # Exclude from final schema if only used for creation logic

class BacktestResultDB(BacktestResultBase):
    id: int
    run_timestamp: datetime
    bot_config_id: int
    # Add user_id if implemented in model
    # user_id: int

    class Config:
        orm_mode = True # Pydantic V1 syntax, use from_attributes = True for V2

# Schema for returning results, potentially including related BotConfig info
class BacktestResult(BacktestResultDB):
    # If you want to include bot config details when retrieving results:
    # from .bot_config import BotConfig # Import here to avoid circular dependency issues if needed
    # bot_config: Optional[BotConfig] = None
    pass # Inherits all fields from BacktestResultDB for now


class BacktestResultWithUUID(BacktestResultDB):
    bot_config_id: uuid.UUID

    class Config:
        orm_mode = True