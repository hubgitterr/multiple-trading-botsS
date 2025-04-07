// components/dashboard/Backtest.js
'use client'; // Mark as client component for state and interactions

import React, { useState, useEffect } from 'react';
import axiosInstance from '../../lib/axiosInstance'; // Import configured Axios instance
// Import result visualization component later
// import BacktestResults from './BacktestResults';

export default function BacktestInterface() {
  // --- State ---
  const [botConfigs, setBotConfigs] = useState([ // Placeholder: Fetch actual configs
     { id: 'dummy-config-1', name: 'Dummy BTC 1h', bot_type: 'DummyBot', symbol: 'BTCUSDT', settings: {} },
     { id: 'momentum-123', name: 'Momentum ETH 1h', bot_type: 'MomentumBot', symbol: 'ETHUSDT', settings: { interval: '1h' } },
     { id: 'grid-456', name: 'Grid ADA', bot_type: 'GridBot', symbol: 'ADAUSDT', settings: { lower_price: 0.5, upper_price: 0.7, num_grids: 10 } },
     { id: 'dca-789', name: 'DCA BTC Weekly', bot_type: 'DCABot', symbol: 'BTCUSDT', settings: { purchase_amount: 100, purchase_frequency_hours: 168 } },
  ]);
  const [selectedConfigId, setSelectedConfigId] = useState('');
  const [startDate, setStartDate] = useState('2023-01-01'); // Default start date
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]); // Default end date (today)
  const [initialCapital, setInitialCapital] = useState(10000);
  const [commission, setCommission] = useState(0.1); // Commission in percent

  const [isRunning, setIsRunning] = useState(false);
  const [backtestResults, setBacktestResults] = useState(null);
  const [error, setError] = useState(null);

  // TODO: Fetch bot configurations from API
  // useEffect(() => {
  //    const fetchConfigs = async () => {
  //       try {
  //          // const response = await axios.get('/api/bots/configs');
  //          // setBotConfigs(response.data);
  //          // if (response.data.length > 0) {
  //          //    setSelectedConfigId(response.data[0].id); // Select first by default
  //          // }
  //       } catch (err) {
  //          console.error("Error fetching bot configs:", err);
  //          setError("Failed to load bot configurations.");
  //       }
  //    };
  //    fetchConfigs();
  // }, []);

  const handleRunBacktest = async (event) => {
    event.preventDefault();
    if (!selectedConfigId) {
      setError("Please select a bot configuration to backtest.");
      return;
    }

    setIsRunning(true);
    setError(null);
    setBacktestResults(null); // Clear previous results
    console.log(`Running backtest for config: ${selectedConfigId}, Start: ${startDate}, End: ${endDate}`);

    // Implement API call to backend backtesting endpoint
    try {
      const payload = {
        config_id: selectedConfigId,
        start_date: startDate,
        end_date: endDate,
        initial_capital: initialCapital,
        commission_percent: commission / 100.0, // Convert percentage to decimal
      };
      console.log("Sending backtest request:", payload); // Log the payload

      const response = await axiosInstance.post('/backtest/run', payload);

      console.log("Backtest response received:", response.data); // Log the response
      setBacktestResults(response.data);

    } catch (err) {
       console.error("Backtest error:", err);
       setError(err.response?.data?.detail || "An error occurred during the backtest.");
       setBacktestResults(null);
    } finally {
       setIsRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Configuration Section */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-white mb-4">Configure Backtest</h3>
        <form onSubmit={handleRunBacktest} className="space-y-4">
          {/* Bot Selection */}
          <div>
            <label htmlFor="botConfig" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Bot Configuration</label>
            <select
              id="botConfig"
              name="botConfig"
              value={selectedConfigId}
              onChange={(e) => setSelectedConfigId(e.target.value)}
              required
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md dark:bg-gray-700 dark:text-white"
            >
              <option value="" disabled>Select a configuration...</option>
              {botConfigs.map(config => (
                <option key={config.id} value={config.id}>
                  {config.name || `${config.bot_type} (${config.symbol})`}
                </option>
              ))}
            </select>
          </div>

          {/* Date Range */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="startDate" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Start Date</label>
              <input
                type="date"
                id="startDate"
                name="startDate"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white"
              />
            </div>
            <div>
              <label htmlFor="endDate" className="block text-sm font-medium text-gray-700 dark:text-gray-300">End Date</label>
              <input
                type="date"
                id="endDate"
                name="endDate"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>

           {/* Capital & Commission */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
             <div>
               <label htmlFor="initialCapital" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Initial Capital ($)</label>
               <input
                 type="number"
                 id="initialCapital"
                 name="initialCapital"
                 value={initialCapital}
                 onChange={(e) => setInitialCapital(parseFloat(e.target.value))}
                 min="1"
                 required
                 className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white"
               />
             </div>
              <div>
               <label htmlFor="commission" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Commission (%)</label>
               <input
                 type="number"
                 step="0.01"
                 id="commission"
                 name="commission"
                 value={commission}
                 onChange={(e) => setCommission(parseFloat(e.target.value))}
                 min="0"
                 max="10"
                 required
                 className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white"
               />
             </div>
          </div>


          {/* Run Button */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={isRunning || !selectedConfigId}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {isRunning ? 'Running Backtest...' : 'Run Backtest'}
            </button>
          </div>
           {error && <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>}
        </form>
      </div>

      {/* Results Section */}
      {isRunning && (
         <div className="text-center p-4 text-gray-500 dark:text-gray-400">
            Running backtest, please wait...
            {/* Optional: Add a spinner */}
         </div>
      )}

      {backtestResults && !isRunning && (
         <div className="mt-6">
            <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-white mb-4">Backtest Results</h3>
            {/* TODO: Pass results to a dedicated results component */}
            {/* <BacktestResults results={backtestResults} /> */}
            <pre className="bg-gray-100 dark:bg-gray-900 p-4 rounded overflow-x-auto text-xs text-gray-700 dark:text-gray-300">
               {JSON.stringify(backtestResults, null, 2)}
            </pre>
         </div>
      )}
    </div>
  );
}