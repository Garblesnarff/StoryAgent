import React from 'react';

/**
 * Props for the ErrorBoundary component
 * 
 * @interface ErrorBoundaryProps
 * @property {React.ReactNode} children - Components to be wrapped with error handling
 * @example
 * ```tsx
 * // Basic usage
 * <ErrorBoundary>
 *   <Component />
 * </ErrorBoundary>
 * ```
 */
interface ErrorBoundaryProps {
  children: React.ReactNode;
}

/**
 * State interface for the ErrorBoundary component
 * @interface ErrorBoundaryState
 * @property {boolean} hasError - Indicates whether an error has occurred
 * @property {Error | null} error - The caught error object, if any
 */
interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error Boundary Component
 * 
 * A React component that catches JavaScript errors anywhere in its child component tree.
 * Prevents the entire application from crashing and provides a graceful fallback UI.
 * 
 * Key Features:
 * - Captures and handles runtime errors in components
 * - Provides user-friendly error messages
 * - Maintains application stability
 * - Offers recovery options through UI
 * - Logs errors for debugging purposes
 * 
 * Implementation Details:
 * - Uses React's componentDidCatch lifecycle method
 * - Maintains error state using getDerivedStateFromError
 * - Renders fallback UI when errors occur
 * - Provides reload functionality for recovery
 * 
 * Usage Notes:
 * - Place at top-level for broad error coverage
 * - Can be nested for granular error handling
 * - Ideal for protecting critical application flows
 * 
 * @component
 * @extends {React.Component<ErrorBoundaryProps, ErrorBoundaryState>}
 * 
 * @example
 * ```tsx
 * // Application-wide error boundary
 * const root = createRoot(container);
 * root.render(
 *   <ErrorBoundary>
 *     <App />
 *   </ErrorBoundary>
 * );
 * 
 * // Component-specific error boundary
 * function FeatureComponent() {
 *   return (
 *     <ErrorBoundary>
 *       <FeatureContent />
 *     </ErrorBoundary>
 *   );
 * }
 * ```
 */
class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null 
    };
  }

  /**
   * Static method to update state when an error occurs
   * Called during the render phase, before componentDidCatch
   * 
   * @param {Error} error - The error that was thrown
   * @returns {ErrorBoundaryState} New state with error information
   */
  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { 
      hasError: true, 
      error 
    };
  }

  /**
   * Lifecycle method called after an error has been caught
   * Used for error logging and analytics
   * 
   * @param {Error} error - The error that was thrown
   * @param {React.ErrorInfo} errorInfo - Component stack information
   */
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    // Log to error monitoring service or console
    console.error('React Error Boundary caught an error:', error, errorInfo);
  }

  render(): React.ReactNode {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-background">
          <div className="max-w-md p-8 rounded-lg bg-card shadow-lg">
            <h2 className="text-2xl font-bold text-destructive mb-4">Something went wrong</h2>
            <p className="text-muted-foreground mb-4">
              {this.state.error?.message || 'An unexpected error occurred'}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
