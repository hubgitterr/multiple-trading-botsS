import os
import asyncio
import time
from binance import Client, AsyncClient, BinanceSocketManager # Use AsyncClient for FastAPI
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
             return # Prevent initialization without credentials
             
        try:
            self.client = await AsyncClient.create(self.api_key, self.secret_key, testnet=self.testnet)
            self.bsm = BinanceSocketManager(self.client)
            logging.info(f"Binance AsyncClient initialized successfully (Testnet: {self.testnet}).")
            # Perform a test connection
            await self.test_connection()
        except Exception as e:
            logging.error(f"Failed to initialize Binance AsyncClient: {e}")
            self.client = None
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
            return None

    async def get_klines(self, symbol: str, interval: str, start_str: str = None, end_str: str = None, limit: int = 500):
        """Fetch historical klines (candlestick data)."""
        if not self.client: return None
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
            # Process klines if needed (e.g., convert to DataFrame)
            return klines
        except Exception as e:
            logging.error(f"Error fetching klines for {symbol}: {e}")
            return []

    # --- Order Management Methods (Placeholders) ---
    async def create_order(self, symbol: str, side: str, order_type: str, quantity: float = None, price: float = None, **kwargs):
        """Create a new order."""
        if not self.client: return None
        await self._rate_limiter()
        logging.info(f"Attempting to create order: {symbol}, {side}, {order_type}, Qty: {quantity}, Price: {price}")
        # TODO: Implement actual order creation logic using self.client.create_order()
        # Handle different order types (MARKET, LIMIT, etc.)
        # Add error handling and response parsing
        await asyncio.sleep(0.1) # Simulate API call
        return {"status": "Order creation placeholder", "symbol": symbol}

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