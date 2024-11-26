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
        console.error('Error caught by boundary:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="alert alert-danger">
                    <h4 className="alert-heading">Error Loading Story Editor</h4>
                    <p>{this.state.errorMessage || 'Something went wrong. Please try refreshing the page.'}</p>
                    <hr />
                    <button 
                        className="btn btn-outline-danger"
                        onClick={() => window.location.reload()}
                    >
                        Refresh Page
                    </button>
                </div>
            );
        }
        return this.props.children;
    }
}

// Validate story data structure
function validateStoryData(data) {
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

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    console.log('[customize.js] Initializing story editor');
    
    const container = document.getElementById('node-editor');
    if (!container) {
        console.error('Node editor container not found');
        return;
    }

    // Parse and validate story data
    let storyData;
    try {
        const storyAttr = container.getAttribute('data-story');
        if (!storyAttr) {
            throw new Error('No story data attribute found');
        }
        
        storyData = JSON.parse(storyAttr);
        console.log('[customize.js] Parsed story data:', storyData);
        
        // Validate story data structure
        validateStoryData(storyData);
    } catch (error) {
        console.error('[customize.js] Failed to parse or validate story data:', error);
        showError(error.message);
        return;
    }

    function showError(message) {
        container.innerHTML = `
            <div class="alert alert-warning text-center">
                <h4 class="alert-heading">Story Editor Error</h4>
                <p>${message}</p>
                <hr>
                <p class="mb-0">Redirecting to story generation page...</p>
            </div>
        `;
        setTimeout(() => {
            window.location.href = '/';
        }, 3000);
    }

    // Create root and render with ErrorBoundary
    try {
        console.log('[customize.js] Creating React root and rendering NodeEditor');
        const root = createRoot(container);
        root.render(
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
                                paragraphs: updatedParagraphs.map((p, index) => ({
                                    index,
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
                                showError(error.message);
                            } else {
                                alert(error.message || 'Failed to update style');
                            }
                        });
                    }}
                />
            </ErrorBoundary>
        );
    } catch (error) {
        console.error('[customize.js] Error rendering NodeEditor:', error);
        showError('Failed to initialize story editor');
    }
});
