import asyncio
import logging
from typing import Dict, Any, Optional, List

# Import base class and utilities
from backend.bots.base_bot import BaseBot
from backend.utils.binance_client import BinanceAPIClient
from backend.utils import grid as grid_utils # Import our grid calculation functions

# Configure logging for this specific bot type
logger = logging.getLogger(f"bot.{__name__}")
# Ensure root logger is configured elsewhere

class GridBot(BaseBot):
    """
    A trading bot that implements a grid trading strategy.
    Places buy orders below the current price and sell orders above.
    """
    def __init__(self, bot_id: str, user_id: str, config: Dict[str, Any], binance_client: BinanceAPIClient):
        super().__init__(bot_id, user_id, config, binance_client)
        
        # --- Strategy Specific Configuration ---
        settings = self.config.get("settings", {})
        self.lower_price: float = settings.get("lower_price")
        self.upper_price: float = settings.get("upper_price")
        self.num_grids: int = settings.get("num_grids")
        self.grid_type: str = settings.get("grid_type", "arithmetic").lower() # 'arithmetic' or 'geometric'
        self.total_investment: float = settings.get("total_investment") # Amount of quote currency for buys
        self.base_asset_amount: Optional[float] = settings.get("base_asset_amount") # Amount of base currency for sells (optional, can be calculated)
        
        # Validate essential config
        if not all([self.lower_price, self.upper_price, self.num_grids, self.total_investment]):
             # Log error and potentially prevent initialization or set an error state
             logger.error(f"GridBot {self.bot_id}: Missing essential configuration (lower_price, upper_price, num_grids, total_investment).")
             # raise ValueError("Missing essential grid configuration") # Or handle gracefully
             self.state['status'] = 'Error: Missing configuration'
             self.is_running = False # Prevent starting

        # --- Strategy Specific State ---
        self.state['grid_levels'] = []
        self.state['buy_orders'] = {} # Store active buy order IDs {price_level: order_id}
        self.state['sell_orders'] = {} # Store active sell order IDs {price_level: order_id}
        self.state['order_quantity_per_grid'] = 0.0
        self.state['initial_setup_complete'] = False
        self.state['last_check_time'] = None

        logger.info(f"GridBot {self.bot_id} initialized: Range ({self.lower_price}-{self.upper_price}), Grids: {self.num_grids} ({self.grid_type}), Investment: {self.total_investment}")


    async def _calculate_and_setup_grid(self):
        """Calculates grid levels and quantity, then places initial orders."""
        logger.info(f"GridBot {self.bot_id}: Setting up grid...")
        
        # 1. Calculate Grid Levels
        if self.grid_type == "geometric":
            levels = grid_utils.calculate_geometric_grid_levels(self.lower_price, self.upper_price, self.num_grids)
        else: # Default to arithmetic
            levels = grid_utils.calculate_arithmetic_grid_levels(self.lower_price, self.upper_price, self.num_grids)

        if not levels:
            logger.error(f"GridBot {self.bot_id}: Failed to calculate grid levels.")
            self.state['status'] = 'Error: Grid calculation failed'
            self.is_running = False
            return False
        
        self.state['grid_levels'] = levels
        logger.info(f"GridBot {self.bot_id}: Calculated {len(levels)} levels: {[f'{lvl:.4f}' for lvl in levels]}")

        # 2. Get Current Price to determine buy/sell levels
        current_price = await self.get_market_price()
        if not current_price:
             logger.error(f"GridBot {self.bot_id}: Failed to get current market price for setup.")
             self.state['status'] = 'Error: Failed to get market price'
             self.is_running = False
             return False
        
        logger.info(f"GridBot {self.bot_id}: Current market price: {current_price}")

        # 3. Determine Buy/Sell Levels and Calculate Quantity
        buy_levels = [lvl for lvl in levels if lvl < current_price]
        sell_levels = [lvl for lvl in levels if lvl > current_price]
        
        # Ensure there's at least one buy and one sell level for basic operation
        if not buy_levels or not sell_levels:
             logger.error(f"GridBot {self.bot_id}: Grid setup requires levels both above and below current price ({current_price}). Buy levels: {len(buy_levels)}, Sell levels: {len(sell_levels)}")
             self.state['status'] = 'Error: Invalid grid setup (price outside range?)'
             self.is_running = False
             return False

        # Calculate quantity per grid (using buy side investment)
        # Note: Assumes equal quantity for buy/sell for simplicity. Real strategy might differ.
        num_buy_grids = len(buy_levels)
        self.state['order_quantity_per_grid'] = grid_utils.calculate_order_size_per_grid(
            self.total_investment, num_buy_grids, current_price # Use current price as estimate
        )
        
        if not self.state['order_quantity_per_grid'] or self.state['order_quantity_per_grid'] <= 0:
             logger.error(f"GridBot {self.bot_id}: Failed to calculate valid order quantity.")
             self.state['status'] = 'Error: Order quantity calculation failed'
             self.is_running = False
             return False
             
        qty = self.state['order_quantity_per_grid']
        logger.info(f"GridBot {self.bot_id}: Order quantity per grid: {qty:.8f}")

        # 4. Place Initial Orders (LIMIT orders)
        # Cancel any existing orders first (important for restarts/rebalancing)
        # await self._cancel_all_grid_orders() # Implement this helper

        logger.info(f"GridBot {self.bot_id}: Placing initial grid orders...")
        placed_buy_orders = {}
        placed_sell_orders = {}

        # Place buy orders
        for level in buy_levels:
            # TODO: Add proper error handling and retry logic for order placement
            order_result = await self.place_order(side="BUY", order_type="LIMIT", quantity=qty, price=level, timeInForce="GTC")
            if order_result and order_result.get('orderId'):
                placed_buy_orders[f"{level:.8f}"] = order_result['orderId'] # Use formatted price as key
                logger.info(f"Placed BUY @ {level:.4f}, ID: {order_result['orderId']}")
            else:
                logger.error(f"Failed to place BUY order at level {level:.4f}")
                # Handle failure - maybe stop the bot or retry?
        
        # Place sell orders
        for level in sell_levels:
             # TODO: Add proper error handling and retry logic
            order_result = await self.place_order(side="SELL", order_type="LIMIT", quantity=qty, price=level, timeInForce="GTC")
            if order_result and order_result.get('orderId'):
                placed_sell_orders[f"{level:.8f}"] = order_result['orderId']
                logger.info(f"Placed SELL @ {level:.4f}, ID: {order_result['orderId']}")
            else:
                logger.error(f"Failed to place SELL order at level {level:.4f}")
                # Handle failure

        self.state['buy_orders'] = placed_buy_orders
        self.state['sell_orders'] = placed_sell_orders
        self.state['initial_setup_complete'] = True
        logger.info(f"GridBot {self.bot_id}: Initial grid setup complete. {len(placed_buy_orders)} buys, {len(placed_sell_orders)} sells placed.")
        return True


    async def _check_and_replace_orders(self):
        """Checks status of grid orders and replaces filled ones."""
        if not self.state.get('initial_setup_complete'):
             logger.warning(f"GridBot {self.bot_id}: Grid setup not complete, cannot check orders.")
             return

        logger.debug(f"GridBot {self.bot_id}: Checking order status...")
        qty = self.state['order_quantity_per_grid']
        
        # --- Check Buy Orders ---
        filled_buy_levels = []
        current_buy_orders = self.state['buy_orders'].copy() # Iterate over a copy
        for level_str, order_id in current_buy_orders.items():
            try:
                level = float(level_str)
                # TODO: Implement efficient order status check (maybe fetch all open orders?)
                order_status = await self.binance_client.get_order_status(self.symbol, order_id) 
                
                if not order_status:
                     logger.warning(f"Could not get status for BUY order {order_id} at {level:.4f}. Assuming active.")
                     continue

                if order_status.get('status') == 'FILLED':
                    logger.info(f"BUY order FILLED at {level:.4f} (ID: {order_id}).")
                    filled_buy_levels.append(level)
                    self.log_trade({"side": "BUY", "price": level, "qty": qty, **order_status})
                    
                    # Place corresponding SELL order one grid level higher
                    sell_level_index = self.state['grid_levels'].index(level) + 1
                    if sell_level_index < len(self.state['grid_levels']):
                        sell_price = self.state['grid_levels'][sell_level_index]
                        logger.info(f"Placing corresponding SELL order at {sell_price:.4f}")
                        sell_order_result = await self.place_order(side="SELL", order_type="LIMIT", quantity=qty, price=sell_price, timeInForce="GTC")
                        if sell_order_result and sell_order_result.get('orderId'):
                             self.state['sell_orders'][f"{sell_price:.8f}"] = sell_order_result['orderId']
                        else:
                             logger.error(f"Failed to place corresponding SELL order at {sell_price:.4f}")
                    else:
                         logger.warning(f"Buy filled at lowest level {level:.4f}, no higher sell level to place.")

                    # Remove filled buy order from state
                    del self.state['buy_orders'][level_str]

                elif order_status.get('status') in ['CANCELED', 'EXPIRED', 'REJECTED']:
                     logger.warning(f"BUY order {order_id} at {level:.4f} is inactive ({order_status.get('status')}). Removing from tracking.")
                     del self.state['buy_orders'][level_str]
                     # TODO: Decide whether to replace it immediately or wait for rebalancing

            except Exception as e:
                 logger.exception(f"Error checking BUY order {order_id} at {level_str}: {e}")


        # --- Check Sell Orders ---
        filled_sell_levels = []
        current_sell_orders = self.state['sell_orders'].copy()
        for level_str, order_id in current_sell_orders.items():
             try:
                level = float(level_str)
                order_status = await self.binance_client.get_order_status(self.symbol, order_id)

                if not order_status:
                     logger.warning(f"Could not get status for SELL order {order_id} at {level:.4f}. Assuming active.")
                     continue

                if order_status.get('status') == 'FILLED':
                    logger.info(f"SELL order FILLED at {level:.4f} (ID: {order_id}).")
                    filled_sell_levels.append(level)
                    self.log_trade({"side": "SELL", "price": level, "qty": qty, **order_status})

                    # Place corresponding BUY order one grid level lower
                    buy_level_index = self.state['grid_levels'].index(level) - 1
                    if buy_level_index >= 0:
                        buy_price = self.state['grid_levels'][buy_level_index]
                        logger.info(f"Placing corresponding BUY order at {buy_price:.4f}")
                        buy_order_result = await self.place_order(side="BUY", order_type="LIMIT", quantity=qty, price=buy_price, timeInForce="GTC")
                        if buy_order_result and buy_order_result.get('orderId'):
                             self.state['buy_orders'][f"{buy_price:.8f}"] = buy_order_result['orderId']
                        else:
                             logger.error(f"Failed to place corresponding BUY order at {buy_price:.4f}")
                    else:
                         logger.warning(f"Sell filled at highest level {level:.4f}, no lower buy level to place.")
                         
                    # Remove filled sell order from state
                    del self.state['sell_orders'][level_str]
                    
                elif order_status.get('status') in ['CANCELED', 'EXPIRED', 'REJECTED']:
                     logger.warning(f"SELL order {order_id} at {level:.4f} is inactive ({order_status.get('status')}). Removing from tracking.")
                     del self.state['sell_orders'][level_str]
                     # TODO: Decide whether to replace it

             except Exception as e:
                 logger.exception(f"Error checking SELL order {order_id} at {level_str}: {e}")

        self.state['last_check_time'] = asyncio.get_event_loop().time()


    async def _run_logic(self):
        """The main logic loop for the Grid Bot."""
        logger.info(f"GridBot {self.bot_id}: Starting logic loop.")

        # Initial grid setup
        setup_success = await self._calculate_and_setup_grid()
        if not setup_success:
             logger.error(f"GridBot {self.bot_id}: Initial setup failed. Stopping.")
             self.state['status'] = 'Error: Setup Failed'
             self.is_running = False # Ensure it stops if setup fails
             return # Stop execution

        check_interval = 60 # Check order status every 60 seconds (adjust as needed)

        while self.is_running:
            try:
                start_time = asyncio.get_event_loop().time()
                
                # Check status of orders and replace filled ones
                await self._check_and_replace_orders()

                # TODO: Implement rebalancing logic if price moves significantly
                # E.g., if price moves outside grid range, or too many orders filled on one side.
                # This might involve cancelling all orders and running _calculate_and_setup_grid again.

                # Wait for the next check cycle
                end_time = asyncio.get_event_loop().time()
                elapsed = end_time - start_time
                wait_time = max(0, check_interval - elapsed) 
                logger.debug(f"GridBot {self.bot_id}: Check cycle finished in {elapsed:.2f}s. Waiting {wait_time:.2f}s.")
                await asyncio.sleep(wait_time)

            except asyncio.CancelledError:
                logger.info(f"GridBot {self.bot_id}: Logic loop cancelled.")
                # TODO: Implement cleanup - cancel open orders on stop?
                # await self._cancel_all_grid_orders() 
                break 
            except Exception as e:
                logger.exception(f"GridBot {self.bot_id}: Unhandled error in logic loop: {e}")
                # Consider stopping the bot or waiting before retry
                await asyncio.sleep(60) 

        logger.info(f"GridBot {self.bot_id}: Logic loop finished.")
        # Optional: Final cleanup if needed after loop ends naturally (e.g., if is_running becomes false)


    # --- Helper for cleanup ---
    async def _cancel_all_grid_orders(self):
         """Cancels all tracked buy and sell orders for this grid."""
         logger.info(f"GridBot {self.bot_id}: Cancelling all open grid orders...")
         all_orders = {**self.state.get('buy_orders',{}), **self.state.get('sell_orders',{})}
         cancelled_count = 0
         for level_str, order_id in all_orders.items():
              try:
                   # Use the client's cancel method
                   cancel_result = await self.binance_client.cancel_order(symbol=self.symbol, order_id=order_id)
                   # TODO: Check cancel_result for success confirmation
                   logger.info(f"Cancelled order {order_id} at level {level_str}. Result: {cancel_result}")
                   cancelled_count += 1
              except Exception as e:
                   # Log error but continue trying to cancel others
                   # Handle cases where order might already be filled/cancelled
                   logger.error(f"Failed to cancel order {order_id} at level {level_str}: {e}")
         
         logger.info(f"GridBot {self.bot_id}: Cancellation attempt finished. {cancelled_count}/{len(all_orders)} orders processed.")
         # Clear local tracking after attempting cancellation
         self.state['buy_orders'] = {}
         self.state['sell_orders'] = {}