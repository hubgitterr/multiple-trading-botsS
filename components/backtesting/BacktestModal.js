'use client';

import React, { useState, useEffect, useCallback } from 'react';
import axiosInstance from '../../lib/axiosInstance'; // Import axios instance

export default function BacktestModal({ isOpen, onClose, onSubmit, configId }) {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [interval, setInterval] = useState('1d'); // Default interval
  const [initialCapital, setInitialCapital] = useState(10000); // Default value
  const [formError, setFormError] = useState(''); // Renamed to avoid conflict
  const [isSubmitting, setIsSubmitting] = useState(false);

  // State for saved results list
  const [savedResults, setSavedResults] = useState([]);
  const [selectedResultIds, setSelectedResultIds] = useState(new Set());
  const [isLoadingResults, setIsLoadingResults] = useState(false);
  const [resultsError, setResultsError] = useState(null);
  const [comparisonResults, setComparisonResults] = useState(null); // State for comparison data

  // Reset form when modal opens or configId changes
  useEffect(() => {
    if (isOpen) {
      const today = new Date().toISOString().split('T')[0];
      const oneYearAgo = new Date();
      oneYearAgo.setFullYear(oneYearAgo.getFullYear() - 1);
      const oneYearAgoStr = oneYearAgo.toISOString().split('T')[0];

      setStartDate(oneYearAgoStr); // Default start date: 1 year ago
      setEndDate(today); // Default end date: today
      setInitialCapital(10000);
      setInterval('1d'); // Reset interval to default
      setFormError('');
      setIsSubmitting(false);
      // Reset results state as well
      setSavedResults([]);
      setSelectedResultIds(new Set());
      setIsLoadingResults(false);
      setResultsError(null);
      setComparisonResults(null); // Also clear comparison on open
    }
  }, [isOpen, configId]);

  // Fetch saved results when the modal opens
  useEffect(() => {
    if (isOpen) {
      const fetchResults = async () => {
        setIsLoadingResults(true);
        setResultsError(null);
        try {
          // Assuming the backend expects configId as a filter, adjust if needed
          // If no filtering is needed, remove the params object
          const response = await axiosInstance.get('backtest/results/'); // Use relative path as baseURL includes /api
          // Assuming the response data is an array of results under a 'results' key or similar
          // Adjust data access based on the actual API response structure
          setSavedResults(response.data || []);
        } catch (err) {
          console.error("Error fetching saved backtest results:", err);
          setResultsError(err.response?.data?.detail || err.message || 'Failed to load saved results.');
        } finally {
          setIsLoadingResults(false);
        }
      };
      fetchResults();
    }
  }, [isOpen]); // Re-fetch when modal opens

  // Handler for checkbox changes
  const handleCheckboxChange = useCallback((resultId) => {
    setSelectedResultIds(prevSelectedIds => {
      const newSelectedIds = new Set(prevSelectedIds);
      if (newSelectedIds.has(resultId)) {
        newSelectedIds.delete(resultId);
      } else {
        newSelectedIds.add(resultId);
      }
      return newSelectedIds;
    });
  }, []);

  // Simple formatting helpers (could be moved to utils later)
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch (e) {
      return dateString; // Return original if formatting fails
    }
  };

  const formatCurrency = (amount) => {
    if (amount === null || amount === undefined) return 'N/A';
    return amount.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
  };

  // Handler for the "Compare Selected" button
  const handleCompareClick = () => {
    const selectedObjects = savedResults.filter(result =>
      selectedResultIds.has(result.id) // Using Set's has method
    );
    setComparisonResults(selectedObjects);
  };

  const validateForm = () => {
    if (!startDate || !endDate || !initialCapital) {
      setFormError('Start date, end date, and initial capital are required.');
      return false;
    }
    if (new Date(endDate) <= new Date(startDate)) {
      setFormError('End date must be after start date.');
      return false;
    }
    if (initialCapital <= 0) {
      setFormError('Initial capital must be positive.');
      return false;
    }
    setFormError('');
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm() || isSubmitting) {
      return;
    }
    setIsSubmitting(true);
    setFormError(''); // Clear previous form errors

    try {
      await onSubmit({
        start_date: startDate,
        end_date: endDate,
        interval: interval,
        initial_capital: Number(initialCapital),
      });
      // onSubmit should handle closing the modal on success if desired
    } catch (apiError) {
      console.error("Backtest submission error:", apiError);
      setFormError(apiError.response?.data?.detail || apiError.message || 'Failed to start backtest.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-gray-600 bg-opacity-75 transition-opacity">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay, click outside to close */}
        <div className="fixed inset-0 transition-opacity" aria-hidden="true" onClick={onClose}>
          <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>

        {/* This element is to trick the browser into centering the modal contents. */}
        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full"
             role="dialog" aria-modal="true" aria-labelledby="modal-headline">
          <form onSubmit={handleSubmit}>
            <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <div className="sm:flex sm:items-start w-full">
                <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                  <div className="flex justify-between items-center">
                     <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white" id="modal-headline">
                       Configure Backtest (ID: {configId})
                     </h3>
                     <button
                       type="button"
                       onClick={onClose}
                       className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none"
                       disabled={isSubmitting}
                     >
                       &times; {/* Close button */}
                     </button>
                  </div>

                  <div className="mt-4 space-y-4">
                    {/* Start Date */}
                    <div>
                      <label htmlFor="start-date" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        Start Date
                      </label>
                      <input
                        type="date"
                        id="start-date"
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        className="mt-1 block w-full pl-3 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white"
                        required
                        disabled={isSubmitting}
                      />
                    </div>

                    {/* End Date */}
                    <div>
                      <label htmlFor="end-date" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        End Date
                      </label>
                      <input
                        type="date"
                        id="end-date"
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        className="mt-1 block w-full pl-3 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white"
                        required
                        disabled={isSubmitting}
                      />
                    </div>

                    {/* Interval */}
                    <div>
                      <label htmlFor="interval" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        Interval
                      </label>
                      <select
                        id="interval"
                        value={interval}
                        onChange={(e) => setInterval(e.target.value)}
                        className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md dark:bg-gray-700 dark:text-white"
                        required
                        disabled={isSubmitting}
                      >
                        <option value="1m">1 Minute</option>
                        <option value="5m">5 Minutes</option>
                        <option value="15m">15 Minutes</option>
                        <option value="1h">1 Hour</option>
                        <option value="4h">4 Hours</option>
                        <option value="1d">1 Day</option>
                      </select>
                    </div>

                    {/* Initial Capital */}
                    <div>
                      <label htmlFor="initial-capital" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        Initial Capital ($)
                      </label>
                      <input
                        type="number"
                        id="initial-capital"
                        value={initialCapital}
                        onChange={(e) => setInitialCapital(parseFloat(e.target.value) || 0)}
                        min="1" // Basic HTML5 validation
                        step="any" // Allow decimals if needed, though backend might expect integer
                        className="mt-1 block w-full pl-3 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white"
                        required
                        disabled={isSubmitting}
                      />
                    </div>

                    {/* Error Message */}
                    {formError && (
                      <p className="text-sm text-red-600 dark:text-red-400">{formError}</p>
                    )}
                  </div>

                  {/* Section for Saved Results */}
                  <div className="mt-6 border-t border-gray-200 dark:border-gray-700 pt-4">
                    <h4 className="text-md font-medium text-gray-800 dark:text-gray-200 mb-3">
                      Select Saved Results to Compare
                    </h4>
                    {isLoadingResults && <p className="text-sm text-gray-500 dark:text-gray-400">Loading saved results...</p>}
                    {resultsError && <p className="text-sm text-red-600 dark:text-red-400">Error: {resultsError}</p>}
                    {!isLoadingResults && !resultsError && (
                      <div className="max-h-60 overflow-y-auto space-y-2 pr-2">
                        {savedResults.length === 0 ? (
                          <p className="text-sm text-gray-500 dark:text-gray-400">No saved results found.</p>
                        ) : (
                          savedResults.map((result) => (
                            <div key={result.id} className="flex items-center justify-between p-2 border border-gray-200 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700">
                              <div className="flex items-center space-x-3">
                                <input
                                  type="checkbox"
                                  id={`result-${result.id}`}
                                  checked={selectedResultIds.has(result.id)}
                                  onChange={() => handleCheckboxChange(result.id)}
                                  className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500 dark:bg-gray-700 dark:border-gray-600"
                                  disabled={isSubmitting}
                                />
                                <label htmlFor={`result-${result.id}`} className="text-sm text-gray-700 dark:text-gray-300 cursor-pointer">
                                  <span className="font-medium">Run:</span> {formatDate(result.run_timestamp)} (<span className="font-medium">Profit:</span> {formatCurrency(result.total_profit)})
                                  <br />
                                  <span className="text-xs text-gray-500 dark:text-gray-400">
                                    Config: {result.bot_config_id} | {formatDate(result.start_date)} - {formatDate(result.end_date)}
                                  </span>
                                </label>
                              </div>
                              {/* Add a button/link to view details if needed later */}
                            </div>
                          ))
                        )}
                      </div>
                    )}
                     {/* Placeholder for Compare Button - to be implemented later */}
                     {selectedResultIds.size > 1 && (
                        <div className="mt-4 text-right">
                            <button
                                type="button"
                                onClick={handleCompareClick} // Attach the handler
                                className="inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-green-600 text-base font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 sm:text-sm"
                                disabled={isSubmitting || selectedResultIds.size < 2} // Disable if form is submitting or less than 2 selected
                            >
                                Compare Selected ({selectedResultIds.size})
                            </button>
                        </div>
                    )}
                  </div>
                  {/* End Section for Saved Results */}

                  {/* Section for Comparison Results */}
                  {comparisonResults && (
                    <div className="mt-6 border-t border-gray-200 dark:border-gray-700 pt-4">
                      <div className="flex justify-between items-center mb-3">
                        <h4 className="text-md font-medium text-gray-800 dark:text-gray-200">
                          Comparison Results
                        </h4>
                        <button
                          type="button"
                          onClick={() => setComparisonResults(null)}
                          className="text-sm text-indigo-600 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-300"
                        >
                          Clear Comparison
                        </button>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                          <thead className="bg-gray-50 dark:bg-gray-700">
                            <tr>
                              <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                Metric
                              </th>
                              {comparisonResults.map((result) => (
                                <th key={result.id} scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                                  Run {formatDate(result.run_timestamp)}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                            {/* Define metrics to compare */}
                            {[
                              { key: 'total_profit', label: 'Total Profit', format: formatCurrency },
                              { key: 'sharpe_ratio', label: 'Sharpe Ratio', format: (v) => v?.toFixed(3) ?? 'N/A' },
                              { key: 'max_drawdown', label: 'Max Drawdown', format: (v) => v ? `${(v * 100).toFixed(2)}%` : 'N/A' },
                              { key: 'win_rate', label: 'Win Rate', format: (v) => v ? `${(v * 100).toFixed(2)}%` : 'N/A' },
                              { key: 'total_trades', label: 'Total Trades', format: (v) => v ?? 'N/A' },
                              { key: 'start_date', label: 'Start Date', format: formatDate },
                              { key: 'end_date', label: 'End Date', format: formatDate },
                              { key: 'initial_capital', label: 'Initial Capital', format: formatCurrency },
                              { key: 'final_balance', label: 'Final Balance', format: formatCurrency },
                              { key: 'interval', label: 'Interval', format: (v) => v ?? 'N/A' },
                              { key: 'bot_config_id', label: 'Config ID', format: (v) => v ?? 'N/A' },
                            ].map(({ key, label, format }) => (
                              <tr key={key}>
                                <td className="px-4 py-2 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">{label}</td>
                                {comparisonResults.map((result) => (
                                  <td key={`${result.id}-${key}`} className="px-4 py-2 whitespace-nowrap text-sm text-gray-500 dark:text-gray-300">
                                    {format(result[key])}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                  {/* End Section for Comparison Results */}

                </div>
              </div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse items-center">
             {/* Submit Button for New Backtest */}
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
              >
                {isSubmitting ? 'Starting Backtest...' : 'Start Backtest'}
              </button>
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 dark:border-gray-600 shadow-sm px-4 py-2 bg-white dark:bg-gray-800 text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}