import pandas as pd
import pandas_ta as ta # Added for technical indicators
import numpy as np # Added for grid calculation
from typing import List, Dict, Any, Optional
from backend.schemas.bot_config import BotConfig
from backend.backtesting.metrics import calculate_metrics
from pydantic import BaseModel
import math # Added for checking NaN

# Schemas (KLine, Trade, BacktestResult) are now defined in backend.schemas.backtest
from backend.schemas.backtest import KLine, Trade, BacktestResult

def run_backtest(
    bot_config: BotConfig,
    historical_data: pd.DataFrame, # Or List[KLine]
    initial_capital: float
) -> BacktestResult:
    """
    Runs a backtest simulation for a given bot configuration and historical data.

    Args:
        bot_config: The configuration of the bot to backtest.
        historical_data: DataFrame or list of KLine data for the backtest period.
        initial_capital: The starting capital for the simulation.

    Returns:
        A BacktestResult object containing performance metrics and simulated trades.
    """
    print(f"Running backtest for bot: {bot_config.name} ({bot_config.bot_type})")
    print(f"Initial capital: {initial_capital}")
    print(f"Historical data points: {len(historical_data)}")

    # --- Simulation Core Logic ---
    # 1. Initialize simulation state
    balance = initial_capital
    position_quantity = 0.0  # Quantity of the base asset held
    equity_curve = []
    trades: List[Trade] = []
    # Track average entry price for strategies like DCA/Grid
    average_entry_price = 0.0
    # Remove simple open_trade, manage position directly
    # open_trade: Optional[Trade] = None

    # Add initial equity point - handle potential empty data
    if not historical_data.empty:
        start_timestamp = historical_data.iloc[0]['timestamp']
        equity_curve.append({'timestamp': start_timestamp, 'equity': initial_capital})
        # Initialize last_price for grid bot
        last_price = historical_data.iloc[0]['close']
    else:
        # Handle case with no historical data
        return BacktestResult(metrics=calculate_metrics([], [], initial_capital), trades=[], equity_curve=[])


    # 2. Initialize bot-specific parameters or state if needed
    bot_params = bot_config.parameters
    # --- Bot-Specific Initialization ---
    grid_levels = []
    grid_states = {} # {level_price: 'empty'/'bought'}
    last_buy_timestamp = -1 # For DCA

    if bot_config.bot_type == "Grid":
        lower = bot_params['lower_bound']
        upper = bot_params['upper_bound']
        n_grids = bot_params['num_grids']
        if n_grids > 1:
            grid_levels = np.linspace(lower, upper, n_grids).tolist()
            for level in grid_levels:
                grid_states[level] = 'empty' # Initially no positions at any level
            print(f"Grid Levels Initialized: {grid_levels}")
        else:
            print("Warning: num_grids <= 1, GridBot simulation might not work as expected.")

    elif bot_config.bot_type == "DCA":
        # Initialize last_buy_timestamp to allow immediate buy if condition met on first kline
        if not historical_data.empty:
             # Start potentially buying from the first kline
             last_buy_timestamp = historical_data.iloc[0]['timestamp'] - (bot_params['buy_interval_seconds'] * 1000)
        print(f"DCA Initialized. Last buy timestamp: {last_buy_timestamp}")

    # 3. Iterate through historical data (k-lines)
    print(f"Starting simulation loop...")
    for index, kline in historical_data.iterrows():
        current_price = kline['close']
        current_timestamp = kline['timestamp']
        # Ensure we have enough data for indicators
        if index < bot_params.get('ema_long_period', 26) and bot_config.bot_type == "Momentum": # Min lookback needed
             # Update equity curve even if skipping trade logic
            current_equity = balance + (position_quantity * current_price)
            equity_curve.append({'timestamp': current_timestamp, 'equity': current_equity})
            if bot_config.bot_type == "Grid": # Update last price for grid even if skipping
                last_price = current_price
            continue # Skip until enough data

        data_so_far = historical_data.iloc[:index+1] # Data up to current point

        # --- Bot-Specific Logic ---
        signal = None # 'BUY', 'SELL', 'CLOSE', None
        trade_quantity = 0.0 # Quantity for this potential trade
        order_cost = 0.0 # Cost for BUY, proceeds for SELL

        if bot_config.bot_type == "Momentum":
            # --- Momentum Bot Simulation ---
            try:
                # a. Calculate indicators
                rsi_period = bot_params.get('rsi_period', 14)
                rsi_oversold = bot_params.get('rsi_oversold', 30)
                rsi_overbought = bot_params.get('rsi_overbought', 70)
                macd_fast = bot_params.get('macd_fast', 12)
                macd_slow = bot_params.get('macd_slow', 26)
                macd_signal_p = bot_params.get('macd_signal', 9)
                ema_short_period = bot_params.get('ema_short_period', 9)
                ema_long_period = bot_params.get('ema_long_period', 21)
                order_qty = bot_params.get('order_quantity', 0) # Get order quantity

                # Use pandas_ta
                data_so_far.ta.rsi(length=rsi_period, append=True)
                data_so_far.ta.macd(fast=macd_fast, slow=macd_slow, signal=macd_signal_p, append=True)
                data_so_far.ta.ema(length=ema_short_period, append=True)
                data_so_far.ta.ema(length=ema_long_period, append=True)

                # Get latest indicator values (handle potential NaN)
                latest_rsi = data_so_far[f'RSI_{rsi_period}'].iloc[-1]
                latest_macd_line = data_so_far[f'MACD_{macd_fast}_{macd_slow}_{macd_signal_p}'].iloc[-1]
                latest_macd_signal = data_so_far[f'MACDs_{macd_fast}_{macd_slow}_{macd_signal_p}'].iloc[-1]
                latest_ema_short = data_so_far[f'EMA_{ema_short_period}'].iloc[-1]
                latest_ema_long = data_so_far[f'EMA_{ema_long_period}'].iloc[-1]

                # Check for NaN before generating signals
                if not any(math.isnan(x) for x in [latest_rsi, latest_macd_line, latest_macd_signal, latest_ema_short, latest_ema_long]):
                    # b. Generate signal
                    buy_condition = (latest_rsi < rsi_oversold and
                                     latest_macd_line > latest_macd_signal and
                                     latest_ema_short > latest_ema_long and
                                     position_quantity == 0) # Only buy if flat

                    sell_condition = ((latest_rsi > rsi_overbought or latest_ema_short < latest_ema_long) and
                                      position_quantity > 0) # Only sell if holding position

                    if buy_condition:
                        signal = 'BUY'
                        trade_quantity = order_qty
                    elif sell_condition:
                        signal = 'SELL'
                        trade_quantity = position_quantity # Sell entire position

            except Exception as e:
                print(f"Error calculating Momentum indicators at index {index}: {e}")
                # Optionally skip this kline or handle error differently
                pass

        elif bot_config.bot_type == "Grid":
            # --- Grid Bot Simulation ---
            order_qty_per_grid = bot_params.get('order_quantity', 0)
            if order_qty_per_grid > 0 and grid_levels:
                # Check crossings
                for level in sorted(grid_levels): # Process lower levels first for buys, higher for sells
                    # Cross Down (Buy Trigger)
                    if last_price > level >= current_price and grid_states[level] == 'empty':
                        if balance >= order_qty_per_grid * current_price:
                            signal = 'BUY'
                            trade_quantity = order_qty_per_grid
                            grid_states[level] = 'bought' # Mark level as bought
                            print(f"Grid BUY triggered at level {level:.2f} (Price: {current_price:.2f})")
                            break # Process one trade per kline for simplicity

                    # Cross Up (Sell Trigger) - Sell the quantity bought at the level below
                    elif last_price < level <= current_price and grid_states[level] == 'empty':
                         # Find the nearest bought level below this sell level
                         bought_levels_below = [lvl for lvl, state in grid_states.items() if state == 'bought' and lvl < level]
                         if bought_levels_below:
                             # Simplification: Sell one grid's quantity if *any* lower level was bought
                             if position_quantity >= order_qty_per_grid:
                                 signal = 'SELL'
                                 trade_quantity = order_qty_per_grid
                                 # Mark the highest bought level below as empty again (simplification)
                                 level_to_reset = max(bought_levels_below)
                                 grid_states[level_to_reset] = 'empty'
                                 print(f"Grid SELL triggered at level {level:.2f} (Price: {current_price:.2f}), resetting level {level_to_reset:.2f}")
                                 break # Process one trade per kline

            last_price = current_price # Update last price for next iteration

        elif bot_config.bot_type == "DCA":
            # --- DCA Bot Simulation ---
            interval_ms = bot_params['buy_interval_seconds'] * 1000
            order_amount = bot_params['order_amount_quote']

            # a. Check if it's time for a DCA buy
            if current_timestamp - last_buy_timestamp >= interval_ms:
                # b. If yes and enough balance, generate BUY signal
                if balance >= order_amount:
                    signal = 'BUY'
                    trade_quantity = order_amount / current_price
                    last_buy_timestamp = current_timestamp # Update last buy time
                    print(f"DCA BUY triggered at {pd.to_datetime(current_timestamp, unit='ms')}")
                # else: # Not enough balance, maybe log or just skip
                #    print(f"DCA interval reached, but insufficient balance ({balance:.2f} < {order_amount})")

        # --- Simulate Order Execution ---
        if signal == 'BUY' and balance > 0 and trade_quantity > 0:
            order_cost = trade_quantity * current_price
            if balance >= order_cost:
                # Update average entry price before changing position_quantity
                if position_quantity + trade_quantity > 1e-9: # Avoid division by zero
                    new_total_cost = (average_entry_price * position_quantity) + order_cost
                    average_entry_price = new_total_cost / (position_quantity + trade_quantity)
                else:
                     average_entry_price = current_price # First buy

                balance -= order_cost
                position_quantity += trade_quantity
                print(f"{pd.to_datetime(current_timestamp, unit='ms')} - BUY {trade_quantity:.8f} @ {current_price:.2f}, Cost: {order_cost:.2f}, Balance: {balance:.2f}, Pos Qty: {position_quantity:.8f}, Avg Entry: {average_entry_price:.2f}")

                # Record entry trade immediately for BUY signal
                # Note: PnL is calculated only when position is closed/reduced by a SELL
                trades.append(Trade(
                    entry_timestamp=current_timestamp,
                    entry_price=current_price, # Price of this specific buy
                    quantity=trade_quantity,
                    side='BUY',
                    avg_entry_price=average_entry_price # Store avg price at time of trade
                ))

        elif signal == 'SELL' and position_quantity > 0 and trade_quantity > 0:
            sell_quantity = min(position_quantity, trade_quantity) # Ensure we don't sell more than we have
            proceeds = sell_quantity * current_price

            # Calculate PnL for this sell portion based on average entry price
            pnl = (current_price - average_entry_price) * sell_quantity

            balance += proceeds
            position_quantity -= sell_quantity
            print(f"{pd.to_datetime(current_timestamp, unit='ms')} - SELL {sell_quantity:.8f} @ {current_price:.2f}, Proceeds: {proceeds:.2f}, PnL: {pnl:.2f}, Balance: {balance:.2f}, Pos Qty: {position_quantity:.8f}")

            # Record the sell trade details - Find corresponding BUYs to close?
            # Simplification: Record a single SELL trade event. PnL reflects the profit/loss
            # for the quantity sold based on the running average entry price.
            # We need to link sells to buys for accurate per-trade metrics later if needed.
            # For now, store the sell event and its PnL.
            trades.append(Trade(
                entry_timestamp=current_timestamp, # Timestamp of the sell action
                entry_price=current_price,        # Price of the sell action
                exit_timestamp=current_timestamp, # Sell is an exit in this context
                exit_price=current_price,
                quantity=sell_quantity,
                pnl=pnl,
                side='SELL', # Indicate this record is a sell action
                avg_entry_price=average_entry_price # Avg price *before* this sell
            ))

            # If position fully closed, reset average entry price
            if position_quantity < 1e-9: # Use tolerance for float comparison
                average_entry_price = 0.0
                position_quantity = 0.0 # Clean up small residuals

        # Removed explicit 'CLOSE' signal handling, as SELL logic now handles position reduction/closure

        # --- Update Equity Curve ---
        current_equity = balance + (position_quantity * current_price)
        equity_curve.append({'timestamp': current_timestamp, 'equity': current_equity})


        # last_price update moved into Grid Bot logic section

    # --- End of Simulation Loop ---
    print("Simulation loop finished.")

    # Mark-to-market for any remaining position at the end
    if position_quantity > 1e-9:
        last_price = historical_data.iloc[-1]['close']
        last_timestamp = historical_data.iloc[-1]['timestamp']
        print(f"Marking remaining position ({position_quantity:.8f}) to market at final price {last_price:.2f}")

        # Calculate unrealized PnL based on average entry price
        unrealized_pnl = (last_price - average_entry_price) * position_quantity
        final_equity = balance + (position_quantity * last_price)

        # Record a final "trade" representing the closing of the position for metrics
        trades.append(Trade(
            entry_timestamp=last_timestamp, # Use last timestamp
            entry_price=average_entry_price, # Use average entry
            exit_timestamp=last_timestamp,
            exit_price=last_price,
            quantity=position_quantity,
            pnl=unrealized_pnl,
            side='CLOSE', # Special side for end-of-backtest close
            avg_entry_price=average_entry_price
        ))
        balance = final_equity # Update balance to reflect final equity
        position_quantity = 0.0
        print(f"Final Equity after mark-to-market: {final_equity:.2f}")
    else:
        final_equity = balance # No position, final equity is just balance
    # 4. Calculate performance metrics
    print("Calculating performance metrics...")
    # The current metrics function might need adjustment to handle the new trade format
    # (e.g., differentiate BUY/SELL entries vs. PnL records)
    # For now, pass all trades.
    metrics = calculate_metrics(trades, equity_curve, initial_capital)

    # 5. Return results
    print("Backtest complete.")
    return BacktestResult(metrics=metrics, trades=trades, equity_curve=equity_curve)


# --- Helper functions (e.g., for indicator calculation) can be added here ---
# Indicator calculations are now inline using pandas_ta