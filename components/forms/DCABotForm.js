// components/forms/DCABotForm.js
'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import axiosInstance from '../../lib/axiosInstance'; // Import the configured Axios instance

export default function DCABotForm({ onSubmit, initialData = {} }) { // Remove isSubmitting from props, use formState
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({ // Use formState.isSubmitting
    defaultValues: {
      symbol: initialData.symbol || 'BTCUSDT',
      settings: {
        purchase_amount: initialData.settings?.purchase_amount || '',
        purchase_frequency_hours: initialData.settings?.purchase_frequency_hours || 168,
      }
    }
  });
  const [apiError, setApiError] = useState(null); // State for API errors

  const handleFormSubmit = async (data) => {
    setApiError(null); // Clear previous errors
    const payload = {
      bot_type: 'DCABot',
      symbol: data.symbol,
      settings: {
        purchase_amount: parseFloat(data.settings.purchase_amount),
        purchase_frequency_hours: parseInt(data.settings.purchase_frequency_hours, 10),
        // Add other settings as needed
      }
    };

    // Base URL is handled by axiosInstance
    const method = initialData.id ? 'put' : 'post';
    const url = initialData.id ? `/bots/configs/${initialData.id}` : '/bots/configs'; // Use relative paths

    try {
      // Use axiosInstance, headers are handled by the interceptor
      const response = await axiosInstance({
        method: method,
        url: url,
        data: payload,
      });
      console.log('API Response:', response.data);
      onSubmit(response.data); // Pass the response data (or confirmation) back up
    } catch (error) {
      console.error('API Submission Error:', error.response?.data || error.message);
      setApiError(error.response?.data?.detail || error.message || 'An unexpected error occurred.');
    }
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-white">DCA Bot Configuration</h3>
      
      <div>
        <label htmlFor="symbol" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Symbol</label>
        <input
          type="text"
          id="symbol"
          {...register("symbol", { required: "Symbol is required" })}
          className={`mt-1 block w-full px-3 py-2 border ${errors.symbol ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`}
        />
        {errors.symbol && <p className="mt-1 text-sm text-red-600">{errors.symbol.message}</p>}
      </div>

      <div>
        <label htmlFor="purchase_amount" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Purchase Amount (Quote Asset)</label>
        <input
          type="number"
          step="any"
          id="purchase_amount"
          {...register("settings.purchase_amount", {
            required: "Purchase amount is required",
            valueAsNumber: true,
            validate: value => value > 0 || "Purchase amount must be positive"
          })}
          className={`mt-1 block w-full px-3 py-2 border ${errors.settings?.purchase_amount ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`}
        />
        {errors.settings?.purchase_amount && <p className="mt-1 text-sm text-red-600">{errors.settings.purchase_amount.message}</p>}
      </div>
      <div>
        <label htmlFor="purchase_frequency_hours" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Purchase Frequency (Hours)</label>
        <input
          type="number"
          id="purchase_frequency_hours"
          {...register("settings.purchase_frequency_hours", {
            required: "Purchase frequency is required",
            valueAsNumber: true,
            min: { value: 1, message: "Frequency must be at least 1 hour" },
            validate: value => Number.isInteger(value) || "Frequency must be an integer"
          })}
          className={`mt-1 block w-full px-3 py-2 border ${errors.settings?.purchase_frequency_hours ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`}
        />
        {errors.settings?.purchase_frequency_hours && <p className="mt-1 text-sm text-red-600">{errors.settings.purchase_frequency_hours.message}</p>}
      </div>

      {/* TODO: Add fields for Dip Buying and Trailing Stop Loss later */}
      {/* <div className="relative flex items-start mt-4">
         <div className="flex items-center h-5">
           <input id="enable_dip_buying" name="enable_dip_buying" type="checkbox" className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded" />
         </div>
         <div className="ml-3 text-sm">
           <label htmlFor="enable_dip_buying" className="font-medium text-gray-700 dark:text-gray-300">Enable Dip Buying</label>
         </div>
       </div> */}

      {apiError && (
        <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          <p className="font-medium">Error:</p>
          <p>{apiError}</p>
        </div>
      )}

      <div className="pt-2">
        <button
          type="submit"
          disabled={isSubmitting}
          className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          {isSubmitting ? 'Saving...' : (initialData.id ? 'Update Configuration' : 'Create Configuration')}
        </button>
      </div>
    </form>
  );
}