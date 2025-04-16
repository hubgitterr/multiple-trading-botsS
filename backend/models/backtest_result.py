# backend/models/backtest_result.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.db.session import Base
from .bot_config import BotConfig # Import BotConfig for relationship
import uuid
from sqlalchemy.dialects.postgresql import UUID # Assuming PostgreSQL

class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True, index=True)
    run_timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    bot_config_id = Column(UUID(as_uuid=True), ForeignKey("bot_configs.id"), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    interval = Column(String, nullable=False)
    initial_capital = Column(Float, nullable=False)

    # Key Metrics (store individually for easier querying/comparison)
    total_profit = Column(Float, nullable=True)
    total_profit_pct = Column(Float, nullable=True) # Percentage profit
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    max_drawdown_pct = Column(Float, nullable=True) # Percentage drawdown
    win_rate = Column(Float, nullable=True) # Percentage (0.0 to 1.0)
    total_trades = Column(Integer, nullable=True)
    # Add other important metrics as needed, e.g.:
    # sortino_ratio = Column(Float, nullable=True)
    # avg_trade_pnl = Column(Float, nullable=True)
    # profit_factor = Column(Float, nullable=True)

    # Store detailed results as JSON if needed (optional, metrics above are preferred for querying)
    # metrics_json = Column(JSON, nullable=True) # The original metrics dict
    # trades_json = Column(JSON, nullable=True) # List of trades
    # equity_curve_json = Column(JSON, nullable=True) # Equity curve data

    # Relationship to BotConfig
    bot_config = relationship("BotConfig") # No back_populates needed if BotConfig doesn't need direct access back

    # Consider adding a user_id ForeignKey if results are user-specific
    # user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # owner = relationship("User")