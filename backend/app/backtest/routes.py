from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid # Added for UUID conversion
from uuid import UUID
from datetime import datetime
import pandas as pd # For data handling

from backend.db.session import get_db
from backend.app.auth_utils import get_current_user, UserPayload # Corrected import and added UserPayload
from backend import schemas, models
from backend.db import crud_bot_config
from backend.backtesting.engine import run_backtest
# Assuming a utility exists for fetching historical data, e.g., in backend/utils/market_data.py
# Need to confirm the actual location and function name. Let's assume 'fetch_historical_klines' for now.
from backend.utils.binance_client import BinanceAPIClient # Corrected import to use actual class name

router = APIRouter()

@router.post("/{config_id}", response_model=schemas.backtest.BacktestResult, status_code=status.HTTP_200_OK)
async def trigger_backtest(
    config_id: UUID,
    request_data: schemas.backtest.BacktestRequest,
    db: Session = Depends(get_db),
    user_payload: UserPayload = Depends(get_current_user), # Changed dependency to use correct function and type
):
    """
    Triggers a backtest simulation for a specific bot configuration.
    """
    # 1. Retrieve BotConfig
    db_bot_config = crud_bot_config.get_bot_config(db=db, config_id=config_id, user_id=uuid.UUID(user_payload.sub)) # Corrected kwarg and added user_id check
    if db_bot_config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot configuration not found")
    # Compare against the user ID from the JWT payload (subject)
    if db_bot_config.user_id != uuid.UUID(user_payload.sub):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this configuration")

    # 2. Determine symbol and interval from BotConfig
    # Assuming symbol and interval are stored directly or within parameters
    # Adjust based on actual BotConfig model structure
    symbol = db_bot_config.parameters.get("symbol") # Example access
    interval = db_bot_config.parameters.get("interval") # Example access

    if not symbol or not interval:
         raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST,
             detail="Bot configuration is missing required 'symbol' or 'interval' parameters for backtesting."
         )

    # 3. Initialize Binance Client
    # TODO: Handle potential API key requirements if needed for the client
    client = BinanceAPIClient() # Use correct class name

    # 4. Fetch Historical Data
    try:
        print(f"Fetching historical data for {symbol}, interval {interval}, from {request_data.start_date} to {request_data.end_date}")
        # Convert datetime to string format suitable for the API client
        start_str = request_data.start_date.isoformat()
        end_str = request_data.end_date.isoformat()

        # Assuming fetch_historical_klines returns a pandas DataFrame
        # Adjust parameters as needed based on the actual function signature
        # Assuming get_klines returns a pandas DataFrame compatible with the backtesting engine
        historical_data_df: pd.DataFrame = await client.get_klines(
            symbol=symbol,
            interval=interval,
            start_str=start_str, # Use string format
            end_str=end_str      # Use string format
        )
        print(f"Fetched {len(historical_data_df)} klines.")
        if historical_data_df.empty:
             raise HTTPException(
                 status_code=status.HTTP_404_NOT_FOUND,
                 detail=f"No historical data found for {symbol} ({interval}) in the specified date range."
             )

    except Exception as e:
        # Log the error details for debugging
        print(f"Error fetching historical data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch historical data for {symbol}. Error: {str(e)}"
        )

    # 5. Run Backtest
    try:
        print(f"Running backtest engine for config {config_id}...")
        # Ensure BotConfig schema matches what run_backtest expects
        # We might need to convert the DB model (models.BotConfig) to the Pydantic schema (schemas.BotConfig)
        # If crud returns the DB model, convert it. Let's assume crud returns a model compatible with schemas.BotConfig for now.
        # Or, more likely, run_backtest should accept the DB model or we convert here.
        # Let's assume run_backtest can handle the DB model or we adapt it later.
        # For now, pass the DB model directly if its structure is compatible enough.
        # A safer approach is to explicitly convert:
        bot_config_schema = schemas.BotConfig.from_orm(db_bot_config)


        backtest_result: schemas.backtest.BacktestResult = run_backtest(
            bot_config=bot_config_schema, # Pass the Pydantic schema instance
            historical_data=historical_data_df,
            initial_capital=request_data.initial_capital
        )
        print(f"Backtest completed. Result metrics: {backtest_result.metrics}")

    except Exception as e:
        # Log the error details for debugging
        print(f"Error running backtest engine: {e}")
        # Consider more specific error handling based on potential engine errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backtesting simulation failed. Error: {str(e)}"
        )

    # 6. Return Results
    return backtest_result