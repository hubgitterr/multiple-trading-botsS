# backend/db/crud_backtest_result.py
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.backtest_result import BacktestResult
from ..schemas.backtest import BacktestResultCreate # Assuming an Update schema might be needed later

def _populate_metrics(db_obj: BacktestResult, metrics: Dict[str, Any]):
    """Helper to populate individual metric fields from a dictionary."""
    db_obj.total_profit = metrics.get("Total Profit")
    db_obj.total_profit_pct = metrics.get("Total Profit (%)")
    db_obj.sharpe_ratio = metrics.get("Sharpe Ratio")
    db_obj.max_drawdown = metrics.get("Max Drawdown")
    db_obj.max_drawdown_pct = metrics.get("Max Drawdown (%)")
    db_obj.win_rate = metrics.get("Win Rate (%)", 0) / 100.0 if metrics.get("Win Rate (%)") is not None else None # Assuming Win Rate is percentage
    db_obj.total_trades = metrics.get("Total Trades")
    # Add assignments for other metrics defined in the model
    # db_obj.sortino_ratio = metrics.get("Sortino Ratio")
    # ... etc.

def create_backtest_result(db: Session, *, result_in: BacktestResultCreate) -> BacktestResult:
    """
    Creates a new backtest result record in the database.
    """
    # Create the DB model instance excluding the raw_metrics if present
    db_obj_data = result_in.dict(exclude={"raw_metrics"})
    db_obj = BacktestResult(**db_obj_data)

    # Populate individual metric fields from the raw_metrics dict if provided
    if result_in.raw_metrics:
        _populate_metrics(db_obj, result_in.raw_metrics)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_backtest_result(db: Session, result_id: int) -> Optional[BacktestResult]:
    """
    Retrieves a single backtest result by its ID.
    """
    return db.query(BacktestResult).filter(BacktestResult.id == result_id).first()

def get_backtest_results(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
    bot_config_id: Optional[int] = None,
    # user_id: Optional[int] = None # Add if user association is implemented
) -> List[BacktestResult]:
    """
    Retrieves a list of backtest results, with optional filtering and pagination.
    """
    query = db.query(BacktestResult)
    if bot_config_id is not None:
        query = query.filter(BacktestResult.bot_config_id == bot_config_id)
    # if user_id is not None:
    #     query = query.filter(BacktestResult.user_id == user_id)

    results = query.order_by(BacktestResult.run_timestamp.desc()).offset(skip).limit(limit).all()
    return results

# Optional: Add update and delete functions if needed later
# def update_backtest_result(db: Session, *, db_obj: BacktestResult, obj_in: BacktestResultUpdate) -> BacktestResult:
#     ...
#
# def remove_backtest_result(db: Session, *, result_id: int) -> BacktestResult:
#     ...