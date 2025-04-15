from fastapi import APIRouter, HTTPException, Depends, Query, Request # Added Request
from typing import List, Optional, Annotated
import logging
import asyncio # Added for concurrent price fetching
import json # Needed for formatting symbols list

# Import Schemas
from backend.schemas.market_data import (
    CurrentPrice, KlineData, KlinesResponse, TickerData, FormattedHeatmapDataPoint, FormattedHeatmapResponse # Updated Schemas
)
# Import the Binance client (adjust path if necessary)
from backend.utils.binance_client import BinanceAPIClient
# Import Binance constants if needed, e.g., for intervals
from binance import Client as BinanceLibClient
from binance.exceptions import BinanceAPIException # For specific error handling

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter(
    # prefix="/market", # Prefix removed, handled during inclusion in main.py
    tags=["market"],  # Tag for OpenAPI documentation
    responses={404: {"description": "Not found"}},
)

# --- Dependency for Binance Client ---
# REMOVED global instance - Client is now managed via lifespan in main.py

async def get_binance_client(request: Request) -> BinanceAPIClient:
    """Dependency to get the initialized Binance client from application state."""
    client: Optional[BinanceAPIClient] = request.app.state.binance_client
    if client is None:
        logging.error("Binance client is not available in application state. Initialization likely failed.")
        raise HTTPException(status_code=503, detail="Binance client is unavailable. Check server logs.")
    if not client.client: # Double check if the underlying client exists (might be None if init failed but state was set)
        logging.error("Binance client found in state, but underlying async client is not initialized.")
        raise HTTPException(status_code=503, detail="Binance client is unavailable (initialization failed). Check server logs.")
    return client

# --- API Endpoints ---

@router.get("/price/{symbol}", response_model=CurrentPrice, summary="Get Current Price for a Single Symbol")
async def get_current_price(
    symbol: str,
    client: BinanceAPIClient = Depends(get_binance_client)
) -> CurrentPrice:
    """
    Retrieves the latest price for a given trading symbol (e.g., BTCUSDT).
    """
    try:
        # Use get_tickers for consistency, even for one symbol, or keep get_current_price
        # price = await client.get_current_price(symbol.upper()) # Original method
        tickers = await client.get_tickers(symbols=[symbol.upper()])
        if not tickers:
             raise HTTPException(status_code=404, detail=f"Could not fetch ticker data for symbol: {symbol}")
        
        ticker_data = tickers[0] # Get the first (and only) ticker
        price = ticker_data.get('lastPrice')

        if price is None:
            raise HTTPException(status_code=404, detail=f"Could not extract price for symbol: {symbol} from ticker data")
            
        return CurrentPrice(symbol=symbol.upper(), price=price)
    except BinanceAPIException as e:
        logging.error(f"Binance API Error in /price/{symbol}: {e}")
        raise HTTPException(status_code=e.status_code or 500, detail=f"Binance API Error: {e.message}")
    except Exception as e:
        logging.error(f"Error in /price/{symbol} endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error fetching price for {symbol}")

@router.get("/prices/current", response_model=dict[str, float], summary="Get Current Prices for Multiple Symbols")
async def get_current_prices(
    symbols: str = Query(..., description="Comma-separated list of trading symbols (e.g., BTCUSDT,ETHUSDT)"),
    client: BinanceAPIClient = Depends(get_binance_client)
) -> dict[str, float]:
    """
    Retrieves the latest prices for a list of trading symbols.
    """
    if not symbols:
        raise HTTPException(status_code=400, detail="Symbols query parameter cannot be empty.")

    # Split the comma-separated string into a list and ensure uppercase
    symbol_list = [s.strip().upper() for s in symbols.split(',') if s.strip()]
    if not symbol_list:
        raise HTTPException(status_code=400, detail="No valid symbols provided after splitting.")
    upper_symbols = symbol_list # Use the split list

    prices_dict: dict[str, float] = {}
    try:
        # Call get_tickers with the list of uppercase symbols
        logging.debug(f"Calling get_tickers with symbols: {upper_symbols} (original input: '{symbols}')")
        tickers_list = await client.get_tickers(symbols=upper_symbols)

        if not tickers_list:
            logging.warning(f"Received empty list from get_tickers for symbols: {upper_symbols}")
            return {} # Return empty dict if API returns nothing

        # Process the list of ticker dictionaries
        for ticker_data in tickers_list:
            # Use 'price' key as returned by get_symbol_ticker
            if ticker_data and 'symbol' in ticker_data and 'price' in ticker_data:
                try:
                    prices_dict[ticker_data['symbol']] = float(ticker_data['price'])
                except (ValueError, TypeError):
                    logging.warning(f"Could not convert price '{ticker_data.get('price')}' to float for symbol: {ticker_data.get('symbol')}")
            else:
                logging.warning(f"Received incomplete or invalid ticker data in list: {ticker_data}")

        logging.info(f"Successfully fetched prices for {len(prices_dict)} out of {len(upper_symbols)} symbols.")
        return prices_dict

    except BinanceAPIException as e:
        # Handle API errors specifically for the get_tickers call
        logging.error(f"Binance API Error in get_tickers for symbols {upper_symbols}: Status={e.status_code}, Message={e.message}")
        # As per previous logic for API errors during price fetch, return empty dict
        return {}
    except Exception as e:
        # Catch any other unexpected errors during the process
        logging.error(f"Unexpected error in /prices/current for symbols {upper_symbols}: {e}", exc_info=True)
        # Raise a generic 500 error for unexpected issues
        raise HTTPException(status_code=500, detail=f"Internal server error processing prices for {upper_symbols}")


@router.get("/klines", response_model=KlinesResponse, summary="Get Historical Klines (Candlesticks)") # Changed path
async def get_historical_klines( # Renamed function
    symbol: str = Query(..., description="Trading symbol (e.g., BTCUSDT)"),
    interval: str = Query(default=BinanceLibClient.KLINE_INTERVAL_1HOUR, description=f"Candlestick interval (e.g., {BinanceLibClient.KLINE_INTERVAL_1MINUTE}, {BinanceLibClient.KLINE_INTERVAL_1HOUR}, {BinanceLibClient.KLINE_INTERVAL_1DAY})"),
    limit: int = Query(default=100, ge=1, le=1000, description="Number of klines to retrieve (max 1000)"),
    startTime: Optional[int] = Query(default=None, description="Start timestamp in milliseconds"),
    endTime: Optional[int] = Query(default=None, description="End timestamp in milliseconds"),
    client: BinanceAPIClient = Depends(get_binance_client)
) -> KlinesResponse:
    """
    Retrieves historical kline (candlestick) data for a given symbol and interval.
    Timestamps (startTime, endTime) should be provided in milliseconds since epoch.
    Returns raw kline data arrays from Binance.
    """
    # Convert timestamps to string format if provided, as expected by python-binance
    start_str = str(startTime) if startTime else None
    end_str = str(endTime) if endTime else None
    upper_symbol = symbol.upper()

    try:
        # The client's get_klines method returns a DataFrame, but the API returns raw lists
        klines_df = await client.get_klines(
            symbol=upper_symbol,
            interval=interval,
            limit=limit,
            start_str=start_str,
            end_str=end_str
        )

        # Convert DataFrame back to list of lists if needed, or adjust client method
        # For now, let's assume the client method was changed or we re-fetch raw
        # Re-fetching raw data to match the schema:
        raw_klines = await client.client.get_klines( # Access underlying async client
             symbol=upper_symbol,
             interval=interval,
             limit=limit,
             startTime=start_str, # Use startTime/endTime as expected by underlying client
             endTime=end_str
        )

        if not raw_klines:
            logging.warning(f"No klines returned for {upper_symbol} interval {interval} limit {limit}")
            # Return empty list if no data found for valid query
            return KlinesResponse(symbol=upper_symbol, interval=interval, klines=[])

        # Optional: Format klines using KlineData schema if needed by frontend
        # formatted_klines = [KlineData(
        #         timestamp=k[0], open=k[1], high=k[2], low=k[3], close=k[4],
        #         volume=k[5], close_time=k[6], quote_asset_volume=k[7],
        #         number_of_trades=k[8], taker_buy_base_asset_volume=k[9],
        #         taker_buy_quote_asset_volume=k[10]
        #     ) for k in raw_klines]
        # return KlinesResponse(symbol=upper_symbol, interval=interval, klines=raw_klines, klines_formatted=formatted_klines)

        return KlinesResponse(symbol=upper_symbol, interval=interval, klines=raw_klines)

    except BinanceAPIException as e:
        logging.error(f"Binance API Error in /klines for symbol {upper_symbol}: {e}")
        raise HTTPException(status_code=e.status_code or 500, detail=f"Binance API Error: {e.message}")
    except Exception as e:
        logging.error(f"Error in /klines endpoint for symbol {upper_symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error fetching klines for {upper_symbol}")


@router.get("/heatmap", response_model=FormattedHeatmapResponse, summary="Get Formatted Market Data for Heatmap")
async def get_heatmap_data(
    top_n: int = Query(default=20, ge=5, le=100, description="Number of top USDT pairs by volume to include"),
    client: BinanceAPIClient = Depends(get_binance_client)
) -> FormattedHeatmapResponse:
    """
    Retrieves formatted 24hr price change data for top USDT pairs by volume,
    suitable for direct use in a heatmap component.
    """
    try:
        # Fetch 24hr ticker statistics for all symbols - more likely to have % change and volume
        # Accessing underlying client directly as the wrapper might not expose get_ticker() cleanly
        logging.info("Fetching 24hr ticker statistics for heatmap...")
        tickers = await client.client.get_ticker() # Use the 24hr ticker endpoint

        if not tickers:
            logging.warning("No ticker data returned from Binance for heatmap.")
            raise HTTPException(status_code=404, detail="Could not fetch any ticker data for heatmap.")

        # Filter for USDT pairs and ensure necessary data exists
        usdt_tickers = []
        for ticker in tickers:
            symbol = ticker.get('symbol')
            price_change_percent_str = ticker.get('priceChangePercent')
            quote_volume_str = ticker.get('quoteVolume')

            # Ensure it's a USDT pair and required data exists
            if (symbol and symbol.endswith('USDT') and
                price_change_percent_str is not None and
                quote_volume_str is not None):
                try:
                    # Validate and convert necessary fields
                    ticker_data = {
                        'symbol': symbol,
                        # Default to 0.0 if conversion fails for any reason
                        'priceChangePercent': float(price_change_percent_str or 0.0),
                        'quoteVolume': float(quote_volume_str or 0.0)
                    }
                    usdt_tickers.append(ticker_data)
                except (ValueError, TypeError) as e:
                    logging.warning(f"Could not parse data for ticker {symbol} for heatmap (Values: Pct='{price_change_percent_str}', Vol='{quote_volume_str}'): {e}") # Log values on error

        if not usdt_tickers:
             logging.warning("No valid USDT tickers found for heatmap after filtering.")
             # Return empty structure if filtering removed all tickers
             return FormattedHeatmapResponse(data=[], xLabels=[], yLabels=[])

        # Sort by quote volume (descending)
        usdt_tickers.sort(key=lambda x: x['quoteVolume'], reverse=True)

        # Take top N
        top_tickers = usdt_tickers[:top_n]

        # Format for heatmap response
        heatmap_data_points = []
        x_labels = []
        y_label = "24h Change %" # Only one metric in this simple case

        for ticker in top_tickers:
            symbol = ticker['symbol']
            value = ticker['priceChangePercent']
            heatmap_data_points.append(FormattedHeatmapDataPoint(x=symbol, y=y_label, v=value))
            x_labels.append(symbol)

        logging.info(f"Returning heatmap data for {len(top_tickers)} symbols.")
        return FormattedHeatmapResponse(
            data=heatmap_data_points,
            xLabels=x_labels,
            yLabels=[y_label] # Only one y-label for this implementation
        )

    except BinanceAPIException as e:
        logging.error(f"Binance API Error in /heatmap: {e}")
        raise HTTPException(status_code=e.status_code or 500, detail=f"Binance API Error: {e.message}")
    except Exception as e:
        logging.error(f"Error in /heatmap endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching heatmap data")

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