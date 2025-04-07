// lib/axiosInstance.js
import axios from 'axios';
import { supabase } from './supabase'; // Import your Supabase client

// Define the base URL for your backend API
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'; 

const axiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // Set a reasonable timeout (e.g., 10 seconds)
  headers: {
    'Content-Type': 'application/json',
    // Add other default headers if needed
  },
});

// Request Interceptor
axiosInstance.interceptors.request.use(
  async (config) => {
    // Check if supabase client is available
    if (!supabase) {
       console.error("Supabase client not available in Axios interceptor.");
       // Optionally handle this case, e.g., by rejecting the request or allowing it without auth
       return config; 
    }

    // Get the current session from Supabase
    const { data: { session }, error } = await supabase.auth.getSession();

    if (error) {
      console.error("Error getting Supabase session in interceptor:", error);
      // Handle error, maybe reject the request or proceed without token
      return config; 
    }

    if (session?.access_token) {
      console.log("Attaching Supabase token to request header.");
      config.headers['Authorization'] = `Bearer ${session.access_token}`;
    } else {
       console.log("No active Supabase session found, request sent without token.");
       // Ensure any previous Authorization header is removed if no session exists
       delete config.headers['Authorization'];
    }

    return config;
  },
  (error) => {
    // Handle request error
    console.error("Axios request error:", error);
    return Promise.reject(error);
  }
);

// Optional: Response Interceptor (e.g., for handling global errors like 401 Unauthorized)
axiosInstance.interceptors.response.use(
  (response) => {
    // Any status code that lie within the range of 2xx cause this function to trigger
    return response;
  },
  (error) => {
    // Any status codes that falls outside the range of 2xx cause this function to trigger
    console.error("Axios response error:", error.response?.status, error.response?.data);
    
    // Example: Handle 401 Unauthorized globally (e.g., trigger sign out)
    if (error.response && error.response.status === 401) {
       console.warn("Received 401 Unauthorized response. Potential session expiry.");
       // TODO: Implement logic to sign out the user or refresh the token if possible
       // Example: Trigger sign out via context or event emitter
       // window.dispatchEvent(new Event('auth-sign-out-request')); 
    }
    
    return Promise.reject(error);
  }
);


export default axiosInstance;