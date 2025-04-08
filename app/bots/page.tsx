// app/bots/page.tsx
'use client';

import React, { useState, useCallback, useRef } from 'react'; // Removed useEffect as it's not used directly here
import DashboardLayout from '@/components/dashboard/Layout';
import BotControlPanel from '@/components/dashboard/BotControl';
// Import Bot configuration forms
import MomentumBotForm from '@/components/forms/MomentumBotForm';
import GridBotForm from '@/components/forms/GridBotForm';
import DCABotForm from '@/components/forms/DCABotForm';
import BacktestModal from '@/components/backtesting/BacktestModal'; // Import the BacktestModal
import axiosInstance from '@/lib/axiosInstance';
import { mutate } from 'swr';
import { BotConfig, BacktestResult } from '@/lib/types'; // Import BacktestResult type
import BacktestResultsDisplay from '@/components/backtesting/BacktestResultsDisplay'; // Import the results display component
// Removed Modal import
// Define a type for the API Key data structure (Keep for reference, but not used here now)
// interface ApiKey {
//   id: string; 
//   label: string | null;
//   api_key_public: string;
// }

export default function BotsPage() {
  const [showFormModal, setShowFormModal] = useState(false); // Controls modal visibility
  const [selectedBotType, setSelectedBotType] = useState('');
  const [editingBotData, setEditingBotData] = useState<BotConfig | null>(null); // Holds data for editing
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [isBacktestModalOpen, setIsBacktestModalOpen] = useState(false); // State for backtest modal
  const [backtestingConfigId, setBacktestingConfigId] = useState<string | null>(null); // State for target config ID
  
  // State for backtest results
  const [backtestResults, setBacktestResults] = useState<BacktestResult | null>(null);
  const [isBacktestLoading, setIsBacktestLoading] = useState(false);
  const [backtestError, setBacktestError] = useState<string | null>(null);
  const isSubmittingRef = useRef(false);

  // Renamed and modified to handle both create and edit
  const handleSubmit = useCallback(async (formData: any) => {
    // Prevent double submission using ref
    if (isSubmittingRef.current) {
      console.warn("Submission already in progress (ref guard), ignoring duplicate call.");
      return; 
    }
    isSubmittingRef.current = true; 
    setIsSubmitting(true); 
    setFormError(null);
    const isEditing = !!editingBotData;
    const url = isEditing ? `/bots/configs/${editingBotData.id}` : '/bots/configs';
    const method = isEditing ? 'put' : 'post';
    console.log(`${isEditing ? 'Updating' : 'Creating'} bot config:`, formData);
    console.log(`URL: ${method.toUpperCase()} ${url}`);

    try {
      // Remove api_key_id if it exists (temporary workaround)
      const payload = { ...formData };
      delete payload.api_key_id;

      await axiosInstance({ method, url, data: payload });
      console.log(`Bot configuration ${isEditing ? 'updated' : 'created'} successfully!`);
      // Mutate both status and configs to ensure list updates
      mutate('/bots/status');
      mutate('/bots/configs');
      setShowFormModal(false); // Close modal on success
      setSelectedBotType('');
      setEditingBotData(null); // Clear editing state
    } catch (err: any) { 
      console.error("Error creating bot config:", err);
      const detail = err?.response?.data?.detail;
      setFormError(typeof detail === 'string' ? detail : `Failed to ${isEditing ? 'update' : 'create'} configuration.`);
    } finally {
      setIsSubmitting(false);
      isSubmittingRef.current = false;
    }
  }, [editingBotData, isSubmitting, setIsSubmitting, setFormError, setShowFormModal, setSelectedBotType, setEditingBotData]);

  // Function to handle clicking the edit button in BotControlPanel
  const handleEditClick = useCallback((botData: BotConfig) => {
    console.log("Editing bot:", botData);
    setEditingBotData(botData);
    setSelectedBotType(botData.bot_type); // Set type based on bot being edited
    setFormError(null);
    setShowFormModal(true); // Open the modal
  }, [setEditingBotData, setSelectedBotType, setFormError, setShowFormModal]);

  // Function to handle clicking the backtest button in BotControlPanel
  const handleBacktestClick = useCallback((botData: BotConfig) => {
    console.log("Backtesting bot:", botData);
    setBacktestingConfigId(botData.id); // Store the ID of the bot to backtest
    setIsBacktestModalOpen(true); // Open the backtest modal
    setBacktestResults(null); // Clear previous results when opening modal
    setBacktestError(null); // Clear previous errors
  }, [setBacktestingConfigId, setIsBacktestModalOpen]);

  // Function to handle the submission of the backtest form
  const handleBacktestSubmit = useCallback(async (backtestParams: { start_date: string; end_date: string; initial_capital: number }) => {
    if (!backtestingConfigId) {
      console.error("BotsPage: No config ID selected for backtesting.");
      setBacktestError("No configuration selected for backtest.");
      return; // Exit early
    }
    console.log(`BotsPage: Starting backtest for config ${backtestingConfigId} with params:`, backtestParams);

    setIsBacktestLoading(true); // Set loading state
    setBacktestError(null); // Clear previous errors
    setBacktestResults(null); // Clear previous results

    try {
      const response = await axiosInstance.post<BacktestResult>(`/backtest/${backtestingConfigId}`, backtestParams);
      console.log("BotsPage: Backtest completed successfully:", response.data);
      setBacktestResults(response.data); // Store results
      setIsBacktestModalOpen(false); // Close modal on success
      setBacktestingConfigId(null); // Clear the selected config ID
      // TODO: Decide where/how to display results (next step)
    } catch (err: any) {
      console.error("BotsPage: Error running backtest:", err);
      const detail = err?.response?.data?.detail;
      const errorMessage = typeof detail === 'string' ? detail : 'Failed to run backtest.';
      setBacktestError(errorMessage); // Store error message
      setBacktestResults(null); // Ensure results are cleared on error
    } finally {
      setIsBacktestLoading(false); // Clear loading state regardless of outcome
    }
  }, [backtestingConfigId]); // Dependencies for handleBacktestSubmit

  // Renamed and modified to render form for create/edit
  const renderForm = () => {
    // Pass initialData if editing
    const initialData = editingBotData || undefined;
    let formComponent = null;
    switch (selectedBotType) {
      case 'MomentumBot':
        formComponent = <MomentumBotForm onSubmit={handleSubmit} isSubmitting={isSubmitting} initialData={initialData} />;
        break;
      case 'GridBot':
        formComponent = <GridBotForm onSubmit={handleSubmit} isSubmitting={isSubmitting} initialData={initialData} />;
        break;
      case 'DCABot':
        // Pass isSubmitting and initialData to DCABotForm as well
        formComponent = <DCABotForm onSubmit={handleSubmit} isSubmitting={isSubmitting} initialData={initialData} />;
        break;
      default:
        formComponent = <p className="text-gray-500 dark:text-gray-400">Select a bot type above to configure.</p>;
    }
    return formComponent; 
  };

  return (
    <DashboardLayout>
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">Bots Management</h1>

      {/* Button to open the Create Bot modal */}
      <div className="mb-6">
        <button
          onClick={() => {
            setEditingBotData(null); // Ensure not in edit mode
            setSelectedBotType(''); // Reset type selector
            setFormError(null);
            setShowFormModal(true); // Open modal for creation
          }}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
        >
          Create New Bot Configuration
        </button>
      </div>

      {/* Conditionally render Create/Edit Form Section */}
      {showFormModal && (
        <div className="mb-6 bg-white dark:bg-gray-800 shadow rounded-lg p-4 sm:p-6">
           <div className="flex justify-between items-center mb-4">
             <h2 className="text-lg font-medium text-gray-900 dark:text-white">
               {editingBotData ? `Edit Bot: ${editingBotData.name}` : "Create New Bot"}
             </h2>
              <button onClick={() => { setShowFormModal(false); setSelectedBotType(''); setEditingBotData(null); setFormError(null); }} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                 &times; {/* Close button */}
              </button>
           </div>

          {/* Only show type selector when CREATING */}
          {!editingBotData && (
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
                <option value="" disabled>-- Select Type --</option>
                <option value="MomentumBot">Momentum Bot</option>
                <option value="GridBot">Grid Bot</option>
                <option value="DCABot">DCA Bot</option>
              </select>
            </div>
          )}

          {/* Render the appropriate form based on selected type */}
          {selectedBotType && renderForm()}
          {formError && <p className="mt-2 text-sm text-red-600 dark:text-red-400">{formError}</p>}
        </div>
      )}

      {/* Existing Bot Control Panel */}
      <div className="mt-8">
         <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Bot Status & Control</h2>
         <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">Start/Stop bots based on their saved configurations.</p>
         {/* Pass handleEditClick and handleBacktestClick down to BotControlPanel */}
         <BotControlPanel onEditClick={handleEditClick} onBacktestClick={handleBacktestClick} />

         {/* --- Backtest Results Section --- */}
         <div className="mt-6">
           {isBacktestLoading && (
             <div className="p-4 text-center text-gray-600 dark:text-gray-400">
               <p>Running backtest...</p>
               {/* Optional: Add a spinner here */}
             </div>
           )}
           {backtestError && (
             <div className="p-4 bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-600 text-red-700 dark:text-red-300 rounded-md">
               <p className="font-medium">Backtest Error:</p>
               <p>{backtestError}</p>
             </div>
           )}
           {backtestResults && !isBacktestLoading && !backtestError && (
             <BacktestResultsDisplay results={backtestResults} />
           )}
         </div>
         {/* --- End Backtest Results Section --- */}
      </div>

      {/* Backtest Modal */}
      <BacktestModal
        isOpen={isBacktestModalOpen}
        onClose={() => {
          setIsBacktestModalOpen(false);
          setBacktestingConfigId(null); // Clear ID when closing manually
        }}
        onSubmit={handleBacktestSubmit} // Pass the updated handler
        configId={backtestingConfigId}
        // Note: The modal itself doesn't need loading/error/results state, the parent handles it.
        // Results are displayed outside the modal now.
      />
      {/* Conditional rendering for results is now handled above */}
    </DashboardLayout>
  );
}