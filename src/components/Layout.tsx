import React from 'react';
import { Link, Outlet } from 'react-router-dom';
import { Button } from './ui/button';
import { Breadcrumb } from './ui/breadcrumb';

/**
 * Navigation configuration for the main application menu.
 * Each item defines a route path and display label.
 * 
 * @constant
 * @type {{ path: string; label: string }[]}
 */
const NAV_ITEMS = [
  { path: '/create-story', label: 'Create Story' },
  { path: '/upload-book', label: 'Upload Book' }
] as const;

/**
 * Main application layout component that provides the overall structure.
 * 
 * Features:
 * - Responsive navigation header with dynamic menu items
 * - Breadcrumb navigation for user orientation
 * - Flexible content container with proper spacing
 * - Consistent styling across all pages
 * 
 * @component
 * @example
 * ```tsx
 * <Layout>
 *   <ChildComponent />
 * </Layout>
 * ```
 */
const Layout: React.FC = () => {
  return (
    // Main container with full viewport height and background
    <div className="min-h-screen bg-background">
      {/* Header section with navigation */}
      <header className="border-b">
        <nav className="container mx-auto px-4 h-16 flex items-center justify-between">
          {/* Home link with hover effect */}
          <Link to="/" className="text-xl font-bold hover:text-primary transition-colors">
            Story Generator
          </Link>
          {/* Navigation buttons container */}
          <div className="space-x-4">
            {NAV_ITEMS.map(({ path, label }) => (
              <Link key={path} to={path}>
                <Button variant="ghost">{label}</Button>
              </Link>
            ))}
          </div>
        </nav>
      </header>
      {/* Main content area */}
      <main className="container mx-auto px-4 py-6 relative">
        <div className="max-w-7xl mx-auto">
          {/* Breadcrumb navigation for current location */}
          <Breadcrumb />
          {/* Outlet for rendering child routes */}
          <Outlet />
        </div>
      </main>
    </div>
  );
}

export default Layout;
