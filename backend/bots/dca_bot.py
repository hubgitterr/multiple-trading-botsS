import asyncio
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# Import base class and utilities
from backend.bots.base_bot import BaseBot
from backend.utils.binance_client import BinanceAPIClient

# Configure logging for this specific bot type
logger = logging.getLogger(f"bot.{__name__}")
# Ensure root logger is configured elsewhere

class DCABot(BaseBot):
    """
    A trading bot that implements a Dollar-Cost Averaging (DCA) strategy.
    Makes regular purchases of a fixed amount at specified intervals.
    Optionally includes logic for dip-buying and trailing stop-loss (placeholders).
    """
    def __init__(self, bot_id: str, user_id: str, config: Dict[str, Any], binance_client: BinanceAPIClient):
        super().__init__(bot_id, user_id, config, binance_client)
        
        # --- Strategy Specific Configuration ---
        settings = self.config.get("settings", {})
        self.purchase_amount: float = settings.get("purchase_amount") # Amount of quote currency (e.g., USDT) per purchase
        self.purchase_frequency_hours: int = settings.get("purchase_frequency_hours", 24 * 7) # Default: weekly
        # Optional Dip Buying config (placeholders)
        self.enable_dip_buying: bool = settings.get("enable_dip_buying", False)
        self.dip_percentage: float = settings.get("dip_percentage", 5.0) # e.g., 5% dip from recent high
        self.dip_buy_amount_multiplier: float = settings.get("dip_buy_amount_multiplier", 1.0) # Buy same or more on dips
        # Optional Trailing Stop Loss config (placeholders)
        self.enable_tsl: bool = settings.get("enable_tsl", False)
        self.tsl_percentage: float = settings.get("tsl_percentage", 10.0) # e.g., 10% trailing stop

        # Validate essential config
        if not self.purchase_amount or self.purchase_amount <= 0:
             logger.error(f"DCABot {self.bot_id}: Invalid or missing 'purchase_amount'.")
             self.state['status'] = 'Error: Missing purchase_amount'
             self.is_running = False
        if self.purchase_frequency_hours <= 0:
             logger.error(f"DCABot {self.bot_id}: Invalid 'purchase_frequency_hours'. Must be positive.")
             self.state['status'] = 'Error: Invalid purchase_frequency_hours'
             self.is_running = False

        # --- Strategy Specific State ---
        self.state['last_purchase_time'] = None
        self.state['next_purchase_time'] = None
        self.state['total_invested'] = 0.0 # Track total quote currency spent
        self.state['total_base_acquired'] = 0.0 # Track total base currency bought
        self.state['position_value'] = 0.0 # Estimated current value
        # State for dip buying / TSL (placeholders)
        self.state['recent_high_price'] = None 
        self.state['tsl_activation_price'] = None
        self.state['tsl_stop_price'] = None

        logger.info(f"DCABot {self.bot_id} initialized: Amount={self.purchase_amount}, Freq={self.purchase_frequency_hours}hrs")


    async def _schedule_next_purchase(self):
        """Calculates and sets the next scheduled purchase time."""
        now = time.time()
        if self.state.get('last_purchase_time') is None:
             # First run, schedule the first purchase immediately or after a short delay?
             # Let's schedule it for the next interval start for consistency.
             # Or make the first purchase on start? Let's buy on start.
             self.state['next_purchase_time'] = now 
        else:
             # Schedule based on last purchase time + frequency
             self.state['next_purchase_time'] = self.state['last_purchase_time'] + (self.purchase_frequency_hours * 3600)

        # Ensure next purchase time is not in the past (e.g., if bot was stopped for a long time)
        if self.state['next_purchase_time'] < now:
             # Missed schedule, buy now? Or skip to next interval?
             # Let's schedule for the *next* valid interval from now to avoid rapid catch-up buys.
             missed_intervals = (now - self.state['next_purchase_time']) // (self.purchase_frequency_hours * 3600)
             self.state['next_purchase_time'] += (missed_intervals + 1) * (self.purchase_frequency_hours * 3600)
             logger.warning(f"DCABot {self.bot_id}: Missed purchase schedule. Next purchase rescheduled to {datetime.fromtimestamp(self.state['next_purchase_time']).isoformat()}")

        logger.info(f"DCABot {self.bot_id}: Next scheduled purchase at: {datetime.fromtimestamp(self.state['next_purchase_time']).isoformat()}")


    async def _execute_dca_purchase(self, amount: float):
        """Executes a market buy order for the specified quote amount."""
        logger.info(f"DCABot {self.bot_id}: Executing DCA purchase of {amount} {self.config.get('quote_currency', 'USDT')} worth of {self.symbol}.")
        
        # Use quoteOrderQty for MARKET BUY with quote amount
        order_result = await self.place_order(
            side="BUY", 
            order_type="MARKET", 
            quantity=None, # Quantity is determined by quoteOrderQty
            quoteOrderQty=amount 
        )

        if order_result and order_result.get('status') == 'FILLED':
            filled_qty = float(order_result.get('executedQty', 0))
            filled_quote_amount = float(order_result.get('cummulativeQuoteQty', 0))
            self.state['last_purchase_time'] = time.time()
            self.state['total_invested'] = self.state.get('total_invested', 0.0) + filled_quote_amount
            self.state['total_base_acquired'] = self.state.get('total_base_acquired', 0.0) + filled_qty
            logger.info(f"DCA Purchase successful: Bought {filled_qty:.8f} {self.symbol} for ~{filled_quote_amount:.2f} {self.config.get('quote_currency', 'USDT')}")
            self.log_trade({"type": "DCA_REGULAR", "amount_quote": amount, **order_result})
            return True
        else:
            logger.error(f"DCABot {self.bot_id}: Failed to execute DCA purchase. Result: {order_result}")
            # Handle error - maybe retry?
            return False


    async def _check_dip_and_buy(self):
        """Placeholder for dip detection and buying logic."""
        if not self.enable_dip_buying:
            return False # Dip buying disabled

        logger.debug(f"DCABot {self.bot_id}: Checking for dip buying opportunities...")
        # TODO: Implement dip detection logic
        # 1. Get recent price data (e.g., daily highs or moving average)
        # 2. Compare current price to recent high/average
        # 3. If dip percentage is met, execute dip buy
        
        # Example placeholder logic:
        # current_price = await self.get_market_price()
        # recent_high = self.state.get('recent_high_price') # Need to track this
        # if current_price and recent_high and current_price < recent_high * (1 - self.dip_percentage / 100):
        #     logger.info(f"Dip detected! Price {current_price} is >{self.dip_percentage}% below recent high {recent_high}")
        #     dip_amount = self.purchase_amount * self.dip_buy_amount_multiplier
        #     await self._execute_dca_purchase(dip_amount) # Consider separate logging/tracking for dip buys
        #     # Reset dip condition or add cooldown?
        #     return True
             
        return False # No dip buy executed


    async def _check_trailing_stop_loss(self):
        """Placeholder for Trailing Stop Loss logic."""
        if not self.enable_tsl or self.state.get('total_base_acquired', 0) <= 0:
            return # TSL disabled or no position to protect

        logger.debug(f"DCABot {self.bot_id}: Checking Trailing Stop Loss...")
        # TODO: Implement TSL logic
        # 1. Get current price
        # 2. Update TSL activation price (highest price seen since position opened/TSL enabled)
        # 3. Calculate TSL stop price based on activation price and percentage
        # 4. If current price drops below TSL stop price, execute market sell order for entire position.
        
        # Example placeholder logic:
        # current_price = await self.get_market_price()
        # if not current_price: return
        #
        # activation_price = self.state.get('tsl_activation_price')
        # if activation_price is None or current_price > activation_price:
        #      self.state['tsl_activation_price'] = current_price
        #      activation_price = current_price
        #      logger.info(f"TSL Activation Price updated to: {activation_price}")
        # 
        # stop_price = activation_price * (1 - self.tsl_percentage / 100)
        # self.state['tsl_stop_price'] = stop_price
        # logger.debug(f"Current TSL Stop Price: {stop_price}")
        #
        # if current_price < stop_price:
        #      logger.warning(f"Trailing Stop Loss triggered! Price {current_price} < Stop Price {stop_price}")
        #      sell_qty = self.state.get('total_base_acquired', 0) 
        #      # TODO: Get actual available balance instead of relying solely on state tracking
        #      if sell_qty > 0:
        #           logger.info(f"Executing TSL Market Sell for {sell_qty:.8f} {self.symbol}")
        #           order_result = await self.place_order(side="SELL", order_type="MARKET", quantity=sell_qty)
        #           if order_result:
        #                self.log_trade({"type": "TSL_TRIGGERED", **order_result})
        #                # Reset state after TSL sell
        #                self.state['total_invested'] = 0.0
        #                self.state['total_base_acquired'] = 0.0
        #                self.state['tsl_activation_price'] = None
        #                self.state['tsl_stop_price'] = None
        #                # Consider stopping the bot or pausing after TSL?
        #                # self.is_running = False 
        #           else:
        #                logger.error("Failed to execute TSL sell order.")
        #      else:
        #           logger.warning("TSL triggered but no quantity to sell in state.")


    async def _run_logic(self):
        """The main logic loop for the DCA Bot."""
        logger.info(f"DCABot {self.bot_id}: Starting logic loop.")

        # Schedule the first purchase time
        await self._schedule_next_purchase()
        
        # Make initial purchase immediately on start? (Optional based on strategy preference)
        # logger.info("Executing initial purchase on start...")
        # await self._execute_dca_purchase(self.purchase_amount)
        # await self._schedule_next_purchase() # Reschedule after initial buy

        check_interval = 60 # Check status every 60 seconds (adjust as needed)

        while self.is_running:
            try:
                now = time.time()
                
                # --- Scheduled Purchase ---
                next_purchase_time = self.state.get('next_purchase_time')
                if next_purchase_time and now >= next_purchase_time:
                    logger.info(f"DCABot {self.bot_id}: Scheduled purchase time reached.")
                    await self._execute_dca_purchase(self.purchase_amount)
                    # Schedule the next one immediately after execution
                    await self._schedule_next_purchase() 
                
                # --- Optional Dip Buying ---
                # Check more frequently than scheduled buys?
                await self._check_dip_and_buy() # Placeholder call

                # --- Optional Trailing Stop Loss ---
                await self._check_trailing_stop_loss() # Placeholder call
                
                # --- Update Position Value (optional) ---
                # current_price = await self.get_market_price()
                # if current_price and self.state.get('total_base_acquired', 0) > 0:
                #      self.state['position_value'] = self.state['total_base_acquired'] * current_price

                # --- Wait for next check ---
                # Calculate sleep time until the *earlier* of the next check or the next purchase
                sleep_until = now + check_interval
                if next_purchase_time:
                     sleep_until = min(sleep_until, next_purchase_time)
                     
                wait_time = max(0, sleep_until - time.time())
                logger.debug(f"DCABot {self.bot_id}: Waiting {wait_time:.2f}s for next check/purchase.")
                await asyncio.sleep(wait_time)

            except asyncio.CancelledError:
                logger.info(f"DCABot {self.bot_id}: Logic loop cancelled.")
                break 
            except Exception as e:
                logger.exception(f"DCABot {self.bot_id}: Unhandled error in logic loop: {e}")
                await asyncio.sleep(60) # Wait before retrying

        logger.info(f"DCABot {self.bot_id}: Logic loop finished.")