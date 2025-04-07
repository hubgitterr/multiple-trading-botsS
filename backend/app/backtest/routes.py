# backend/app/backtest/routes.py
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime # Added missing import

# Dependencies and Utils
from backend.db.session import get_db
from backend.app.auth_utils import get_current_user, UserPayload
from backend.db import crud_bot_config, crud_api_key # Need crud for bot config and potentially keys
from backend.utils.historical import fetch_historical_data
from backend.utils.backtest import BacktestEngine
from backend.utils.binance_client import BinanceAPIClient # Needed for historical fetch
from backend.schemas import backtest as schemas_backtest # Import backtest schemas

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/backtest",
    tags=["backtest"],
    dependencies=[Depends(get_current_user)], # Protect backtesting endpoint
    responses={404: {"description": "Not found"}},
)

# --- Helper to get Binance client instance (potentially shared) ---
# Reuse or adapt the one from market/order routes if suitable
# For simplicity, create a new one here for the backtest context
# In a real app, manage client instances more carefully (e.g., lifespan events)
async def get_backtest_binance_client(
     user_id: uuid.UUID, # Pass user ID to fetch correct keys
     db: Session = Depends(get_db)
) -> BinanceAPIClient:
     # TODO: Implement logic to fetch the *correct* API key for the user
     # (e.g., a default one, or one specified in bot config?)
     # For now, we assume keys are in .env or use a placeholder/mock client

     # Placeholder: Fetch first key for user (replace with proper logic)
     api_keys = crud_api_key.get_api_keys_by_user(db=db, user_id=user_id)
     public_key = api_keys[0].api_key_public if api_keys else None

     decrypted_secret = None
     if public_key:
          decrypted_secret = crud_api_key.get_decrypted_secret_key(db=db, user_id=user_id, api_key_public=public_key)

     if not public_key or not decrypted_secret:
          logger.error(f"No valid API keys found or decryption failed for user {user_id} for backtest data fetching.")
          # Fallback to environment keys or raise error? Using env keys for now.
          client = BinanceAPIClient() # Uses keys from .env by default
     else:
          client = BinanceAPIClient(api_key=public_key, secret_key=decrypted_secret)

     await client.initialize() # Ensure client is initialized
     if not client.client:
          raise HTTPException(status_code=503, detail="Failed to initialize Binance client for historical data.")
     return client

# --- Backtest Endpoint ---

@router.post("/run", response_model=schemas_backtest.BacktestResults, summary="Run Backtest Simulation")
async def run_backtest(
    request: schemas_backtest.BacktestRequest,
    background_tasks: BackgroundTasks, # Use background tasks for potentially long runs
    db: Session = Depends(get_db),
    current_user: UserPayload = Depends(get_current_user)
):
    """
    Initiates a backtest simulation for a given bot configuration and date range.
    """
    user_id = uuid.UUID(current_user.sub) # Convert JWT sub to UUID
    logger.info(f"Received backtest request for config_id={request.config_id} by user={user_id}")

    # 1. Fetch Bot Configuration from DB
    # Assuming crud_bot_config expects UUID for user_id based on typical patterns
    bot_config_model = crud_bot_config.get_bot_config(db=db, config_id=request.config_id, user_id=user_id)
    if not bot_config_model:
        raise HTTPException(status_code=404, detail="Bot configuration not found or access denied.")

    # Convert SQLAlchemy model to dict for BacktestEngine (or use Pydantic schema)
    bot_config_dict = {c.name: getattr(bot_config_model, c.name) for c in bot_config_model.__table__.columns}
    # Ensure settings is a dict
    bot_config_dict['settings'] = bot_config_dict.get('settings', {})

    # 2. Fetch Historical Data (using a potentially user-specific client)
    # For simplicity now, assume backtest uses default client keys from .env
    # binance_client = await get_backtest_binance_client(user_id=user_id, db=db) # Pass user_id and db
    binance_client = BinanceAPIClient() # Simpler: Use env keys for now
    await binance_client.initialize()
    if not binance_client.client:
         raise HTTPException(status_code=503, detail="Failed to initialize Binance client for historical data.")

    interval = bot_config_dict.get("settings", {}).get("interval", "1h") # Get interval from config
    symbol = bot_config_dict.get("symbol")

    if not symbol:
        raise HTTPException(status_code=400, detail="Bot configuration is missing the 'symbol'.")


    logger.info(f"Fetching historical data for {symbol} ({interval})...")
    historical_data = await fetch_historical_data(
        client=binance_client,
        symbol=symbol,
        interval=interval,
        start_date_str=request.start_date.isoformat(),
        end_date_str=request.end_date.isoformat(),
        use_cache=True # Enable caching for backtests
    )
    await binance_client.close_connection() # Close client after fetching

    if historical_data is None or historical_data.empty:
        raise HTTPException(status_code=404, detail=f"Could not fetch historical data for {symbol} in the specified range.")

    # 3. Initialize and Run Backtest Engine
    logger.info("Initializing Backtest Engine...")
    try:
        engine = BacktestEngine(
            historical_data=historical_data,
            bot_config=bot_config_dict,
            initial_capital=request.initial_capital,
            commission_percent=request.commission_percent / 100.0 # Convert percentage
        )

        # Running synchronously for now, consider background task for long backtests
        results_dict = engine.run()

        if not results_dict:
             raise HTTPException(status_code=500, detail="Backtest engine failed to produce results.")

        # 4. Format and Return Results (potentially truncated)
        # Convert timestamps in equity curve for Pydantic validation
        results_dict['equity_curve'] = [
             {"timestamp": ts, "value": val} for ts, val in results_dict.get('equity_curve', [])
        ]
         # Convert timestamps in trades
        for trade in results_dict.get('trades', []):
             if isinstance(trade.get('timestamp'), datetime):
                  trade['timestamp'] = trade['timestamp'] # Already datetime
             # Add handling if timestamp is not datetime (e.g., from older format)

        # Truncate results if necessary before validation
        # Accessing Pydantic v1 style field info - adjust if using v2 model_config
        max_trades = schemas_backtest.BacktestResults.__fields__['trades'].field_info.max_items if hasattr(schemas_backtest.BacktestResults.__fields__['trades'].field_info, 'max_items') else 1000
        max_equity = schemas_backtest.BacktestResults.__fields__['equity_curve'].field_info.max_items if hasattr(schemas_backtest.BacktestResults.__fields__['equity_curve'].field_info, 'max_items') else 2000

        if len(results_dict.get('trades', [])) > max_trades:
             logger.warning(f"Truncating trades list from {len(results_dict['trades'])} to {max_trades}")
             results_dict['trades'] = results_dict['trades'][:max_trades]
        if len(results_dict.get('equity_curve', [])) > max_equity:
             logger.warning(f"Truncating equity curve from {len(results_dict['equity_curve'])} to {max_equity}")
             results_dict['equity_curve'] = results_dict['equity_curve'][:max_equity]


        # Validate results against Pydantic schema before returning
        validated_results = schemas_backtest.BacktestResults(**results_dict)

        logger.info(f"Backtest completed successfully for config_id={request.config_id}")
        return validated_results

    except ValueError as ve:
         logger.error(f"Value error during backtest initialization or run: {ve}")
         raise HTTPException(status_code=400, detail=f"Backtest configuration error: {ve}")
    except Exception as e:
        logger.exception(f"Unexpected error during backtest run for config_id={request.config_id}: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during the backtest.")

# TODO: Add endpoint to get saved backtest results by ID?
# @router.get("/results/{result_id}", ...)