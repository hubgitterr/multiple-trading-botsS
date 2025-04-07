// app/bots/page.tsx
'use client';

import React, { useState, useCallback, useRef } from 'react'; // Import useRef
import DashboardLayout from '@/components/dashboard/Layout';
import BotControlPanel from '@/components/dashboard/BotControl';
// Import Bot configuration forms
import MomentumBotForm from '@/components/forms/MomentumBotForm';
import GridBotForm from '@/components/forms/GridBotForm';
import DCABotForm from '@/components/forms/DCABotForm';
import axiosInstance from '@/lib/axiosInstance'; // For API calls
import { mutate } from 'swr'; // To trigger refresh of bot list after creation

export default function BotsPage() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedBotType, setSelectedBotType] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false); // Restore parent submitting state
  const [formError, setFormError] = useState<string | null>(null);
  const isSubmittingRef = useRef(false); // Ref to track active submission

  // Wrap submit handler in useCallback to stabilize its reference
  const handleCreateSubmit = useCallback(async (formData: any) => {
    // Prevent double submission using ref
    if (isSubmittingRef.current) {
      console.warn("Submission already in progress (ref guard), ignoring duplicate call.");
      return;
    }
    isSubmittingRef.current = true; // Set ref flag
    setIsSubmitting(true); // Keep state for potential UI feedback if needed
    setFormError(null);
    console.log("Creating bot config:", formData);
    try {
      await axiosInstance.post('/bots/configs', formData);
      console.log('Bot configuration created successfully!'); // Log instead
      // Mutate both status and configs to ensure list updates
      mutate('/bots/status');
      mutate('/bots/configs');
      setShowCreateForm(false); // Close form on success
      setSelectedBotType(''); // Reset selection
    } catch (err: any) { // Basic type for error
      console.error("Error creating bot config:", err);
      const detail = err?.response?.data?.detail;
      setFormError(typeof detail === 'string' ? detail : "Failed to create configuration.");
    } finally {
      setIsSubmitting(false);
      isSubmittingRef.current = false; // Reset ref flag
    }
  // Dependencies for useCallback (ref doesn't need to be included)
  }, [isSubmitting, setIsSubmitting, setFormError, setShowCreateForm, setSelectedBotType]);

  const renderCreateForm = () => {
    switch (selectedBotType) {
      case 'MomentumBot':
        return <MomentumBotForm onSubmit={handleCreateSubmit} isSubmitting={isSubmitting} />; // Restore isSubmitting prop
      case 'GridBot':
        return <GridBotForm onSubmit={handleCreateSubmit} isSubmitting={isSubmitting} />; // Restore isSubmitting prop
      case 'DCABot':
        return <DCABotForm onSubmit={handleCreateSubmit} />; // Remove isSubmitting prop
      default:
        return <p className="text-gray-500 dark:text-gray-400">Select a bot type above to configure.</p>;
    }
  };

  return (
    <DashboardLayout>
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">Bots Management</h1>

      {/* Section to Create New Bot Config */}
      <div className="mb-6">
        {!showCreateForm ? (
          <button
            onClick={() => setShowCreateForm(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Create New Bot Configuration
          </button>
        ) : (
          <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-4 sm:p-6">
             <div className="flex justify-between items-center mb-4">
               <h2 className="text-lg font-medium text-gray-900 dark:text-white">Create New Bot</h2>
                <button onClick={() => { setShowCreateForm(false); setSelectedBotType(''); setFormError(null); }} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                   &times; {/* Close button */}
                </button>
             </div>

            <div className="mb-4">
              <label htmlFor="botTypeSelect" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Select Bot Type</label>
              <select
                id="botTypeSelect"
                value={selectedBotType}
                onChange={(e) => { setSelectedBotType(e.target.value); setFormError(null); }}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md dark:bg-gray-700 dark:text-white"
              >
                <option value="" disabled>-- Select Type --</option>
                <option value="MomentumBot">Momentum Bot</option>
                <option value="GridBot">Grid Bot</option>
                <option value="DCABot">DCA Bot</option>
                {/* Add other bot types as they are implemented */}
              </select>
            </div>

            {selectedBotType && renderCreateForm()}
            {formError && <p className="mt-2 text-sm text-red-600 dark:text-red-400">{formError}</p>}
          </div>
        )}
      </div>

      {/* Existing Bot Control Panel */}
      {/* TODO: Add a component here to LIST existing configurations fetched from /api/bots/configs */}
      {/* <BotConfigList /> */}
      <div className="mt-8">
         <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Bot Status & Control</h2>
         <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">Start/Stop bots based on their saved configurations.</p>
         <BotControlPanel />
      </div>
    </DashboardLayout>
  );
}