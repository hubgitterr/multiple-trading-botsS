// components/forms/MomentumBotForm.js
'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import axiosInstance from '../../lib/axiosInstance'; // Import the configured Axios instance

export default function MomentumBotForm({ onSubmit, initialData = {}, isSubmitting: parentIsSubmitting }) {
  const { register, handleSubmit, formState: { errors, isSubmitting: formIsSubmitting }, setError, reset } = useForm({
    defaultValues: {
      name: initialData.name || '',
      symbol: initialData.symbol || 'BTCUSDT',
      settings: {
        interval: initialData.settings?.interval || '1h',
        rsi_period: initialData.settings?.rsi_period || 14,
        rsi_overbought: initialData.settings?.rsi_overbought || 70,
        rsi_oversold: initialData.settings?.rsi_oversold || 30,
        macd_fast: initialData.settings?.macd_fast || 12,
        macd_slow: initialData.settings?.macd_slow || 26,
        macd_signal: initialData.settings?.macd_signal || 9,
        ema_period: initialData.settings?.ema_period || 200,
        order_quantity: initialData.settings?.order_quantity || 0.001,
      }
    }
  });
  const [apiError, setApiError] = useState(null);

  const handleFormSubmit = async (data) => {
    console.log("MomentumBotForm handleFormSubmit called with data:", data); // Add log here
    setApiError(null); // Clear previous errors
    const payload = {
      name: data.name,
      bot_type: 'MomentumBot',
      symbol: data.symbol,
      settings: {
        interval: data.settings.interval,
        rsi_period: parseInt(data.settings.rsi_period, 10),
        rsi_overbought: parseInt(data.settings.rsi_overbought, 10),
        rsi_oversold: parseInt(data.settings.rsi_oversold, 10),
        macd_fast: parseInt(data.settings.macd_fast, 10),
        macd_slow: parseInt(data.settings.macd_slow, 10),
        macd_signal: parseInt(data.settings.macd_signal, 10),
        ema_period: parseInt(data.settings.ema_period, 10),
        order_quantity: parseFloat(data.settings.order_quantity),
      }
    };

    const url = initialData.id
      ? `/bots/configs/${initialData.id}` // Use relative path
      : '/bots/configs'; // Use relative path
    const method = initialData.id ? 'put' : 'post';

    try {
      const response = await axiosInstance[method](url, payload);
      onSubmit(response.data); // Pass response data to parent handler
      // Optionally reset form after successful submission
      // if (!initialData.id) reset();
    } catch (error) {
      console.error("API Error:", error.response?.data || error.message);
      const errorMsg = error.response?.data?.detail || 'Failed to save configuration. Please try again.';
      setApiError(errorMsg);
      // Optionally set field errors if the API provides them
      // setError("root.serverError", { type: "manual", message: errorMsg });
    }
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-white">Momentum Bot Configuration</h3>

      {apiError && <p className="mt-2 text-sm text-red-600">{apiError}</p>}
      {/* {errors.root?.serverError && <p className="mt-2 text-sm text-red-600">{errors.root.serverError.message}</p>} */}

      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Bot Name</label>
        <input
          type="text"
          name="name"
          id="name"
          {...register("name", { required: "Bot name is required" })}
          className={`mt-1 block w-full px-3 py-2 border ${errors.name ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`}
        />
        {errors.name && <p className="mt-1 text-xs text-red-500">{errors.name.message}</p>}
      </div>

      <div>
        <label htmlFor="symbol" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Symbol (e.g., BTCUSDT)</label>
        <input
          type="text"
          name="symbol"
          id="symbol"
          {...register("symbol", { required: "Symbol is required" })}
          className={`mt-1 block w-full px-3 py-2 border ${errors.symbol ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`}
        />
        {errors.symbol && <p className="mt-1 text-xs text-red-500">{errors.symbol.message}</p>}
      </div>

      <div>
        <label htmlFor="interval" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Candle Interval</label>
        <select
          name="interval"
          id="interval"
          {...register("settings.interval")}
          className={`mt-1 block w-full pl-3 pr-10 py-2 text-base border ${errors.settings?.interval ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md dark:bg-gray-700 dark:text-white`}
        >
          <option value="1m">1 Minute</option>
          <option value="5m">5 Minutes</option>
          <option value="15m">15 Minutes</option>
          <option value="1h">1 Hour</option>
          <option value="4h">4 Hours</option>
          <option value="1d">1 Day</option>
        </select>
      </div>
      
      {/* --- Indicator Settings --- */}
      <h4 className="text-md font-medium text-gray-800 dark:text-gray-200 pt-2">Indicator Settings</h4>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label htmlFor="rsi_period" className="block text-sm font-medium text-gray-700 dark:text-gray-300">RSI Period</label>
          <input
            type="number"
            id="rsi_period"
            min="1"
            {...register("settings.rsi_period", { required: "RSI Period is required", valueAsNumber: true, min: { value: 1, message: "Must be at least 1" } })}
            className={`mt-1 block w-full px-3 py-2 border ${errors.settings?.rsi_period ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`}
          />
          {errors.settings?.rsi_period && <p className="mt-1 text-xs text-red-500">{errors.settings.rsi_period.message}</p>}
        </div>
        <div>
          <label htmlFor="rsi_overbought" className="block text-sm font-medium text-gray-700 dark:text-gray-300">RSI Overbought</label>
          <input type="number" id="rsi_overbought" min="50" max="100" {...register("settings.rsi_overbought", { required: true, valueAsNumber: true, min: 50, max: 100 })} className={`mt-1 block w-full px-3 py-2 border ${errors.settings?.rsi_overbought ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`} />
          {errors.settings?.rsi_overbought && <p className="mt-1 text-xs text-red-500">Overbought level required (50-100)</p>}
        </div>
        <div>
          <label htmlFor="rsi_oversold" className="block text-sm font-medium text-gray-700 dark:text-gray-300">RSI Oversold</label>
          <input type="number" id="rsi_oversold" min="0" max="50" {...register("settings.rsi_oversold", { required: true, valueAsNumber: true, min: 0, max: 50 })} className={`mt-1 block w-full px-3 py-2 border ${errors.settings?.rsi_oversold ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`} />
          {errors.settings?.rsi_oversold && <p className="mt-1 text-xs text-red-500">Oversold level required (0-50)</p>}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label htmlFor="macd_fast" className="block text-sm font-medium text-gray-700 dark:text-gray-300">MACD Fast</label>
          <input type="number" id="macd_fast" min="1" {...register("settings.macd_fast", { required: true, valueAsNumber: true, min: 1 })} className={`mt-1 block w-full px-3 py-2 border ${errors.settings?.macd_fast ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`} />
          {errors.settings?.macd_fast && <p className="mt-1 text-xs text-red-500">Fast period required</p>}
        </div>
        <div>
          <label htmlFor="macd_slow" className="block text-sm font-medium text-gray-700 dark:text-gray-300">MACD Slow</label>
          <input type="number" id="macd_slow" min="1" {...register("settings.macd_slow", { required: true, valueAsNumber: true, min: 1 })} className={`mt-1 block w-full px-3 py-2 border ${errors.settings?.macd_slow ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`} />
          {errors.settings?.macd_slow && <p className="mt-1 text-xs text-red-500">Slow period required</p>}
        </div>
        <div>
          <label htmlFor="macd_signal" className="block text-sm font-medium text-gray-700 dark:text-gray-300">MACD Signal</label>
          <input type="number" id="macd_signal" min="1" {...register("settings.macd_signal", { required: true, valueAsNumber: true, min: 1 })} className={`mt-1 block w-full px-3 py-2 border ${errors.settings?.macd_signal ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`} />
          {errors.settings?.macd_signal && <p className="mt-1 text-xs text-red-500">Signal period required</p>}
        </div>
      </div>

      <div>
        <label htmlFor="ema_period" className="block text-sm font-medium text-gray-700 dark:text-gray-300">EMA Period (Trend Filter)</label>
        <input
          type="number"
          id="ema_period"
          min="1"
          {...register("settings.ema_period", { required: "EMA Period is required", valueAsNumber: true, min: { value: 1, message: "Must be at least 1" } })}
          className={`mt-1 block w-full px-3 py-2 border ${errors.settings?.ema_period ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`}
        />
        {errors.settings?.ema_period && <p className="mt-1 text-xs text-red-500">{errors.settings.ema_period.message}</p>}
      </div>

      {/* --- Order Settings --- */}
      <h4 className="text-md font-medium text-gray-800 dark:text-gray-200 pt-2">Order Settings</h4>

      <div>
        <label htmlFor="order_quantity" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Order Quantity (Base Asset)</label>
        <input
          type="number"
          step="any" // Allow decimals
          id="order_quantity"
          min="0"
          {...register("settings.order_quantity", {
            required: "Order quantity is required",
            valueAsNumber: true,
            validate: value => value > 0 || "Quantity must be positive"
          })}
          className={`mt-1 block w-full px-3 py-2 border ${errors.settings?.order_quantity ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`}
        />
        {errors.settings?.order_quantity && <p className="mt-1 text-xs text-red-500">{errors.settings.order_quantity.message}</p>}
      </div>

      <div className="pt-2">
        <button
          type="submit"
          disabled={parentIsSubmitting || formIsSubmitting} // Use parent prop or form state
          className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          {(parentIsSubmitting || formIsSubmitting) ? 'Saving...' : (initialData.id ? 'Update Configuration' : 'Create Configuration')}
        </button>
      </div>
    </form>
  );
}