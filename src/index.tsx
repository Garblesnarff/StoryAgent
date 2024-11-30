import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import ErrorBoundary from './components/ErrorBoundary';

/**
 * Application Entry Point
 * 
 * Sets up the React application with error boundaries and strict mode.
 * Includes proper type checking and error handling for root element.
 * 
 * Features:
 * - Error Boundary for graceful error handling
 * - Strict Mode for development checks
 * - TypeScript type safety
 * - Clear error messaging
 */

// Get root element with proper type checking
const container: HTMLElement | null = document.getElementById('root');

// Validate root element existence
if (!container) {
  throw new Error(
    'Root element not found! Please add a div with id="root" to your HTML'
  );
}

// Create root with proper typing
const root = createRoot(container);

// Render application with error handling
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);
