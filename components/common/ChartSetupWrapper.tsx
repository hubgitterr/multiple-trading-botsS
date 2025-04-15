// components/common/ChartSetupWrapper.tsx
'use client';

import { useEffect } from 'react';
import '../../lib/chartjs-setup.ts'; // Import the setup file

export default function ChartSetupWrapper({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    // The import itself should trigger the registration logic in chartjs-setup.ts
    // If chartjs-setup.ts exports a function, call it here.
    // console.log('Chart.js setup executed.'); // Optional: for debugging
  }, []); // Empty dependency array ensures it runs only once on mount

  return <>{children}</>;
}