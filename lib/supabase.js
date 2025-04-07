import { createClient } from '@supabase/supabase-js';

// Ensure these environment variables are set in your Next.js environment
// (e.g., in .env.local) prefixed with NEXT_PUBLIC_
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

if (!supabaseUrl) {
  console.error("Error: Missing Supabase URL. Make sure NEXT_PUBLIC_SUPABASE_URL is set in your environment variables.");
  // Optionally throw an error or handle this case appropriately
  // throw new Error("Missing Supabase URL environment variable.");
}

if (!supabaseAnonKey) {
  console.error("Error: Missing Supabase Anon Key. Make sure NEXT_PUBLIC_SUPABASE_ANON_KEY is set in your environment variables.");
  // Optionally throw an error or handle this case appropriately
  // throw new Error("Missing Supabase Anon Key environment variable.");
}

// Create and export the Supabase client instance
// Handle the case where variables might be missing during build/runtime
export const supabase = (supabaseUrl && supabaseAnonKey) 
  ? createClient(supabaseUrl, supabaseAnonKey) 
  : null;

// You might want to add a check elsewhere in your app to ensure supabase is not null before using it.
// Example: if (!supabase) { /* handle error */ }