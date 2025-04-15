'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Chart } from 'react-chartjs-2';
import axiosInstance from '@/lib/axiosInstance'; // Import axios instance
import { AxiosError } from 'axios'; // Import AxiosError for type checking
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  Title,
  Tooltip,
  Legend,
  // No TimeScale needed for this basic heatmap example
} from 'chart.js';
import { MatrixController, MatrixElement } from 'chartjs-chart-matrix';
import { ChartConfiguration } from 'chart.js'; // Import ChartConfiguration type

// Register necessary Chart.js components and the matrix plugin elements
ChartJS.register(
  CategoryScale, // Use CategoryScale for labels
  LinearScale,   // Use LinearScale for values
  Title,
  Tooltip,
  Legend,
  MatrixController,
  MatrixElement
);

// Mock data generation removed

// Define the structure for a single data point in the heatmap
interface HeatmapDataPoint {
  x: string; // Typically the column label (e.g., Asset Symbol)
  y: string; // Typically the row label (e.g., Metric or another Asset Symbol)
  v: number; // The value for the cell (e.g., correlation, performance)
}

// Define the expected structure of the API response
interface HeatmapApiResponse {
  data: HeatmapDataPoint[];
  xLabels: string[]; // Unique labels for the x-axis
  yLabels: string[]; // Unique labels for the y-axis
}

// Define the structure for the chart's dataset state
interface HeatmapChartDataState {
  datasets: {
    label: string;
    data: HeatmapDataPoint[];
    backgroundColor: (context: any) => string;
    borderColor: string;
    borderWidth: number;
    width: (context: any) => number;
    height: (context: any) => number;
  }[];
}

const HeatmapChart = () => {
  const [chartData, setChartData] = useState<HeatmapChartDataState | null>(null);
  const [xLabels, setXLabels] = useState<string[]>([]);
  const [yLabels, setYLabels] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await axiosInstance.get<HeatmapApiResponse>('market/heatmap');
      const apiData = response.data;

      if (!apiData || !apiData.data || !apiData.xLabels || !apiData.yLabels) {
          throw new Error("Invalid data format received from heatmap API.");
      }

      setXLabels(apiData.xLabels);
      setYLabels(apiData.yLabels);

      const numCols = apiData.xLabels.length;
      const numRows = apiData.yLabels.length;

      setChartData({
        datasets: [
          {
            label: 'Market Heatmap', // Updated label
            data: apiData.data,
            backgroundColor: (context: any) => {
              if (!context.raw) return 'rgba(200,200,200,0.2)'; // Color for missing/null data
              const value = context.raw.v;
              // Example: Red/Green for correlation (-1 to 1) or performance
              // Assuming value range is -1 to 1 for correlation example
              const alpha = Math.abs(value); // Intensity based on magnitude
              const r = value > 0 ? 0 : 255; // Red for negative correlation
              const g = value > 0 ? 255 : 0; // Green for positive correlation
              // Adjust this logic based on the actual meaning and range of 'v'
              // If 'v' is performance (0-100), use the previous blue-red gradient:
              // const alpha = (value / 100);
              // const r = 255 * alpha;
              // const b = 255 * (1 - alpha);
              // return `rgba(${r}, 0, ${b}, ${0.2 + alpha * 0.8})`; // Make intensity vary too
              return `rgba(${r}, ${g}, 0, ${0.1 + alpha * 0.9})`; // Opacity based on magnitude
            },
            borderColor: 'rgba(100, 100, 100, 0.5)',
            borderWidth: 1,
            // Adjust cell size based on fetched label counts
            width: (context: any) => context.chart.chartArea?.width / (numCols + 1), // Add padding
            height: (context: any) => context.chart.chartArea?.height / (numRows + 1), // Add padding
          },
        ],
      });

    } catch (err) {
      console.error('Error fetching heatmap data:', err);
       if (err instanceof AxiosError) {
         setError(`Failed to fetch heatmap: ${err.response?.data?.detail || err.message}`);
       } else if (err instanceof Error) {
         setError(`Failed to fetch heatmap: ${err.message}`);
       } else {
         setError('An unknown error occurred while fetching heatmap data.');
       }
      setChartData(null); // Clear data on error
      setXLabels([]);
      setYLabels([]);
    } finally {
      setIsLoading(false);
    }
  }, []); // No dependencies needed if it fetches static heatmap data once

  useEffect(() => {
    fetchData();
  }, [fetchData]);
  // Options need to be constructed dynamically based on fetched labels

  // Define options with explicit types where possible
  // Define options dynamically based on fetched labels
  const options: ChartConfiguration<'matrix'>['options'] = React.useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      title: { display: true, text: 'Market Heatmap' },
      tooltip: {
        callbacks: {
          title: () => '',
          label: (context: any) => {
            const item = context.raw as HeatmapDataPoint;
            if (!item) return '';
            // Adjust tooltip based on what x/y represent (e.g., Asset vs Metric, Asset vs Asset)
            return `${item.y} / ${item.x}: ${item.v?.toFixed(2) ?? 'N/A'}`;
          },
        },
      },
    },
    scales: {
      x: {
        type: 'category',
        labels: xLabels, // Use fetched labels
        grid: { display: false },
        ticks: { display: true, autoSkip: false, maxRotation: 90, minRotation: 45 }, // Rotate labels if needed
        position: 'bottom', // Ensure x-axis is at the bottom
      },
      y: {
        type: 'category',
        labels: yLabels, // Use fetched labels
        offset: true,
        grid: { display: false },
        ticks: { display: true, autoSkip: false },
        position: 'left', // Ensure y-axis is on the left
      },
    },
    layout: {
      padding: { top: 10, bottom: 50, left: 50, right: 10 }, // Adjust padding for labels
    },
  }), [xLabels, yLabels]); // Recompute options when labels change

  if (isLoading) {
    return <div className="flex justify-center items-center h-64">Loading heatmap data...</div>;
  }

  if (error) {
    return <div className="flex justify-center items-center h-64 text-red-500">Error: {error}</div>;
  }

  if (!chartData || !chartData.datasets || chartData.datasets.length === 0 || chartData.datasets[0].data.length === 0) {
    return <div className="flex justify-center items-center h-64">No heatmap data available.</div>;
  }

  // Use the generic Chart component with type 'matrix'
  // Use the generic Chart component with type 'matrix'
  return <div className="relative h-64 md:h-96"> {/* Added container for sizing */}
           <Chart type='matrix' options={options} data={chartData} />
         </div>;
};

export default HeatmapChart;