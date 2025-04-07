'use client'; // Mark as client component because it uses hooks/components that need client-side rendering

import React from 'react';
import DashboardLayout from '@/components/dashboard/Layout'; // Import the main layout
import MarketOverview from '@/components/dashboard/MarketOverview';
import BotControlPanel from '@/components/dashboard/BotControl';
import PriceChart from '@/components/charts/PriceChart'; // Example chart
// Import other dashboard components as needed
// import PerformanceDashboard from '@/components/dashboard/Performance';
// import BacktestInterface from '@/components/dashboard/Backtest';

export default function DashboardPage() {
  // This page now represents the main dashboard view

  // Example: Fetch data needed for charts or pass down props
  const exampleChartSymbol = 'BTCUSDT'; 
  // In a real app, fetch chart data here or within PriceChart using SWR/useEffect

  return (
    <DashboardLayout>
      {/* Wrap content in the layout */}
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-white mb-6">Dashboard</h1>

      {/* Add dashboard components here */}
      <div className="space-y-6">
        <MarketOverview />
        <BotControlPanel />
        
        {/* Example of including a chart */}
        <PriceChart symbol={exampleChartSymbol} /* chartData={fetchedChartData} */ /> 

        {/* Add other components like Performance, Backtest interface etc. */}
        {/* <PerformanceDashboard /> */}
        {/* <BacktestInterface /> */}
      </div>
    </DashboardLayout>
  );
}
