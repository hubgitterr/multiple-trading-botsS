// components/forms/GridBotForm.js
'use client';

import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
// Removed axiosInstance import

// Use consistent prop name 'isSubmitting'
export default function GridBotForm({ onSubmit, initialData = {}, isSubmitting }) {
   // Removed apiError state
   const { register, handleSubmit, watch, formState: { errors }, reset } = useForm({ // Removed isSubmitting from formState
     // Add name and is_enabled to defaultValues
     defaultValues: initialData ? {
       name: initialData.name || '',
       symbol: initialData.symbol || 'BTCUSDT',
       lower_price: initialData.settings?.lower_price || '',
       upper_price: initialData.settings?.upper_price || '',
       num_grids: initialData.settings?.num_grids || 5,
       total_investment: initialData.settings?.total_investment || '',
       grid_type: initialData.settings?.grid_type || 'arithmetic',
       is_enabled: initialData.is_enabled !== undefined ? initialData.is_enabled : true,
     } : {
       name: '',
       symbol: 'BTCUSDT',
       lower_price: '', upper_price: '', num_grids: 5, total_investment: '', grid_type: 'arithmetic',
       is_enabled: true,
     }
   });

   // Remove initialApiKeyId calculation

   // Uncomment and update useEffect to reset form on initialData change
   useEffect(() => {
        if (initialData) {
            reset({
                name: initialData.name || '',
                symbol: initialData.symbol || 'BTCUSDT',
                lower_price: initialData.settings?.lower_price || '',
                upper_price: initialData.settings?.upper_price || '',
                num_grids: initialData.settings?.num_grids || 5,
                total_investment: initialData.settings?.total_investment || '',
                grid_type: initialData.settings?.grid_type || 'arithmetic',
                is_enabled: initialData.is_enabled !== undefined ? initialData.is_enabled : true,
            });
        } else {
             reset({ // Reset to default create state
                name: '',
                symbol: 'BTCUSDT',
                lower_price: '', upper_price: '', num_grids: 5, total_investment: '', grid_type: 'arithmetic',
                is_enabled: true,
            });
        }
   }, [
     initialData?.name,
     initialData?.symbol,
     initialData?.settings?.lower_price,
     initialData?.settings?.upper_price,
     initialData?.settings?.num_grids,
     initialData?.settings?.total_investment,
     initialData?.settings?.grid_type,
     initialData?.is_enabled,
     reset // Keep reset as it's used in the effect
   ]);

   const lowerPrice = watch('lower_price');
   const upperPrice = watch('upper_price');

   // Simplified submit handler
   const handleFormSubmit = (data) => {
     // setApiError(null); // Parent handles errors
     const payload = {
       name: data.name, // Include name
       bot_type: 'GridBot',
       symbol: data.symbol,
       settings: {
         lower_price: parseFloat(data.lower_price),
         upper_price: parseFloat(data.upper_price),
         num_grids: parseInt(data.num_grids, 10),
         total_investment: parseFloat(data.total_investment),
         grid_type: data.grid_type,
       },
       is_enabled: data.is_enabled, // Include is_enabled
     };
     // Pass formatted payload to parent onSubmit
     onSubmit(payload);
     // Don't reset here, parent handles closing/clearing
   };

   // Use isSubmitting prop directly for button state
   // const isButtonDisabled = isSubmitting; // No longer needed

   return (
     <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
       <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-white">Grid Bot Configuration</h3>

       {/* Removed local apiError display */}

       {/* Add Name Field */}
       <div>
         <label htmlFor="name_grid" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Bot Name</label>
         <input
           type="text"
           id="name_grid" // Unique ID
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
           {...register('symbol', { required: 'Symbol is required' })}
           className={`mt-1 block w-full px-3 py-2 border ${errors.symbol ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`}
         />
         {errors.symbol && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.symbol.message}</p>}
       </div>
       
       <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
         <div>
           <label htmlFor="lower_price" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Lower Price</label>
           <input
             type="number" 
             step="any" 
             id="lower_price"
             {...register('lower_price', {
               required: 'Lower price is required',
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
             type="number" 
             step="any" 
             id="upper_price"
             {...register('upper_price', {
               required: 'Upper price is required',
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
             type="number" 
             id="num_grids"
             {...register('num_grids', {
               required: 'Number of grids is required',
               min: { value: 2, message: 'Must have at least 2 grids' }, 
               validate: value => Number.isInteger(parseFloat(value)) || 'Number of grids must be an integer' 
             })}
             className={`mt-1 block w-full px-3 py-2 border ${errors.num_grids ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`}
           />
           {errors.num_grids && <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.num_grids.message}</p>}
         </div>

        <div>
           <label htmlFor="total_investment" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Total Investment (Quote Asset)</label>
           <input
             type="number" 
             step="any" 
             id="total_investment"
             {...register('total_investment', {
               required: 'Total investment is required',
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

       {/* Add is_enabled Checkbox */}
        <div className="flex items-center pt-2">
          <input
            id="is_enabled_grid" // Unique ID
            type="checkbox"
            {...register("is_enabled")}
            className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded dark:bg-gray-700 dark:border-gray-600"
          />
          <label htmlFor="is_enabled_grid" className="ml-2 block text-sm text-gray-900 dark:text-gray-300">
            Enable this bot configuration?
          </label>
        </div>

       <div className="pt-2">
         <button type="submit" disabled={isSubmitting} className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50">
           {isSubmitting ? 'Saving...' : (initialData.id ? 'Update Configuration' : 'Create Configuration')} {/* Consistent button text */}
         </button>
       </div>
     </form>
   );
 }