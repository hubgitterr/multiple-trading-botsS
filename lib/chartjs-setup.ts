// lib/chartjs-setup.ts
import {
  Chart,
  // Import necessary components from chart.js
  LinearScale,
  CategoryScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  TimeScale, // Needed for time axes
  Filler // Needed for area fills if used
  // Add other registerables as needed by your charts (BarElement, ArcElement, etc.)
} from 'chart.js';
import {
  CandlestickController,
  CandlestickElement,
  // OhlcController, // Uncomment if using OHLC charts
  // OhlcElement    // Uncomment if using OHLC charts
} from 'chartjs-chart-financial';
import 'chartjs-adapter-date-fns'; // Import the date adapter

// Register all necessary components
Chart.register(
  // Core components
  LinearScale,
  CategoryScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  TimeScale,
  Filler, // Register Filler if needed

  // Financial chart components
  CandlestickController, // Essential for type: 'candlestick'
  CandlestickElement   // Essential for rendering candlestick elements
  // OhlcController,    // Uncomment if using OHLC charts
  // OhlcElement       // Uncomment if using OHLC charts
  // Add other controllers/elements if needed (e.g., BarController, BarElement)
);

// You can optionally export Chart if needed elsewhere, but the registration is the main goal.
// export { Chart };