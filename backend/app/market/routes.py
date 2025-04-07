from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging

# Import the Binance client (adjust path if necessary)
from backend.utils.binance_client import BinanceAPIClient 
# Import Binance constants if needed, e.g., for intervals
from binance import Client as BinanceLibClient 

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter(
    prefix="/market", # Prefix for all routes in this router
    tags=["market"],  # Tag for OpenAPI documentation
    responses={404: {"description": "Not found"}},
)

# --- Dependency for Binance Client ---
# This creates a single client instance potentially shared across requests (consider lifespan management)
# For simplicity now, we create it here. In a larger app, manage it via FastAPI dependencies/lifespan events.
binance_client = BinanceAPIClient() 

async def get_binance_client() -> BinanceAPIClient:
    """Dependency to get the initialized Binance client."""
    if not binance_client.client:
        logging.info("Initializing Binance client for request...")
        await binance_client.initialize() # Ensure client is initialized
        if not binance_client.client:
             raise HTTPException(status_code=503, detail="Binance client initialization failed. Check API keys and connection.")
    return binance_client

# --- API Endpoints ---

@router.get("/price/{symbol}", summary="Get Current Price")
async def get_current_price(
    symbol: str, 
    client: BinanceAPIClient = Depends(get_binance_client)
):
    """
    Retrieves the latest price for a given trading symbol (e.g., BTCUSDT).
    """
    try:
        price = await client.get_current_price(symbol.upper())
        if price is None:
            raise HTTPException(status_code=404, detail=f"Could not fetch price for symbol: {symbol}")
        return {"symbol": symbol.upper(), "price": price}
    except Exception as e:
        logging.error(f"Error in /price/{symbol} endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error fetching price for {symbol}")

@router.get("/klines/{symbol}", summary="Get Historical Klines (Candlesticks)")
async def get_historical_klines(
    symbol: str,
    interval: str = Query(default=BinanceLibClient.KLINE_INTERVAL_1HOUR, description=f"Candlestick interval (e.g., {BinanceLibClient.KLINE_INTERVAL_1MINUTE}, {BinanceLibClient.KLINE_INTERVAL_1HOUR}, {BinanceLibClient.KLINE_INTERVAL_1DAY})"),
    limit: int = Query(default=100, ge=1, le=1000, description="Number of klines to retrieve (max 1000)"),
    startTime: Optional[int] = Query(default=None, description="Start timestamp in milliseconds"),
    endTime: Optional[int] = Query(default=None, description="End timestamp in milliseconds"),
    client: BinanceAPIClient = Depends(get_binance_client)
):
    """
    Retrieves historical kline (candlestick) data for a given symbol and interval.
    Timestamps (startTime, endTime) should be provided in milliseconds since epoch.
    """
    # Convert timestamps to string format if provided, as expected by python-binance
    start_str = str(startTime) if startTime else None
    end_str = str(endTime) if endTime else None

    try:
        klines = await client.get_klines(
            symbol=symbol.upper(), 
            interval=interval, 
            limit=limit, 
            start_str=start_str, 
            end_str=end_str
        )
        if not klines:
            # Could be an invalid symbol/interval or just no data for the period
            logging.warning(f"No klines returned for {symbol} interval {interval} limit {limit}")
            # Return empty list instead of 404, as it's valid query but no results
            # raise HTTPException(status_code=404, detail=f"No kline data found for {symbol} with specified parameters.")
        
        # Optional: Format klines for better readability if needed
        # formatted_klines = [
        #     {
        #         "open_time": k[0], "open": k[1], "high": k[2], "low": k[3], "close": k[4], 
        #         "volume": k[5], "close_time": k[6], "quote_asset_volume": k[7], 
        #         "number_of_trades": k[8], "taker_buy_base_asset_volume": k[9], 
        #         "taker_buy_quote_asset_volume": k[10]
        #     } 
        #     for k in klines
        # ]
        return {"symbol": symbol.upper(), "interval": interval, "klines": klines} # Return raw klines for now
    
    except Exception as e:
        logging.error(f"Error in /klines/{symbol} endpoint: {e}")
        # Consider more specific error handling based on Binance API errors
        raise HTTPException(status_code=500, detail=f"Internal server error fetching klines for {symbol}")

# Placeholder for WebSocket streaming endpoint (more complex setup needed)
# @router.websocket("/ws/kline/{symbol}")
# async def websocket_kline_endpoint(websocket: WebSocket, symbol: str, interval: str = "1m"):
#     await websocket.accept()
#     client = await get_binance_client() # Get client instance
#     
#     async def callback(msg):
#         # Process message and send to client
#         if msg and 'stream' in msg:
#             await websocket.send_json(msg['data'])
#         elif msg and 'e' in msg and msg['e'] == 'error':
#              logging.error(f"WebSocket Error: {msg}")
#              # Optionally close connection or notify client
#
#     conn_key = await client.start_kline_socket(symbol, interval, callback)
#     if not conn_key:
#         await websocket.close(code=1011, reason="Failed to start WebSocket stream")
#         return
#
#     try:
#         while True:
#             # Keep connection alive or handle client messages
#             await asyncio.sleep(60) # Keep alive or use receive_text/bytes
#     except WebSocketDisconnect:
#         logging.info(f"WebSocket disconnected for {symbol}@{interval}")
#     finally:
#         await client.stop_socket(conn_key['socket_key']) # Ensure socket is stopped