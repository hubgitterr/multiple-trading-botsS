import pandas as pd
import numpy as np
from typing import List, Dict, Any

def calculate_total_pnl(trades: List[Dict[str, Any]], initial_capital: float, final_equity: float) -> Dict[str, float]:
    """Calculates total Profit and Loss (PnL)."""
    if not trades:
        return {"absolute_pnl": 0.0, "percentage_pnl": 0.0}

    absolute_pnl = final_equity - initial_capital
    percentage_pnl = (absolute_pnl / initial_capital) * 100 if initial_capital else 0.0

    return {
        "absolute_pnl": round(absolute_pnl, 4),
        "percentage_pnl": round(percentage_pnl, 2)
    }

def calculate_win_rate(trades: List[Dict[str, Any]]) -> float:
    """Calculates the win rate (percentage of profitable trades)."""
    if not trades:
        return 0.0

    winning_trades = sum(1 for trade in trades if trade.get('pnl', 0) > 0)
    total_trades = len(trades)

    return round((winning_trades / total_trades) * 100, 2) if total_trades else 0.0

def calculate_profit_factor(trades: List[Dict[str, Any]]) -> float:
    """Calculates the profit factor (Gross Profit / Gross Loss)."""
    if not trades:
        return 0.0

    gross_profit = sum(trade.get('pnl', 0) for trade in trades if trade.get('pnl', 0) > 0)
    gross_loss = abs(sum(trade.get('pnl', 0) for trade in trades if trade.get('pnl', 0) < 0))

    return round(gross_profit / gross_loss, 2) if gross_loss else float('inf') # Avoid division by zero

def calculate_max_drawdown(equity_curve: pd.DataFrame) -> Dict[str, float]:
    """
    Calculates the maximum drawdown from an equity curve DataFrame.
    Equity curve DataFrame should have 'timestamp' and 'equity' columns.
    """
    if equity_curve.empty or len(equity_curve) < 2:
        return {"absolute_max_drawdown": 0.0, "percentage_max_drawdown": 0.0}

    # Ensure unique timestamp index, keeping the last equity value for duplicates
    equity_curve = equity_curve.sort_values(by='timestamp')
    equity_curve = equity_curve.drop_duplicates(subset=['timestamp'], keep='last')
    equity_curve = equity_curve.set_index('timestamp')['equity']
    cumulative_max = equity_curve.cummax()
    drawdown = equity_curve - cumulative_max
    max_drawdown_absolute = drawdown.min() # This will be negative or zero

    peak_at_max_drawdown = cumulative_max[drawdown.idxmin()]
    max_drawdown_percentage = (max_drawdown_absolute / peak_at_max_drawdown) * 100 if pd.notna(peak_at_max_drawdown) and peak_at_max_drawdown > 0 else 0.0

    return {
        "absolute_max_drawdown": round(abs(max_drawdown_absolute), 4),
        "percentage_max_drawdown": round(abs(max_drawdown_percentage), 2)
    }


def calculate_sharpe_ratio(equity_curve: pd.DataFrame, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
    """
    Calculates the Sharpe Ratio.
    Assumes daily data if periods_per_year is 252. Adjust for different frequencies.
    """
    if equity_curve.empty or len(equity_curve) < 2:
        return 0.0

    # Ensure unique timestamp index, keeping the last equity value for duplicates
    equity_curve = equity_curve.sort_values(by='timestamp')
    equity_curve = equity_curve.drop_duplicates(subset=['timestamp'], keep='last')
    equity_curve = equity_curve.set_index('timestamp')['equity']
    returns = equity_curve.pct_change().dropna()

    if returns.empty or returns.std() == 0:
        return 0.0

    # Calculate excess returns over the risk-free rate
    # Adjust risk-free rate to the period frequency
    risk_free_rate_period = (1 + risk_free_rate)**(1/periods_per_year) - 1
    excess_returns = returns - risk_free_rate_period

    # Calculate annualized Sharpe Ratio
    sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * np.sqrt(periods_per_year)

    return round(sharpe_ratio, 3)


def calculate_metrics(
    trades: List[Dict[str, Any]],
    equity_curve_data: List[Dict[str, Any]], # Expects list of dicts [{'timestamp': ts, 'equity': eq}]
    initial_capital: float
) -> Dict[str, Any]:
    """
    Calculates all performance metrics based on simulation results.
    """
    if not equity_curve_data:
        return {
            "total_trades": 0,
            "total_profit": {"absolute_pnl": 0.0, "percentage_pnl": 0.0},
            "win_rate_percentage": 0.0,
            "profit_factor": 0.0,
            "max_drawdown": {"absolute_max_drawdown": 0.0, "percentage_max_drawdown": 0.0},
            "sharpe_ratio": 0.0,
            "message": "No equity data provided for calculation."
        }

    equity_curve_df = pd.DataFrame(equity_curve_data)
    final_equity = equity_curve_df['equity'].iloc[-1]

    total_pnl = calculate_total_pnl(trades, initial_capital, final_equity)
    win_rate = calculate_win_rate(trades)
    profit_factor = calculate_profit_factor(trades)
    max_drawdown = calculate_max_drawdown(equity_curve_df)
    # Assuming daily data for Sharpe ratio calculation (252 trading days)
    # TODO: Make periods_per_year dynamic based on kline interval
    sharpe = calculate_sharpe_ratio(equity_curve_df, risk_free_rate=0.0, periods_per_year=252)

    return {
        "total_trades": len(trades),
        "total_profit": total_pnl['absolute_pnl'],
        "total_profit_pct": total_pnl['percentage_pnl'],
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "max_drawdown": max_drawdown['absolute_max_drawdown'],
        "max_drawdown_pct": max_drawdown['percentage_max_drawdown'],
        "sharpe_ratio": sharpe,
    }