from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

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

class BacktestResult(BaseModel):
    metrics: Dict[str, Any]
    trades: List[Trade]
    equity_curve: List[Dict[str, Any]] # List of {'timestamp': int, 'equity': float}

# --- New schema for the backtest request ---

class BacktestRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    initial_capital: float
    # timeframe: Optional[str] = None # Decided against adding timeframe here, should be derived from BotConfig

    class Config:
        orm_mode = True # Keep or remove based on usage, might not be needed here