import React from 'react';
import './styles/globals.css';
import { 
  createBrowserRouter, 
  RouterProvider,
  Route,
  createRoutesFromElements,
  RouteObject
} from 'react-router-dom';
import Layout from './components/Layout';
import LandingPage from './pages/LandingPage';
import StoryGeneration from './pages/StoryGeneration';
import BookUpload from './pages/BookUpload';
import NodeEditor from './components/NodeEditor';

/**
 * Application Router Configuration
 * 
 * Defines the main routing structure for the application using React Router.
 * The router is configured with the following routes:
 * - / : Landing page (index route)
 * - /create-story: Story generation interface
 * - /upload-book: Book upload functionality
 * - /story/edit: Node-based story editor
 * 
 * All routes are wrapped in a common Layout component that provides:
 * - Consistent navigation header
 * - Page transitions
 * - Error boundaries
 */
const router = createBrowserRouter(
  createRoutesFromElements(
    <Route element={<Layout />}>
      <Route 
        index 
        element={<LandingPage />} 
        handle={{ crumb: 'Home' }}
      />
      <Route 
        path="/create-story" 
        element={<StoryGeneration />}
        handle={{ crumb: 'Create Story' }}
      />
      <Route 
        path="/upload-book" 
        element={<BookUpload />}
        handle={{ crumb: 'Upload Book' }}
      />
      <Route 
        path="/story/edit" 
        element={<NodeEditor />}
        handle={{ crumb: 'Story Editor' }}
      />
    </Route>
  ),
  {
    future: {
      // Remove future flags for now to fix TypeScript errors
      // These can be re-enabled when upgrading to React Router v7
    }
  }
);

/**
 * Main Application Component
 * 
 * Provides the router context to the entire application.
 * Wrapped in StrictMode for development checks and ErrorBoundary
 * for graceful error handling.
 * 
 * @returns {JSX.Element} The root application component
 */
function App(): JSX.Element {
  return <RouterProvider router={router} />;
}

export default App;
