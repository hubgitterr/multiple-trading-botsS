// components/dashboard/Performance.js
'use client'; // Mark as client component for state and data fetching

import React, { useState, useEffect } from 'react';
// import useSWR from 'swr'; // For data fetching later
// import axios from 'axios'; // For API calls later
// Import chart components if needed, e.g., for equity curve
// import { Line } from 'react-chartjs-2'; 

// Placeholder fetcher function
// const fetcher = url => axios.get(url).then(res => res.data);

// Helper to format currency
const formatCurrency = (value) => {
   if (value === null || value === undefined) return '$--.--';
   return value.toLocaleString('en-US', { style: 'currency', currency: 'USD' }); // Assuming USD
};

export default function PerformanceDashboard() {
  // Placeholder state - replace with actual data fetching
  const [performanceData, setPerformanceData] = useState({
    totalPL: 1250.75,
    winRate: 65.5,
    totalTrades: 58,
    sharpeRatio: 1.2, // Example metric
    // Add more summary stats
  });
  const [tradeHistory, setTradeHistory] = useState([
     { id: 1, timestamp: '2024-01-10T10:30:00Z', botId: 'momentum-123', symbol: 'ETHUSDT', side: 'BUY', price: 2500.50, quantity: 0.1, pnl: null },
     { id: 2, timestamp: '2024-01-10T14:45:00Z', botId: 'momentum-123', symbol: 'ETHUSDT', side: 'SELL', price: 2550.75, quantity: 0.1, pnl: 50.25 },
     { id: 3, timestamp: '2024-01-11T08:00:00Z', botId: 'grid-456', symbol: 'ADAUSDT', side: 'BUY', price: 0.55, quantity: 100, pnl: null },
     // Add more trades
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // TODO: Implement data fetching for performance summary and trade history
  // useEffect(() => {
  //    const fetchData = async () => {
  //       setIsLoading(true);
  //       setError(null);
  //       try {
  //          // Fetch summary data (e.g., from a dedicated performance endpoint or calculated client-side)
  //          // const summaryRes = await fetch('/api/performance/summary'); 
  //          // const summary = await summaryRes.json();
  //          // setPerformanceData(summary);

  //          // Fetch trade history
  //          // const historyRes = await fetch('/api/trades/history?limit=50'); // Example API call
  //          // const history = await historyRes.json();
  //          // setTradeHistory(history);

  //       } catch (err) {
  //          console.error("Error fetching performance data:", err);
  //          setError("Failed to load performance data.");
  //       } finally {
  //          setIsLoading(false);
  //       }
  //    };
  //    fetchData();
  // }, []); // Fetch on component mount

  // Placeholder for Equity Curve Chart Data
  const equityCurveData = {
     labels: tradeHistory.map(t => new Date(t.timestamp)), // Example labels
     datasets: [{
        label: 'Portfolio Value',
        data: [10000, 10050, 10100, 10150], // Example cumulative P/L or value
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1
     }]
  };
   const chartOptions = { /* Basic chart options */ };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Performance Overview</h2>

      {isLoading && <p className="text-gray-500 dark:text-gray-400">Loading performance data...</p>}
      {error && <p className="text-red-600 dark:text-red-400">{error}</p>}

      {/* Performance Summary Stats */}
      {!isLoading && !error && (
         <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Example Stat Card */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-4">
               <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Total P/L</dt>
               <dd className={`mt-1 text-2xl font-semibold ${performanceData.totalPL >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {formatCurrency(performanceData.totalPL)}
               </dd>
            </div>
             <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-4">
               <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Win Rate</dt>
               <dd className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">
                  {performanceData.winRate?.toFixed(1) ?? '--'}%
               </dd>
            </div>
             <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-4">
               <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Total Trades</dt>
               <dd className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">
                  {performanceData.totalTrades ?? '--'}
               </dd>
            </div>
             <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-4">
               <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">Sharpe Ratio</dt>
               <dd className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">
                  {performanceData.sharpeRatio?.toFixed(2) ?? '--'}
               </dd>
            </div>
            {/* Add more stat cards */}
         </div>
      )}
      
      {/* Equity Curve Chart (Placeholder) */}
      {/* <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-4 h-72">
         <h4 className="text-md font-medium text-gray-900 dark:text-white mb-2">Equity Curve</h4>
         {equityCurveData ? <Line options={chartOptions} data={equityCurveData} /> : <p>Loading chart...</p>}
      </div> */}

      {/* Trade History Table */}
      <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg mt-6">
         <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">Trade History</h3>
         </div>
         <div className="border-t border-gray-200 dark:border-gray-700 overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
               <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                     <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Time</th>
                     <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Bot ID</th>
                     <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Symbol</th>
                     <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Side</th>
                     <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Price</th>
                     <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Quantity</th>
                     <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">P/L</th>
                  </tr>
               </thead>
               <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600">
                  {tradeHistory.map((trade) => (
                     <tr key={trade.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{new Date(trade.timestamp).toLocaleString()}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{trade.botId}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">{trade.symbol}</td>
                        <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${trade.side === 'BUY' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>{trade.side}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500 dark:text-gray-400">{formatCurrency(trade.price)}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500 dark:text-gray-400">{trade.quantity}</td>
                        <td className={`px-6 py-4 whitespace-nowrap text-right text-sm font-medium ${trade.pnl === null ? 'text-gray-500 dark:text-gray-400' : (trade.pnl >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400')}`}>
                           {trade.pnl !== null ? formatCurrency(trade.pnl) : '--'}
                        </td>
                     </tr>
                  ))}
                  {tradeHistory.length === 0 && (
                     <tr><td colSpan="7" className="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">No trades recorded yet.</td></tr>
                  )}
               </tbody>
            </table>
         </div>
      </div>
      {/* Add more sections: Risk Metrics, etc. */}
    </div>
  );
}