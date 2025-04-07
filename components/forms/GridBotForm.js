// components/forms/GridBotForm.js
'use client';

import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import axiosInstance from '../../lib/axiosInstance'; // Import the configured Axios instance

export default function GridBotForm({ onSubmit, initialData = {}, isSubmitting: isSubmittingProp }) {
   const [apiError, setApiError] = useState(null);
   // Use isSubmitting from formState for button disabling
   const { register, handleSubmit, watch, formState: { errors, isSubmitting }, reset } = useForm({
     defaultValues: {
       symbol: initialData.symbol || 'BTCUSDT',
       lower_price: initialData.settings?.lower_price || '',
       upper_price: initialData.settings?.upper_price || '',
       num_grids: initialData.settings?.num_grids || 5,
       total_investment: initialData.settings?.total_investment || '',
       grid_type: initialData.settings?.grid_type || 'arithmetic',
     }
   });

   // Reset form if initialData changes (e.g., when selecting a different bot to edit)
   // useEffect(() => {
   //      reset({
   //          symbol: initialData.symbol || 'BTCUSDT',
   //          lower_price: initialData.settings?.lower_price || '',
   //          upper_price: initialData.settings?.upper_price || '',
   //          num_grids: initialData.settings?.num_grids || 5,
   //          total_investment: initialData.settings?.total_investment || '',
   //          grid_type: initialData.settings?.grid_type || 'arithmetic',
   //      });
   // }, [initialData, reset]); // Temporarily remove useEffect causing potential infinite loop


   const lowerPrice = watch('lower_price');
   const upperPrice = watch('upper_price');

   const handleFormSubmit = async (data) => {
     setApiError(null); // Clear previous errors
     const payload = {
       bot_type: 'GridBot',
       symbol: data.symbol,
       settings: {
         lower_price: parseFloat(data.lower_price),
         upper_price: parseFloat(data.upper_price),
         num_grids: parseInt(data.num_grids, 10),
         total_investment: parseFloat(data.total_investment),
         grid_type: data.grid_type,
       }
     };

     // Base URL is now handled by axiosInstance
     const url = initialData.id
       ? `/bots/configs/${initialData.id}` // Use relative path
       : `/bots/configs`; // Use relative path
     const method = initialData.id ? 'put' : 'post';

     try {
       // Use axiosInstance, headers are handled by the interceptor
       const response = await axiosInstance({
         method: method,
         url: url,
         data: payload,
       });
       onSubmit(response.data); // Pass created/updated data back
       reset(); // Reset form on successful submission
     } catch (error) {
       console.error("API Error:", error.response?.data || error.message);
       setApiError(error.response?.data?.detail || error.message || 'Failed to save configuration.');
     }
   };

   // Button disabled state uses isSubmitting from useForm and the isSubmittingProp from parent
   const isButtonDisabled = isSubmitting || isSubmittingProp;

   return (
     // Pass handleFormSubmit to handleSubmit
     <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
       <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-white">Grid Bot Configuration</h3>

       {apiError && (
         <div className="p-3 text-sm text-red-700 bg-red-100 rounded-md dark:bg-red-900 dark:text-red-300" role="alert">
           <span className="font-medium">Error:</span> {apiError}
         </div>
       )}

       <div>
         <label htmlFor="symbol" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Symbol</label>
         <input
           type="text"
           id="symbol"
           {...register('symbol', { required: 'Symbol is required' })}
           className={`mt-1 block w-full px-3 py-2 border ${errors.symbol ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`}
         />
         {errors.symbol && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.symbol.message}</p>}
       </div>

       <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
         <div>
           <label htmlFor="lower_price" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Lower Price</label>
           <input
             type="number" // Revert to number
             // inputMode="decimal"
             step="any" // Keep step for potential browser handling
             id="lower_price"
             {...register('lower_price', {
               required: 'Lower price is required',
               // valueAsNumber: true, // Keep commented out
               // Keep validation commented out for now
               // validate: {
               //   positive: value => parseFloat(value) > 0 || 'Lower price must be positive',
               //   lessThanUpper: value => !upperPrice || parseFloat(value) < parseFloat(upperPrice) || 'Lower price must be less than Upper price'
               // }
             })}
             className={`mt-1 block w-full px-3 py-2 border ${errors.lower_price ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`}
           />
           {errors.lower_price && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.lower_price.message}</p>}
         </div>
          <div>
           <label htmlFor="upper_price" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Upper Price</label>
           <input
             type="number" // Revert to number
             // inputMode="decimal"
             step="any" // Keep step
             id="upper_price"
             {...register('upper_price', {
               required: 'Upper price is required',
               // valueAsNumber: true, // Remove this, parse in submit handler
               validate: {
                 positive: value => parseFloat(value) > 0 || 'Upper price must be positive',
                 greaterThanLower: value => !lowerPrice || parseFloat(value) > parseFloat(lowerPrice) || 'Upper price must be greater than Lower price'
               }
             })}
             className={`mt-1 block w-full px-3 py-2 border ${errors.upper_price ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`}
           />
           {errors.upper_price && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.upper_price.message}</p>}
         </div>
       </div>

        <div>
           <label htmlFor="num_grids" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Number of Grids</label>
           <input
             type="number" // Revert to number
             // inputMode="numeric"
             id="num_grids"
             {...register('num_grids', {
               required: 'Number of grids is required',
               // valueAsNumber: true, // Remove this, parse in submit handler
               min: { value: 2, message: 'Must have at least 2 grids' }, // Grid bot needs at least 2 grids (1 buy, 1 sell)
               validate: value => Number.isInteger(parseFloat(value)) || 'Number of grids must be an integer' // Use parseFloat here
             })}
             className={`mt-1 block w-full px-3 py-2 border ${errors.num_grids ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`}
           />
           {errors.num_grids && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.num_grids.message}</p>}
         </div>

        <div>
           <label htmlFor="total_investment" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Total Investment (Quote Asset)</label>
           <input
             type="number" // Revert to number
             // inputMode="decimal"
             step="any" // Keep step
             id="total_investment"
             {...register('total_investment', {
               required: 'Total investment is required',
               // valueAsNumber: true, // Remove this, parse in submit handler
               min: { value: 0, message: 'Total investment cannot be negative' }
             })}
             className={`mt-1 block w-full px-3 py-2 border ${errors.total_investment ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`}
           />
           {errors.total_investment && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.total_investment.message}</p>}
         </div>

        <div>
         <label htmlFor="grid_type" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Grid Type</label>
         <select
           id="grid_type"
           {...register('grid_type', { required: 'Grid type is required' })}
           className={`mt-1 block w-full pl-3 pr-10 py-2 text-base border ${errors.grid_type ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md dark:bg-gray-700 dark:text-white`}
         >
           <option value="arithmetic">Arithmetic</option>
           <option value="geometric">Geometric</option>
         </select>
         {errors.grid_type && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.grid_type.message}</p>}
       </div>

       <div className="pt-2">
         {/* Use the combined disabled state */}
         <button type="submit" disabled={isButtonDisabled} className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50">
           {isButtonDisabled ? 'Saving...' : (initialData.id ? 'Update Configuration' : 'Save Configuration')}
         </button>
       </div>
     </form>
   );
 }