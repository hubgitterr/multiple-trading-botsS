import asyncio
import logging
import pandas as pd
from typing import Dict, Any, Optional

# Import base class and utilities
from backend.bots.base_bot import BaseBot
from backend.utils.binance_client import BinanceAPIClient
from backend.utils import indicators # Import our indicator functions
from binance import Client as BinanceLibClient # For interval constants

# Configure logging for this specific bot type
logger = logging.getLogger(f"bot.{__name__}")
# Ensure root logger is configured elsewhere

class MomentumBot(BaseBot):
    """
    A trading bot that implements a momentum strategy based on technical indicators.
    """
    def __init__(self, bot_id: str, user_id: str, config: Dict[str, Any], binance_client: BinanceAPIClient):
        super().__init__(bot_id, user_id, config, binance_client)
        
        # --- Strategy Specific Configuration ---
        # Extract parameters from config with defaults
        self.interval = self.config.get("settings", {}).get("interval", BinanceLibClient.KLINE_INTERVAL_1HOUR)
        self.rsi_period = self.config.get("settings", {}).get("rsi_period", 14)
        self.rsi_oversold = self.config.get("settings", {}).get("rsi_oversold", 30)
        self.rsi_overbought = self.config.get("settings", {}).get("rsi_overbought", 70)
        self.macd_fast = self.config.get("settings", {}).get("macd_fast", 12)
        self.macd_slow = self.config.get("settings", {}).get("macd_slow", 26)
        self.macd_signal = self.config.get("settings", {}).get("macd_signal", 9)
        self.ema_short_period = self.config.get("settings", {}).get("ema_short_period", 9)
        self.ema_long_period = self.config.get("settings", {}).get("ema_long_period", 21)
        self.order_quantity = self.config.get("settings", {}).get("order_quantity", 0.001) # Example quantity
        self.kline_limit = max(self.macd_slow, self.ema_long_period) + self.macd_signal + 5 # Ensure enough data for indicators

        # --- Strategy Specific State ---
        self.state['position_open'] = False # Is there an active position?
        self.state['last_signal'] = None # 'BUY', 'SELL', or None
        self.state['last_indicators'] = {} # Store latest indicator values

        logger.info(f"MomentumBot {self.bot_id} initialized with interval: {self.interval}, RSI: {self.rsi_period}, MACD: ({self.macd_fast},{self.macd_slow},{self.macd_signal}), EMAs: ({self.ema_short_period},{self.ema_long_period})")


    async def _fetch_and_prepare_data(self) -> Optional[pd.DataFrame]:
        """Fetches kline data and prepares it in a DataFrame."""
        try:
            klines = await self.binance_client.get_klines(
                symbol=self.symbol,
                interval=self.interval,
                limit=self.kline_limit 
            )
            if not klines or len(klines) < self.kline_limit:
                logger.warning(f"Bot {self.bot_id}: Insufficient kline data received ({len(klines)}/{self.kline_limit}).")
                return None

            # Convert to DataFrame
            cols = ["OpenTime", "Open", "High", "Low", "Close", "Volume", "CloseTime", 
                    "QuoteAssetVolume", "NumTrades", "TakerBuyBaseAssetVolume", 
                    "TakerBuyQuoteAssetVolume", "Ignore"]
            df = pd.DataFrame(klines, columns=cols)

            # Convert relevant columns to numeric
            numeric_cols = ["Open", "High", "Low", "Close", "Volume"]
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col])
            
            # Convert timestamps (optional, but good practice)
            df['OpenTime'] = pd.to_datetime(df['OpenTime'], unit='ms')
            df['CloseTime'] = pd.to_datetime(df['CloseTime'], unit='ms')
            df.set_index('CloseTime', inplace=True) # Set time as index

            return df

        except Exception as e:
            logger.exception(f"Bot {self.bot_id}: Error fetching or preparing data: {e}")
            return None


    async def _calculate_indicators(self, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Calculates required indicators based on the DataFrame."""
        if df is None or df.empty:
            return None
        try:
            close_prices = df['Close']
            
            # Calculate indicators using utility functions
            rsi = indicators.calculate_rsi(close_prices, self.rsi_period).iloc[-1]
            macd_df = indicators.calculate_macd(close_prices, self.macd_fast, self.macd_slow, self.macd_signal)
            macd = macd_df['MACD'].iloc[-1]
            signal = macd_df['Signal'].iloc[-1]
            histogram = macd_df['Histogram'].iloc[-1]
            ema_short = indicators.calculate_ema(close_prices, self.ema_short_period).iloc[-1]
            ema_long = indicators.calculate_ema(close_prices, self.ema_long_period).iloc[-1]

            indicator_values = {
                "rsi": rsi,
                "macd": macd,
                "macd_signal": signal,
                "macd_hist": histogram,
                "ema_short": ema_short,
                "ema_long": ema_long,
                "close_price": close_prices.iloc[-1] # Include last close price
            }
            self.state['last_indicators'] = indicator_values # Update state
            return indicator_values

        except Exception as e:
            logger.exception(f"Bot {self.bot_id}: Error calculating indicators: {e}")
            return None


    async def _generate_signal(self, indicators_data: Dict[str, Any]) -> Optional[str]:
        """Generates a 'BUY', 'SELL', or None signal based on indicator values."""
        if not indicators_data:
            return None

        # --- Simple Example Strategy Logic ---
        # (Replace with your desired momentum strategy)
        
        # Conditions for BUY signal (example: MACD crossover + RSI not overbought + EMA confirmation)
        macd_crossed_up = indicators_data['macd'] > indicators_data['macd_signal'] and \
                          self.state.get('last_indicators', {}).get('macd', 0) <= self.state.get('last_indicators', {}).get('macd_signal', 0) # Check previous state for crossover
        rsi_ok_buy = indicators_data['rsi'] < self.rsi_overbought
        ema_confirm_buy = indicators_data['ema_short'] > indicators_data['ema_long']

        # Conditions for SELL signal (example: MACD crossdown + RSI not oversold + EMA confirmation)
        macd_crossed_down = indicators_data['macd'] < indicators_data['macd_signal'] and \
                            self.state.get('last_indicators', {}).get('macd', 0) >= self.state.get('last_indicators', {}).get('macd_signal', 0)
        rsi_ok_sell = indicators_data['rsi'] > self.rsi_oversold
        ema_confirm_sell = indicators_data['ema_short'] < indicators_data['ema_long']

        signal = None
        if macd_crossed_up and rsi_ok_buy and ema_confirm_buy:
            signal = "BUY"
        elif macd_crossed_down and rsi_ok_sell and ema_confirm_sell:
            signal = "SELL"
            
        self.state['last_signal'] = signal # Update state
        logger.info(f"Bot {self.bot_id}: Generated signal: {signal}. Indicators: { {k: round(v, 2) if isinstance(v, float) else v for k, v in indicators_data.items()} }")
        return signal


    async def _execute_trade(self, signal: str):
        """Executes a trade based on the signal."""
        if signal == "BUY" and not self.state.get('position_open', False):
            logger.info(f"Bot {self.bot_id}: Executing BUY order.")
            order_result = await self.place_order(side="BUY", order_type="MARKET", quantity=self.order_quantity)
            if order_result: # Check if order placement was successful (or simulated)
                self.state['position_open'] = True
                # TODO: Log trade details, update PnL, etc.
                self.log_trade({"signal": "BUY", **order_result})
            else:
                 logger.error(f"Bot {self.bot_id}: Failed to execute BUY order.")
                 
        elif signal == "SELL" and self.state.get('position_open', False):
            logger.info(f"Bot {self.bot_id}: Executing SELL order (closing position).")
            order_result = await self.place_order(side="SELL", order_type="MARKET", quantity=self.order_quantity)
            if order_result:
                self.state['position_open'] = False
                # TODO: Log trade details, update PnL, etc.
                self.log_trade({"signal": "SELL", **order_result})
            else:
                 logger.error(f"Bot {self.bot_id}: Failed to execute SELL order.")
        else:
             logger.debug(f"Bot {self.bot_id}: No trade execution needed for signal '{signal}' and position state {self.state.get('position_open')}.")


    async def _run_logic(self):
        """The main logic loop for the Momentum Bot."""
        logger.info(f"MomentumBot {self.bot_id}: Starting logic loop.")
        
        # Calculate sleep time based on interval (e.g., run shortly after candle close)
        # This is a simplified approach; robust timing needs careful handling of candle close times.
        sleep_duration = 60 # Default: check every minute
        if self.interval.endswith('m'):
             sleep_duration = int(self.interval[:-1]) * 60
        elif self.interval.endswith('h'):
             sleep_duration = int(self.interval[:-1]) * 3600
        elif self.interval.endswith('d'):
             sleep_duration = int(self.interval[:-1]) * 86400
        
        # Add a small buffer to run after candle close
        run_buffer = 10 # seconds after candle close (adjust as needed)
        
        while self.is_running:
            try:
                start_time = asyncio.get_event_loop().time()
                
                # 1. Fetch Data
                data_df = await self._fetch_and_prepare_data()
                if data_df is None:
                    logger.warning(f"Bot {self.bot_id}: Failed to get data, skipping cycle.")
                    await asyncio.sleep(sleep_duration / 4) # Wait shorter time on data error
                    continue # Skip to next iteration

                # 2. Calculate Indicators
                indicators_data = await self._calculate_indicators(data_df)
                if indicators_data is None:
                    logger.warning(f"Bot {self.bot_id}: Failed to calculate indicators, skipping cycle.")
                    await asyncio.sleep(sleep_duration / 4) 
                    continue

                # 3. Generate Signal
                signal = await self._generate_signal(indicators_data)
                
                # 4. Execute Trade (if signal generated)
                if signal:
                    await self._execute_trade(signal)
                    
                # 5. Wait for next cycle
                end_time = asyncio.get_event_loop().time()
                elapsed = end_time - start_time
                wait_time = max(0, sleep_duration - elapsed + run_buffer) 
                logger.debug(f"Bot {self.bot_id}: Cycle finished in {elapsed:.2f}s. Waiting {wait_time:.2f}s for next cycle.")
                await asyncio.sleep(wait_time)

            except asyncio.CancelledError:
                logger.info(f"MomentumBot {self.bot_id}: Logic loop cancelled.")
                break # Exit loop immediately on cancellation
            except Exception as e:
                logger.exception(f"MomentumBot {self.bot_id}: Unhandled error in logic loop: {e}")
                # Decide whether to stop the bot or wait and retry
                await asyncio.sleep(60) # Wait a minute before retrying after error

        logger.info(f"MomentumBot {self.bot_id}: Logic loop finished.")