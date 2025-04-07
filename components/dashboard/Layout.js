// components/dashboard/Layout.js
'use client'; // Mark as client component for potential stateful elements (like sidebar toggle)

import React, { useState } from 'react';
import { useAuth } from '../../lib/context/AuthContext'; // Import useAuth
import Link from 'next/link'; // Import Link for navigation
// import { UserIcon, MenuIcon, XIcon } from '@heroicons/react/outline'; // Example icons
export default function DashboardLayout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false); // Example state for mobile sidebar
  const { user, loading, signOut } = useAuth(); // Get auth state and functions
  // User Dropdown Component using Auth Context
  const UserDropdown = ({ user, loading, signOut }) => {
    const [dropdownOpen, setDropdownOpen] = useState(false);

    if (loading) {
      return <div className="ml-3 text-sm text-gray-500 dark:text-gray-400">Loading...</div>;
    }

    return (
      <div className="relative ml-3">
        <div>
          <button
            type="button"
            className="flex items-center max-w-xs p-1 bg-gray-200 dark:bg-gray-700 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            id="user-menu-button"
            aria-expanded={dropdownOpen}
            aria-haspopup="true"
            onClick={() => setDropdownOpen(!dropdownOpen)}
          >
            <span className="sr-only">Open user menu</span>
            {/* User Icon or Initials - Placeholder for now */}
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-gray-600 dark:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
               <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
             {user && <span className="hidden sm:inline ml-2 text-sm text-gray-700 dark:text-gray-200">{user.email}</span>}
          </button>
        </div>

        {/* Dropdown menu */}
        {dropdownOpen && (
          <div
            className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white dark:bg-gray-800 ring-1 ring-black ring-opacity-5 focus:outline-none"
            role="menu"
            aria-orientation="vertical"
            aria-labelledby="user-menu-button"
            tabIndex="-1"
          >
            {user ? (
              <>
                <div className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-200 border-b border-gray-200 dark:border-gray-700">
                  Signed in as <br/><strong>{user.email}</strong>
                </div>
                {/* Add other links like Profile, Settings here if needed */}
                <button
                  onClick={() => {
                    signOut();
                    setDropdownOpen(false); // Close dropdown after sign out
                  }}
                  className="block w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700"
                  role="menuitem"
                  tabIndex="-1"
                  id="user-menu-item-signout"
                >
                  Sign out
                </button>
              </>
            ) : (
              // Optionally show Sign In link if needed, though AuthProvider handles redirection
              <a href="/auth/login" className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700" role="menuitem" tabIndex="-1">
                Sign In
              </a>
            )}
          </div>
        )}
      </div>
    );
  };

  // Sidebar Navigation Links using Next.js Link
  const NavLinks = () => (
     <nav className="mt-5 flex-1 px-2 space-y-1">
        {/* Use Link component for client-side navigation */}
        <Link href="/" className="bg-gray-200 dark:bg-gray-900 text-gray-900 dark:text-white group flex items-center px-2 py-2 text-sm font-medium rounded-md">
          {/* Placeholder Icon */}
          <svg xmlns="http://www.w3.org/2000/svg" className="mr-3 flex-shrink-0 h-6 w-6 text-gray-500 dark:text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
          Dashboard
        </Link>
        <Link href="/bots" className="text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white group flex items-center px-2 py-2 text-sm font-medium rounded-md">
           <svg xmlns="http://www.w3.org/2000/svg" className="mr-3 flex-shrink-0 h-6 w-6 text-gray-400 dark:text-gray-500 group-hover:text-gray-500 dark:group-hover:text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
           </svg>
          Bots
        </Link>
         <Link href="/performance" className="text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white group flex items-center px-2 py-2 text-sm font-medium rounded-md">
           <svg xmlns="http://www.w3.org/2000/svg" className="mr-3 flex-shrink-0 h-6 w-6 text-gray-400 dark:text-gray-500 group-hover:text-gray-500 dark:group-hover:text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
           </svg>
          Performance
        </Link>
         <Link href="/settings" className="text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white group flex items-center px-2 py-2 text-sm font-medium rounded-md">
           <svg xmlns="http://www.w3.org/2000/svg" className="mr-3 flex-shrink-0 h-6 w-6 text-gray-400 dark:text-gray-500 group-hover:text-gray-500 dark:group-hover:text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
             <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
           </svg>
          Settings
        </Link>
        {/* Add more links here */}
      </nav>
  );

  return (
    <div className="min-h-screen flex overflow-hidden bg-gray-100 dark:bg-gray-900">
      {/* --- Mobile Sidebar --- */}
      {/* Implement transition later */}
      {sidebarOpen && (
         <div className="md:hidden" role="dialog" aria-modal="true">
            <div className="fixed inset-0 flex z-40">
               {/* Overlay */}
               <div className="fixed inset-0 bg-gray-600 bg-opacity-75" aria-hidden="true" onClick={() => setSidebarOpen(false)}></div>
               {/* Sidebar Content */}
               <div className="relative flex-1 flex flex-col max-w-xs w-full pt-5 pb-4 bg-white dark:bg-gray-800">
                  <div className="absolute top-0 right-0 -mr-12 pt-2">
                     <button
                        type="button"
                        className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
                        onClick={() => setSidebarOpen(false)}
                     >
                        <span className="sr-only">Close sidebar</span>
                        {/* Placeholder X Icon */}
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                     </button>
                  </div>
                  <div className="flex-shrink-0 flex items-center px-4">
                     {/* Placeholder Logo */}
                     <span className="text-xl font-bold text-gray-900 dark:text-white">TradingBots</span>
                  </div>
                  <div className="mt-5 flex-1 h-0 overflow-y-auto">
                     <NavLinks />
                  </div>
               </div>
               <div className="flex-shrink-0 w-14" aria-hidden="true">{/* Dummy element */}</div>
            </div>
         </div>
      )}

      {/* --- Static Sidebar for Desktop --- */}
      <div className="hidden md:flex md:flex-shrink-0">
        <div className="flex flex-col w-64">
          <div className="flex flex-col h-0 flex-1 border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <div className="flex items-center flex-shrink-0 px-4 h-16">
              {/* Placeholder Logo */}
              <span className="text-xl font-bold text-gray-900 dark:text-white">TradingBots</span>
            </div>
            <div className="flex-1 flex flex-col overflow-y-auto">
              <NavLinks />
            </div>
          </div>
        </div>
      </div>

      {/* --- Main Content Area --- */}
      <div className="flex flex-col w-0 flex-1 overflow-hidden">
        {/* Header */}
        <div className="relative z-10 flex-shrink-0 flex h-16 bg-white dark:bg-gray-800 shadow">
          {/* Mobile Menu Button */}
          <button
            type="button"
            className="px-4 border-r border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500 md:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <span className="sr-only">Open sidebar</span>
            {/* Placeholder Menu Icon */}
            <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          {/* Header Content */}
          <div className="flex-1 px-4 flex justify-between">
            <div className="flex-1 flex">
              {/* Placeholder for Search or other header items */}
            </div>
            <div className="ml-4 flex items-center md:ml-6">
              {/* Placeholder for Notifications */}
              <button className="p-1 rounded-full text-gray-400 dark:text-gray-500 hover:text-gray-500 dark:hover:text-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                 <span className="sr-only">View notifications</span>
                 <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                 </svg>
              </button>
              {/* User Dropdown */}
              <UserDropdown user={user} loading={loading} signOut={signOut} />
            </div>
          </div>
        </div>

        {/* Page Content */}
        <main className="flex-1 relative overflow-y-auto focus:outline-none">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
              {/* Placeholder Title */}
              {/* <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Dashboard</h1> */}
            </div>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
              {/* Content goes here */}
              <div className="py-4">
                {/* Example Content Card */}
                {/* <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                  <div className="px-4 py-5 sm:p-6">
                     Main dashboard content rendered via children prop below
                  </div>
                </div> */}
                {children} 
              </div>
              {/* /End content */}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}