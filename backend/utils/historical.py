import pandas as pd
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import time
import os
import asyncio # Added this import as it's used later

# Import the Binance client (adjust path if necessary)
from backend.utils.binance_client import BinanceAPIClient 
# Import Binance constants if needed, e.g., for intervals
from binance import Client as BinanceLibClient 

logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.INFO) # Uncomment for standalone testing

# --- Configuration ---
# Define a path for potentially caching historical data (optional)
# Ensure this directory exists or is created
CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'data_cache', 'historical')
# os.makedirs(CACHE_DIR, exist_ok=True) # Create cache dir if it doesn't exist

# --- Helper Functions ---

def _klines_to_dataframe(klines: List[List[Any]]) -> Optional[pd.DataFrame]:
    """Converts raw kline list from Binance API to a pandas DataFrame."""
    if not klines:
        return None
    try:
        cols = ["OpenTime", "Open", "High", "Low", "Close", "Volume", "CloseTime", 
                "QuoteAssetVolume", "NumTrades", "TakerBuyBaseAssetVolume", 
                "TakerBuyQuoteAssetVolume", "Ignore"]
        df = pd.DataFrame(klines, columns=cols)
        
        # Convert relevant columns to numeric
        numeric_cols = ["Open", "High", "Low", "Close", "Volume", "QuoteAssetVolume", "NumTrades", 
                        "TakerBuyBaseAssetVolume", "TakerBuyQuoteAssetVolume"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col])
        
        # Convert timestamps and set index
        df['OpenTime'] = pd.to_datetime(df['OpenTime'], unit='ms')
        df['CloseTime'] = pd.to_datetime(df['CloseTime'], unit='ms')
        df.set_index('CloseTime', inplace=True) 
        
        # Drop the 'Ignore' column
        df.drop(columns=['Ignore'], inplace=True, errors='ignore')
        
        return df
    except Exception as e:
        logger.exception(f"Error converting klines to DataFrame: {e}")
        return None


# --- Main Data Retrieval Function ---

async def fetch_historical_data(
    client: BinanceAPIClient, 
    symbol: str, 
    interval: str, 
    start_date_str: str, 
    end_date_str: Optional[str] = None,
    use_cache: bool = False, # Optional caching flag
    cache_dir: str = CACHE_DIR 
) -> Optional[pd.DataFrame]:
    """
    Fetches historical kline data for a given symbol, interval, and date range.
    Handles pagination to retrieve more than the API limit per request.
    Optionally uses a simple file cache.

    Args:
        client: Initialized BinanceAPIClient instance.
        symbol: Trading symbol (e.g., 'BTCUSDT').
        interval: Kline interval (e.g., '1h', '1d').
        start_date_str: Start date in 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS' format.
        end_date_str: End date (optional, defaults to now). Format same as start_date_str.
        use_cache: If True, attempts to load from cache first and save after fetching.
        cache_dir: Directory to use for caching data.

    Returns:
        A pandas DataFrame containing the historical data, or None if an error occurs.
    """
    symbol = symbol.upper()
    filename_base = f"{symbol}_{interval}_{start_date_str.split(' ')[0]}_{end_date_str.split(' ')[0] if end_date_str else 'latest'}.parquet"
    cache_filepath = os.path.join(cache_dir, filename_base)

    # --- Optional Caching ---
    if use_cache:
        os.makedirs(cache_dir, exist_ok=True) # Ensure cache dir exists
        if os.path.exists(cache_filepath):
            try:
                logger.info(f"Loading historical data from cache: {cache_filepath}")
                df_cached = pd.read_parquet(cache_filepath)
                # TODO: Add validation? Check if date range matches request?
                return df_cached
            except Exception as e:
                logger.warning(f"Failed to load data from cache file {cache_filepath}: {e}. Fetching from API.")

    # --- Fetching Logic ---
    if not client or not client.client:
        logger.error("Binance client not initialized. Cannot fetch historical data.")
        return None

    logger.info(f"Fetching historical data for {symbol} ({interval}) from {start_date_str} to {end_date_str or 'now'}...")
    
    all_klines = []
    limit_per_req = 1000 # Binance API limit per request

    # Convert dates to milliseconds timestamps
    try:
         # Attempt parsing with time first, then just date
        try:
             start_dt = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
             start_dt = datetime.strptime(start_date_str, '%Y-%m-%d')
        start_milli = int(start_dt.timestamp() * 1000)

        end_milli = None
        if end_date_str:
             try:
                  end_dt = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')
             except ValueError:
                  end_dt = datetime.strptime(end_date_str, '%Y-%m-%d')
             end_milli = int(end_dt.timestamp() * 1000)
        else:
             end_milli = int(datetime.now().timestamp() * 1000) # Default to now if no end date

    except ValueError as e:
         logger.error(f"Invalid date format: {e}. Use 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS'.")
         return None

    current_start_milli = start_milli
    fetch_count = 0

    while True:
        fetch_count += 1
        logger.debug(f"Fetching chunk {fetch_count}: Start={datetime.fromtimestamp(current_start_milli/1000)}, End={datetime.fromtimestamp(end_milli/1000) if end_milli else 'Now'}")
        try:
            # Fetch klines for the current chunk
            klines = await client.client.get_klines( # Access the underlying AsyncClient
                symbol=symbol,
                interval=interval,
                startTime=current_start_milli,
                endTime=end_milli, # Use original end time for all requests
                limit=limit_per_req
            )
            
            if not klines:
                logger.debug("No more klines returned in this chunk.")
                break # No more data in this range

            all_klines.extend(klines)
            
            # Get the timestamp of the last kline received to use as the start for the next request
            last_kline_close_time = klines[-1][6] 
            
            # Move start time to *after* the last received kline's close time
            current_start_milli = last_kline_close_time + 1 

            # Break if we've fetched enough data (e.g., reached the end time implicitly or explicitly)
            # or if the last fetch returned less than the limit (usually means end of data)
            if len(klines) < limit_per_req:
                 logger.debug("Last fetch returned less than limit, assuming end of data.")
                 break
            if end_milli and current_start_milli >= end_milli:
                 logger.debug("Reached specified end time.")
                 break
                 
            # Optional: Add a small delay between requests to avoid potential rate limits
            await asyncio.sleep(0.2) 

        except Exception as e:
            logger.exception(f"Error fetching kline chunk: {e}")
            # Decide whether to retry or abort
            return None # Abort on error for now

    if not all_klines:
        logger.warning(f"No historical data found for {symbol} in the specified range.")
        return pd.DataFrame() # Return empty DataFrame

    logger.info(f"Fetched a total of {len(all_klines)} klines for {symbol}.")

    # Convert to DataFrame
    df = _klines_to_dataframe(all_klines)
    if df is None:
         return None # Error during conversion

    # Filter DataFrame to ensure it's within the requested start/end times precisely (optional)
    # df = df[(df.index >= pd.to_datetime(start_milli, unit='ms')) & (df.index <= pd.to_datetime(end_milli, unit='ms'))]

    # --- Optional Caching ---
    if use_cache and not df.empty:
         try:
              logger.info(f"Saving historical data to cache: {cache_filepath}")
              df.to_parquet(cache_filepath)
         except Exception as e:
              logger.warning(f"Failed to save data to cache file {cache_filepath}: {e}")

    return df


# --- Data Processing Utilities (Placeholder) ---

def resample_data(df: pd.DataFrame, timeframe: str) -> Optional[pd.DataFrame]:
    """
    Resamples OHLCV data to a different timeframe (e.g., '4h', '1d').
    Requires DataFrame with DatetimeIndex.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
         logger.error("DataFrame index must be DatetimeIndex for resampling.")
         return None
    
    logger.info(f"Resampling data to timeframe: {timeframe}")
    try:
        # Define aggregation rules
        agg_rules = {
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum',
            'QuoteAssetVolume': 'sum',
            'NumTrades': 'sum',
            'TakerBuyBaseAssetVolume': 'sum',
            'TakerBuyQuoteAssetVolume': 'sum',
        }
        # Resample and apply aggregation
        resampled_df = df.resample(timeframe).agg(agg_rules)
        # Drop rows where all values are NaN (often happens at the start/end of resampling)
        resampled_df.dropna(how='all', inplace=True) 
        return resampled_df
    except Exception as e:
        logger.exception(f"Error resampling data to {timeframe}: {e}")
        return None


# --- Example Usage ---
async def main_test():
    # NOTE: Requires a valid BinanceAPIClient instance. 
    # This test won't run standalone without providing keys or mocking the client.
    
    # Mock client or provide real one
    # For testing structure, we can skip actual client interaction
    class MockBinanceClient: # Very basic mock
         async def get_klines(self, **kwargs):
              print(f"Mock get_klines called with: {kwargs}")
              # Simulate returning one chunk of data
              if kwargs.get('startTime', 0) < int(datetime(2023,1,2).timestamp()*1000):
                   # Return 10 dummy klines for Jan 1st 2023 (hourly)
                   base_time = int(datetime(2023,1,1,0).timestamp()*1000)
                   return [
                        [base_time + i*3600*1000, 50000+i, 50100+i, 49900+i, 50050+i, 10+i, base_time + (i+1)*3600*1000 -1, 500000, 100, 5, 250000, 0] 
                        for i in range(10) 
                   ]
              else:
                   return [] # No more data
    
    mock_api_client = type('obj', (object,), {'client': MockBinanceClient()})() # Mock the structure

    symbol = "BTCUSDT"
    interval = "1h"
    start = "2023-01-01"
    end = "2023-01-03"

    logger.info(f"\n--- Testing fetch_historical_data ({symbol} {interval}) ---")
    hist_df = await fetch_historical_data(mock_api_client, symbol, interval, start, end, use_cache=False)

    if hist_df is not None:
        logger.info(f"Fetched DataFrame shape: {hist_df.shape}")
        logger.info("Head:\n" + str(hist_df.head()))
        
        logger.info(f"\n--- Testing resample_data (to 4h) ---")
        resampled_df = resample_data(hist_df, '4h')
        if resampled_df is not None:
             logger.info(f"Resampled DataFrame shape: {resampled_df.shape}")
             logger.info("Head:\n" + str(resampled_df.head()))
    else:
         logger.error("Failed to fetch historical data.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # asyncio.run(main_test()) # Requires async environment and potentially valid client/keys
    print("Historical data utility structure defined. Run tests with an async runner and potentially valid API client.")