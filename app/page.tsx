'use client'; // Mark as client component because it uses hooks/components that need client-side rendering

import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react'; // Keep useEffect for now, might be used by modal later
import DashboardLayout from '@/components/dashboard/Layout'; // Import the main layout
import MarketOverview from '@/components/dashboard/MarketOverview';
import BotControlPanel from '@/components/dashboard/BotControl';
// Import the new chart components
import RealTimeChart from '@/components/charts/RealTimeChart';
import CandlestickChart from '@/components/charts/CandlestickChart';
import HeatmapChart from '@/components/charts/HeatmapChart';
// Import Bot configuration forms needed for the modal
import MomentumBotForm from '@/components/forms/MomentumBotForm';
import GridBotForm from '@/components/forms/GridBotForm';
import DCABotForm from '@/components/forms/DCABotForm';
import BacktestModal from '@/components/backtesting/BacktestModal'; // Import the BacktestModal
import axiosInstance from '@/lib/axiosInstance'; // For API calls
import { mutate } from 'swr'; // To refresh data after edit
import { BotConfig, BacktestResult } from '@/lib/types'; // Type for bot data and backtest results
import BacktestResultsDisplay from '@/components/backtesting/BacktestResultsDisplay'; // Import the results display component
// Import other dashboard components as needed
// import PerformanceDashboard from '@/components/dashboard/Performance';
// import BacktestInterface from '@/components/dashboard/Backtest';
export default function DashboardPage() {
  // This page now represents the main dashboard view

  // State for modal, editing, submission, errors (similar to app/bots/page.tsx)
  const [showFormModal, setShowFormModal] = useState(false);
  const [selectedBotType, setSelectedBotType] = useState('');
  const [editingBotData, setEditingBotData] = useState<BotConfig | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const isSubmittingRef = useRef(false);

  // State for backtest modal
  const [isBacktestModalOpen, setIsBacktestModalOpen] = useState(false);
  const [backtestingConfigId, setBacktestingConfigId] = useState<string | null>(null);
  
  // State for backtest results
  const [backtestResults, setBacktestResults] = useState<BacktestResult | null>(null);
  const [isBacktestLoading, setIsBacktestLoading] = useState(false);
  const [backtestError, setBacktestError] = useState<string | null>(null);

  // Placeholder: In a real app, fetch data needed for charts or pass down props
  // Define symbols for the RealTimeChart and memoize them
  const realTimeChartSymbols = useMemo(() => ['BTCUSDT', 'ETHUSDT'], []);

  // const exampleChartSymbol = 'BTCUSDT';

  // --- Handlers and Form Logic (copied/adapted from app/bots/page.tsx) ---

  // Handle form submission (for editing bots)
  const handleSubmit = useCallback(async (formData: any) => {
    if (isSubmittingRef.current) return;
    isSubmittingRef.current = true;
    setIsSubmitting(true);
    setFormError(null);

    // On the dashboard, we only handle editing existing bots
    if (!editingBotData) {
      console.error("handleSubmit called without editingBotData on dashboard page.");
      setFormError("Cannot create new bots from the dashboard view.");
      setIsSubmitting(false);
      isSubmittingRef.current = false;
      return;
    }

    const url = `/bots/configs/${editingBotData.id}`;
    const method = 'put';
    console.log(`Updating bot config:`, formData);
    console.log(`URL: ${method.toUpperCase()} ${url}`);

    try {
      const payload = { ...formData };
      delete payload.api_key_id; // Ensure api_key_id is not sent if present

      await axiosInstance({ method, url, data: payload });
      console.log(`Bot configuration updated successfully!`);
      mutate('/bots/status'); // Refresh status
      mutate('/bots/configs'); // Refresh configs list
      setShowFormModal(false); // Close modal
      setSelectedBotType('');
      setEditingBotData(null); // Clear editing state
    } catch (err: any) {
      console.error("Error updating bot config:", err);
      const detail = err?.response?.data?.detail;
      setFormError(typeof detail === 'string' ? detail : `Failed to update configuration.`);
    } finally {
      setIsSubmitting(false);
      isSubmittingRef.current = false;
    }
  }, [editingBotData]); // Dependencies for handleSubmit

  // Handle clicking the edit button in BotControlPanel
  const handleEditClick = useCallback((botData: BotConfig) => {
    console.log("Dashboard: Editing bot:", botData);
   console.log("Dashboard: handleEditClick - botData received:", JSON.stringify(botData)); // LOG 1: Log data received
    setEditingBotData(botData);
    setSelectedBotType(botData.bot_type); // Set type based on bot being edited
    setFormError(null);
    setShowFormModal(true); // Open the modal
  }, []); // Dependencies for handleEditClick
// LOG 2: Log editingBotData when the modal becomes visible
useEffect(() => {
  if (showFormModal) {
    console.log("Dashboard: Modal opened. editingBotData:", JSON.stringify(editingBotData, null, 2));
  }
}, [showFormModal, editingBotData]);

  // Function to handle clicking the backtest button in BotControlPanel
  const handleBacktestClick = useCallback((botData: BotConfig) => {
    console.log("Dashboard: Backtesting bot:", botData);
    setBacktestingConfigId(botData.id); // Store the ID of the bot to backtest
    setIsBacktestModalOpen(true); // Open the backtest modal
    setBacktestResults(null); // Clear previous results when opening modal
    setBacktestError(null); // Clear previous errors
  }, []); // Dependencies for handleBacktestClick

  // Function to handle the submission of the backtest form (Dashboard version)
  const handleBacktestSubmit = useCallback(async (backtestParams: { start_date: string; end_date: string; initial_capital: number }) => {
    if (!backtestingConfigId) {
      console.error("Dashboard: No config ID selected for backtesting.");
      // Set error state for the page, not just throwing for modal
      setBacktestError("No configuration selected for backtest.");
      return; // Exit early
    }
    console.log(`Dashboard: Starting backtest for config ${backtestingConfigId} with params:`, backtestParams);

    setIsBacktestLoading(true); // Set loading state
    setBacktestError(null); // Clear previous errors
    setBacktestResults(null); // Clear previous results

    try {
      const response = await axiosInstance.post<BacktestResult>(`/backtest/${backtestingConfigId}`, backtestParams);
      console.log("Dashboard: Backtest completed successfully:", response.data);
      setBacktestResults(response.data); // Store results
      setIsBacktestModalOpen(false); // Close modal on success
      setBacktestingConfigId(null); // Clear the selected config ID
      // TODO: Decide where/how to display results (next step)
    } catch (err: any) {
      console.error("Dashboard: Error running backtest:", err);
      const detail = err?.response?.data?.detail;
      const errorMessage = typeof detail === 'string' ? detail : 'Failed to run backtest.';
      setBacktestError(errorMessage); // Store error message
      setBacktestResults(null); // Ensure results are cleared on error
    } finally {
      setIsBacktestLoading(false); // Clear loading state regardless of outcome
    }
  }, [backtestingConfigId]); // Dependencies for handleBacktestSubmit


// Render the correct form based on the bot type being edited
  // Render the correct form based on the bot type being edited
  const renderForm = () => {
    if (!editingBotData) return null; // Should not happen if modal is open for edit

    const initialData = editingBotData;
    let formComponent = null;
    switch (selectedBotType) {
      case 'MomentumBot':
        formComponent = <MomentumBotForm onSubmit={handleSubmit} isSubmitting={isSubmitting} initialData={initialData} />;
        break;
      case 'GridBot':
        formComponent = <GridBotForm onSubmit={handleSubmit} isSubmitting={isSubmitting} initialData={initialData} />;
        break;
      case 'DCABot':
        formComponent = <DCABotForm onSubmit={handleSubmit} isSubmitting={isSubmitting} initialData={initialData} />;
        break;
      default:
        formComponent = <p className="text-gray-500 dark:text-gray-400">Unknown bot type for editing.</p>;
    }
    return formComponent;
  };

  // --- End Handlers and Form Logic ---
  return (
    <DashboardLayout>
      {/* Wrap content in the layout */}
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">Dashboard</h1>

      {/* Main Dashboard Content Area */}
      <div className="space-y-6">
        {/* Market Overview - Spans full width */}
        <MarketOverview />

        {/* Grid Layout for Charts and Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Real-time Chart */}
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Live Feed</h2>
            <div className="h-64 md:h-80"> {/* Fixed height container */}
               {/* Pass the memoized symbols array */}
               <RealTimeChart symbols={realTimeChartSymbols} />
            </div>
          </div>

          {/* Candlestick Chart */}
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Price Action</h2>
             <div className="h-64 md:h-80"> {/* Fixed height container */}
              <CandlestickChart />
            </div>
          </div>

          {/* Heatmap Chart */}
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Market Heatmap</h2>
             <div className="h-64 md:h-80"> {/* Fixed height container */}
              <HeatmapChart />
            </div>
          </div>

          {/* Bot Control Panel */}
          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Bot Controls</h2>
            {/* Pass the handleEditClick and handleBacktestClick functions down */}
            <BotControlPanel onEditClick={handleEditClick} onBacktestClick={handleBacktestClick} />
          </div>
        </div>
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
        
        {/* Removed old PriceChart example */}
        {/* Add other components like Performance, Backtest interface etc. if needed */}
        {/* <PerformanceDashboard /> */}
        {/* <BacktestInterface /> */}
      </div>
      {/* --- Edit Bot Modal Section (copied/adapted from app/bots/page.tsx) --- */}
      {showFormModal && editingBotData && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-gray-600 bg-opacity-75 transition-opacity">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            {/* Background overlay */}
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>

            {/* Modal panel */}
            <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left w-full">
                     <div className="flex justify-between items-center mb-4">
                       <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white" id="modal-title">
                         Edit Bot: {editingBotData.name} ({editingBotData.bot_type})
                       </h3>
                       <button
                         onClick={() => { setShowFormModal(false); setSelectedBotType(''); setEditingBotData(null); setFormError(null); }}
                         className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none"
                       >
                          &times; {/* Close button */}
                       </button>
                     </div>
                    <div className="mt-2">
                      {/* Render the appropriate form */}
                      {renderForm()}
                      {formError && <p className="mt-2 text-sm text-red-600 dark:text-red-400">{formError}</p>}
                    </div>
                  </div>
                </div>
              </div>
              {/* Modal Footer (optional, can add Save/Cancel buttons linked to form submission/closing) */}
              {/* <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                 Buttons here if needed, form handles submission internally now
              </div> */}
            </div>
          </div>
        </div>
      )}
      {/* --- End Edit Bot Modal Section --- */}

      {/* --- Backtest Modal Section --- */}
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
      {/* --- End Backtest Modal Section --- */}

    </DashboardLayout>
  );
}
