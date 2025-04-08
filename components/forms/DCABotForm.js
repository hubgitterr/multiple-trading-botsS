// components/forms/DCABotForm.js
'use client';

import React, { useState, useEffect } from 'react'; // Added useEffect
import { useForm } from 'react-hook-form';
// Removed axiosInstance import as parent handles submission

// Accept isSubmitting prop from parent
export default function DCABotForm({ onSubmit, initialData = {}, isSubmitting }) {
  const { register, handleSubmit, formState: { errors }, reset } = useForm({ // Removed isSubmitting from formState destructuring
    // Use initialData for defaultValues directly
    defaultValues: initialData ? {
      name: initialData.name || '', // Add name if it exists in your model
      symbol: initialData.symbol || 'BTCUSDT',
      settings: {
        purchase_amount: initialData.settings?.purchase_amount || '',
        purchase_frequency_hours: initialData.settings?.purchase_frequency_hours || 168,
      },
      is_enabled: initialData.is_enabled !== undefined ? initialData.is_enabled : true, // Add is_enabled
    } : {
      name: '',
      symbol: 'BTCUSDT',
      settings: { purchase_amount: '', purchase_frequency_hours: 168 },
      is_enabled: true,
    }
  });

  // Reset form when initialData changes (e.g., when opening edit form)
  useEffect(() => {
    if (initialData) {
      reset({
        name: initialData.name || '',
        symbol: initialData.symbol || 'BTCUSDT',
        settings: {
          purchase_amount: initialData.settings?.purchase_amount || '',
          purchase_frequency_hours: initialData.settings?.purchase_frequency_hours || 168,
        },
        is_enabled: initialData.is_enabled !== undefined ? initialData.is_enabled : true,
      });
    } else {
      // Reset to default create state if initialData becomes null/undefined
       reset({
        name: '',
        symbol: 'BTCUSDT',
        settings: { purchase_amount: '', purchase_frequency_hours: 168 },
        is_enabled: true,
      });
    }
  }, [initialData?.id, reset]); // Depend on ID instead of object reference
  const [apiError, setApiError] = useState(null);
  // Remove initialApiKeyId calculation

  // Simplified submit handler: format data and pass to parent onSubmit
  const handleFormSubmit = (data) => {
    setApiError(null);
    const payload = {
      bot_type: 'DCABot',
      name: data.name, // Include name
      symbol: data.symbol,
      settings: {
        purchase_amount: parseFloat(data.settings.purchase_amount),
        purchase_frequency_hours: parseInt(data.settings.purchase_frequency_hours, 10),
      },
      is_enabled: data.is_enabled, // Include is_enabled
    };
    // Pass the formatted payload to the parent's submit handler
    onSubmit(payload);
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-white">DCA Bot Configuration</h3>
      
      {/* Add Name Field */}
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Bot Name</label>
        <input
          type="text"
          id="name"
          {...register("name", { required: "Bot name is required" })}
          className={`mt-1 block w-full px-3 py-2 border ${errors.name ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`}
        />
        {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>}
      </div>

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

      {/* Add is_enabled Checkbox */}
       <div className="flex items-center">
         <input
           id="is_enabled"
           type="checkbox"
           {...register("is_enabled")}
           className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded dark:bg-gray-700 dark:border-gray-600"
         />
         <label htmlFor="is_enabled" className="ml-2 block text-sm text-gray-900 dark:text-gray-300">
           Enable this bot configuration?
         </label>
       </div>

      {/* Display API error if passed down (though parent handles it now) */}
      {/* {apiError && (
        <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          <p className="font-medium">Error:</p>
          <p>{apiError}</p>
        </div>
      )} */}

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