import { supabase } from './supabase'; // Import the Supabase client

// Ensure Supabase client is initialized before using it
const checkSupabase = () => {
  if (!supabase) {
    console.error("Supabase client is not initialized. Check environment variables and supabase.js");
    throw new Error("Supabase client failed to initialize.");
  }
};

// --- User Management ---

/**
 * Fetches the current user's profile data.
 * Assumes user is authenticated via Supabase Auth.
 */
export const getUserProfile = async () => {
  checkSupabase();
  const { data: { user }, error: userError } = await supabase.auth.getUser();
  if (userError || !user) {
    console.error("Error fetching user:", userError?.message);
    return null;
  }
  
  const { data, error } = await supabase
    .from('users') // Assumes 'users' table exists
    .select('*')
    .eq('id', user.id)
    .single();

  if (error) {
    console.error("Error fetching user profile:", error.message);
    return null;
  }
  return data;
};

/**
 * Updates the current user's profile data.
 */
export const updateUserProfile = async (profileData) => {
   checkSupabase();
   const { data: { user }, error: userError } = await supabase.auth.getUser();
   if (userError || !user) {
     console.error("Error fetching user for update:", userError?.message);
     return { data: null, error: userError || new Error("User not found") };
   }

   const { data, error } = await supabase
     .from('users')
     .update(profileData)
     .eq('id', user.id)
     .select() // Return the updated data
     .single();

   if (error) {
     console.error("Error updating user profile:", error.message);
   }
   return { data, error };
};


// --- Bot Configuration Management ---

/**
 * Fetches all bot configurations for the current user.
 */
export const getBotConfigs = async () => {
  checkSupabase();
  // RLS policy should automatically filter by user_id if set up correctly
  const { data, error } = await supabase
    .from('bot_configs') // Assumes 'bot_configs' table exists
    .select('*'); 

  if (error) {
    console.error("Error fetching bot configs:", error.message);
    return [];
  }
  return data;
};

/**
 * Fetches a specific bot configuration by its ID.
 */
export const getBotConfigById = async (configId) => {
  checkSupabase();
  const { data, error } = await supabase
    .from('bot_configs')
    .select('*')
    .eq('id', configId)
    .single(); // Assumes RLS allows access

  if (error) {
    console.error(`Error fetching bot config ${configId}:`, error.message);
    return null;
  }
  return data;
};

/**
 * Creates a new bot configuration for the current user.
 */
export const createBotConfig = async (configData) => {
  checkSupabase();
  // user_id should likely be added automatically by a trigger/policy or passed in
  const { data, error } = await supabase
    .from('bot_configs')
    .insert([configData]) 
    .select()
    .single();

  if (error) {
    console.error("Error creating bot config:", error.message);
  }
  return { data, error };
};

/**
 * Updates an existing bot configuration.
 */
export const updateBotConfig = async (configId, updateData) => {
  checkSupabase();
  const { data, error } = await supabase
    .from('bot_configs')
    .update(updateData)
    .eq('id', configId) // Assumes RLS allows update
    .select()
    .single();

  if (error) {
    console.error(`Error updating bot config ${configId}:`, error.message);
  }
  return { data, error };
};

/**
 * Deletes a bot configuration.
 */
export const deleteBotConfig = async (configId) => {
  checkSupabase();
  const { error } = await supabase
    .from('bot_configs')
    .delete()
    .eq('id', configId); // Assumes RLS allows delete

  if (error) {
    console.error(`Error deleting bot config ${configId}:`, error.message);
  }
  return { error };
};


// --- Trade History ---

/**
 * Fetches trade history for the current user.
 * Add filtering/pagination parameters as needed.
 */
export const getTradeHistory = async (filters = {}) => {
  checkSupabase();
  let query = supabase
    .from('trades') // Assumes 'trades' table exists
    .select('*');
    // Add filters based on RLS or passed parameters, e.g., .eq('bot_config_id', filters.botId)
    // Add ordering, e.g., .order('timestamp', { ascending: false })
    
  const { data, error } = await query;

  if (error) {
    console.error("Error fetching trade history:", error.message);
    return [];
  }
  return data;
};


// --- Performance Data ---

/**
 * Fetches performance data for a specific bot or overall.
 */
export const getPerformanceData = async (filters = {}) => {
  checkSupabase();
  let query = supabase
    .from('performance') // Assumes 'performance' table exists
    .select('*');
    // Add filters, e.g., .eq('bot_config_id', filters.botId)
    // Add ordering or aggregation as needed

  const { data, error } = await query;

  if (error) {
    console.error("Error fetching performance data:", error.message);
    return [];
  }
  return data;
};

// --- Market Data Cache (Example - might be handled differently) ---

/**
 * Fetches cached market data.
 * Note: Caching might be better handled server-side or via other mechanisms.
 */
export const getCachedMarketData = async (symbol) => {
  checkSupabase();
  const { data, error } = await supabase
    .from('market_data') // Assumes 'market_data' table exists
    .select('data, last_updated')
    .eq('symbol', symbol)
    .single();

  if (error) {
    // Might be normal if data isn't cached yet
    // console.warn(`No cached market data for ${symbol}:`, error.message);
    return null; 
  }
  // Add logic here to check if data is stale based on 'last_updated'
  return data;
};