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
  TimeScale, // Import TimeScale
} from 'chart.js';
import { CandlestickController, OhlcElement } from 'chartjs-chart-financial';
import 'chartjs-adapter-date-fns'; // Import the adapter
// import { subDays, format } from 'date-fns'; // No longer needed for mock data
// Register necessary Chart.js components and the financial plugin elements
ChartJS.register(
  CategoryScale,
  LinearScale,
  Title,
  Tooltip,
  Legend,
  TimeScale, // Register TimeScale
  CandlestickController,
  OhlcElement
);

// Mock data generation removed

// Define the structure for OHLC data points used by the chart
interface OhlcDataPoint {
  x: number; // Timestamp
  o: number; // Open
  h: number; // High
  l: number; // Low
  c: number; // Close
}

// Define the structure for the chart's dataset state
interface CandlestickChartDataState {
  datasets: {
    label: string;
    data: OhlcDataPoint[];
    borderColor?: string;
    borderWidth?: number;
    color?: {
      up: string;
      down: string;
      unchanged: string;
    };
  }[];
}

// Define the expected raw kline tuple format from the API
type KlineTuple = [number, string, string, string, string, string, ...any[]];

// Define the actual API response structure
interface ApiKlinesResponse {
  symbol: string;
  interval: string;
  klines: KlineTuple[];
}
interface CandlestickChartProps {
  symbol?: string;
  interval?: string;
  limit?: number;
}

const CandlestickChart: React.FC<CandlestickChartProps> = ({
  symbol = 'BTCUSDT',
  interval = '1h',
  limit = 100,
}) => {
  const [chartData, setChartData] = useState<CandlestickChartDataState>({ datasets: [] });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await axiosInstance.get<ApiKlinesResponse>('market/klines', {
        params: { symbol, interval, limit },
      });
      console.log('Raw klines response:', response.data); // Debugging line
      const klineData = response.data.klines; // Access the nested array

      // Process API data into chart format
      let processedData: OhlcDataPoint[] = [];
      if (Array.isArray(klineData)) {
        processedData = klineData.map((kline) => ({
          x: kline[0], // Timestamp (already a number)
          o: parseFloat(kline[1]), // Open
          h: parseFloat(kline[2]), // High
          l: parseFloat(kline[3]), // Low
          c: parseFloat(kline[4]), // Close
        }));
      } else {
        console.error("Received kline data is not an array:", klineData);
        setError("Received invalid kline data format from server.");
        // Keep processedData as empty array
      }

      setChartData({
        datasets: [
          {
            label: `${symbol} ${interval}`,
            data: processedData,
            borderColor: 'black',
            borderWidth: 1,
            color: {
              up: 'rgba(8, 153, 129, 1)', // Green
              down: 'rgba(215, 84, 66, 1)', // Red
              unchanged: 'rgba(201, 203, 207, 1)', // Grey
            },
          },
        ],
      });
    } catch (err) {
      console.error(`Error fetching klines for ${symbol}:`, err);
      if (err instanceof AxiosError) {
         setError(`Failed to fetch klines: ${err.response?.data?.detail || err.message}`);
       } else if (err instanceof Error) {
         setError(`Failed to fetch klines: ${err.message}`);
       } else {
         setError('An unknown error occurred while fetching kline data.');
       }
      setChartData({ datasets: [] }); // Clear data on error
    } finally {
      setIsLoading(false);
    }
  }, [symbol, interval, limit]);

  useEffect(() => {
    fetchData();
  }, [fetchData]); // Re-fetch when symbol, interval, or limit changes
  // Chart options remain largely the same, but update title dynamically

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false, // Often hide legend for candlestick
      },
      title: {
        display: true,
        text: `${symbol} Candlestick Chart (${interval})`,
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
      },
    },
    scales: {
      x: {
        type: 'time' as const,
        time: {
          // Unit might need adjustment based on interval, but 'auto' or letting adapter handle it is often fine
          // unit: 'day' as const, // Keep or adjust based on typical interval usage
          tooltipFormat: 'PPpp', // More detailed tooltip
           displayFormats: {
             // Let the adapter choose the best display format based on zoom/data range
             // day: 'MMM d'
          }
        },
        title: {
          display: true,
          text: 'Date',
        },
         ticks: {
          source: 'auto' as const,
          maxRotation: 0,
          autoSkip: true,
        }
      },
      y: {
        beginAtZero: false,
        title: {
          display: true,
          text: 'Price',
        },
      },
    },
  };

  if (isLoading) {
    return <div className="flex justify-center items-center h-64">Loading candlestick data...</div>;
  }

  if (error) {
    return <div className="flex justify-center items-center h-64 text-red-500">Error: {error}</div>;
  }

   if (!chartData || !chartData.datasets || chartData.datasets.length === 0 || chartData.datasets[0].data.length === 0) {
     return <div className="flex justify-center items-center h-64">No data available for {symbol}.</div>;
   }

  // Use the generic Chart component with type 'candlestick'
  return <div className="relative h-64 md:h-96"> {/* Added container for sizing */}
           <Chart type='candlestick' options={options as any} data={chartData} />
         </div>;
};

export default CandlestickChart;