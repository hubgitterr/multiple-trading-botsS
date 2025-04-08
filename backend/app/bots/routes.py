import asyncio
from fastapi import APIRouter, HTTPException, Depends, Body, Path
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging
from backend.app.auth_utils import get_current_user, UserPayload # Added auth imports
import uuid
from uuid import UUID # Import UUID type
from sqlalchemy.orm import Session # Import Session

# Import Base Bot and specific bot types later
from backend.bots.base_bot import BaseBot, DummyBot # Import DummyBot for example
from backend.bots.momentum_bot import MomentumBot
from backend.bots.grid_bot import GridBot
from backend.bots.dca_bot import DCABot
# Import the Binance client and dependency function
from backend.utils.binance_client import BinanceAPIClient
# from backend.app.market.routes import get_binance_client # Don't reuse, bots need specific keys
from backend.db import crud_api_key # Import API key CRUD

# Import database session, schemas and crud functions
from backend.db.session import get_db
from backend.schemas import bot_config as schemas # Import the new schemas
from backend.db import crud_bot_config # Import the CRUD functions
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/bots",     # Prefix for all routes in this router
    tags=["bots"],      # Tag for OpenAPI documentation
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(get_current_user)] # Added authentication dependency
)

# --- In-Memory Bot Management (Replace with persistent storage/management) ---
# WARNING: This is a simple in-memory store for demonstration. 
# Running bots will be lost if the server restarts.
# A real implementation needs a persistent way to track configs and potentially 
# manage bot processes/tasks (e.g., using Celery, Redis Queue, DB status field).
running_bots: Dict[str, BaseBot] = {} 
# Store bot configurations persistently (e.g., in Supabase)
# bot_configurations: Dict[str, Dict] = {} # Replace with DB interaction

# --- Pydantic Models defined in schemas/bot_config.py ---
# (Old inline models removed)
class BotStatus(BaseModel):
    bot_id: str
    user_id: str
    type: str
    symbol: str
    is_running: bool
    status_message: str
    config: Dict[str, Any] # Or a specific config model
    runtime_state: Dict[str, Any]

# --- Helper Functions ---

def get_bot_instance(bot_id: str) -> Optional[BaseBot]:
    """Retrieve a running bot instance by ID."""
    return running_bots.get(bot_id)

async def _create_and_run_bot(config_id: str, user_id: str, config_data: Dict, db: Session): # Accept db session instead of client
    """Helper to instantiate and start a bot based on config."""
    bot_type = config_data.get("bot_type")
    bot_id = config_id # Use config ID as the running bot ID for simplicity here
    
    # TODO: Replace this with dynamic loading based on bot_type
    if bot_type == "DummyBot":
        bot_class = DummyBot
    elif bot_type == "MomentumBot":
        # from backend.bots.momentum_bot import MomentumBot # Import moved to top
        bot_class = MomentumBot
    elif bot_type == "GridBot":
        bot_class = GridBot
    elif bot_type == "DCABot":
         bot_class = DCABot
    else:
        logger.error(f"Unknown bot type: {bot_type}")
        return None

    # --- Fetch User's API Keys and Initialize Client ---
    user_uuid = uuid.UUID(user_id)
    # Revert to fetching all keys and using the first one
    api_keys = crud_api_key.get_api_keys_by_user(db=db, user_id=user_uuid)
    if not api_keys:
        logger.error(f"No API keys found for user {user_id}. Cannot start bot {bot_id}.")
        return None

    # Using the first key found as placeholder
    selected_key = api_keys[0]
    decrypted_secret = crud_api_key.get_decrypted_secret_key(db=db, user_id=user_uuid, api_key_public=selected_key.api_key_public)
    if not decrypted_secret:
        logger.error(f"Failed to decrypt secret key for API key {selected_key.api_key_public} (ID: {selected_key.id}). Cannot start bot {bot_id}.")
        return None

    logger.info(f"Initializing Binance client for bot {bot_id} using user's stored API key (Label: {selected_key.label}).")
    # Create a new client instance specifically for this bot run
    user_binance_client = BinanceAPIClient(api_key=selected_key.api_key_public, secret_key=decrypted_secret)
    await user_binance_client.initialize()

    if not user_binance_client.client:
         logger.error(f"Failed to initialize user-specific Binance client for bot {bot_id}.")
         return None
    # --- End API Key Handling ---

    if bot_id in running_bots:
         logger.warning(f"Bot {bot_id} is already running.")
         return running_bots[bot_id]

    try:
        # Pass the user-specific client to the bot instance
        bot_instance = bot_class(bot_id=bot_id, user_id=user_id, config=config_data, binance_client=user_binance_client)
        running_bots[bot_id] = bot_instance
        await bot_instance.start() # Start the bot's async task
        logger.info(f"Successfully created and started bot {bot_id} of type {bot_type}")
        return bot_instance
    except Exception as e:
        logger.exception(f"Failed to create or start bot {bot_id}: {e}")
        if bot_id in running_bots: # Clean up if instance was created but start failed
             del running_bots[bot_id]
        return None

# --- API Endpoints ---

# CRUD for Bot Configurations (interacting with DB ideally)

@router.post("/configs", summary="Create Bot Configuration", status_code=201, response_model=schemas.BotConfig)
async def create_bot_configuration(
    config_data: schemas.BotConfigCreate, # Use schema from schemas module
    db: Session = Depends(get_db), # Inject DB session
    current_user: UserPayload = Depends(get_current_user) # Added auth dependency
):
    """
    Creates a new bot configuration entry in the database.
    Does not start the bot automatically.
    Requires authentication (placeholder user_id used for now).
    """
    user_id = current_user.sub # Use actual user ID from auth
    logger.info(f"User {user_id} creating bot config: {config_data.dict()}")
    
    # Call CRUD function to create the config in the DB
    # Call CRUD function with the correct keyword argument 'config_data'
    new_config = crud_bot_config.create_bot_config(db=db, user_id=user_id, config_data=config_data.dict())
    
    # crud function handles commit, refresh ensures we get DB defaults (like ID, created_at)
    return new_config

@router.get("/configs", summary="List Bot Configurations", response_model=List[schemas.BotConfig]) # Use schema list
async def list_bot_configurations(
    db: Session = Depends(get_db), # Inject DB session
    current_user: UserPayload = Depends(get_current_user) # Added auth dependency
):
    """
    Lists all bot configurations for the authenticated user (placeholder user_id used for now).
    Requires authentication.
    """
    user_id = current_user.sub # Use actual user ID from auth
    logger.info(f"User {user_id} listing bot configs.")
    
    # Call CRUD function to fetch configs for the user
    # Call CRUD function with the correct name
    user_configs = crud_bot_config.get_bot_configs_by_user(db=db, user_id=user_id)
    
    return user_configs


@router.get("/configs/{config_id}", summary="Get Bot Configuration", response_model=schemas.BotConfig) # Use schema
async def get_bot_configuration(
    config_id: UUID = Path(..., description="The ID of the bot configuration"), # Use UUID type
    db: Session = Depends(get_db), # Inject DB session
    current_user: UserPayload = Depends(get_current_user) # Added auth dependency
):
    """
    Retrieves details of a specific bot configuration.
    Requires authentication and ownership (placeholder user_id used for now).
    """
    user_id = current_user.sub # Use actual user ID from auth
    logger.info(f"User {user_id} getting bot config: {config_id}")
    
    # Call CRUD function to fetch config by ID, ensuring user owns it (implicitly via user_id)
    config = crud_bot_config.get_bot_config(db=db, config_id=config_id, user_id=user_id) # Already using user_id
    
    if not config:
        raise HTTPException(status_code=404, detail="Bot configuration not found")
        
    return config

@router.put("/configs/{config_id}", summary="Update Bot Configuration", response_model=schemas.BotConfig) # Use schema
async def update_bot_configuration(
    config_id: UUID = Path(..., description="The ID of the bot configuration to update"), # Use UUID type
    update_data: schemas.BotConfigUpdate = Body(...), # Use schema from schemas module
    db: Session = Depends(get_db), # Inject DB session
    current_user: UserPayload = Depends(get_current_user) # Added auth dependency
):
    """
    Updates an existing bot configuration.
    Requires authentication and ownership (placeholder user_id used for now).
    """
    user_id = current_user.sub # Use actual user ID from auth
    logger.info(f"User {user_id} updating bot config: {config_id} with {update_data.dict(exclude_unset=True)}")
    
    # Call CRUD function to update the config, ensuring user owns it
    updated_config = crud_bot_config.update_bot_config(
        db=db,
        config_id=config_id,
        user_id=user_id, # Already using user_id
        update_data=update_data.dict(exclude_unset=True) # Convert Pydantic model to dict
    )
    
    if not updated_config:
         raise HTTPException(status_code=404, detail="Bot configuration not found or update failed")

    # If bot is running and config changed, maybe stop/restart it? Requires careful handling.
    running_bot = get_bot_instance(str(config_id)) # get_bot_instance expects str
    if running_bot:
        logger.warning(f"Config {config_id} updated, but bot is running. Restart needed for changes to apply.")

    return updated_config


@router.delete("/configs/{config_id}", summary="Delete Bot Configuration", status_code=204)
async def delete_bot_configuration(
    config_id: UUID = Path(..., description="The ID of the bot configuration to delete"), # Use UUID type
    db: Session = Depends(get_db), # Inject DB session
    current_user: UserPayload = Depends(get_current_user) # Added auth dependency
):
    """
    Deletes a bot configuration. Stops the bot if it's running.
    Requires authentication and ownership (placeholder user_id used for now).
    """
    user_id = current_user.sub # Use actual user ID from auth
    logger.info(f"User {user_id} deleting bot config: {config_id}")

    # Stop the bot if it's running using this config ID
    running_bot = get_bot_instance(str(config_id)) # get_bot_instance expects str
    if running_bot:
        logger.info(f"Stopping running bot {config_id} before deleting configuration.")
        await running_bot.stop()
        if str(config_id) in running_bots:
             del running_bots[str(config_id)] # Remove from running list

    # Call CRUD function to delete the config, ensuring user owns it
    deleted_config = crud_bot_config.delete_bot_config(db=db, config_id=config_id, user_id=user_id) # Already using user_id
    
    if not deleted_config:
         raise HTTPException(status_code=404, detail="Bot configuration not found or delete failed")

    return None # No content response (HTTP 204)


# Bot Lifecycle Management

@router.post("/{bot_id}/start", summary="Start a Bot Instance")
async def start_bot( # Removed client dependency, added db
    bot_id: str = Path(..., description="The ID of the bot configuration to start"),
    # client: BinanceAPIClient = Depends(get_binance_client), # Removed client dependency
    db: Session = Depends(get_db), # Inject DB session for config fetch
    current_user: UserPayload = Depends(get_current_user) # Added auth dependency
):
    """
    Starts a bot instance based on its configuration ID.
    Requires authentication and ownership of the configuration.
    """
    user_id = current_user.sub # Use actual user ID
    logger.info(f"User {user_id} requesting to start bot with config ID: {bot_id}")

    if bot_id in running_bots:
         raise HTTPException(status_code=400, detail=f"Bot {bot_id} is already running.")

    # Fetch bot configuration from DB, ensuring user owns it
    config = crud_bot_config.get_bot_config(db=db, config_id=UUID(bot_id), user_id=user_id) # Fetch config using UUID
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found or access denied")
    if not config.is_enabled:
        raise HTTPException(status_code=400, detail="Bot configuration is disabled.")
        
    # Convert SQLAlchemy model to dict for bot instantiation
    config_data = schemas.BotConfig.from_orm(config).dict()

    if not config_data: # Should not happen if config was found, but keep check
         raise HTTPException(status_code=404, detail="Configuration data could not be loaded")

    # Pass db session to the helper function now, not a client instance
    bot_instance = await _create_and_run_bot(config_id=bot_id, user_id=user_id, config_data=config_data, db=db)

    if not bot_instance:
        raise HTTPException(status_code=500, detail=f"Failed to create or start bot {bot_id}.")

    return {"message": f"Bot {bot_id} started successfully.", "status": bot_instance.get_status()}


@router.post("/{bot_id}/stop", summary="Stop a Bot Instance")
async def stop_bot(
    bot_id: str = Path(..., description="The ID of the running bot instance to stop"),
    current_user: UserPayload = Depends(get_current_user) # Added auth dependency
):
    """
    Stops a running bot instance.
    Requires authentication and ownership.
    """
    user_id = current_user.sub # Use actual user ID
    logger.info(f"User {user_id} requesting to stop bot instance: {bot_id}")
    
    bot_instance = get_bot_instance(bot_id)
    if not bot_instance:
        raise HTTPException(status_code=404, detail=f"Bot instance {bot_id} not found or not running.")

    # Check if the current user owns this bot instance
    if bot_instance.user_id != user_id:
         raise HTTPException(status_code=403, detail="Access denied to stop this bot.")

    await bot_instance.stop()
    
    if bot_id in running_bots: # Remove from in-memory store after stopping
         del running_bots[bot_id]

    return {"message": f"Bot {bot_id} stopped successfully.", "status": bot_instance.get_status()}


@router.get("/status", summary="Get Status of All Running Bots", response_model=List[BotStatus])
async def get_all_bots_status(
    current_user: UserPayload = Depends(get_current_user) # Added auth dependency
):
    """
    Retrieves the status of all currently running bot instances for the user.
    Requires authentication.
    """
    user_id = current_user.sub # Use actual user ID
    logger.info(f"User {user_id} requesting status of all running bots.")
    
    user_bots_status = []
    for bot_id, bot_instance in running_bots.items():
        # Filter by user_id
        if bot_instance.user_id == user_id:
             user_bots_status.append(bot_instance.get_status())
             
    return user_bots_status


@router.get("/{bot_id}/status", summary="Get Status of a Specific Bot", response_model=BotStatus)
async def get_specific_bot_status(
    bot_id: str = Path(..., description="The ID of the bot instance"),
    db: Session = Depends(get_db), # Inject DB session for config check
    current_user: UserPayload = Depends(get_current_user) # Added auth dependency
):
    """
    Retrieves the status of a specific running bot instance.
    Requires authentication and ownership.
    """
    user_id = current_user.sub # Use actual user ID
    logger.info(f"User {user_id} requesting status for bot instance: {bot_id}")

    bot_instance = get_bot_instance(bot_id)
    if not bot_instance:
        # Check if it's a config ID that's just not running
        try:
            config = crud_bot_config.get_bot_config(db=db, config_id=UUID(bot_id), user_id=user_id) # Check DB
        except ValueError: # Handle case where bot_id is not a valid UUID
            config = None
            
        if config: # Check ownership implicitly via user_id in get_bot_config
             # Return a status indicating it's configured but not running
             config_data = schemas.BotConfig.from_orm(config).dict()
             return BotStatus(
                 bot_id=str(config.id), user_id=config.user_id, type=config.bot_type,
                 symbol=config.symbol, is_running=False,
                 status_message="Stopped/Not Running", config=config_data, runtime_state={}
             )
        else:
             raise HTTPException(status_code=404, detail=f"Bot instance or configuration {bot_id} not found.")

    # Check if the current user owns this bot instance
    if bot_instance.user_id != user_id:
         raise HTTPException(status_code=403, detail="Access denied to this bot's status.")
         
    return bot_instance.get_status()