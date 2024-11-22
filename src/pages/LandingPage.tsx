import React from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';

const LandingPage: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] text-center">
      <h1 className="text-4xl font-bold mb-6">Welcome to Story Generator</h1>
      <p className="text-xl mb-8 max-w-2xl">
        Create captivating stories with AI assistance or upload your books for enhanced processing
      </p>
      <div className="flex gap-4">
        <Link to="/create-story">
          <Button size="lg">Start Creating</Button>
        </Link>
        <Link to="/upload-book">
          <Button size="lg" variant="outline">Upload Book</Button>
        </Link>
      </div>
    </div>
  );
}

export default LandingPage;
