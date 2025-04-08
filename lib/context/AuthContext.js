// lib/context/AuthContext.js
'use client'; // Context provider needs to be a client component

import React, { createContext, useState, useEffect, useContext, useMemo } from 'react';
import { supabase } from '../supabase'; // Import your Supabase client
import { useRouter, usePathname } from 'next/navigation'; // For route protection

// Create the context
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null); // Store Supabase user object
  const [session, setSession] = useState(null); // Store Supabase session object
  const [loading, setLoading] = useState(true); // Initial loading state
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    let authListener = null;

    const getInitialSession = async () => {
       setLoading(true);
       try {
          const { data: { session: initialSession }, error } = await supabase.auth.getSession();
          if (error) throw error;
          
          setSession(initialSession);
          setUser(initialSession?.user ?? null);

          // Start listener after getting initial session
          const { data } = supabase.auth.onAuthStateChange((event, changedSession) => {
             try {
                console.log('Auth State Change:', event, changedSession);
                setSession(changedSession);
                setUser(changedSession?.user ?? null);


                // Basic Route Protection (redirect if logged out from protected route)
                // Define protected routes - adjust as needed
                const protectedRoutes = ['/dashboard', '/settings', '/bots']; // Example protected routes
                const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route));
                
                if (event === 'SIGNED_OUT' && isProtectedRoute) {
                   console.log('User signed out from protected route, redirecting to login.');
                   router.push('/auth/login');
                }
                // Optional: Redirect if signed in on auth pages
                // const isAuthPage = pathname.startsWith('/auth');
                // if (event === 'SIGNED_IN' && isAuthPage) {
                //    router.push('/dashboard');
                // }
             } catch (callbackError) {
                console.error("Error inside onAuthStateChange callback:", callbackError);
             } finally {
                setLoading(false); // Ensure loading is set to false even if callback errors
             }
          });
          authListener = data.subscription;

       } catch (error) {
          console.error("AuthContext: Error during getInitialSession:", error?.message || error); // Log error message specifically
          setLoading(false); // Still finish loading on error
       } 
    };

    getInitialSession();

    // Cleanup listener on unmount
    return () => {
      if (authListener) {
        authListener.unsubscribe();
        console.log('Auth listener unsubscribed.');
      }
    };
  }, [router, pathname]); // Rerun effect if router/pathname changes (for protection logic)


  // --- Basic Route Protection ---
  // Redirect if trying to access protected routes while logged out (and not loading)
  useEffect(() => {
     const protectedRoutes = ['/dashboard', '/settings', '/bots']; // Example protected routes
     const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route));
     
     if (!loading && !user && isProtectedRoute) {
        console.log('Not logged in and accessing protected route, redirecting.');
        router.push('/auth/login');
     }
  }, [user, loading, pathname, router]);


  // Function to sign out
  const signOut = async () => {
    setLoading(true); // Optional: show loading during sign out
    const { error } = await supabase.auth.signOut();
    if (error) {
       console.error("Error signing out:", error);
       // Handle error appropriately
    }
    // State update will be handled by onAuthStateChange listener
    // setLoading(false); // Listener will set loading false
    router.push('/auth/login'); // Redirect after sign out
  };

  // Memoize the context value to prevent unnecessary re-renders
  const value = useMemo(() => ({
    user,
    session,
    loading,
    signOut,
  }), [user, session, loading]); // signOut is stable due to useCallback pattern (implicitly via useEffect)

  // Render children only after initial loading attempt, or show loading indicator
  // Or, allow rendering children immediately and let them handle the loading state
  // if (loading) {
  //    return <div>Loading authentication...</div>; // Or a spinner component
  // }

  return (
    <AuthContext.Provider value={value}>
      {/* Render children, potentially adding a check for loading state if needed */}
      {/* {!loading ? children : <div>Loading...</div>} */}
      {children} 
    </AuthContext.Provider>
  );
}

// Custom hook to use the auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  // Return context directly, or null if context hasn't been initialized yet
  return context; 
};