import React from 'react';
import { Button } from '../components/ui/button';

const BookUpload: React.FC = () => {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Upload Book</h1>
      <div className="max-w-xl">
        <div className="border-2 border-dashed rounded-lg p-12 text-center">
          <input
            type="file"
            id="book-file"
            className="hidden"
            accept=".pdf,.epub,.txt"
          />
          <label htmlFor="book-file">
            <Button variant="outline" className="mb-4">
              Choose File
            </Button>
          </label>
          <p className="text-sm text-muted-foreground">
            Supported formats: PDF, EPUB, TXT
          </p>
        </div>
      </div>
    </div>
  );
}

export default BookUpload;
