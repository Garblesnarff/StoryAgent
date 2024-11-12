import React from 'react';
import ReactDOM from 'react-dom';
import { ReactFlowProvider } from 'reactflow';
import StoryFlow from './StoryFlow';

const initializeReactFlow = () => {
  const container = document.getElementById('node-editor');
  if (!container) return;

  try {
    const storyData = JSON.parse(container.dataset.story || '{}');
    const root = ReactDOM.createRoot(container);
    
    // Wrap with all required providers
    root.render(
      <React.StrictMode>
        <div style={{ width: '100%', height: '100vh' }}>
          <ReactFlowProvider>
            <StoryFlow storyData={storyData} />
          </ReactFlowProvider>
        </div>
      </React.StrictMode>
    );
  } catch (error) {
    console.error('Failed to initialize ReactFlow:', error);
    container.innerHTML = '<div class="alert alert-danger">Failed to load editor</div>';
  }
};

// Initialize after DOM load
document.addEventListener('DOMContentLoaded', initializeReactFlow);