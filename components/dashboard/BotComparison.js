// components/dashboard/BotComparison.js
'use client'; // Mark as client component for state and interactions

import React, { useState, useEffect } from 'react';
// import Select from 'react-select'; // Example for a multi-select dropdown

// Helper to format currency (reuse if available globally, or define locally)
const formatCurrency = (value) => {
   if (value === null || value === undefined) return '$--.--';
   return value.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
};

export default function BotComparison() {
  // Placeholder state - replace with actual data fetching and selection logic
  const [allBots, setAllBots] = useState([ // Assume we fetch a list of configured bots
    { id: 'momentum-123', name: 'Momentum ETH', type: 'MomentumBot', symbol: 'ETHUSDT', performance: { totalPL: 550.20, winRate: 68, totalTrades: 35 } },
    { id: 'grid-456', name: 'Grid ADA', type: 'GridBot', symbol: 'ADAUSDT', performance: { totalPL: -50.10, winRate: 45, totalTrades: 80 } },
    { id: 'dca-789', name: 'DCA BTC Weekly', type: 'DCABot', symbol: 'BTCUSDT', performance: { totalPL: 750.65, winRate: 100, totalTrades: 15 } }, // Win rate might not apply to DCA
  ]);
  const [selectedBots, setSelectedBots] = useState([]); // Store IDs of bots selected for comparison
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // TODO: Implement fetching list of available bots and their summary performance
  // useEffect(() => { ... fetch logic ... }, []);

  // TODO: Implement selection logic (e.g., using checkboxes or a multi-select dropdown)
  const handleSelectBot = (botId) => {
     setSelectedBots(prev => 
        prev.includes(botId) ? prev.filter(id => id !== botId) : [...prev, botId]
     );
  };

  const botsToCompare = allBots.filter(bot => selectedBots.includes(bot.id));

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg mt-6">
      <div className="px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
          Bot Performance Comparison
        </h3>
        <p className="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">
          Select bots to compare their performance metrics.
        </p>
      </div>

      {/* Bot Selection Area (Placeholder) */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
         <h4 className="text-md font-medium text-gray-700 dark:text-gray-300 mb-2">Select Bots to Compare:</h4>
         <div className="flex flex-wrap gap-4">
            {allBots.map(bot => (
               <div key={bot.id} className="flex items-center">
                  <input
                     id={`compare-${bot.id}`}
                     name={`compare-${bot.id}`}
                     type="checkbox"
                     checked={selectedBots.includes(bot.id)}
                     onChange={() => handleSelectBot(bot.id)}
                     className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                  />
                  <label htmlFor={`compare-${bot.id}`} className="ml-2 block text-sm text-gray-900 dark:text-gray-200">
                     {bot.name || `${bot.type} (${bot.symbol})`}
                  </label>
               </div>
            ))}
         </div>
         {/* TODO: Replace checkboxes with a better multi-select component if needed */}
      </div>

      {/* Comparison Table */}
      <div className="overflow-x-auto">
         {isLoading && <p className="p-4 text-gray-500 dark:text-gray-400">Loading comparison data...</p>}
         {error && <p className="p-4 text-red-600 dark:text-red-400">{error}</p>}
         
         {!isLoading && !error && botsToCompare.length > 0 && (
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
               <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                     <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Metric</th>
                     {botsToCompare.map(bot => (
                        <th key={bot.id} scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                           {bot.name || `${bot.type} (${bot.symbol})`}
                        </th>
                     ))}
                  </tr>
               </thead>
               <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600">
                  {/* Example Rows - Add more metrics */}
                  <tr>
                     <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">Total P/L</td>
                     {botsToCompare.map(bot => (
                        <td key={bot.id} className={`px-6 py-4 whitespace-nowrap text-right text-sm font-medium ${bot.performance?.totalPL >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                           {formatCurrency(bot.performance?.totalPL)}
                        </td>
                     ))}
                  </tr>
                   <tr>
                     <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">Win Rate</td>
                     {botsToCompare.map(bot => (
                        <td key={bot.id} className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500 dark:text-gray-400">
                           {bot.performance?.winRate?.toFixed(1) ?? '--'}%
                        </td>
                     ))}
                  </tr>
                   <tr>
                     <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">Total Trades</td>
                     {botsToCompare.map(bot => (
                        <td key={bot.id} className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500 dark:text-gray-400">
                           {bot.performance?.totalTrades ?? '--'}
                        </td>
                     ))}
                  </tr>
                  {/* Add more rows for other metrics (Sharpe Ratio, Max Drawdown, etc.) */}
               </tbody>
            </table>
         )}
         {!isLoading && !error && botsToCompare.length === 0 && (
             <p className="p-4 text-center text-sm text-gray-500 dark:text-gray-400">Select at least one bot to compare.</p>
         )}
      </div>
    </div>
  );
}