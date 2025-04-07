// components/dashboard/MarketOverview.js
'use client'; // Mark as client component

import React from 'react';
import PriceTicker from './PriceTicker'; // Import the ticker component

export default function MarketOverview() {
  // List of symbols to display in the overview
  // TODO: Make this configurable or fetch from user preferences/API
  const symbols = ['BTCUSDT', 'ETHUSDT', 'BNBBUSD', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT'];

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
       <div className="px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-gray-700">
         <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
           Market Overview
         </h3>
         <p className="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">
           Live prices for selected markets.
         </p>
       </div>
       <div className="p-4 grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
         {symbols.map((symbol) => (
           <PriceTicker key={symbol} symbol={symbol} />
         ))}
       </div>
    </div>
  );
}