import pandas as pd
import numpy as np
import logging

# Configure logging
logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO) # Uncomment for standalone testing

def calculate_sma(data: pd.Series, window: int) -> pd.Series:
    """Calculates the Simple Moving Average (SMA)."""
    if not isinstance(data, pd.Series):
        raise ValueError("Input data must be a pandas Series.")
    if window <= 0:
        raise ValueError("Window period must be positive.")
    if len(data) < window:
        logger.warning(f"Data length ({len(data)}) is less than SMA window ({window}). Returning NaNs.")
        return pd.Series([np.nan] * len(data), index=data.index)
        
    return data.rolling(window=window, min_periods=window).mean()

def calculate_ema(data: pd.Series, window: int) -> pd.Series:
    """Calculates the Exponential Moving Average (EMA)."""
    if not isinstance(data, pd.Series):
        raise ValueError("Input data must be a pandas Series.")
    if window <= 0:
        raise ValueError("Window period must be positive.")
    if len(data) < window: # EMA can technically start earlier, but often needs warmup
         logger.warning(f"Data length ({len(data)}) may be insufficient for stable EMA window ({window}).")
         # Return NaNs for insufficient length based on common practice, adjust if needed
         # return pd.Series([np.nan] * len(data), index=data.index) 

    # alpha = 2 / (window + 1) # Standard alpha calculation
    # return data.ewm(span=window, adjust=False, min_periods=window).mean()
    # Using adjust=True is often preferred as it accounts for the initial points better
    return data.ewm(span=window, adjust=True, min_periods=window).mean()


def calculate_rsi(data: pd.Series, window: int = 14) -> pd.Series:
    """Calculates the Relative Strength Index (RSI)."""
    if not isinstance(data, pd.Series):
        raise ValueError("Input data must be a pandas Series.")
    if window <= 0:
        raise ValueError("Window period must be positive.")
    if len(data) < window + 1: # Need at least window+1 periods for one delta calculation
        logger.warning(f"Data length ({len(data)}) is less than RSI window+1 ({window+1}). Returning NaNs.")
        return pd.Series([np.nan] * len(data), index=data.index)

    delta = data.diff()

    gain = delta.where(delta > 0, 0).fillna(0)
    loss = -delta.where(delta < 0, 0).fillna(0)

    # Use EMA for smoothing gains and losses (common practice)
    avg_gain = gain.ewm(com=window - 1, adjust=True, min_periods=window).mean()
    avg_loss = loss.ewm(com=window - 1, adjust=True, min_periods=window).mean()
    
    # Avoid division by zero
    rs = np.where(avg_loss == 0, np.inf, avg_gain / avg_loss)
    
    rsi = 100 - (100 / (1 + rs))
    
    # Handle the case where avg_loss was 0 (rs is inf), RSI should be 100
    rsi = np.where(avg_loss == 0, 100, rsi) 
    
    # Ensure output is a Series with the original index
    rsi_series = pd.Series(rsi, index=data.index)
    
    # Set initial NaNs where calculation wasn't possible
    rsi_series.iloc[:window] = np.nan 

    return rsi_series


def calculate_macd(data: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
    """
    Calculates the Moving Average Convergence Divergence (MACD).

    Returns:
        pd.DataFrame: DataFrame with columns 'MACD', 'Signal', 'Histogram'.
    """
    if not isinstance(data, pd.Series):
        raise ValueError("Input data must be a pandas Series.")
    if not (fast_period > 0 and slow_period > 0 and signal_period > 0):
         raise ValueError("All MACD periods must be positive.")
    if fast_period >= slow_period:
        raise ValueError("Fast period must be less than slow period for MACD.")
    if len(data) < slow_period:
         logger.warning(f"Data length ({len(data)}) is less than MACD slow period ({slow_period}). Results may be unstable or NaN.")
         # Return empty/NaN DataFrame matching expected columns
         return pd.DataFrame({'MACD': np.nan, 'Signal': np.nan, 'Histogram': np.nan}, index=data.index)

    ema_fast = calculate_ema(data, window=fast_period)
    ema_slow = calculate_ema(data, window=slow_period)

    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, window=signal_period)
    histogram = macd_line - signal_line

    macd_df = pd.DataFrame({
        'MACD': macd_line,
        'Signal': signal_line,
        'Histogram': histogram
    }, index=data.index)

    return macd_df


# --- Example Usage ---
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
    close_prices = pd.Series(np.random.randn(100).cumsum() + 50, index=dates)
    logger.info("Sample Close Prices:")
    logger.info(close_prices.head())

    # Calculate indicators
    sma_10 = calculate_sma(close_prices, 10)
    ema_10 = calculate_ema(close_prices, 10)
    rsi_14 = calculate_rsi(close_prices, 14)
    macd_data = calculate_macd(close_prices)

    logger.info("\nSMA(10):")
    logger.info(sma_10.tail())

    logger.info("\nEMA(10):")
    logger.info(ema_10.tail())
    
    logger.info("\nRSI(14):")
    logger.info(rsi_14.tail())

    logger.info("\nMACD Data:")
    logger.info(macd_data.tail())

    # Test edge cases
    short_data = pd.Series([50, 51, 52])
    logger.info("\nTesting with short data (length 3):")
    logger.info(f"SMA(5): {calculate_sma(short_data, 5).tolist()}")
    logger.info(f"EMA(5): {calculate_ema(short_data, 5).tolist()}")
    logger.info(f"RSI(5): {calculate_rsi(short_data, 5).tolist()}")
    logger.info(f"MACD(3,5,3):\n{calculate_macd(short_data, 3, 5, 3)}")