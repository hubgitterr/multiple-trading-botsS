// lib/types.ts

// Define a type for the API Key data structure
export interface ApiKey {
  id: string; // Assuming UUID comes as string from API
  label: string | null;
  api_key_public: string;
  // Add other relevant fields if needed (e.g., created_at)
}

// Define a type for Bot Configuration (can be expanded)
export interface BotConfig {
    id: string;
    user_id: string;
    bot_type: string;
    name: string | null;
    symbol: string;
    settings: Record<string, any>; // Use Record<string, any> for flexible settings
    is_enabled: boolean;
    api_key_id?: string | null; // Optional, might not be set initially
    created_at: string; // Assuming ISO string format from API
    updated_at?: string | null;
}

// Add other shared types here as needed

// Type for a single simulated trade from backtesting
export interface Trade {
  entry_timestamp: number; // Unix timestamp (seconds or ms - check API response)
  exit_timestamp?: number | null;
  entry_price: number;
  exit_price?: number | null;
  quantity: number;
  pnl?: number | null;
  side: 'BUY' | 'SELL' | 'CLOSE'; // Match backend schema
  avg_entry_price?: number | null; // Optional average entry price
}

// Type for the overall backtest result
export interface BacktestResult {
  metrics: Record<string, any>; // Flexible dictionary for various metrics
  trades: Trade[];
  equity_curve: { timestamp: number; equity: number }[]; // Array of equity points
}