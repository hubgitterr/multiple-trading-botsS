'use client';

import React, { useState, useEffect } from 'react';

export default function BacktestModal({ isOpen, onClose, onSubmit, configId }) {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [interval, setInterval] = useState('1d'); // Default interval
  const [initialCapital, setInitialCapital] = useState(10000); // Default value
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

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
      setError('');
      setIsSubmitting(false);
    }
  }, [isOpen, configId]);

  const validateForm = () => {
    if (!startDate || !endDate || !initialCapital) {
      setError('Start date, end date, and initial capital are required.');
      return false;
    }
    if (new Date(endDate) <= new Date(startDate)) {
      setError('End date must be after start date.');
      return false;
    }
    if (initialCapital <= 0) {
      setError('Initial capital must be positive.');
      return false;
    }
    setError('');
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm() || isSubmitting) {
      return;
    }
    setIsSubmitting(true);
    setError(''); // Clear previous errors

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
      setError(apiError.message || 'Failed to start backtest.');
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
                    {error && (
                      <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
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