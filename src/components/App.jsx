import React from 'react';
import { createRoot } from 'react-dom/client';
import { ReactFlowProvider } from 'reactflow';
import StoryFlow from './StoryFlow';
import '../styles/customize.css';

// Separate StoryFlow into its own component file
const App = ({ storyData }) => {
  return (
    <ReactFlowProvider>
      <StoryFlow storyData={storyData} />
    </ReactFlowProvider>
  );
};

// Initialize app with proper error handling
const initializeApp = () => {
  const container = document.getElementById('node-editor');
  if (!container) {
    console.error('Container not found');
    return;
  }

  try {
    const storyData = JSON.parse(container.dataset.story || '{}');
    const root = createRoot(container);
    
    root.render(
      <React.StrictMode>
        <App storyData={storyData} />
      </React.StrictMode>
    );
  } catch (error) {
    console.error('Failed to initialize app:', error);
    container.innerHTML = '<div class="alert alert-danger">Failed to initialize editor</div>';
  }
};

// Call initialization when DOM is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}
