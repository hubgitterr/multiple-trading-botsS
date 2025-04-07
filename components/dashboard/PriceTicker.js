// components/dashboard/PriceTicker.js
'use client'; // Mark as client component for state and potential real-time updates

import React, { useState, useEffect } from 'react';
// import useSWR from 'swr'; // For data fetching later
// import { // Icons for price up/down
//   ArrowSmUpIcon,
//   ArrowSmDownIcon,
// } from '@heroicons/react/solid'; 

// Placeholder fetcher function
// const fetcher = url => fetch(url).then(res => res.json());

// Helper to format price
const formatPrice = (price) => {
  if (price === null || price === undefined) return '---';
  // Adjust formatting based on price magnitude
  if (price > 1000) return price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  if (price > 1) return price.toLocaleString('en-US', { minimumFractionDigits: 4, maximumFractionDigits: 4 });
  return price.toLocaleString('en-US', { minimumFractionDigits: 8, maximumFractionDigits: 8 });
};

export default function PriceTicker({ symbol }) {
  const [currentPrice, setCurrentPrice] = useState(null);
  const [previousPrice, setPreviousPrice] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // TODO: Implement real-time data fetching (e.g., WebSockets or frequent polling with SWR)
  useEffect(() => {
    // Placeholder: Simulate fetching initial price and then updates
    setIsLoading(true);
    setError(null);
    const fetchInitialPrice = async () => {
      try {
        // Replace with actual API call: e.g., fetch(`/api/market/price/${symbol}`)
        await new Promise(resolve => setTimeout(resolve, 300)); // Simulate delay
        const initialPrice = Math.random() * 50000 + 10000; // Random initial price
        setCurrentPrice(initialPrice);
        setPreviousPrice(initialPrice); // Set previous price initially
        setIsLoading(false);
      } catch (err) {
        console.error(`Error fetching initial price for ${symbol}:`, err);
        setError('Failed to load price');
        setIsLoading(false);
      }
    };

    fetchInitialPrice();

    // Simulate price updates every few seconds
    const intervalId = setInterval(() => {
      setCurrentPrice(prevPrice => {
        if (prevPrice === null) return null;
        setPreviousPrice(prevPrice); // Update previous price
        const change = (Math.random() - 0.5) * (prevPrice * 0.005); // Simulate small % change
        return Math.max(0, prevPrice + change); // Ensure price doesn't go negative
      });
    }, 5000); // Update every 5 seconds

    return () => clearInterval(intervalId); // Cleanup interval on unmount
  }, [symbol]); // Re-run effect if symbol changes

  const priceChange = currentPrice !== null && previousPrice !== null ? currentPrice - previousPrice : 0;
  const priceChangePercent = previousPrice !== null && previousPrice !== 0 ? (priceChange / previousPrice) * 100 : 0;
  const priceColor = priceChange >= 0 ? 'text-green-500 dark:text-green-400' : 'text-red-500 dark:text-red-400';

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-4 flex flex-col items-center justify-center min-w-[150px]">
      <p className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">{symbol}</p>
      {isLoading ? (
         <div className="h-6 mt-1 w-20 bg-gray-300 dark:bg-gray-600 rounded animate-pulse"></div>
      ) : error ? (
         <p className="mt-1 text-sm text-red-500 dark:text-red-400">{error}</p>
      ) : (
        <>
          <p className={`mt-1 text-xl font-semibold text-gray-900 dark:text-white ${priceColor}`}>
            {formatPrice(currentPrice)}
          </p>
          <p className={`mt-1 text-xs flex items-center ${priceColor}`}>
             {/* Placeholder Icons */}
             {priceChange >= 0 ? 
                <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 mr-0.5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" /></svg> 
                : 
                <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 mr-0.5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" /></svg>
             }
            {priceChange.toFixed(4)} ({priceChangePercent.toFixed(2)}%)
          </p>
        </>
      )}
    </div>
  );
}