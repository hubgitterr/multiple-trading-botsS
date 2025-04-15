'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import axiosInstance from '@/lib/axiosInstance'; // Import axios instance
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale, // Import TimeScale
} from 'chart.js';
import 'chartjs-adapter-date-fns'; // Import the adapter
import { AxiosError } from 'axios'; // Import AxiosError for type checking
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale // Register TimeScale
);

// Define the structure for individual data points and datasets
interface ChartPoint {
  x: Date;
  y: number | null;
}

interface ChartDataset {
  label: string;
  data: ChartPoint[];
  borderColor: string;
  tension: number;
  fill: boolean;
}

// Define the structure for our chart data state
interface ChartDataState {
  // labels: Date[]; // Removed labels array
  datasets: ChartDataset[];
}

const MAX_DATA_POINTS = 60; // Keep the last 60 data points (e.g., 5 minutes at 5s interval)
const POLLING_INTERVAL = 5000; // Poll every 5 seconds
const COLORS = [
  'rgb(75, 192, 192)',
  'rgb(255, 99, 132)',
  'rgb(54, 162, 235)',
  'rgb(255, 206, 86)',
  'rgb(153, 102, 255)',
  'rgb(255, 159, 64)',
];

interface RealTimeChartProps {
  symbols?: string[];
}

// Define the structure for the API response
interface PriceResponse {
  [symbol: string]: number;
}


const RealTimeChart: React.FC<RealTimeChartProps> = ({ symbols = ['BTCUSDT', 'ETHUSDT'] }) => {
  const [chartData, setChartData] = useState<ChartDataState>({ datasets: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const chartRef = useRef(null);

  // Initialize datasets based on symbols prop
  useEffect(() => {
    // Initialize datasets with the new structure
    setChartData({
      datasets: symbols.map((symbol, index) => ({
        label: symbol,
        data: [], // Data is now an array of {x, y} objects
        borderColor: COLORS[index % COLORS.length],
        tension: 0.1,
        fill: false,
      })),
    });
    // Reset loading/error state when symbols change
    setIsLoading(true);
    setError(null);
  }, [symbols]); // Re-run if symbols prop changes

  const fetchData = useCallback(async () => {
    if (symbols.length === 0) {
        setIsLoading(false);
        setError("No symbols provided.");
        return;
    }
    try {
      // console.log(`Fetching prices for: ${symbols.join(',')}`);
      const response = await axiosInstance.get<PriceResponse>('market/prices/current', {
        params: { symbols: symbols.join(',') },
      });
      const prices = response.data;
      const now = new Date();
      // console.log('Received prices:', prices);

      setChartData((prevData): ChartDataState => {
        // --- START NEW COMPARISON LOGIC ---
        let hasChanged = false;
        const latestPrevDataPoints: { [key: string]: number | null } = {};

        // 1. Get latest points from previous state
        prevData.datasets.forEach(dataset => {
          // Ensure data exists and has length before accessing the last element
          if (dataset.data && dataset.data.length > 0) {
            latestPrevDataPoints[dataset.label] = dataset.data[dataset.data.length - 1].y;
          } else {
            latestPrevDataPoints[dataset.label] = null; // Mark as null if no data previously
          }
        });

        // 2. Compare with incoming prices
        for (const symbol in prices) {
          const newPrice = prices[symbol]; // Price from the latest fetch
          const oldPrice = latestPrevDataPoints[symbol]; // Last recorded price from state

          // Check if the symbol is new OR if the price value differs (including null changes)
          if (!(symbol in latestPrevDataPoints) || oldPrice !== newPrice) {
            hasChanged = true;
            break;
          }
        }

        // 3. Check for removed symbols that previously had data
        if (!hasChanged) { // Only check if no change found yet
          for (const symbol in latestPrevDataPoints) {
            // If a symbol existed in prevData but not in new prices, AND it wasn't already null
            if (!(symbol in prices) && latestPrevDataPoints[symbol] !== null) {
              hasChanged = true;
              break;
            }
          }
        }
        // --- END NEW COMPARISON LOGIC ---

        // 4. If no significant change, return previous state reference immediately
        if (!hasChanged) {
          // console.log('No significant data change detected (latest prices are the same), skipping state update.');
          return prevData;
        }

        // 5. If changed, proceed with creating the new state object
        // console.log('Data changed, proceeding with state update.');
        const now = new Date(); // Get timestamp only when needed for update

        // Create new datasets based on the previous state and new prices
        const updatedDatasets = prevData.datasets
          .filter(dataset => dataset.label in prices) // Keep only datasets for symbols still present
          .map((dataset) => {
            const newPrice = prices[dataset.label]; // Price must exist due to filter above
            const newPoint: ChartPoint = {
              x: now,
              y: newPrice, // Use the fetched price (cannot be undefined here)
            };

            // Append the new point and limit the data array size
            const currentData = dataset.data || []; // Handle potentially empty initial data
            const updatedData = [...currentData, newPoint].slice(-MAX_DATA_POINTS);

            return {
              ...dataset,
              data: updatedData,
            };
        });

        // Add datasets for any *new* symbols present in prices but not in prevData
        for (const symbol in prices) {
            if (!prevData.datasets.some(ds => ds.label === symbol)) {
                const newPrice = prices[symbol];
                // Use the COLORS array defined earlier
                const colorIndex = updatedDatasets.length % COLORS.length;
                const color = COLORS[colorIndex];

                updatedDatasets.push({
                    label: symbol,
                    data: [{ x: now, y: newPrice }],
                    borderColor: color,
                    // backgroundColor: `${color}33`, // Removed: Not a valid property in ChartDataset interface
                    fill: false,
                    tension: 0.1,
                    // Add any other necessary default dataset properties defined in ChartDataset or expected by Chart.js
                    // pointRadius: 3, // Example: if pointRadius is needed, ensure it's part of the type or add it
                });
            }
        }

        return { datasets: updatedDatasets }; // Return the new state object with updated and new datasets
      });

      setError(null); // Clear error on successful fetch
    } catch (err) {
      console.error('Error fetching real-time prices:', err);
       if (err instanceof AxiosError) {
         setError(`Failed to fetch prices: ${err.response?.data?.detail || err.message}`);
       } else if (err instanceof Error) {
         setError(`Failed to fetch prices: ${err.message}`);
       } else {
         setError('An unknown error occurred while fetching prices.');
       }
    } finally {
       // Set loading to false after the first fetch attempt completes
       // Subsequent fetches won't show the loading state again unless symbols change
       if (isLoading) {
           setIsLoading(false);
       }
    }
  }, [symbols]); // Removed isLoading dependency to break potential infinite loop

  // Effect for initial fetch and polling
  useEffect(() => {
    fetchData(); // Initial fetch

    const intervalId = setInterval(fetchData, POLLING_INTERVAL);

    return () => clearInterval(intervalId); // Cleanup interval on component unmount or symbols change
  }, [fetchData]); // Dependency array includes fetchData which includes symbols


  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Live Market Data Feed',
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
      },
    },
    scales: {
      x: {
        type: 'time' as const, // Use time scale for x-axis
        time: {
          unit: 'second' as const,
          tooltipFormat: 'PPpp', // Format for tooltip
          displayFormats: {
             second: 'HH:mm:ss' // Format for axis labels
          }
        },
        title: {
          display: true,
          text: 'Time',
        },
        ticks: {
          maxTicksLimit: 10, // Limit number of ticks for readability
          source: 'auto' as const,
        }
      },
      y: {
        beginAtZero: false, // Don't force y-axis to start at 0
        title: {
          display: true,
          text: 'Price',
        },
      },
    },
    animation: {
        duration: 500 // Smoother animation for updates
    } as const, // Add 'as const' for type safety if needed
  };

  if (isLoading) {
    return <div className="flex justify-center items-center h-64">Loading live data...</div>;
  }

  if (error) {
    return <div className="flex justify-center items-center h-64 text-red-500">Error: {error}</div>;
  }

  // Ensure chartData and datasets are valid before rendering
  // Check if datasets exist and at least one dataset has data points
  if (!chartData || !chartData.datasets || chartData.datasets.length === 0 || chartData.datasets.every(ds => ds.data.length === 0)) {
     return <div className="flex justify-center items-center h-64">Waiting for initial data...</div>;
  }


  // Type assertion needed because react-chartjs-2 types might not perfectly align with Chart.js v4 options structure sometimes
  return <div className="relative h-64 md:h-96"> {/* Added container for sizing */}
           <Line ref={chartRef} options={options as any} data={chartData} />
         </div>;
};

export default RealTimeChart;