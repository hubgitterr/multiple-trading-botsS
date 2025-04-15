from pydantic import BaseModel, Field
from typing import List, Optional, Any
import datetime

# --- Schemas for Current Price Endpoint ---

class CurrentPrice(BaseModel):
    """Schema for a single symbol's current price."""
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDT)")
    price: float = Field(..., description="Current price of the symbol")

# CurrentPricesResponse removed as the endpoint now returns dict[str, float]

# --- Schemas for Historical Klines (Candlestick) Endpoint ---

class KlineData(BaseModel):
    """Schema representing a single candlestick data point (OHLCV)."""
    timestamp: int = Field(..., description="Kline open time timestamp (milliseconds)")
    open: float = Field(..., description="Open price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Close price")
    volume: float = Field(..., description="Volume")
    close_time: int = Field(..., description="Kline close time timestamp (milliseconds)")
    quote_asset_volume: float = Field(..., description="Quote asset volume")
    number_of_trades: int = Field(..., description="Number of trades")
    taker_buy_base_asset_volume: float = Field(..., description="Taker buy base asset volume")
    taker_buy_quote_asset_volume: float = Field(..., description="Taker buy quote asset volume")

    class Config:
        orm_mode = True # Kept for potential future ORM use, though not strictly needed for list conversion
        # If converting directly from Binance list format, might need custom parsing or validator

class KlinesResponse(BaseModel):
    """Schema for the response containing historical kline data."""
    symbol: str = Field(..., description="Trading symbol")
    interval: str = Field(..., description="Kline interval")
    klines: List[List[Any]] = Field(..., description="List of kline data arrays from Binance")
    # Alternatively, use List[KlineData] if formatting is done in the route:
    # klines_formatted: Optional[List[KlineData]] = Field(None, description="Formatted list of kline data objects")


# --- Schemas for Heatmap Endpoint ---

class TickerData(BaseModel):
    """Schema representing relevant data from a 24hr ticker (kept for potential other uses)."""
    symbol: str = Field(..., description="Trading symbol")
    priceChangePercent: Optional[float] = Field(None, description="24hr price change percentage")
    lastPrice: Optional[float] = Field(None, description="Last traded price")
    volume: Optional[float] = Field(None, description="Total traded base asset volume in 24hr")
    quoteVolume: Optional[float] = Field(None, description="Total traded quote asset volume in 24hr")
    # Add other fields from get_ticker if needed
    # e.g., highPrice, lowPrice

    class Config:
        orm_mode = True # Useful if converting from ORM objects later

# --- Schemas for Formatted Heatmap Endpoint ---

class FormattedHeatmapDataPoint(BaseModel):
    """Schema for a single data point in the formatted heatmap response."""
    x: str = Field(..., description="X-axis label (e.g., Symbol)")
    y: str = Field(..., description="Y-axis label (e.g., Metric Name)")
    v: float = Field(..., description="Value for the heatmap cell")

class FormattedHeatmapResponse(BaseModel):
    """Schema for the formatted response suitable for the heatmap component."""
    data: List[FormattedHeatmapDataPoint] = Field(..., description="List of data points for the heatmap cells")
    xLabels: List[str] = Field(..., description="List of labels for the X-axis")
    yLabels: List[str] = Field(..., description="List of labels for the Y-axis")