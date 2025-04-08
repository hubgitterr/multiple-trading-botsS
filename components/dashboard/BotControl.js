// components/dashboard/BotControl.js
'use client';

import React, { useState, useMemo } from 'react';
import useSWR, { mutate } from 'swr';
import axiosInstance from '../../lib/axiosInstance';

const fetcher = async (url) => {
  try {
    const res = await axiosInstance.get(url);
    return res.data;
  } catch (error) {
    console.error(`SWR fetch error for ${url}:`, error);
    const fetchError = new Error(error.response?.data?.detail || error.message || 'An error occurred while fetching the data.');
    throw fetchError;
  }
};

// Accept onEditClick prop from parent
export default function BotControlPanel({ onEditClick, onBacktestClick }) { // Add onBacktestClick prop
  // Fetch bot configurations list
  const { data: botConfigs, error: configError, isLoading: isLoadingConfigs } = useSWR(
    '/bots/configs',
    fetcher,
    { refreshInterval: 10000 } // Refresh configs less often
  );

  // Fetch running bot status list
  const { data: runningStatuses, error: statusError, isLoading: isLoadingStatus } = useSWR(
    '/bots/status',
    fetcher,
    { refreshInterval: 3000 } // Refresh status more often
  );

  const [loadingStates, setLoadingStates] = useState({});
  const [actionError, setActionError] = useState(null);

  // Combine config and status data
  const combinedBotData = useMemo(() => {
    console.log("DEBUG: useMemo triggered. Configs:", botConfigs, "Statuses:", runningStatuses); // DEBUG LOG 1
    // Wait until configurations are loaded
    if (!Array.isArray(botConfigs)) return []; 

    // Create a map of running statuses for quick lookup
    const statusMap = new Map();
    if (Array.isArray(runningStatuses)) {
      runningStatuses.forEach(status => statusMap.set(status.bot_id, status));
    }

    // Map configurations and merge with status data if available
    const combinedData = botConfigs.map(config => {
      const status = statusMap.get(config.id); // Match config ID with status bot_id
      const merged = {
        ...config, // Spread config details
        is_running: status ? status.is_running : false, // Get running state from status
        status_message: status ? status.status_message : (config.is_enabled ? 'Stopped' : 'Disabled'), // Get message from status or derive
        runtime_state: status ? status.runtime_state : {}, // Get runtime state
      };
      // console.log(`DEBUG: Merged data for ${config.id}:`, merged); // DEBUG LOG 2 (Optional - can be verbose)
      return merged;
    });
    console.log("DEBUG: useMemo computed combinedBotData:", combinedData); // DEBUG LOG 3
    return combinedData;
  }, [botConfigs, runningStatuses]); // Recompute when either configs or statuses change


  const handleStartBot = async (botId) => {
    setLoadingStates(prev => ({ ...prev, [botId]: true }));
    setActionError(null);
    console.log(`Attempting to start bot: ${botId}`);
    try {
      await axiosInstance.post(`/bots/${botId}/start`);
      console.log(`Successfully requested start for bot ${botId}`);
      // Trigger immediate refresh of status after action
      // Trigger immediate refresh of status AND configs after action
      mutate('/bots/status');
      mutate('/bots/configs');
    } catch (err) {
      console.error(`Error starting bot ${botId}:`, err);
      const errorMessage = err.response?.data?.detail || `Failed to start bot ${botId}.`;
      setActionError(errorMessage);
    } finally {
      setLoadingStates(prev => ({ ...prev, [botId]: false }));
    }
  };

  const handleStopBot = async (botId) => {
    setLoadingStates(prev => ({ ...prev, [botId]: true }));
    setActionError(null);
    console.log(`Attempting to stop bot: ${botId}`);
    try {
      await axiosInstance.post(`/bots/${botId}/stop`);
      console.log(`Successfully requested stop for bot ${botId}`);
      // Trigger immediate refresh of status AND configs after action
      mutate('/bots/status');
      mutate('/bots/configs');
      // Optionally mutate configs if stopping disables it
      // mutate('/bots/configs'); 
    } catch (err) {
      console.error(`Error stopping bot ${botId}:`, err);
      const errorMessage = err.response?.data?.detail || `Failed to stop bot ${botId}.`;
      setActionError(errorMessage);
    } finally {
      setLoadingStates(prev => ({ ...prev, [botId]: false }));
    }
  };

  // Determine display status based on combined data
  const getDisplayStatus = (botData) => {
     if (!botData) return { text: 'Unknown', color: 'text-gray-500 dark:text-gray-400', dot: 'bg-gray-400' };
     
     // Prioritize running status from the status endpoint
     if (botData.is_running) {
         // Check for specific messages within running state
         if (botData.status_message?.toLowerCase().includes('error')) {
             return { text: botData.status_message, color: 'text-red-500 dark:text-red-400', dot: 'bg-red-400' };
         }
         return { text: botData.status_message || 'Running', color: 'text-green-500 dark:text-green-400', dot: 'bg-green-400' };
     } 
     // If not running, check if it's explicitly disabled in config
     else if (!botData.is_enabled) {
         return { text: 'Disabled', color: 'text-gray-500 dark:text-gray-400', dot: 'bg-gray-400' };
     } 
     // Otherwise, assume it's stopped (enabled but not running)
     else {
         return { text: botData.status_message || 'Stopped', color: 'text-gray-500 dark:text-gray-400', dot: 'bg-gray-400' };
     }
  }

  const isLoading = isLoadingConfigs; // Primarily wait for configs to load the list
  const fetchError = configError || statusError; // Show error if either fetch fails

  console.log("DEBUG: Rendering BotControlPanel. Combined Data:", combinedBotData); // DEBUG LOG 4
  return (
    <div className="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-lg">
      <div className="px-4 py-5 sm:px-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
          Bot Control Panel
        </h3>
        <p className="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">
          Manage and monitor your bot configurations.
        </p>
        {fetchError && <p className="mt-2 text-sm text-red-600 dark:text-red-400">Error loading bot data: {fetchError.message}</p>}
        {actionError && <p className="mt-2 text-sm text-red-600 dark:text-red-400">{actionError}</p>}
      </div>
      <div className="border-t border-gray-200 dark:border-gray-700">
        <ul role="list" className="divide-y divide-gray-200 dark:divide-gray-700">
          {isLoading && (
             <li className="px-4 py-4 text-sm text-gray-500 dark:text-gray-400">Loading bot configurations...</li>
          )}
          {!isLoading && !fetchError && (!Array.isArray(combinedBotData) || combinedBotData.length === 0) && (
             <li className="px-4 py-4 text-sm text-gray-500 dark:text-gray-400">No bot configurations found. Create one above.</li>
          )}
          {/* Use combinedBotData which includes merged status */}
          {Array.isArray(combinedBotData) && combinedBotData.map((botData) => { 
            const displayStatus = getDisplayStatus(botData);
            const isLoadingAction = loadingStates[botData.id];
            // Determine if start should be disabled (not enabled OR already running OR in error state)
            const isStartDisabled = isLoadingAction || !botData.is_enabled || botData.is_running || displayStatus.color.includes('red');
            // Determine if stop should be disabled (not running OR loading action)
            const isStopDisabled = isLoadingAction || !botData.is_running;

            return (
              <li key={botData.id} className="px-4 py-4 sm:px-6 flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-indigo-600 dark:text-indigo-400 truncate">{botData.name || botData.bot_type} ({botData.symbol})</p>
                  <p className="mt-1 flex items-center text-sm text-gray-500 dark:text-gray-400">
                    <span className={`mr-1.5 h-2 w-2 rounded-full ${displayStatus.dot}`}></span>
                    <span className={displayStatus.color}>{displayStatus.text}</span>
                  </p>
                  <p className="text-xs text-gray-400 dark:text-gray-500">ID: {botData.id}</p>
                </div>
                <div className="ml-4 flex-shrink-0 space-x-2"> {/* Added space-x-2 for button spacing */}
                  {/* Edit Button */}
                  <button
                    type="button"
                    onClick={() => {
                      // Ensure onEditClick is a function before calling
                      if (typeof onEditClick === 'function') {
                        onEditClick(botData);
                      } else {
                        console.error("onEditClick is not a function!", onEditClick);
                      }
                    }}
                    disabled={isLoadingAction} // Disable if another action is loading
                    className="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 text-xs font-medium rounded-md shadow-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                  >
                    Edit
                  </button>

                  {/* Backtest Button */}
                  <button
                    type="button"
                    onClick={() => {
                      // Ensure onBacktestClick is a function before calling
                      if (typeof onBacktestClick === 'function') {
                        onBacktestClick(botData); // Pass the bot data
                      } else {
                        console.error("onBacktestClick is not a function!", onBacktestClick);
                      }
                    }}
                    disabled={isLoadingAction} // Disable if another action is loading
                    className="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 text-xs font-medium rounded-md shadow-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                  >
                    Backtest
                  </button>

                  {/* Start/Stop Button */}
                  {botData.is_running ? (
                    <button
                      type="button"
                      onClick={() => handleStopBot(botData.id)}
                      disabled={isStopDisabled}
                      className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md shadow-sm text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                    >
                      {isLoadingAction ? 'Stopping...' : 'Stop'}
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => handleStartBot(botData.id)}
                      disabled={isStartDisabled}
                      className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                       {isLoadingAction ? 'Starting...' : 'Start'}
                    </button>
                  )}
                   {/* TODO: Add Delete button */}
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}