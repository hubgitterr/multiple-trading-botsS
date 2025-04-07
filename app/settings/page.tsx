// app/settings/page.tsx
'use client';

import React from 'react';
import DashboardLayout from '@/components/dashboard/Layout';
import ApiKeyManager from '@/components/settings/ApiKeyManager'; // Import the API Key Manager

export default function SettingsPage() {
  return (
    <DashboardLayout>
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">Settings</h1>
      
      <div className="space-y-8">
         {/* API Key Management Section */}
         <ApiKeyManager />

         {/* TODO: Add other settings sections */}
         {/* Example: User Preferences */}
         {/* <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-4 sm:p-6">
            <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-white mb-4">Preferences</h3>
            {/* Add form elements for theme, notifications, etc. */}
         {/* </div> */}

      </div>

    </DashboardLayout>
  );
}