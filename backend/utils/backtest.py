import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional, Type # To reference bot classes
from copy import deepcopy
import time
import os # Added for example usage path joining

# Import bot base class and specific types for simulation
from backend.bots.base_bot import BaseBot
from backend.bots.momentum_bot import MomentumBot
from backend.bots.grid_bot import GridBot # Import GridBot structure
from backend.bots.dca_bot import DCABot     # Import DCABot structure
# Import indicator utils if needed directly by the engine (or rely on bot's internal calls)
from backend.utils import indicators
# Import grid utils conditionally for GridBot simulation
try:
    from backend.utils import grid_utils
except ImportError:
    grid_utils = None # Handle case where grid_utils might not exist yet

logger = logging.getLogger(__name__)
# Configure logging for standalone testing if needed
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- Constants ---
DEFAULT_INITIAL_CAPITAL = 10000.0 # Example starting capital in quote currency
DEFAULT_COMMISSION_PERCENT = 0.001 # Example trading commission (0.1%)

# --- Backtesting Engine Class ---

class BacktestEngine:
    """
    Simulates a trading strategy over historical market data.
    """
    def __init__(
        self,
        historical_data: pd.DataFrame,
        bot_config: Dict[str, Any],
        initial_capital: float = DEFAULT_INITIAL_CAPITAL,
        commission_percent: float = DEFAULT_COMMISSION_PERCENT
    ):
        """
        Initializes the backtesting engine.

        Args:
            historical_data: DataFrame containing OHLCV data with a DatetimeIndex.
                               Columns must include 'Open', 'High', 'Low', 'Close'.
            bot_config: Configuration dictionary for the bot strategy to be tested.
                        Must include 'bot_type' and 'symbol'. Bot-specific settings
                        should be nested under a 'settings' key.
            initial_capital: Starting capital in the quote currency.
            commission_percent: Trading commission fee per trade (e.g., 0.001 for 0.1%).
        """
        if not isinstance(historical_data, pd.DataFrame) or historical_data.empty:
            raise ValueError("Historical data must be a non-empty pandas DataFrame.")
        if not isinstance(historical_data.index, pd.DatetimeIndex):
             raise ValueError("Historical data DataFrame must have a DatetimeIndex.")
        required_cols = {'Open', 'High', 'Low', 'Close'}
        if not required_cols.issubset(historical_data.columns):
            raise ValueError(f"Historical data must contain columns: {required_cols}")
        if not bot_config or 'bot_type' not in bot_config:
             raise ValueError("Bot configuration must be provided and include 'bot_type'.")
        if 'symbol' not in bot_config:
             raise ValueError("Bot configuration must include 'symbol'.")

        self.historical_data = historical_data.copy() # Work on a copy
        self.bot_config = deepcopy(bot_config) # Use a deep copy
        self.initial_capital = initial_capital
        self.commission_percent = commission_percent

        self.bot_type = self.bot_config.get("bot_type")
        self.symbol = self.bot_config.get("symbol")
        self.bot_settings = self.bot_config.get("settings", {}) # Bot specific settings

        # Simulation state
        self.current_step = 0
        self.current_time = None
        self.quote_balance = initial_capital
        self.base_balance = 0.0
        self.portfolio_value = initial_capital
        self.open_orders = [] # List to track simulated open orders {id, type, side, price, qty, quoteOrderQty}
        self.trades = [] # List to record simulated executed trades
        self.equity_curve = [] # List to track portfolio value over time [(time, value)]

        # Placeholder for simulated bot state (e.g., last indicators, position status)
        self.simulated_bot_state = {}
        self._grid_levels = None # Store grid levels if calculated

        logger.info(f"BacktestEngine initialized for {self.bot_type} on {self.symbol}. Capital: {initial_capital}, Commission: {commission_percent*100}%")


    def _get_bot_class(self) -> Optional[Type[BaseBot]]:
         """Gets the bot class based on the configured type."""
         # TODO: Use dynamic loading or a registry for scalability
         if self.bot_type == "MomentumBot":
              return MomentumBot
         elif self.bot_type == "GridBot":
              return GridBot
         elif self.bot_type == "DCABot":
              return DCABot
         # Add other bot types here
         else:
              logger.error(f"Unsupported bot_type for backtesting: {self.bot_type}")
              return None

    def _simulate_order_fill(self, order: Dict, current_candle: pd.Series):
        """
        Checks if a simulated open order should be filled based on the current candle.
        Handles basic MARKET and LIMIT order fill simulation.
        Updates balances and records trades. Returns True if filled.
        """
        order_type = order['type']
        order_side = order['side']
        order_price = order.get('price') # None for MARKET or quoteOrderQty MARKET
        order_qty = order.get('qty') # Base quantity
        order_quote_qty = order.get('quoteOrderQty') # Quote quantity (for MARKET BUY)

        fill_price = None
        filled = False
        actual_qty = order_qty # Default to base quantity

        # Simulate fill based on candle data (Open, High, Low, Close)
        candle_open = current_candle['Open']
        candle_high = current_candle['High']
        candle_low = current_candle['Low']
        # candle_close = current_candle['Close'] # Less common to fill on close in simple backtests

        if order_type == "MARKET":
             # Assume market orders fill at the opening price of the *current* candle
             # (Slightly optimistic, filling at next open is more conservative but complex)
             fill_price = candle_open
             filled = True
             if order_side == "BUY" and order_quote_qty is not None and fill_price > 0:
                 # Calculate base quantity based on quote quantity for market buys
                 actual_qty = order_quote_qty / fill_price
                 logger.debug(f"Simulating MARKET BUY (QuoteQty) fill at {fill_price}, BaseQty={actual_qty:.8f}")
             elif order_side == "BUY" and order_qty is not None:
                 logger.debug(f"Simulating MARKET BUY (BaseQty) fill at {fill_price}")
             elif order_side == "SELL" and order_qty is not None:
                 logger.debug(f"Simulating MARKET SELL fill at {fill_price}")
             else:
                 logger.warning(f"Invalid MARKET order parameters: {order}")
                 filled = False # Cannot determine quantity

        elif order_type == "LIMIT":
             if order_price is None or order_qty is None:
                 logger.warning(f"Invalid LIMIT order parameters: {order}")
                 return False # Limit orders require price and qty

             if order_side == "BUY" and candle_low <= order_price:
                  # Buy limit filled if price drops to or below limit price
                  # Assume fill at the limit price (conservative)
                  fill_price = order_price
                  filled = True
                  logger.debug(f"Simulating LIMIT BUY fill at {fill_price} (Low: {candle_low})")
             elif order_side == "SELL" and candle_high >= order_price:
                  # Sell limit filled if price rises to or above limit price
                  # Assume fill at the limit price
                  fill_price = order_price
                  filled = True
                  logger.debug(f"Simulating LIMIT SELL fill at {fill_price} (High: {candle_high})")

        # If filled, update portfolio and record trade
        if filled and fill_price is not None and actual_qty is not None and actual_qty > 0:
             cost = actual_qty * fill_price
             commission = cost * self.commission_percent

             if order_side == "BUY":
                  required_quote = cost + commission
                  if self.quote_balance >= required_quote:
                       self.quote_balance -= required_quote
                       self.base_balance += actual_qty
                       logger.debug(f"BUY Filled: Qty={actual_qty:.8f}, Price={fill_price:.2f}, Cost={cost:.2f}, Comm={commission:.4f}, QuoteBal={self.quote_balance:.2f}, BaseBal={self.base_balance:.8f}")
                  else:
                       logger.warning(f"Insufficient quote balance ({self.quote_balance:.2f}) to fill BUY order {order['id']} requiring {required_quote:.2f}. Skipping fill.")
                       return False # Cannot fill
             elif order_side == "SELL":
                  if self.base_balance >= actual_qty:
                       self.quote_balance += (cost - commission)
                       self.base_balance -= actual_qty
                       logger.debug(f"SELL Filled: Qty={actual_qty:.8f}, Price={fill_price:.2f}, Revenue={cost:.2f}, Comm={commission:.4f}, QuoteBal={self.quote_balance:.2f}, BaseBal={self.base_balance:.8f}")
                  else:
                       logger.warning(f"Insufficient base balance ({self.base_balance:.8f}) to fill SELL order {order['id']} requiring {actual_qty:.8f}. Skipping fill.")
                       return False # Cannot fill

             # Record the trade
             self.trades.append({
                  'timestamp': self.current_time,
                  'order_id': order['id'],
                  'type': order_type,
                  'side': order_side,
                  'price': fill_price,
                  'quantity': actual_qty, # Record the actual filled quantity
                  'cost': cost, # Cost for BUY, Revenue for SELL (before commission)
                  'commission': commission,
                  'quote_balance': self.quote_balance,
                  'base_balance': self.base_balance,
             })
             return True # Order was filled

        return False # Order not filled in this step


    def _process_bot_actions(self, bot_instance: BaseBot, data_slice: pd.DataFrame):
        """
        Simulates the bot's decision-making process for the current data slice.
        This needs to adapt the bot's async logic to a synchronous simulation step.
        It calls simulated versions of the bot's methods or directly implements
        the strategy logic based on the bot_config and data_slice.
        Returns a list of actions (e.g., new orders to place).
        """
        # This is highly dependent on the bot's structure.
        # Option 1: Instantiate the bot and call its methods (tricky with async)
        # Option 2: Re-implement the core strategy logic here based on config.

        # --- Option 2 Example (Re-implementing simplified logic) ---
        new_orders = []
        cancel_orders = [] # IDs of orders to cancel (Not implemented in this example)

        # Get latest candle/data point
        if data_slice.empty: return new_orders, cancel_orders
        latest_candle = data_slice.iloc[-1]
        current_price = latest_candle['Close'] # Use close price for decisions

        # --- Momentum Bot Simulation Logic (Example) ---
        if self.bot_type == "MomentumBot":
             # Calculate indicators on the data slice
             try:
                  # Access settings safely using bot_instance attributes or self.bot_settings
                  rsi_period = getattr(bot_instance, 'rsi_period', self.bot_settings.get('rsi_period', 14))
                  macd_fast = getattr(bot_instance, 'macd_fast', self.bot_settings.get('macd_fast', 12))
                  macd_slow = getattr(bot_instance, 'macd_slow', self.bot_settings.get('macd_slow', 26))
                  macd_signal = getattr(bot_instance, 'macd_signal', self.bot_settings.get('macd_signal', 9))
                  order_quantity = getattr(bot_instance, 'order_quantity', self.bot_settings.get('order_quantity'))
                  if order_quantity is None:
                      logger.error("MomentumBot backtest: 'order_quantity' not found in settings.")
                      return [], []

                  rsi = indicators.calculate_rsi(data_slice['Close'], rsi_period)
                  macd_df = indicators.calculate_macd(data_slice['Close'], macd_fast, macd_slow, macd_signal)

                  if rsi.empty or macd_df.empty:
                      logger.debug(f"Not enough data for indicators at step {self.current_step}")
                      return [], []

                  latest_rsi = rsi.iloc[-1]
                  latest_macd = macd_df['MACD'].iloc[-1]
                  latest_signal = macd_df['Signal'].iloc[-1]

                  # Get previous values for crossover check (requires storing state)
                  prev_macd = self.simulated_bot_state.get('last_indicators', {}).get('macd')
                  prev_signal = self.simulated_bot_state.get('last_indicators', {}).get('macd_signal')

                  # Update simulated state
                  self.simulated_bot_state['last_indicators'] = {'macd': latest_macd, 'macd_signal': latest_signal, 'rsi': latest_rsi}

                  # Simple Crossover Logic (ignoring RSI/EMA for brevity in this example)
                  buy_signal = latest_macd > latest_signal and (prev_macd is not None and prev_macd <= prev_signal)
                  sell_signal = latest_macd < latest_signal and (prev_macd is not None and prev_macd >= prev_signal)

                  position_open = self.simulated_bot_state.get('position_open', False)

                  if buy_signal and not position_open:
                       logger.info(f"Backtest: {self.current_time} - Momentum BUY signal triggered (MACD cross).")
                       # Use base quantity for momentum bot orders
                       new_orders.append({'type': 'MARKET', 'side': 'BUY', 'qty': order_quantity, 'id': f'sim_buy_{self.current_step}'})
                       self.simulated_bot_state['position_open'] = True
                  elif sell_signal and position_open:
                       logger.info(f"Backtest: {self.current_time} - Momentum SELL signal triggered (MACD cross).")
                       # Ensure we sell the quantity we bought (or manage position size)
                       # For simplicity, assume selling the same fixed quantity
                       new_orders.append({'type': 'MARKET', 'side': 'SELL', 'qty': order_quantity, 'id': f'sim_sell_{self.current_step}'})
                       self.simulated_bot_state['position_open'] = False

             except Exception as e:
                  logger.warning(f"Backtest: Error calculating Momentum indicators at step {self.current_step}: {e}")

        # --- Grid Bot Simulation Logic (Example) ---
        elif self.bot_type == "GridBot":
             # Grid bot logic mainly involves checking existing limit orders against price
             # and placing new ones when one fills. This is handled in _simulate_order_fill
             # and the main loop's order management (placing opposing orders).
             # Initial grid setup is simulated before the loop starts in run().
             pass # No new orders generated here, only reacting to fills

        # --- DCA Bot Simulation Logic (Example) ---
        elif self.bot_type == "DCABot":
             # Access settings safely
             purchase_amount = getattr(bot_instance, 'purchase_amount', self.bot_settings.get('purchase_amount'))
             purchase_frequency_hours = getattr(bot_instance, 'purchase_frequency_hours', self.bot_settings.get('purchase_frequency_hours'))
             if purchase_amount is None or purchase_frequency_hours is None:
                 logger.error("DCABot backtest: 'purchase_amount' or 'purchase_frequency_hours' not found in settings.")
                 return [], []

             # Check if it's time for a scheduled purchase
             now_ts = self.current_time.timestamp()
             next_purchase_ts = self.simulated_bot_state.get('next_purchase_time')

             if next_purchase_ts is None: # First step
                  logger.info(f"Backtest: {self.current_time} - DCA Initial purchase.")
                  # Use quoteOrderQty for DCA market buys
                  new_orders.append({'type': 'MARKET', 'side': 'BUY', 'quoteOrderQty': purchase_amount, 'id': f'sim_dca_{self.current_step}'})
                  self.simulated_bot_state['last_purchase_time'] = now_ts
                  self.simulated_bot_state['next_purchase_time'] = now_ts + (purchase_frequency_hours * 3600)
             elif now_ts >= next_purchase_ts:
                  logger.info(f"Backtest: {self.current_time} - DCA Scheduled purchase.")
                  new_orders.append({'type': 'MARKET', 'side': 'BUY', 'quoteOrderQty': purchase_amount, 'id': f'sim_dca_{self.current_step}'})
                  self.simulated_bot_state['last_purchase_time'] = now_ts
                  # Schedule next one based on *this* purchase time
                  self.simulated_bot_state['next_purchase_time'] = now_ts + (purchase_frequency_hours * 3600)

        # TODO: Add logic for other bot types

        return new_orders, cancel_orders


    def run(self):
        """Runs the backtest simulation step-by-step."""
        start_time = time.time()
        logger.info(f"Starting backtest run for {self.bot_type} on {self.symbol}...")

        BotClass = self._get_bot_class()
        if not BotClass:
            logger.error(f"Cannot run backtest: Bot class for type '{self.bot_type}' not found.")
            return None

        # Instantiate a 'dummy' bot instance just to access its config/parameters easily
        # We don't use its async methods directly in the simulation loop.
        # A mock client is sufficient here as we won't make real API calls.
        mock_binance_client = None # Or a simple mock object if needed by __init__
        try:
            # Pass only the necessary parts of the config if the real bot expects them
            sim_bot_instance = BotClass(bot_id="backtest_sim", user_id="backtest_user", config=self.bot_config, binance_client=mock_binance_client)
        except Exception as e:
            logger.exception(f"Failed to instantiate simulated bot {self.bot_type}: {e}")
            return None

        # --- Initial Setup Simulation (e.g., for Grid Bot) ---
        if self.bot_type == "GridBot":
             logger.info("Simulating Grid Bot initial setup...")
             if grid_utils is None:
                 logger.error("Grid Bot backtest: 'backend.utils.grid_utils' not found or failed to import. Cannot simulate grid setup.")
                 return None
             try:
                 # Access settings safely
                 lower_price = getattr(sim_bot_instance, 'lower_price', self.bot_settings.get('lower_price'))
                 upper_price = getattr(sim_bot_instance, 'upper_price', self.bot_settings.get('upper_price'))
                 num_grids = getattr(sim_bot_instance, 'num_grids', self.bot_settings.get('num_grids'))
                 grid_type = getattr(sim_bot_instance, 'grid_type', self.bot_settings.get('grid_type', 'arithmetic'))
                 total_investment = getattr(sim_bot_instance, 'total_investment', self.bot_settings.get('total_investment')) # Needs quote amount

                 if None in [lower_price, upper_price, num_grids, total_investment]:
                     logger.error("Grid Bot backtest: Missing required settings (lower_price, upper_price, num_grids, total_investment).")
                     return None

                 # Calculate levels based on the *first* available price
                 initial_price = self.historical_data['Close'].iloc[0]
                 if grid_type == "geometric":
                      self._grid_levels = grid_utils.calculate_geometric_grid_levels(lower_price, upper_price, num_grids)
                 else:
                      self._grid_levels = grid_utils.calculate_arithmetic_grid_levels(lower_price, upper_price, num_grids)

                 if self._grid_levels:
                      # Estimate initial buy levels to calculate quantity
                      temp_buy_levels = [lvl for lvl in self._grid_levels if lvl < initial_price]
                      # Use total_investment (quote) to determine base quantity per grid
                      # This calculation might need refinement depending on how total_investment is used (full capital or portion)
                      # Assuming total_investment is the quote amount to allocate across buy grids initially
                      num_buy_grids = len(temp_buy_levels) if len(temp_buy_levels) > 0 else 1 # Avoid division by zero
                      quote_per_buy_grid = total_investment / num_buy_grids
                      # Calculate base qty based on the lowest buy grid price (most conservative)
                      lowest_buy_price = min(temp_buy_levels) if temp_buy_levels else lower_price
                      qty_per_grid = quote_per_buy_grid / lowest_buy_price if lowest_buy_price > 0 else 0
                      # Alternative: Calculate based on average price or use a fixed base qty setting

                      # qty_per_grid = grid_utils.calculate_order_size_per_grid(total_investment, len(buy_levels), initial_price) # Original needs review

                      if qty_per_grid and qty_per_grid > 0:
                           buy_levels = [lvl for lvl in self._grid_levels if lvl < initial_price]
                           sell_levels = [lvl for lvl in self._grid_levels if lvl > initial_price]
                           for level in buy_levels:
                                self.open_orders.append({'id': f'sim_grid_buy_{level:.4f}', 'type': 'LIMIT', 'side': 'BUY', 'price': level, 'qty': qty_per_grid})
                           for level in sell_levels:
                                self.open_orders.append({'id': f'sim_grid_sell_{level:.4f}', 'type': 'LIMIT', 'side': 'SELL', 'price': level, 'qty': qty_per_grid})
                           logger.info(f"Simulated initial grid: {len(buy_levels)} buys, {len(sell_levels)} sells, Qty/Grid: {qty_per_grid:.8f}")
                           # Adjust initial capital - assume investment amount is used for grid setup
                           # This needs clarification: is total_investment deducted from initial_capital?
                           # Assuming yes for now, and it's used to cover potential buys.
                           # self.quote_balance -= total_investment # Or adjust based on actual open buy orders cost
                      else:
                           logger.error("Grid Bot backtest: Failed to calculate initial quantity per grid.")
                           return None # Stop if setup fails
                 else:
                      logger.error("Grid Bot backtest: Failed to calculate initial grid levels.")
                      return None # Stop if setup fails
             except Exception as e:
                 logger.exception(f"Error during Grid Bot initial setup simulation: {e}")
                 return None


        # --- Main Simulation Loop ---
        logger.info(f"Processing {len(self.historical_data)} data points...")
        for i in range(len(self.historical_data)):
            self.current_step = i
            current_candle = self.historical_data.iloc[i]
            self.current_time = self.historical_data.index[i]

            # 1. Simulate Fills for Open Orders based on current candle
            # Process orders in a copy to allow adding new orders during iteration
            orders_to_process = self.open_orders[:]
            self.open_orders = [] # Reset open orders for this step
            filled_in_step = [] # Track orders filled in this specific step

            for order in orders_to_process:
                if self._simulate_order_fill(order, current_candle):
                     filled_in_step.append(order) # Mark as filled
                     # --- Grid Bot: Place opposing order on fill ---
                     if self.bot_type == "GridBot" and order['type'] == 'LIMIT':
                          filled_price = order['price']
                          if self._grid_levels: # Check if levels exist
                              qty = order['qty'] # Use the quantity of the filled order
                              try:
                                   level_index = self._grid_levels.index(filled_price)
                                   if order['side'] == 'BUY' and level_index + 1 < len(self._grid_levels):
                                        sell_price = self._grid_levels[level_index + 1]
                                        new_sell_order = {'id': f'sim_grid_sell_{sell_price:.4f}_{i}', 'type': 'LIMIT', 'side': 'SELL', 'price': sell_price, 'qty': qty}
                                        self.open_orders.append(new_sell_order) # Add new sell order
                                        logger.debug(f"Backtest: Placing opposing SELL at {sell_price:.4f} after BUY fill.")
                                   elif order['side'] == 'SELL' and level_index - 1 >= 0:
                                        buy_price = self._grid_levels[level_index - 1]
                                        new_buy_order = {'id': f'sim_grid_buy_{buy_price:.4f}_{i}', 'type': 'LIMIT', 'side': 'BUY', 'price': buy_price, 'qty': qty}
                                        self.open_orders.append(new_buy_order) # Add new buy order
                                        logger.debug(f"Backtest: Placing opposing BUY at {buy_price:.4f} after SELL fill.")
                              except ValueError:
                                   logger.warning(f"Filled price {filled_price} not found in grid levels during backtest.")
                              except Exception as e:
                                   logger.exception(f"Error placing opposing grid order during backtest: {e}")
                          else:
                              logger.warning("Grid levels not defined for placing opposing order.")
                else:
                     # Keep order if not filled
                     self.open_orders.append(order)


            # 2. Get Data Slice for Bot Logic (e.g., lookback window)
            # Bot needs enough data to calculate its indicators
            # Use kline_limit from bot instance if available, else default
            lookback = getattr(sim_bot_instance, 'kline_limit', self.bot_settings.get('kline_limit', 50))
            start_index = max(0, i - lookback + 1) # Ensure start_index is not negative
            data_slice = self.historical_data.iloc[start_index : i + 1]

            # 3. Process Bot Actions based on the data slice (Generates new orders)
            new_bot_orders, cancel_bot_orders = self._process_bot_actions(sim_bot_instance, data_slice)

            # 4. Update Open Orders List
            # Add new orders generated by the bot in this step
            self.open_orders.extend(new_bot_orders)
            # Remove cancelled orders (if cancel logic implemented)
            # self.open_orders = [o for o in self.open_orders if o['id'] not in cancel_bot_orders]


            # 5. Update Portfolio Value and Equity Curve
            current_price = current_candle['Close'] # Use close price for valuation
            self.portfolio_value = self.quote_balance + (self.base_balance * current_price)
            self.equity_curve.append((self.current_time, self.portfolio_value))

            # Log progress periodically
            if (i + 1) % 1000 == 0 or i == len(self.historical_data) - 1:
                 logger.info(f"Backtest Step: {i+1}/{len(self.historical_data)}, Time: {self.current_time}, Portfolio Value: {self.portfolio_value:.2f}, Open Orders: {len(self.open_orders)}")


        # --- End of Simulation ---
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Backtest finished in {duration:.2f} seconds.")

        # Cancel any remaining open orders at the end (optional simulation step)
        # logger.info(f"Cancelling {len(self.open_orders)} remaining open orders at end of backtest.")
        # self.open_orders = []

        # Calculate final results
        results = self._calculate_results()
        results["simulation_duration_seconds"] = duration # Add simulation time
        return results


    def _calculate_results(self) -> Dict[str, Any]:
        """Calculates performance metrics based on the simulation."""
        logger.info("Calculating backtest results...")

        if not self.equity_curve:
             logger.warning("Equity curve is empty, cannot calculate performance metrics.")
             return {"error": "No simulation steps completed."}

        final_value = self.portfolio_value
        total_return = final_value - self.initial_capital
        total_return_percent = (total_return / self.initial_capital) * 100 if self.initial_capital else 0

        num_trades = len(self.trades)
        commission_paid = sum(t['commission'] for t in self.trades)

        # --- Advanced Metrics (Placeholders - require more detailed calculation) ---
        sharpe_ratio = None
        max_drawdown = None
        win_rate = None

        if num_trades > 0:
            # Win Rate Calculation (Simplified: based on positive PnL per trade)
            wins = 0
            trade_pnl = []
            # Need to properly track entry/exit for PnL calculation per trade cycle
            # This simplified version just looks at individual trade revenue vs cost
            for trade in self.trades:
                pnl = 0
                if trade['side'] == 'SELL':
                    pnl = trade['cost'] - trade['commission'] # Revenue - commission
                    # Need entry cost to calculate actual profit
                elif trade['side'] == 'BUY':
                    pnl = -(trade['cost'] + trade['commission']) # Cost
                    # Need exit revenue to calculate actual profit
                # A better approach tracks positions:
                # 1. Identify entry trades (BUYs or initial SELLs for shorting)
                # 2. Identify corresponding exit trades
                # 3. Calculate PnL for each closed position cycle
                # For now, win_rate remains None

            # Max Drawdown Calculation
            equity_values = pd.Series([val for _, val in self.equity_curve])
            rolling_max = equity_values.cummax()
            drawdown = (equity_values - rolling_max) / rolling_max
            max_drawdown = drawdown.min() * 100 if not drawdown.empty else 0 # In percent

            # Sharpe Ratio Calculation (Simplified: assumes risk-free rate = 0)
            # Requires daily/periodic returns
            equity_df = pd.DataFrame(self.equity_curve, columns=['Timestamp', 'Value']).set_index('Timestamp')
            returns = equity_df['Value'].pct_change().dropna()
            if not returns.empty and returns.std() != 0:
                 # Assuming daily returns for annualization (adjust factor if data freq differs)
                 annualization_factor = np.sqrt(252) if pd.infer_freq(equity_df.index) == 'D' else np.sqrt(252*24) # Approx for hourly
                 sharpe_ratio = (returns.mean() / returns.std()) * annualization_factor


        results = {
            "start_date": self.equity_curve[0][0] if self.equity_curve else None,
            "end_date": self.equity_curve[-1][0] if self.equity_curve else None,
            "duration_days": (self.equity_curve[-1][0] - self.equity_curve[0][0]).days if self.equity_curve else 0,
            "initial_capital": self.initial_capital,
            "final_portfolio_value": final_value,
            "total_return": total_return,
            "total_return_percent": total_return_percent,
            "total_trades": num_trades,
            "commission_paid": commission_paid,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown_percent": max_drawdown,
            "win_rate_percent": win_rate, # Placeholder
            "simulation_duration_seconds": None, # Will be added by run() method
            "trades": self.trades, # Include detailed trades list
            "equity_curve": self.equity_curve # Include equity curve data
        }

        logger.info(f"Backtest Results: Return={total_return_percent:.2f}%, Trades={num_trades}, Final Value={final_value:.2f}, Max Drawdown={max_drawdown:.2f}%")
        return results


# --- Example Usage ---
if __name__ == "__main__":
    # Configure logging for the example
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # This requires sample historical data (e.g., from a CSV or fetched via historical.py)
    # And a sample bot configuration.

    # 1. Load Sample Data (replace with actual data loading)
    sample_data = None
    try:
         # Option A: Load from Parquet (if created by historical.py)
         # cache_dir = os.path.join(os.path.dirname(__file__), '..', 'cache') # Example cache dir relative to utils
         # sample_data_path = os.path.join(cache_dir, 'BTCUSDT_1h_2023-01-01_2023-03-31.parquet')
         # if os.path.exists(sample_data_path):
         #     logger.info(f"Loading sample data from: {sample_data_path}")
         #     sample_data = pd.read_parquet(sample_data_path)
         # else:
         #     logger.warning(f"Sample data file not found at {sample_data_path}. Using dummy data.")

         # Option B: Create dummy data for structure testing:
         if sample_data is None:
             logger.warning("Using dummy data for backtest example.")
             dates = pd.date_range(start='2023-01-01', periods=1000, freq='1h') # More data points
             price_changes = np.random.randn(1000) * 50 # Price fluctuations
             close_prices = 50000 + price_changes.cumsum()
             # Ensure prices don't go below zero
             close_prices = np.maximum(close_prices, 1000)
             # Simulate OHLC based on Close
             open_prices = close_prices - price_changes
             high_prices = np.maximum(open_prices, close_prices) + np.random.rand(1000) * 100
             low_prices = np.minimum(open_prices, close_prices) - np.random.rand(1000) * 100
             low_prices = np.maximum(low_prices, 500) # Ensure low is not too low

             sample_data = pd.DataFrame({
                 'Open': open_prices,
                 'High': high_prices,
                 'Low': low_prices,
                 'Close': close_prices,
                 'Volume': np.random.rand(1000) * 100
             }, index=dates)
             logger.info("Dummy Data Head:\n" + str(sample_data.head()))
             logger.info("Dummy Data Tail:\n" + str(sample_data.tail()))


    except FileNotFoundError:
         logger.error("Sample data file not found. Cannot run backtest example.")
    except Exception as e:
         logger.exception(f"Error loading or generating sample data: {e}")


    if sample_data is not None:
        # 2. Define Bot Configuration (Example: Momentum Bot)
        momentum_config = {
            "bot_type": "MomentumBot",
            "symbol": "BTCUSDT", # Ensure matches data symbol
            "settings": {
                "interval": "1h", # Ensure matches data interval
                "rsi_period": 14,
                "macd_fast": 12,
                "macd_slow": 26,
                "macd_signal": 9,
                "ema_short_period": 9, # Not used in simplified logic above, but part of config
                "ema_long_period": 21, # Not used in simplified logic above
                "order_quantity": 0.001 # Base quantity for orders
            }
        }

        # Example: DCA Bot Config
        dca_config = {
            "bot_type": "DCABot",
            "symbol": "ETHUSDT", # Use a different symbol for clarity if needed
            "settings": {
                "interval": "1h", # Data interval
                "purchase_amount": 100.0, # Quote currency amount per purchase
                "purchase_frequency_hours": 24 # Buy once a day
            }
        }

        # Example: Grid Bot Config
        grid_config = {
            "bot_type": "GridBot",
            "symbol": "BNBBTC",
            "settings": {
                "interval": "1h",
                "lower_price": 0.005,
                "upper_price": 0.010,
                "num_grids": 10,
                "grid_type": "arithmetic", # or "geometric"
                "total_investment": 0.1 # Quote currency (e.g., BTC) to allocate
            }
        }


        # --- Select which bot to test ---
        test_config = momentum_config
        # test_config = dca_config
        # test_config = grid_config

        # 3. Initialize and Run Engine
        try:
             logger.info(f"\n--- Running Backtest for: {test_config['bot_type']} ---")
             engine = BacktestEngine(
                 historical_data=sample_data,
                 bot_config=test_config,
                 initial_capital=10000.0,
                 commission_percent=0.001
             )
             results = engine.run()

             if results and "error" not in results:
                  logger.info("\n--- Backtest Results Summary ---")
                  for key, value in results.items():
                       if key not in ['trades', 'equity_curve']: # Don't print large lists
                            if isinstance(value, float):
                                logger.info(f"{key}: {value:.4f}")
                            else:
                                logger.info(f"{key}: {value}")

                  # Optional: Plot equity curve or save results
                  try:
                      import matplotlib.pyplot as plt
                      equity_df = pd.DataFrame(results['equity_curve'], columns=['Timestamp', 'Value']).set_index('Timestamp')
                      equity_df['Value'].plot(title=f"{test_config['bot_type']} Equity Curve", grid=True)
                      plt.ylabel("Portfolio Value (Quote)")
                      plt.xlabel("Date")
                      plt.tight_layout()
                      # Construct filename based on bot type and date range
                      start_date_str = results['start_date'].strftime('%Y%m%d') if results['start_date'] else 'nodate'
                      end_date_str = results['end_date'].strftime('%Y%m%d') if results['end_date'] else 'nodate'
                      plot_filename = f"backtest_{test_config['bot_type']}_{test_config['symbol']}_{start_date_str}_{end_date_str}.png"
                      # Save plot in the same directory as the script for simplicity
                      plot_path = os.path.join(os.path.dirname(__file__), plot_filename)
                      plt.savefig(plot_path)
                      logger.info(f"Equity curve plot saved to: {plot_path}")
                      # plt.show() # Uncomment to display plot interactively
                      plt.close() # Close plot window
                  except ImportError:
                      logger.warning("Matplotlib not installed. Cannot plot equity curve. Run: pip install matplotlib")
                  except Exception as plot_err:
                      logger.error(f"Error generating or saving plot: {plot_err}")

             elif results and "error" in results:
                 logger.error(f"Backtest failed: {results['error']}")
             else:
                 logger.error("Backtest run returned None.")

        except ValueError as ve:
             logger.error(f"Configuration or Data Error: {ve}")
        except Exception as e:
             logger.exception(f"Error running backtest engine: {e}")