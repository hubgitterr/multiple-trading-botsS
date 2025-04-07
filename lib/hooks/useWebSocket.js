// lib/hooks/useWebSocket.js
'use client'; // Hook can be used in client components

import { useState, useEffect, useRef, useCallback } from 'react';

// Default WebSocket URL (replace with your actual backend WebSocket endpoint)
// Assuming your FastAPI backend serves WebSockets at /ws/{some_path}
const DEFAULT_WS_URL = 'ws://localhost:8000/ws/general'; // Example endpoint

/**
 * Custom hook to manage a WebSocket connection.
 * 
 * @param {string} url The WebSocket server URL. Defaults to DEFAULT_WS_URL.
 * @param {function} onMessageCallback Function to call when a message is received.
 * @param {boolean} shouldConnect Whether the hook should attempt to connect.
 * @returns {object} { lastMessage, connectionStatus, sendMessage }
 */
export function useWebSocket(url = DEFAULT_WS_URL, onMessageCallback, shouldConnect = true) {
  const [lastMessage, setLastMessage] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('Disconnected'); // Disconnected, Connecting, Connected, Error
  const ws = useRef(null); // Ref to hold the WebSocket instance

  const connect = useCallback(() => {
    if (!shouldConnect) {
       console.log('WebSocket connection disabled.');
       setConnectionStatus('Disabled');
       return;
    }

    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected.');
      setConnectionStatus('Connected');
      return;
    }

    console.log(`Attempting to connect WebSocket to ${url}...`);
    setConnectionStatus('Connecting');
    ws.current = new WebSocket(url);

    ws.current.onopen = () => {
      console.log('WebSocket Connected');
      setConnectionStatus('Connected');
      // Optional: Send a message on connect? e.g., authentication or subscription
      // ws.current.send(JSON.stringify({ type: 'subscribe', channel: 'prices' }));
    };

    ws.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log('WebSocket message received:', message);
        setLastMessage(message);
        if (onMessageCallback) {
          onMessageCallback(message); // Pass parsed message to the callback
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', event.data, error);
        // Handle non-JSON messages or errors
        setLastMessage(event.data); // Store raw data if parsing fails
         if (onMessageCallback) {
          onMessageCallback(event.data); 
        }
      }
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket Error:', error);
      setConnectionStatus('Error');
      // Consider adding automatic reconnection logic here with backoff
    };

    ws.current.onclose = (event) => {
      console.log(`WebSocket Disconnected: Code=${event.code}, Reason=${event.reason}`);
      // Avoid setting status to 'Disconnected' if it was intentionally disabled
      if (connectionStatus !== 'Disabled') { 
         setConnectionStatus('Disconnected');
      }
      ws.current = null; // Clear the ref
      // Optional: Attempt to reconnect after a delay if not explicitly closed/disabled
      // if (shouldConnect && connectionStatus !== 'Disabled') {
      //    setTimeout(connect, 5000); // Reconnect after 5 seconds
      // }
    };

  }, [url, onMessageCallback, shouldConnect, connectionStatus]); // Include connectionStatus to avoid reconnect loop if already disabled

  const disconnect = useCallback(() => {
     if (ws.current) {
        console.log('Disconnecting WebSocket...');
        setConnectionStatus('Disabled'); // Set status to prevent auto-reconnect if implemented
        ws.current.close(1000, 'User disconnected'); // 1000 indicates normal closure
        ws.current = null;
     }
  }, []);


  // Effect to manage connection lifecycle
  useEffect(() => {
    connect(); // Attempt to connect when the hook mounts or dependencies change

    // Cleanup function to close WebSocket on unmount or when shouldConnect becomes false
    return () => {
      disconnect();
    };
  }, [connect, disconnect]); // Dependencies ensure connect/disconnect are stable


  // Function to send messages via the WebSocket
  const sendMessage = useCallback((message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      try {
         const messageString = typeof message === 'string' ? message : JSON.stringify(message);
         console.log('Sending WebSocket message:', messageString);
         ws.current.send(messageString);
      } catch (error) {
         console.error("Failed to send WebSocket message:", error);
      }
    } else {
      console.warn('WebSocket is not connected. Cannot send message.');
    }
  }, []);

  return { lastMessage, connectionStatus, sendMessage };
}