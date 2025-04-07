// components/settings/ApiKeyManager.js
'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import useSWR from 'swr';
import axiosInstance from '../../lib/axiosInstance'; // Use configured axios instance
// Import icons later if needed (e.g., TrashIcon)

// Fetcher function for SWR using our axios instance
const fetcher = url => axiosInstance.get(url).then(res => res.data);

export default function ApiKeyManager() {
  const { data: apiKeys, error: fetchError, mutate, isLoading: isLoadingKeys } = useSWR('/user/api-keys', fetcher); // Fetch keys

  const { register, handleSubmit, reset, setError: setFormError, formState: { errors, isSubmitting } } = useForm();
  const [addKeyError, setAddKeyError] = useState(null); // Separate state for add errors
  const [deleteLoading, setDeleteLoading] = useState({}); // Track loading state for delete buttons { public_key: boolean }

  const onSubmitAddKey = async (data) => {
    setAddKeyError(null);
    console.log("Submitting new API key:", { ...data, secret_key: '***' }); // Don't log secret
    try {
      // POST request to add the key
      await axiosInstance.post('/user/api-keys', {
         label: data.label,
         api_key_public: data.api_key_public,
         secret_key: data.secret_key // Send the secret key here
      });
      mutate(); // Re-fetch the list of keys after adding
      reset(); // Clear the form
      alert('API Key added successfully!'); // Simple success feedback
    } catch (err) {
      console.error("Error adding API key:", err);
      const errorMsg = err.response?.data?.detail || "Failed to add API key. Please try again.";
      setAddKeyError(errorMsg);
      // Optionally set form errors if specific fields are invalid based on backend response
      // setFormError('api_key_public', { type: 'manual', message: '...' });
    }
  };

  const handleDeleteKey = async (publicKey) => {
     if (!confirm(`Are you sure you want to delete the API key starting with ${publicKey.substring(0, 5)}...? This action cannot be undone.`)) {
        return;
     }
     setDeleteLoading(prev => ({ ...prev, [publicKey]: true }));
     setAddKeyError(null); // Clear add error when deleting
     console.log("Deleting API key:", publicKey);
     try {
        // DELETE request to remove the key
        await axiosInstance.delete(`/user/api-keys/${publicKey}`);
        mutate(); // Re-fetch the list of keys
        alert('API Key deleted successfully!');
     } catch (err) {
        console.error("Error deleting API key:", err);
        setAddKeyError(err.response?.data?.detail || "Failed to delete API key.");
     } finally {
         setDeleteLoading(prev => ({ ...prev, [publicKey]: false }));
     }
  };

  // Helper to mask keys for display
  const maskKey = (key) => {
     if (!key || key.length < 10) return key;
     return `${key.substring(0, 5)}...${key.substring(key.length - 5)}`;
  }

  return (
    <div className="space-y-6">
      {/* Section to Add New Key */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-4 sm:p-6">
        <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-white mb-4">Add New Binance API Key</h3>
        <form onSubmit={handleSubmit(onSubmitAddKey)} className="space-y-4">
          <div>
            <label htmlFor="label" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Label (Optional)</label>
            <input
              type="text"
              id="label"
              {...register("label")}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white"
              placeholder="e.g., My Main Account"
            />
          </div>
          <div>
            <label htmlFor="api_key_public" className="block text-sm font-medium text-gray-700 dark:text-gray-300">API Key (Public)</label>
            <input
              type="text" // Consider type="password" for slight obfuscation, but still viewable in dev tools
              id="api_key_public"
              {...register("api_key_public", { required: "Public API Key is required" })}
              required
              className={`mt-1 block w-full px-3 py-2 border ${errors.api_key_public ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`}
            />
             {errors.api_key_public && <p className="mt-1 text-xs text-red-500">{errors.api_key_public.message}</p>}
          </div>
           <div>
            <label htmlFor="secret_key" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Secret Key</label>
            <input
              type="password" // Use password type to hide secret
              id="secret_key"
              {...register("secret_key", { required: "Secret Key is required" })}
              required
              className={`mt-1 block w-full px-3 py-2 border ${errors.secret_key ? 'border-red-500' : 'border-gray-300 dark:border-gray-600'} rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:text-white`}
            />
             {errors.secret_key && <p className="mt-1 text-xs text-red-500">{errors.secret_key.message}</p>}
          </div>
          {addKeyError && <p className="text-sm text-red-600 dark:text-red-400">{addKeyError}</p>}
          <div className="pt-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {isSubmitting ? 'Adding Key...' : 'Add API Key'}
            </button>
          </div>
        </form>
      </div>

      {/* Section to List Existing Keys */}
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg mt-6">
         <div className="px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">Saved API Keys</h3>
         </div>
         <div className="overflow-x-auto">
             {isLoadingKeys && <p className="p-4 text-gray-500 dark:text-gray-400">Loading keys...</p>}
             {fetchError && <p className="p-4 text-red-600 dark:text-red-400">Error loading API keys.</p>}
             {!isLoadingKeys && !fetchError && (
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                   <thead className="bg-gray-50 dark:bg-gray-700">
                      <tr>
                         <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Label</th>
                         <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">API Key (Public)</th>
                         <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Added</th>
                         <th scope="col" className="relative px-6 py-3"><span className="sr-only">Actions</span></th>
                      </tr>
                   </thead>
                   <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-600">
                      {apiKeys && apiKeys.length > 0 ? apiKeys.map((key) => (
                         <tr key={key.id}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">{key.label || '--'}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400 font-mono">{maskKey(key.api_key_public)}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{new Date(key.created_at).toLocaleDateString()}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                               <button
                                 onClick={() => handleDeleteKey(key.api_key_public)}
                                 disabled={deleteLoading[key.api_key_public]}
                                 className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300 disabled:opacity-50"
                               >
                                  {deleteLoading[key.api_key_public] ? 'Deleting...' : 'Delete'}
                                  {/* Add TrashIcon later */}
                               </button>
                            </td>
                         </tr>
                      )) : (
                         <tr><td colSpan="4" className="px-6 py-4 text-center text-sm text-gray-500 dark:text-gray-400">No API keys added yet.</td></tr>
                      )}
                   </tbody>
                </table>
             )}
         </div>
      </div>
    </div>
  );
}