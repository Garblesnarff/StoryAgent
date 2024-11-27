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
    const container = document.getElementById('node-editor');
    if (!container) {
        console.error('[customize.js] Node editor container not found');
        return;
    }

    try {
        // Add debug logging
        console.log('[customize.js] Container found:', container);
        console.log('[customize.js] Data story attribute:', container.getAttribute('data-story'));
        
        const storyAttr = container.getAttribute('data-story');
        if (!storyAttr) {
            throw new Error('No story data attribute found');
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

        // Add key with timestamp to force remount
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
                                    if (response.status === 403) {
                                        throw new Error('Session expired. Please generate a new story.');
                                    }
                                    return response.json().then(data => {
                                        throw new Error(data.error || 'Failed to update style');
                                    });
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
                                if (error.message.includes('Session expired')) {
                                    container.innerHTML = `
                                        <div class="alert alert-warning">
                                            <h4>Session Expired</h4>
                                            <p>${error.message}</p>
                                            <button onclick="window.location.href='/'">Return to Home</button>
                                        </div>
                                    `;
                                } else {
                                    alert(error.message || 'Failed to update style');
                                }
                            });
                        }}
                    />
                </ErrorBoundary>
            </React.StrictMode>
        );
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
