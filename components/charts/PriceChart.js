// components/charts/PriceChart.js
'use client'; // Mark as client component for charting library usage

import React from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, TimeScale } from 'chart.js';
import { Line } from 'react-chartjs-2'; // Using Line chart as a base, Candlestick requires adapter/plugin
import 'chartjs-adapter-date-fns'; // Import adapter for time scale

// TODO: Implement or import a candlestick chart type if needed.
// Chart.js v3/v4 doesn't have built-in candlestick.
// Requires plugins like 'chartjs-chart-financial'.
// For now, we'll use a Line chart as a placeholder structure.

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  TimeScale, // Register TimeScale
  Title,
  Tooltip,
  Legend
);

export default function PriceChart({ chartData = null, symbol }) { // Make chartData optional, default to null
  // chartData prop should ideally be in the format expected by chartjs-chart-financial
  // or processed into the format needed by the Line chart.
  // Example structure for Line chart:
  // {
  //   labels: [timestamp1, timestamp2, ...], // or date objects
  //   datasets: [{
  //     label: 'Close Price',
  //     data: [price1, price2, ...],
  //     borderColor: 'rgb(75, 192, 192)',
  //     tension: 0.1
  //   }]
  // }

  // Placeholder data if none provided
  const defaultLabels = [new Date(2024, 0, 1), new Date(2024, 0, 2), new Date(2024, 0, 3), new Date(2024, 0, 4), new Date(2024, 0, 5)];
  const defaultData = {
    labels: defaultLabels,
    datasets: [
      {
        label: 'Close Price (Placeholder)',
        data: [65, 59, 80, 81, 56],
        borderColor: 'rgb(54, 162, 235)', // Blue
        backgroundColor: 'rgba(54, 162, 235, 0.5)',
        tension: 0.1,
      },
      // Add more datasets if needed (e.g., Volume, Moving Averages)
    ],
  };

  const dataToDisplay = chartData || defaultData;

  const options = {
    responsive: true,
    maintainAspectRatio: false, // Allow chart to fill container height
    plugins: {
      legend: {
        position: 'top',
        labels: {
           color: '#9ca3af', // Example: Gray color for legend text (adjust for dark mode)
        }
      },
      title: {
        display: true,
        text: `${symbol || 'Symbol'} Price Chart`,
        color: '#e5e7eb', // Example: Light gray for title (adjust for dark mode)
      },
      tooltip: {
         mode: 'index',
         intersect: false,
      }
    },
    scales: {
      x: {
         type: 'time', // Use time scale - Correct identifier is 'time'
         time: {
            unit: 'day', // Adjust unit based on data granularity (e.g., 'hour', 'minute')
            tooltipFormat: 'PPpp', // Format for tooltip (requires date-fns) - e.g., Feb 6, 2024, 1:30:00 PM
         },
         title: {
            display: true,
            text: 'Date / Time',
            color: '#9ca3af',
         },
         ticks: {
             color: '#9ca3af', // Color for x-axis labels
         },
         grid: {
             color: 'rgba(107, 114, 128, 0.3)', // Example grid line color
         }
      },
      y: {
        title: {
          display: true,
          text: 'Price',
          color: '#9ca3af',
        },
         ticks: {
             color: '#9ca3af', // Color for y-axis labels
         },
         grid: {
             color: 'rgba(107, 114, 128, 0.3)',
         }
      },
      // Add secondary Y axis if needed (e.g., for Volume)
      // y1: { ... }
    },
    interaction: {
       mode: 'nearest',
       axis: 'x',
       intersect: false
    }
  };

  return (
     <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-4 h-96"> {/* Set a fixed height or use aspect ratio */}
        {/* Ensure chartData is valid before rendering */}
        {dataToDisplay && dataToDisplay.labels && dataToDisplay.datasets ? (
           <Line options={options} data={dataToDisplay} />
        ) : (
           <p className="text-center text-gray-500 dark:text-gray-400">Loading chart data...</p>
        )}
     </div>
  );
}