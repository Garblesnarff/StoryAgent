import React from 'react';
import { createRoot } from 'react-dom/client';
import NodeEditor from './node-editor';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, errorMessage: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, errorMessage: error.message };
    }

    componentDidCatch(error, errorInfo) {
        console.error('[ErrorBoundary] Error caught:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="alert alert-danger">
                    <h4>Story Editor Error</h4>
                    <p>{this.state.errorMessage || 'Something went wrong. Please try refreshing the page.'}</p>
                    <button onClick={() => window.location.href = '/'}>
                        Return to Home
                    </button>
                </div>
            );
        }
        return this.props.children;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('[customize.js] Initializing Node Editor...');
    
    const container = document.getElementById('node-editor');
    if (!container) {
        console.error('[customize.js] Node editor container not found');
        return;
    }

    try {
        // Get and validate story data
        const storyAttr = container.getAttribute('data-story');
        console.log('[customize.js] Raw story data:', storyAttr);

        if (!storyAttr) {
            throw new Error('Story data is missing');
        }

        let storyData;
        try {
            storyData = JSON.parse(storyAttr);
            console.log('[customize.js] Parsed story data:', storyData);
        } catch (parseError) {
            console.error('[customize.js] Failed to parse story data:', parseError);
            throw new Error('Invalid story data format');
        }

        if (!storyData || !storyData.paragraphs || !Array.isArray(storyData.paragraphs)) {
            console.error('[customize.js] Invalid story structure:', storyData);
            throw new Error('Invalid story data structure');
        }

        // Create root and render with strict validation
        const root = createRoot(container);
        root.render(
            <React.StrictMode>
                <ErrorBoundary>
                    <NodeEditor 
                        key={`story-${Date.now()}`}
                        story={storyData} 
                        onStyleUpdate={(updatedParagraphs) => {
                            console.log('[customize.js] Style update:', updatedParagraphs);
                            fetch('/story/update_style', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({ 
                                    paragraphs: updatedParagraphs.map(p => ({
                                        index: p.index,
                                        image_style: p.image_style || 'realistic'
                                    }))
                                })
                            })
                            .then(response => {
                                if (!response.ok) {
                                    throw new Error(response.status === 403 
                                        ? 'Session expired. Please generate a new story.'
                                        : 'Failed to update style');
                                }
                                return response.json();
                            })
                            .then(data => {
                                if (!data.success) {
                                    throw new Error(data.error || 'Failed to update style');
                                }
                                console.log('[customize.js] Style update successful');
                            })
                            .catch(error => {
                                console.error('[customize.js] Error updating style:', error);
                                const isSessionExpired = error.message.includes('Session expired');
                                
                                container.innerHTML = `
                                    <div class="alert alert-${isSessionExpired ? 'warning' : 'danger'}">
                                        <h4>${isSessionExpired ? 'Session Expired' : 'Error'}</h4>
                                        <p>${error.message}</p>
                                        <button onclick="window.location.href='/'">Return to Home</button>
                                    </div>
                                `;
                            });
                        }}
                    />
                </ErrorBoundary>
            </React.StrictMode>
        );

        console.log('[customize.js] NodeEditor mounted successfully');

    } catch (error) {
        console.error('[customize.js] Story editor error:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <h4>Story Editor Error</h4>
                <p>${error.message}</p>
                <button onclick="window.location.href='/'">Return to Home</button>
            </div>
        `;
    }
});
