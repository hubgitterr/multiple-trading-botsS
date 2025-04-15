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
    start_date: str # Expecting "YYYY-MM-DD" string from frontend
    end_date: str   # Expecting "YYYY-MM-DD" string from frontend
    interval: str   # e.g., '1h', '4h', '1d'
    initial_capital: float

    # No Config class needed for a simple request body schema unless using ORM features