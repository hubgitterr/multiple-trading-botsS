// app/performance/page.tsx
'use client';

import React from 'react';
import DashboardLayout from '@/components/dashboard/Layout';
import PerformanceDashboard from '@/components/dashboard/Performance';
import BotComparison from '@/components/dashboard/BotComparison';

export default function PerformancePage() {
  return (
    <DashboardLayout>
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">Performance Analysis</h1>
      
      <div className="space-y-6">
         <PerformanceDashboard />
         <BotComparison />
      </div>

    </DashboardLayout>
  );
}