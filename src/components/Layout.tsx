import React from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { Button } from './ui/button';

const Layout: React.FC = () => {
  const location = useLocation();
  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <nav className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link 
            to="/" 
            className="text-xl font-display font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-600"
          >
            Story Generator
          </Link>
          <div className="space-x-2">
            <Link to="/create-story">
              <Button 
                variant={isActive('/create-story') ? 'default' : 'ghost'}
                className={isActive('/create-story') ? 'bg-gradient-to-r from-primary to-purple-600' : ''}
              >
                Create Story
              </Button>
            </Link>
            <Link to="/upload-book">
              <Button 
                variant={isActive('/upload-book') ? 'default' : 'ghost'}
                className={isActive('/upload-book') ? 'bg-gradient-to-r from-primary to-purple-600' : ''}
              >
                Upload Book
              </Button>
            </Link>
          </div>
        </nav>
      </header>
      <main className="container mx-auto px-4 py-8">
        <Outlet />
      </main>
      <footer className="border-t mt-auto py-6">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          <p>Built with AI - Powered by Replit</p>
        </div>
      </footer>
    </div>
  );
}

export default Layout;
