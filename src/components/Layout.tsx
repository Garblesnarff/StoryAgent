import React from 'react';
import { Link, Outlet } from 'react-router-dom';
import { Button } from './ui/button';
import { Breadcrumb } from './ui/breadcrumb';

const Layout: React.FC = () => {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <nav className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="text-xl font-bold">
            Story Generator
          </Link>
          <div className="space-x-4">
            <Link to="/create-story">
              <Button variant="ghost">Create Story</Button>
            </Link>
            <Link to="/upload-book">
              <Button variant="ghost">Upload Book</Button>
            </Link>
          </div>
        </nav>
      </header>
      <main className="container mx-auto px-4 py-6 relative">
        <div className="max-w-7xl mx-auto">
          <Breadcrumb />
          <Outlet />
        </div>
      </main>
    </div>
  );
}

export default Layout;
