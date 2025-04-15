from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid # Added for UUID conversion
from uuid import UUID
from datetime import datetime
import pandas as pd # For data handling

import logging # Add logging import
from backend.db.session import get_db
from backend.app.auth_utils import get_current_user, UserPayload # Corrected import and added UserPayload
from backend import models # Keep models import
from backend.schemas.bot_config import BotConfig # Import BotConfig specifically
from backend.schemas.backtest import BacktestRequest, BacktestResult # Import other needed schemas
from backend.db import crud_bot_config
from backend.backtesting.engine import run_backtest
# Assuming a utility exists for fetching historical data, e.g., in backend/utils/market_data.py
# Need to confirm the actual location and function name. Let's assume 'fetch_historical_klines' for now.
from backend.utils.binance_client import BinanceAPIClient # Corrected import to use actual class name

router = APIRouter()

@router.post("/{config_id}", response_model=BacktestResult, status_code=status.HTTP_200_OK) # Use imported BacktestResult
async def trigger_backtest(
    config_id: UUID,
    backtest_params: BacktestRequest, # Use imported BacktestRequest and rename for clarity
    db: Session = Depends(get_db),
    user_payload: UserPayload = Depends(get_current_user), # Changed dependency to use correct function and type
):
    """
    Triggers a backtest simulation for a specific bot configuration.
    """
    client = None # Initialize client to None outside try block
    try:
        # 1. Retrieve BotConfig
        db_bot_config = crud_bot_config.get_bot_config(db=db, config_id=config_id, user_id=uuid.UUID(user_payload.sub)) # Corrected kwarg and added user_id check
        if db_bot_config is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot configuration not found")
        # Compare against the user ID from the JWT payload (subject)
        if db_bot_config.user_id != uuid.UUID(user_payload.sub):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to access this configuration")

        # 2. Extract symbol from BotConfig and interval from request
        symbol = db_bot_config.symbol # Access symbol directly
        interval = backtest_params.interval # Interval now comes from the request body

        # Validate that symbol exists in the config
        if not symbol:
             raise HTTPException(
                 status_code=status.HTTP_400_BAD_REQUEST,
                 detail="Bot configuration is missing the required 'symbol' parameter."
             )

        # 3. Initialize Binance Client
        # TODO: Handle potential API key requirements if needed for the client
        client = BinanceAPIClient() # Use correct class name
        await client.initialize() # Initialize the async client
        if not client.client: # Check if initialization was successful
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to initialize connection to Binance API. Check API keys and connectivity."
            )
        # 4. Fetch Historical Data
        try:
            print(f"Fetching historical data for {symbol}, interval {interval}, from {backtest_params.start_date} to {backtest_params.end_date}")
            # Parse date strings ("YYYY-MM-DD") to datetime objects
            start_dt = datetime.strptime(backtest_params.start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(backtest_params.end_date, "%Y-%m-%d")
            # Convert datetime objects to milliseconds timestamp strings for Binance API
            start_ms = int(start_dt.timestamp() * 1000)
            end_ms = int(end_dt.timestamp() * 1000)
            start_str = str(start_ms)
            end_str = str(end_ms)

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
            bot_config_schema = BotConfig.from_orm(db_bot_config) # Use imported BotConfig directly


            # Pass parameters explicitly to run_backtest
            # Note: run_backtest function signature might need updating
            # Note: run_backtest function signature might need updating
            backtest_result: BacktestResult = run_backtest(
                symbol=bot_config_schema.symbol,
                bot_type=bot_config_schema.bot_type, # Pass bot_type
                name=bot_config_schema.name,         # Pass name for logging/context
                settings=bot_config_schema.settings, # Pass the settings dict
                interval=backtest_params.interval,
                start_date=backtest_params.start_date, # Pass original string dates if needed by engine/metrics
                end_date=backtest_params.end_date,     # Pass original string dates if needed by engine/metrics
                historical_data=historical_data_df,
                initial_capital=backtest_params.initial_capital
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
    finally:
        # Ensure the client connection is closed if the client was initialized
        if client and client.client:
            logging.info("Closing Binance client connection for backtest request.")
            await client.close_connection()
            logging.info("Binance client connection for backtest request closed.")