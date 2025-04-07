// components/common/Notification.js
'use client';

import React, { useState, useEffect } from 'react';
// Import icons later if needed
// import { CheckCircleIcon, XCircleIcon, InformationCircleIcon, ExclamationIcon } from '@heroicons/react/solid';

export default function Notification({ id, type = 'info', title, message, duration = 5000, onDismiss }) {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (duration) {
      const timer = setTimeout(() => {
        handleDismiss();
      }, duration);
      return () => clearTimeout(timer); // Cleanup timer on unmount or duration change
    }
  }, [duration, id]); // Rerun effect if duration or id changes

  const handleDismiss = () => {
    setIsVisible(false);
    // Allow time for fade-out animation before calling onDismiss
    setTimeout(() => {
      if (onDismiss) {
        onDismiss(id);
      }
    }, 300); // Match animation duration (e.g., 300ms)
  };

  if (!isVisible) {
    return null; // Don't render if dismissed
  }

  // --- Determine styling based on type ---
  let bgColor = 'bg-blue-50 dark:bg-blue-900 border-blue-400 dark:border-blue-700';
  let iconColor = 'text-blue-400 dark:text-blue-300';
  let titleColor = 'text-blue-800 dark:text-blue-100';
  let messageColor = 'text-blue-700 dark:text-blue-200';
  let IconComponent = () => <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" /></svg>; // Placeholder Info Icon

  switch (type) {
    case 'success':
      bgColor = 'bg-green-50 dark:bg-green-900 border-green-400 dark:border-green-700';
      iconColor = 'text-green-400 dark:text-green-300';
      titleColor = 'text-green-800 dark:text-green-100';
      messageColor = 'text-green-700 dark:text-green-200';
      IconComponent = () => <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>; // Placeholder Success Icon
      break;
    case 'warning':
      bgColor = 'bg-yellow-50 dark:bg-yellow-900 border-yellow-400 dark:border-yellow-700';
      iconColor = 'text-yellow-400 dark:text-yellow-300';
      titleColor = 'text-yellow-800 dark:text-yellow-100';
      messageColor = 'text-yellow-700 dark:text-yellow-200';
      IconComponent = () => <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 3.001-1.742 3.001H4.42c-1.53 0-2.493-1.667-1.743-3.001l5.58-9.92zM10 13a1 1 0 110-2 1 1 0 010 2zm-1-4a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z" clipRule="evenodd" /></svg>; // Placeholder Warning Icon
      break;
    case 'error':
      bgColor = 'bg-red-50 dark:bg-red-900 border-red-400 dark:border-red-700';
      iconColor = 'text-red-400 dark:text-red-300';
      titleColor = 'text-red-800 dark:text-red-100';
      messageColor = 'text-red-700 dark:text-red-200';
      IconComponent = () => <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" /></svg>; // Placeholder Error Icon
      break;
    // Default is 'info'
  }

  // Basic fade-out transition (can be improved with libraries like framer-motion)
  const transitionClasses = isVisible ? 'opacity-100' : 'opacity-0';

  return (
    <div 
      className={`max-w-sm w-full ${bgColor} border-l-4 shadow-lg rounded-md pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden transition-opacity duration-300 ease-out ${transitionClasses}`}
    >
      <div className="p-4">
        <div className="flex items-start">
          <div className={`flex-shrink-0 ${iconColor}`}>
            <IconComponent />
          </div>
          <div className="ml-3 w-0 flex-1 pt-0.5">
            {title && <p className={`text-sm font-medium ${titleColor}`}>{title}</p>}
            {message && <p className={`mt-1 text-sm ${messageColor}`}>{message}</p>}
          </div>
          <div className="ml-4 flex-shrink-0 flex">
            <button
              onClick={handleDismiss}
              className={`bg-transparent rounded-md inline-flex ${messageColor} hover:text-opacity-80 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`} // Use message color for button for consistency
            >
              <span className="sr-only">Close</span>
               {/* Placeholder Close Icon */}
               <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                 <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
               </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}