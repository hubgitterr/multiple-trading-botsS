'use client';

import React from 'react';
import { BacktestResult, Trade } from '@/lib/types'; // Import the types

// Helper function to format numbers (e.g., percentages, currency)
const formatNumber = (num, options = {}) => {
  if (num === null || num === undefined || isNaN(num)) {
    return 'N/A';
  }
  return num.toLocaleString(undefined, options);
};

// Helper function to format timestamps (assuming they are Unix seconds)
const formatTimestamp = (timestamp) => {
  if (!timestamp) return 'N/A';
  try {
    // Multiply by 1000 if timestamp is in seconds
    const date = new Date(timestamp * 1000);
    return date.toLocaleString(); // Adjust format as needed
  } catch (e) {
    console.error("Error formatting timestamp:", timestamp, e);
    return 'Invalid Date';
  }
};


export default function BacktestResultsDisplay({ results }) {
  if (!results) {
    return null; // Don't render anything if there are no results
  }

  const { metrics, trades, equity_curve } = results;

  // Basic structure for displaying metrics
  const renderMetrics = () => {
    if (!metrics) return <p>No metrics data available.</p>;

    // Define which metrics to display and how to format them
    const metricDisplayConfig = [
      { key: 'total_pnl_pct', label: 'Total PnL (%)', format: { style: 'percent', minimumFractionDigits: 2 } },
      { key: 'win_rate_pct', label: 'Win Rate (%)', format: { style: 'percent', minimumFractionDigits: 2 } },
      { key: 'profit_factor', label: 'Profit Factor', format: { minimumFractionDigits: 2 } },
      { key: 'max_drawdown_pct', label: 'Max Drawdown (%)', format: { style: 'percent', minimumFractionDigits: 2 } },
      { key: 'sharpe_ratio', label: 'Sharpe Ratio', format: { minimumFractionDigits: 3 } },
      { key: 'total_trades', label: 'Total Trades', format: {} },
      { key: 'avg_trade_pnl', label: 'Avg Trade PnL ($)', format: { style: 'currency', currency: 'USD' } }, // Example additional metric
      { key: 'total_profit', label: 'Total Profit ($)', format: { style: 'currency', currency: 'USD' } },
      { key: 'total_loss', label: 'Total Loss ($)', format: { style: 'currency', currency: 'USD' } },
      // Add more metrics from your backend calculation as needed
    ];

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {metricDisplayConfig.map(({ key, label, format }) => (
          <div key={key} className="bg-gray-100 dark:bg-gray-700 p-4 rounded-lg shadow">
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">{label}</dt>
            <dd className="mt-1 text-xl font-semibold text-gray-900 dark:text-white">
              {formatNumber(metrics[key], format)}
            </dd>
          </div>
        ))}
      </div>
    );
  };

  // Basic structure for displaying trades in a table
  const renderTradesTable = () => {
    if (!trades || trades.length === 0) {
      return <p className="text-gray-500 dark:text-gray-400">No trades executed during this backtest.</p>;
    }

    return (
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Entry Time</th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Exit Time</th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Direction</th>
              <th scope="col" className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Entry Price</th>
              <th scope="col" className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Exit Price</th>
              <th scope="col" className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Quantity</th>
              <th scope="col" className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">PnL ($)</th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {trades.map((trade, index) => (
              <tr key={index} className={trade.pnl > 0 ? 'bg-green-50 dark:bg-green-900/20' : trade.pnl < 0 ? 'bg-red-50 dark:bg-red-900/20' : ''}>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-gray-200">{formatTimestamp(trade.entry_timestamp)}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{formatTimestamp(trade.exit_timestamp)}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900 dark:text-gray-200">{trade.side}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900 dark:text-gray-200">{formatNumber(trade.entry_price, { minimumFractionDigits: 2 })}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-500 dark:text-gray-400">{formatNumber(trade.exit_price, { minimumFractionDigits: 2 })}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-right text-gray-900 dark:text-gray-200">{formatNumber(trade.quantity, { minimumFractionDigits: 4 })}</td>
                <td className={`px-4 py-3 whitespace-nowrap text-sm text-right font-medium ${trade.pnl > 0 ? 'text-green-600 dark:text-green-400' : trade.pnl < 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-gray-200'}`}>
                  {formatNumber(trade.pnl, { style: 'currency', currency: 'USD' })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // TODO: Add Equity Curve Chart visualization using equity_curve data

  return (
    <div className="mt-6 p-4 sm:p-6 bg-white dark:bg-gray-800 shadow rounded-lg">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Backtest Results</h2>

      <section aria-labelledby="metrics-heading" className="mb-6">
        <h3 id="metrics-heading" className="text-lg font-medium text-gray-900 dark:text-white mb-3">Performance Metrics</h3>
        {renderMetrics()}
      </section>

      <section aria-labelledby="trades-heading">
        <h3 id="trades-heading" className="text-lg font-medium text-gray-900 dark:text-white mb-3">Simulated Trades</h3>
        {renderTradesTable()}
      </section>

      {/* Placeholder for Equity Curve Chart */}
      {/* <section aria-labelledby="equity-curve-heading" className="mt-6">
        <h3 id="equity-curve-heading" className="text-lg font-medium text-gray-900 dark:text-white mb-3">Equity Curve</h3>
        <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center">
          <p className="text-gray-500 dark:text-gray-400">[Equity Curve Chart Placeholder]</p>
        </div>
      </section> */}
    </div>
  );
}