# backend/schemas/backtest.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime, date

# Schema for the backtest request
class BacktestRequest(BaseModel):
    config_id: uuid.UUID = Field(..., description="ID of the Bot Configuration to test")
    start_date: date = Field(..., example="2023-01-01", description="Start date for historical data")
    end_date: date = Field(..., example="2023-12-31", description="End date for historical data")
    initial_capital: float = Field(..., gt=0, example=10000.0, description="Initial capital for simulation")
    commission_percent: float = Field(default=0.1, ge=0, le=10, description="Commission fee per trade in percent")

# Schema for individual trade details in results
class BacktestTrade(BaseModel):
    timestamp: datetime
    order_id: str
    type: str
    side: str
    price: float
    quantity: float
    cost: float
    commission: float
    quote_balance: float
    base_balance: float

# Schema for equity curve points
class EquityPoint(BaseModel):
    timestamp: datetime
    value: float

# Schema for the backtest results response
class BacktestResults(BaseModel):
    start_date: date
    end_date: date
    duration_days: int
    initial_capital: float
    final_portfolio_value: float
    total_return_percent: float
    total_trades: int
    commission_paid: float
    sharpe_ratio: Optional[float] = None # Placeholder
    max_drawdown: Optional[float] = None # Placeholder
    win_rate: Optional[float] = None # Placeholder
    # Limit the number of trades/equity points returned in API response for performance
    trades: List[BacktestTrade] = Field(..., max_items=1000) # Example limit
    equity_curve: List[EquityPoint] = Field(..., max_items=2000) # Example limit

    class Config:
         orm_mode = False # Results are dicts, not ORM models
         # Pydantic v2 uses model_config instead of Config class
         # model_config = { "from_attributes": False }