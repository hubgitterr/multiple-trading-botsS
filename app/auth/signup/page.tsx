// app/auth/signup/page.tsx
'use client'; // Mark as a Client Component

import React, { useState } from 'react';
import { supabase } from '../../../lib/supabase'; // Fixed path
import { useRouter } from 'next/navigation';

export default function SignupPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const router = useRouter();

  const handleSignup = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    setError(null);
    setMessage(null);
    // Implement Supabase email/password signup
    try {
      // Ensure supabase client is available (it should be if imported correctly)
      if (!supabase) {
          throw new Error("Supabase client is not available.");
      }
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        // options: { emailRedirectTo: `${window.location.origin}/auth/callback` } // Optional: for email confirmation
      });

      if (error) {
          // Log the specific Supabase error
          console.error("Supabase signup error:", error);
          throw error; // Rethrow to be caught by the catch block
      }

      // Handle successful signup (data.user might contain user info)
      // Check Supabase project settings for email confirmation requirements
      setMessage('Signup successful! Check your email for confirmation.');
      setEmail(''); // Clear form on success
      setPassword('');
      setConfirmPassword('');
      // Optionally redirect:
      // router.push('/auth/login'); // Redirect to login page after signup

    } catch (err: any) {
      console.error("Signup error:", err.message);
      // Use the error message from Supabase if available, otherwise a generic one
      setError(err.message || 'An unexpected error occurred during signup.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900">
      <div className="p-8 max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold text-center text-gray-900 dark:text-white mb-6">
          Create Account
        </h2>
        <form onSubmit={handleSignup}>
          {error && (
            <p className="mb-4 text-center text-red-500">{error}</p>
          )}
          {message && (
            <p className="mb-4 text-center text-green-500">{message}</p>
          )}
          <div className="mb-4">
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Email Address
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              placeholder="you@example.com"
            />
          </div>
          <div className="mb-4">
            <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Password
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6} // Example: Enforce minimum password length
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              placeholder="••••••••"
            />
          </div>
          <div className="mb-6">
            <label
              htmlFor="confirmPassword"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
            >
              Confirm Password
            </label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              placeholder="••••••••"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {loading ? 'Creating Account...' : 'Sign Up'}
          </button>
        </form>
         <p className="mt-4 text-center text-sm text-gray-600 dark:text-gray-400">
            Already have an account?{' '}
            <a href="/auth/login" className="font-medium text-blue-600 hover:text-blue-500">
                Log in
            </a>
        </p>
      </div>
    </div>
  );
}