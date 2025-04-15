import os
import asyncio
import time
from binance import Client, AsyncClient, BinanceSocketManager # Use AsyncClient for FastAPI
from binance.exceptions import BinanceAPIException, BinanceOrderException # Added for specific error handling
from dotenv import load_dotenv
import logging
import pandas as pd # Import pandas

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # Use a specific logger for this module

# Load environment variables from .env file located in the parent directory (backend/)
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env') 
load_dotenv(dotenv_path=dotenv_path)

# Get API keys from environment variables
API_KEY = os.getenv("BINANCE_API_KEY")
SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

# Basic validation
if not API_KEY or not SECRET_KEY:
    logging.error("Binance API Key or Secret Key not found in environment variables.")
    # Depending on the application design, you might raise an error or handle this differently
    # raise ValueError("Binance API Key or Secret Key not found.")
    # For now, we'll allow the script to continue but log the error. Client init will likely fail.
    
class BinanceAPIClient:
    """
    Asynchronous client for interacting with the Binance API (Spot Testnet).
    Handles authentication, basic requests, WebSocket connections, and rate limiting.
    """
    def __init__(self, api_key: str = API_KEY, secret_key: str = SECRET_KEY, testnet: bool = True):
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        self.client = None # Initialize later in an async context
        self.bsm = None    # BinanceSocketManager, initialize later

        # Rate Limiting State (Example: simple token bucket or leaky bucket)
        self.rate_limit_requests = 1200 # Example limit per minute
        self.rate_limit_interval = 60   # seconds
        self.request_timestamps = []

    async def initialize(self):
        """Asynchronously initialize the Binance client."""
        if not self.api_key or not self.secret_key:
            logging.error("Cannot initialize Binance client: API Key or Secret Key is missing.")
            self.client = None # Ensure client is None
            self.bsm = None
            return # Prevent initialization without credentials
        try:
            logging.info("Attempting to create Binance AsyncClient...")
            self.client = await AsyncClient.create(self.api_key, self.secret_key, testnet=self.testnet)
            self.bsm = BinanceSocketManager(self.client)
            logging.info(f"Binance AsyncClient created successfully (Testnet: {self.testnet}).")
            # Perform a test connection
            connected = await self.test_connection()
            if not connected:
                logging.warning("Binance client created, but connection test failed.")
        except Exception as e:
            logging.error(f"Failed to initialize Binance AsyncClient during create/test: {e}", exc_info=True) # Log traceback
            self.client = None # Ensure client is None on error
            self.bsm = None

    async def test_connection(self):
        """Test the API connection."""
        if not self.client:
            logging.warning("Client not initialized, cannot test connection.")
            return False
        try:
            ping = await self.client.ping()
            logging.info(f"Binance API connection successful: {ping}")
            # Optionally check account status
            # account_info = await self.client.get_account()
            # logging.info(f"Account status: {account_info.get('accountType', 'N/A')}")
            return True
        except Exception as e:
            logging.error(f"Binance API connection test failed: {e}")
            return False

    async def _rate_limiter(self):
        """Basic rate limiting implementation (placeholder)."""
        # TODO: Implement a more robust rate limiting strategy (e.g., token bucket)
        now = time.time()
        # Remove timestamps older than the interval
        self.request_timestamps = [ts for ts in self.request_timestamps if now - ts < self.rate_limit_interval]
        
        if len(self.request_timestamps) >= self.rate_limit_requests:
            # Calculate wait time
            wait_time = self.rate_limit_interval - (now - self.request_timestamps[0])
            logging.warning(f"Rate limit likely exceeded. Waiting for {wait_time:.2f} seconds.")
            await asyncio.sleep(wait_time)
            # Re-check after waiting (in case multiple coroutines hit this)
            self.request_timestamps = [ts for ts in self.request_timestamps if time.time() - ts < self.rate_limit_interval]

        self.request_timestamps.append(time.time())


    # --- Market Data Methods ---
    async def get_current_price(self, symbol: str):
        """Fetch the current average price for a symbol."""
        if not self.client: return None
        await self._rate_limiter()
        try:
            ticker = await self.client.get_symbol_ticker(symbol=symbol)
            logging.info(f"Fetched price for {symbol}: {ticker['price']}")
            return float(ticker['price'])
        except Exception as e:
            logging.error(f"Error fetching price for {symbol}: {e}")
            logging.error(f"get_klines called for {symbol} but client is not initialized. Returning None.")
            return None

    async def get_klines(self, symbol: str, interval: str, start_str: str = None, end_str: str = None, limit: int = 1000) -> pd.DataFrame: # Increased limit, added return type hint
        """Fetch historical klines (candlestick data)."""
        # Define standard kline columns for the DataFrame
        kline_columns = [
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ]
        empty_df = pd.DataFrame(columns=kline_columns) # Create an empty DataFrame structure

        if not self.client:
            logging.error(f"get_klines called for {symbol} but client is not initialized. Returning empty DataFrame.")
            return empty_df
        await self._rate_limiter()
        try:
            klines = await self.client.get_klines(
                symbol=symbol, 
                interval=interval, 
                startTime=start_str,
                endTime=end_str,
                limit=limit
            )
            logging.info(f"Fetched {len(klines)} klines for {symbol} interval {interval}")
            # Convert list of lists to DataFrame
            df = pd.DataFrame(klines, columns=kline_columns)
            # Convert relevant columns to numeric types
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume',
                            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce') # Add errors='coerce'
            # Convert timestamp columns to datetime
            # Binance timestamps are in milliseconds
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms', errors='coerce') # Add errors='coerce'
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms', errors='coerce') # Add errors='coerce'
            # Drop rows where conversion failed (optional, depends on how strict you want to be)
            df.dropna(subset=['timestamp', 'open', 'high', 'low', 'close', 'volume'], inplace=True)
            logging.info(f"Successfully converted {len(df)} klines to DataFrame for {symbol}")
            return df
        except Exception as e:
            logging.error(f"Error fetching klines for {symbol}: {e}")
            logging.exception(f"Caught exception in get_klines for {symbol}:") # Log traceback
            return empty_df # Return empty DataFrame on error within the try block
    async def get_tickers(self, symbols: list[str] | None = None) -> list[dict]:
        """
        Fetch 24hr ticker price change statistics.
        Uses get_symbol_ticker for specific symbols or get_all_tickers if symbols is None/empty.
        Returns a list of ticker dictionaries.
        """
        if not self.client:
            logger.error("get_tickers called but client is not initialized. Returning empty list.")
            return []
        
        await self._rate_limiter()
        tickers = [] # Initialize tickers list

        try:
            if symbols and len(symbols) > 0:
                upper_symbols = [s.upper() for s in symbols]
                logger.info(f"Fetching tickers for specific symbols: {upper_symbols}")
                for symbol in upper_symbols:
                    try:
                        ticker_data = await self.client.get_symbol_ticker(symbol=symbol)
                        tickers.append(ticker_data)
                        # logger.debug(f"Successfully fetched ticker for {symbol}") # Optional: debug log
                    except BinanceAPIException as e:
                        logger.error(f"Binance API Exception fetching ticker for symbol {symbol}: {e}", exc_info=False) # Log specific symbol error, maybe not full traceback
                    except Exception as e:
                         logger.error(f"Unexpected error fetching ticker for symbol {symbol}: {e}", exc_info=True) # Log other errors with traceback
                logger.info(f"Fetched {len(tickers)} tickers out of {len(upper_symbols)} requested symbols.")

            else:
                logger.info("Fetching all available tickers using get_all_tickers.")
                try:
                    tickers = await self.client.get_all_tickers()
                    logger.info(f"Fetched all ({len(tickers)}) available tickers.")
                except BinanceAPIException as e:
                    logger.error(f"Binance API Exception fetching all tickers: {e}", exc_info=True)
                    tickers = [] # Ensure tickers is empty on error
                except Exception as e:
                    logger.error(f"Unexpected error fetching all tickers: {e}", exc_info=True)
                    tickers = [] # Ensure tickers is empty on error

            # Convert numeric strings to floats for easier processing (applies to both cases)
            processed_tickers = []
            for ticker in tickers:
                processed_ticker = ticker.copy() # Avoid modifying original if needed elsewhere
                for key in ['priceChange', 'priceChangePercent', 'weightedAvgPrice',
                            'prevClosePrice', 'lastPrice', 'lastQty', 'bidPrice', # Note: get_symbol_ticker only returns 'symbol' and 'price'
                            'bidQty', 'askPrice', 'askQty', 'openPrice', 'highPrice',
                            'lowPrice', 'volume', 'quoteVolume', 'price']: # Added 'price' explicitly
                    if key in processed_ticker:
                        try:
                            processed_ticker[key] = float(processed_ticker[key])
                        except (ValueError, TypeError):
                            logger.warning(f"Could not convert ticker field '{key}' to float for symbol {processed_ticker.get('symbol', 'N/A')}. Value: {processed_ticker[key]}")
                            processed_ticker[key] = None # Or keep as string, or handle differently
                processed_tickers.append(processed_ticker)
            
            return processed_tickers

        except Exception as e:
            # Catch any broader errors (e.g., during rate limiting before the main logic)
            logger.error(f"Unexpected error in get_tickers main block: {e}", exc_info=True)
            return [] # Return empty list on unexpected errors

    # --- Order Management Methods (Placeholders) ---
    async def create_order(self, symbol: str, side: str, order_type: str, quantity: float = None, price: float = None, quoteOrderQty: float = None, **kwargs):
        """
        Create a new order using the python-binance library.

        Handles MARKET and LIMIT orders. For MARKET BUY orders, prefers quoteOrderQty if provided.
        Returns a dictionary with order details on success (including 'orderId'),
        or an error dictionary on failure.
        """
        if not self.client:
            logger.error("Cannot create order: Binance client not initialized.")
            return {"status": "error", "message": "Client not initialized"}

        await self._rate_limiter()
        logger.info(f"Attempting to create order: {symbol}, {side}, {order_type}, Qty: {quantity}, Price: {price}, QuoteQty: {quoteOrderQty}, Extra: {kwargs}")

        params = {
            "symbol": symbol,
            "side": side.upper(), # Ensure side is uppercase
            "type": order_type.upper() # Ensure type is uppercase
        }

        # Add parameters based on order type
        if params["type"] == Client.ORDER_TYPE_MARKET:
            if params["side"] == Client.SIDE_BUY and quoteOrderQty:
                 # Use quote quantity (USDT amount) for MARKET BUY if provided
                params["quoteOrderQty"] = quoteOrderQty
                logger.info(f"Using quoteOrderQty: {quoteOrderQty} for MARKET BUY")
            elif quantity:
                params["quantity"] = quantity
                logger.info(f"Using quantity: {quantity} for MARKET {params['side']}")
            else:
                 logger.error(f"Cannot create MARKET order for {symbol}: quantity or quoteOrderQty (for BUY) must be provided.")
                 return {"status": "error", "message": "Missing quantity/quoteOrderQty for MARKET order"}
        elif params["type"] == Client.ORDER_TYPE_LIMIT:
            if quantity and price:
                params["quantity"] = quantity
                params["price"] = f"{price:.8f}" # Format price to string with appropriate precision
                params["timeInForce"] = kwargs.get('timeInForce', Client.TIME_IN_FORCE_GTC) # Default to GTC
                logger.info(f"Using quantity: {quantity}, price: {params['price']}, timeInForce: {params['timeInForce']} for LIMIT order")
            else:
                logger.error(f"Cannot create LIMIT order for {symbol}: quantity and price must be provided.")
                return {"status": "error", "message": "Missing quantity or price for LIMIT order"}
        else:
            # Handle other order types if necessary, or reject
            logger.error(f"Unsupported order type: {params['type']}")
            return {"status": "error", "message": f"Unsupported order type: {params['type']}"}

        # Add any extra parameters passed in kwargs (e.g., newOrderRespType)
        params.update(kwargs)

        try:
            logger.debug(f"Calling self.client.create_order with params: {params}")
            # Use create_order for actual trading
            # For testing without hitting the real order book, consider self.client.create_test_order(**params)
            # if self.testnet: # Example: Use test order on testnet
            #     order_response = await self.client.create_test_order(**params)
            #     logger.info("Using create_test_order on testnet.")
            # else:
            order_response = await self.client.create_order(**params)
            logger.info(f"Successfully created order for {symbol}. Response: {order_response}")

            # Ensure the response contains the orderId
            if 'orderId' not in order_response:
                 logger.error(f"Order creation successful for {symbol}, but 'orderId' not found in response: {order_response}")
                 return {"status": "error", "message": "Order created but orderId missing in response", "response": order_response}

            # Return relevant details, ensuring 'orderId' key exists
            return {
                "orderId": order_response.get('orderId'),
                "status": order_response.get('status'),
                "symbol": order_response.get('symbol'),
                "side": order_response.get('side'),
                "type": order_response.get('type'),
                "price": order_response.get('price'),
                "origQty": order_response.get('origQty'),
                "executedQty": order_response.get('executedQty'),
                "cummulativeQuoteQty": order_response.get('cummulativeQuoteQty'),
                "clientOrderId": order_response.get('clientOrderId'),
                "transactTime": order_response.get('transactTime'),
                # Add other fields as needed
            }

        except BinanceAPIException as e:
            logger.error(f"Binance API Exception creating order for {symbol}: {e}", exc_info=True)
            return {"status": "error", "message": f"API Error: {e.status_code} - {e.message}"}
        except BinanceOrderException as e:
            logger.error(f"Binance Order Exception creating order for {symbol}: {e}", exc_info=True)
            return {"status": "error", "message": f"Order Error: {e.code} - {e.message}"}
        except Exception as e:
            logger.error(f"Unexpected error creating order for {symbol}: {e}", exc_info=True)
            return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}

    async def cancel_order(self, symbol: str, order_id: str):
        """Cancel an existing order."""
        if not self.client: return None
        await self._rate_limiter()
        logging.info(f"Attempting to cancel order: {symbol}, ID: {order_id}")
        # TODO: Implement actual order cancellation using self.client.cancel_order()
        await asyncio.sleep(0.1) # Simulate API call
        return {"status": "Order cancellation placeholder", "orderId": order_id}

    async def get_order_status(self, symbol: str, order_id: str):
        """Get the status of an order."""
        if not self.client: return None
        await self._rate_limiter()
        logging.info(f"Attempting to get order status: {symbol}, ID: {order_id}")
        # TODO: Implement actual order status check using self.client.get_order()
        await asyncio.sleep(0.1) # Simulate API call
        return {"status": "Order status placeholder", "orderId": order_id}


    # --- WebSocket Methods (Placeholders) ---
    async def start_kline_socket(self, symbol: str, interval: str, callback):
        """Start a WebSocket stream for kline data."""
        if not self.bsm: 
            logging.error("BinanceSocketManager not initialized.")
            return None
        socket_key = f"{symbol.lower()}@kline_{interval}"
        logging.info(f"Starting Kline WebSocket for {socket_key}")
        # TODO: Implement proper WebSocket handling using self.bsm.start_kline_socket
        # ts = self.bsm.start_kline_socket(callback, symbol=symbol, interval=interval)
        # await self.bsm.start() # Start the socket manager loop (might need careful management in FastAPI)
        await asyncio.sleep(0.1) # Simulate setup
        return {"socket_key": socket_key, "status": "WebSocket placeholder"}

    async def stop_socket(self, conn_key):
        """Stop a specific WebSocket connection."""
        if not self.bsm: return
        logging.info(f"Stopping WebSocket connection: {conn_key}")
        # TODO: Implement stopping logic using self.bsm.stop_socket(conn_key)
        await asyncio.sleep(0.1) # Simulate stopping
        
    async def close_connection(self):
        """Close the client connection."""
        if self.client:
            await self.client.close_connection()
            logging.info("Binance client connection closed.")


# Example usage (for testing purposes)
async def main():
    client = BinanceAPIClient()
    await client.initialize()
    
    if client.client: # Check if initialization was successful
        price = await client.get_current_price("BTCUSDT")
        if price:
            logging.info(f"Current BTCUSDT Price: {price}")
        
        klines = await client.get_klines("ETHUSDT", Client.KLINE_INTERVAL_1HOUR, limit=10)
        # print(f"Last 10 hourly klines for ETHUSDT: {klines}")

        # Example order (won't execute with placeholders)
        # order = await client.create_order("BTCUSDT", "BUY", "LIMIT", quantity=0.001, price=50000)
        # print(order)

        await client.close_connection()
    else:
        logging.error("Client initialization failed. Cannot perform operations.")

if __name__ == "__main__":
    # To run this test: python -m backend.utils.binance_client 
    # (ensure backend-env is active and you are in the project root directory)
    asyncio.run(main())