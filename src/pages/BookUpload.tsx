import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Progress } from '../components/ui/progress';
import { Alert, AlertContent, AlertDescription, AlertHeader, AlertTitle, AlertFooter, AlertAction } from '../components/ui/alert';
import { motion } from 'framer-motion';

const BookUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (!selectedFile) return;

    const fileType = selectedFile.name.split('.').pop()?.toLowerCase();
    if (!fileType || !['pdf', 'epub', 'txt', 'html'].includes(fileType)) {
      setError('Please select a valid file type (PDF, EPUB, TXT, or HTML)');
      return;
    }

    setFile(selectedFile);
    setError(null);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setProgress(0);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // Remove any additional headers - let browser set correct Content-Type
      const response = await fetch('/story/upload', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Upload failed');
      }

      if (data.status === 'complete') {
        setProgress(100);
        setTimeout(() => {
          setUploading(false);
          navigate(data.redirect);
        }, 500);
      } else {
        throw new Error(data.error || 'Upload failed');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to upload file';
      setError(errorMessage);
      setProgress(0);
      setUploading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-gradient-to-b from-background to-primary/5">
      <div className="container max-w-2xl mx-auto px-4 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="space-y-8"
        >
          <div className="text-center space-y-2">
            <h1 className="font-display text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-600">
              Upload Your Book
            </h1>
            <p className="font-serif text-lg text-muted-foreground">
              Transform your existing story with AI-powered visualization
            </p>
          </div>

          <div className="bg-card rounded-lg shadow-lg p-8 space-y-6">
            <div
              className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
                file ? 'border-primary' : 'border-border'
              }`}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                const droppedFile = e.dataTransfer.files[0];
                if (droppedFile) setFile(droppedFile);
              }}
            >
              <input
                type="file"
                id="book-file"
                className="hidden"
                accept=".pdf,.epub,.txt,.html"
                onChange={handleFileSelect}
              />
              <label htmlFor="book-file">
                <div className="space-y-4">
                  <div className="mx-auto w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="w-8 h-8 text-primary"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="17 8 12 3 7 8" />
                      <line x1="12" y1="3" x2="12" y2="15" />
                    </svg>
                  </div>
                  <div>
                    <Button variant="outline" className="mb-2">
                      {file ? 'Change File' : 'Choose File'}
                    </Button>
                    <p className="text-sm text-muted-foreground">
                      or drag and drop your file here
                    </p>
                  </div>
                  {file && (
                    <p className="text-sm font-medium text-primary">{file.name}</p>
                  )}
                  <p className="text-sm text-muted-foreground">
                    Supported formats: PDF, EPUB, TXT, HTML
                  </p>
                </div>
              </label>
            </div>

            {error && (
              <Alert open={!!error} onOpenChange={() => setError(null)}>
                <AlertContent>
                  <AlertHeader>
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                  </AlertHeader>
                  <AlertFooter>
                    <AlertAction>OK</AlertAction>
                  </AlertFooter>
                </AlertContent>
              </Alert>
            )}

            {uploading && (
              <div className="space-y-2">
                <Progress value={progress} className="w-full" />
                <p className="text-sm text-center text-muted-foreground">
                  Processing your book...
                </p>
              </div>
            )}

            <Button
              className="w-full bg-gradient-to-r from-primary to-purple-600 hover:from-purple-600 hover:to-primary"
              onClick={handleUpload}
              disabled={!file || uploading}
            >
              {uploading ? 'Processing...' : 'Upload and Process'}
            </Button>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default BookUpload;
