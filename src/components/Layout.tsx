import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from './ui/button';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
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
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  );
}

export default Layout;
