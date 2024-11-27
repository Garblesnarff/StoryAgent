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

function validateStoryData(data) {
    console.log('[customize.js] Validating story data:', data);
    
    if (!data) {
        throw new Error('No story data provided');
    }
    
    if (!Array.isArray(data.paragraphs)) {
        throw new Error('Invalid story format: paragraphs must be an array');
    }
    
    if (data.paragraphs.length === 0) {
        throw new Error('Story has no paragraphs');
    }
    
    data.paragraphs.forEach((para, index) => {
        if (!para.text) {
            throw new Error(`Paragraph ${index + 1} is missing text content`);
        }
    });
    
    return true;
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('[customize.js] DOM Content Loaded');
    
    const container = document.getElementById('node-editor');
    if (!container) {
        console.error('[customize.js] Node editor container not found');
        return;
    }

    let storyData;
    try {
        const storyAttr = container.getAttribute('data-story');
        console.log('[customize.js] Raw story data attribute:', storyAttr);
        
        if (!storyAttr) {
            throw new Error('No story data attribute found');
        }
        
        storyData = JSON.parse(storyAttr);
        console.log('[customize.js] Parsed story data:', storyData);
        
        if (!storyData || !storyData.paragraphs) {
            throw new Error('Invalid story data structure');
        }

        validateStoryData(storyData);
    } catch (error) {
        console.error('[customize.js] Story data error:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <h4>Story Editor Error</h4>
                <p>${error.message}</p>
                <button onclick="window.location.href='/'">Return to Home</button>
            </div>
        `;
        return;
    }

    // Only proceed with React rendering if we have valid data
    try {
        console.log('[customize.js] Creating React root and rendering NodeEditor');
        const root = createRoot(container);
        root.render(
            <React.StrictMode>
                <ErrorBoundary>
                    <NodeEditor 
                        story={storyData} 
                        onStyleUpdate={(updatedParagraphs) => {
                            console.log('[customize.js] Updating paragraph styles:', updatedParagraphs);
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
        console.error('[customize.js] Error rendering NodeEditor:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <h4>Story Editor Error</h4>
                <p>Failed to initialize story editor</p>
                <button onclick="window.location.href='/'">Return to Home</button>
            </div>
        `;
    }
});
