import asyncio
import logging
import time
from datetime import datetime # Import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

# Import the Binance client (adjust path if necessary)
from backend.utils.binance_client import BinanceAPIClient
# Import database interaction logic
from uuid import UUID
from backend.db.session import SessionLocal
from backend.db import crud_trade
# Configure logging for the bot module
logger = logging.getLogger(f"bot.{__name__}")
# Ensure root logger is configured elsewhere (e.g., in main.py or a logging config file)
# If not, uncomment basicConfig here for standalone testing:
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class BaseBot(ABC):
    """
    Abstract Base Class for all trading bots.
    Provides common structure, state management, and interaction with the Binance client.
    """
    def __init__(self, bot_id: str, user_id: str, config: Dict[str, Any], binance_client: BinanceAPIClient):
        """
        Initializes the BaseBot.

        Args:
            bot_id: A unique identifier for this bot instance.
            user_id: The ID of the user who owns this bot.
            config: A dictionary containing the bot's specific configuration.
            binance_client: An initialized instance of the BinanceAPIClient.
        """
        self.bot_id = bot_id
        self.user_id = user_id
        self.config = config
        self.binance_client = binance_client
        
        self.is_running = False
        self._run_task: Optional[asyncio.Task] = None # To hold the main bot loop task
        self.state: Dict[str, Any] = {} # To store bot-specific runtime state

        self.symbol = config.get("symbol", "BTCUSDT").upper() # Default or from config
        logger.info(f"Initializing Bot {self.bot_id} ({self.__class__.__name__}) for user {self.user_id} on symbol {self.symbol}")

    @abstractmethod
    async def _run_logic(self):
        """
        The core logic loop for the specific bot strategy.
        This method must be implemented by subclasses.
        It should contain the main async loop that checks market conditions,
        makes trading decisions, places orders, etc.
        It should periodically yield control (e.g., using asyncio.sleep) 
        to allow other tasks to run and check for stop signals.
        """
        pass

    async def start(self):
        """Starts the bot's main logic loop in a background task."""
        if self.is_running:
            logger.warning(f"Bot {self.bot_id} is already running.")
            return

        if not self.binance_client or not self.binance_client.client:
             logger.error(f"Cannot start Bot {self.bot_id}: Binance client not initialized.")
             # Optionally update state or raise an error
             self.state['status'] = 'Error: Binance client unavailable'
             return

        logger.info(f"Starting Bot {self.bot_id} ({self.__class__.__name__})...")
        self.is_running = True
        self.state['status'] = 'Running'
        # Create and store the task so it can be cancelled
        self._run_task = asyncio.create_task(self._run_logic_wrapper())
        logger.info(f"Bot {self.bot_id} task created.")

    async def _run_logic_wrapper(self):
        """Wraps the _run_logic call with error handling and status updates."""
        try:
            await self._run_logic()
        except asyncio.CancelledError:
            logger.info(f"Bot {self.bot_id} run task was cancelled.")
        except Exception as e:
            logger.exception(f"Error occurred in Bot {self.bot_id} run logic: {e}")
            self.state['status'] = f'Error: {e}'
            # Potentially add more robust error handling/reporting here
        finally:
            logger.info(f"Bot {self.bot_id} logic loop finished.")
            self.is_running = False
            if self.state.get('status') == 'Running': # Update status if not already set to Error/Stopped
                 self.state['status'] = 'Stopped'

    async def stop(self):
        """Stops the bot's main logic loop."""
        if not self.is_running or not self._run_task:
            logger.warning(f"Bot {self.bot_id} is not running or task does not exist.")
            return

        logger.info(f"Stopping Bot {self.bot_id} ({self.__class__.__name__})...")
        self.is_running = False # Signal the loop to stop (if checked within _run_logic)
        self.state['status'] = 'Stopping'

        # Cancel the background task
        self._run_task.cancel()
        try:
            # Wait for the task to acknowledge cancellation
            await self._run_task 
        except asyncio.CancelledError:
             logger.info(f"Bot {self.bot_id} task successfully cancelled.")
        except Exception as e:
             logger.exception(f"Error during bot {self.bot_id} task cancellation: {e}")
        
        self._run_task = None
        self.state['status'] = 'Stopped'
        
        # Close the Binance client session
        if self.binance_client:
            # Call the correct method name: close_connection()
            # Call the correct method name: close_connection()
            try:
                await self.binance_client.close_connection()
                logger.info(f"Binance client closed for bot {self.bot_id}.")
            except Exception as e:
                logger.error(f"Error closing Binance client for bot {self.bot_id}: {e}")

        logger.info(f"Bot {self.bot_id} stopped.")
        # TODO: Add any cleanup logic here (e.g., cancel open orders if configured)

    def get_status(self) -> Dict[str, Any]:
        """Returns the current status and state of the bot."""
        status = {
            "bot_id": self.bot_id,
            "user_id": self.user_id,
            "type": self.__class__.__name__,
            "symbol": self.symbol,
            "is_running": self.is_running,
            "status_message": self.state.get('status', 'Initialized'),
            "config": self.config, # Be careful about exposing sensitive config details
            "runtime_state": self.state,
        }
        return status

    # --- Helper methods for subclasses ---

    async def place_order(self, side: str, order_type: str, quantity: float, price: Optional[float] = None, **kwargs) -> Optional[Dict]:
        """Helper method to place an order using the Binance client."""
        if not self.is_running:
             logger.warning(f"Bot {self.bot_id}: Attempted to place order while not running.")
             return None
        try:
            logger.info(f"Bot {self.bot_id}: Placing {side} {order_type} order for {quantity} {self.symbol} @ {price or 'Market'}")
            order_result = await self.binance_client.create_order(
                symbol=self.symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
                **kwargs
            )
            # TODO: Process order result, update state, log trade
            logger.info(f"Bot {self.bot_id}: Order placement result: {order_result}")
            # Example state update:
            # self.state['last_order_id'] = order_result.get('orderId')
            self.log_trade(order_result) # Persist trade to DB
            return order_result
        except Exception as e:
            logger.exception(f"Bot {self.bot_id}: Error placing order: {e}")
            return None

    async def get_market_price(self) -> Optional[float]:
         """Helper to get the current market price for the bot's symbol."""
         try:
              price = await self.binance_client.get_current_price(self.symbol)
              return price
         except Exception as e:
              logger.error(f"Bot {self.bot_id}: Failed to get market price for {self.symbol}: {e}")
              return None

    # TODO: Add more helper methods as needed (e.g., get_account_balance, get_open_orders, log_trade_to_db)

    def log_trade(self, order_details: Dict):
        """Logs executed trade details to the database."""
        db = None
        try:
            db = SessionLocal() # Create a new session for this operation
            bot_config_id = UUID(self.bot_id) # Convert string bot_id to UUID
            # Map Binance order response fields to the structure expected by create_trade
            # Ensure defaults are provided for potentially missing fields or handle None appropriately
            trade_payload = {
                'symbol': order_details.get('symbol'),
                'order_id': str(order_details.get('orderId', f'sim_{int(time.time())}')), # Ensure string
                'client_order_id': order_details.get('clientOrderId'),
                'side': order_details.get('side', 'UNKNOWN'), # Provide default
                'order_type': order_details.get('type', 'UNKNOWN'), # Provide default
                'price': float(order_details.get('price', 0.0) or 0.0), # Handle None/empty
                'quantity': float(order_details.get('executedQty', 0.0) or 0.0), # Use executedQty
                'quote_quantity': float(order_details.get('cummulativeQuoteQty', 0.0) or 0.0), # Handle None/empty
                'commission': None, # Placeholder - Binance fills might contain this
                'commission_asset': None, # Placeholder
                'timestamp': datetime.fromtimestamp(int(order_details.get('transactTime', time.time() * 1000)) / 1000) if order_details.get('transactTime') else datetime.now() # Ensure transactTime is int before division
            }
            
            # Extract commission from fills if available (Binance specific)
            if order_details.get('fills') and isinstance(order_details['fills'], list) and len(order_details['fills']) > 0:
                 # Assuming commission info is in the first fill for simplicity
                 fill = order_details['fills'][0]
                 trade_payload['commission'] = float(fill.get('commission', 0.0) or 0.0)
                 trade_payload['commission_asset'] = fill.get('commissionAsset')
                 # Use fill price if order price is 0 (e.g., for MARKET orders)
                 if trade_payload['price'] == 0.0:
                      trade_payload['price'] = float(fill.get('price', 0.0) or 0.0)
                 # Use fill quote qty if order quote qty is 0 (e.g., for MARKET orders)
                 if trade_payload['quote_quantity'] == 0.0:
                      trade_payload['quote_quantity'] = float(fill.get('qty', 0.0) or 0.0) * trade_payload['price'] # Approximate


            crud_trade.create_trade(
                db=db,
                user_id=self.user_id,
                bot_config_id=bot_config_id,
                trade_data=trade_payload # Pass the mapped payload
            )
            logger.info(f"Bot {self.bot_id}: Successfully logged trade to DB: {order_details.get('orderId', 'N/A')}")
        except ValueError:
             logger.exception(f"Bot {self.bot_id}: Invalid bot_id format. Cannot convert '{self.bot_id}' to UUID.")
        except Exception as e:
            logger.exception(f"Bot {self.bot_id}: Failed to log trade to DB: {e}")
        finally:
            if db:
                db.close() # Ensure the session is closed


# Example of a simple dummy bot for testing structure
class DummyBot(BaseBot):
    async def _run_logic(self):
        logger.info(f"DummyBot {self.bot_id}: Starting logic loop.")
        while self.is_running:
            logger.info(f"DummyBot {self.bot_id}: Logic loop iteration. Current state: {self.state}")
            # Example: Get price
            price = await self.get_market_price()
            if price:
                 self.state['last_price'] = price
                 logger.info(f"DummyBot {self.bot_id}: Fetched price {price}")
            
            # Simulate some work/decision making
            await asyncio.sleep(10) # Check every 10 seconds
            
            # Check if stop signal received
            if not self.is_running:
                logger.info(f"DummyBot {self.bot_id}: Stop signal received, exiting loop.")
                break 
        logger.info(f"DummyBot {self.bot_id}: Logic loop finished.")