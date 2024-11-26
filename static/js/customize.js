import React from 'react';
import { createRoot } from 'react-dom/client';
import NodeEditor from './node-editor';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        console.error('Error caught by boundary:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="alert alert-danger">
                    Something went wrong. Please try refreshing the page.
                </div>
            );
        }
        return this.props.children;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('node-editor');
    if (!container) {
        console.error('Node editor container not found');
        return;
    }

    // Parse story data
    let storyData;
    try {
        console.log('Initializing node editor...');
        const storyAttr = container.getAttribute('data-story');
        console.log('Raw story attribute:', storyAttr);
        
        if (!storyAttr) {
            throw new Error('No story data attribute found');
        }

        // Check for HTML content in response
        if (storyAttr.includes('<!DOCTYPE html>') || storyAttr.includes('<html>')) {
            console.error('Received HTML content instead of JSON:', storyAttr.substring(0, 200));
            throw new Error('Invalid response format: Received HTML instead of JSON');
        }

        // Log raw data before parsing
        console.log('Attempting to parse raw data:', {
            length: storyAttr.length,
            preview: storyAttr.substring(0, 100),
            isValidJSON: (() => {
                try {
                    JSON.parse(storyAttr);
                    return true;
                } catch (e) {
                    return false;
                }
            })()
        });
        
        storyData = JSON.parse(storyAttr);
        console.log('Successfully parsed story data:', {
            type: typeof storyData,
            isParagraphsArray: Array.isArray(storyData?.paragraphs),
            paragraphCount: storyData?.paragraphs?.length,
            structure: storyData ? Object.keys(storyData) : 'Invalid data'
        });
        
        if (!storyData || typeof storyData !== 'object') {
            throw new Error('Invalid story data: Not a valid object');
        }

        if (!Array.isArray(storyData.paragraphs)) {
            throw new Error('Invalid story data: paragraphs is not an array');
        }

        if (storyData.paragraphs.length === 0) {
            throw new Error('Invalid story data: Empty paragraphs array');
        }
        
        // Validate paragraph structure
        const invalidParagraphs = storyData.paragraphs.filter((p, idx) => {
            const isValid = p && typeof p === 'object' && typeof p.text === 'string' && p.text.trim().length > 0;
            if (!isValid) {
                console.warn(`Invalid paragraph at index ${idx}:`, p);
            }
            return !isValid;
        });

        if (invalidParagraphs.length > 0) {
            console.error('Found invalid paragraphs:', invalidParagraphs);
            throw new Error(`${invalidParagraphs.length} paragraphs are missing required text property`);
        }
        
        console.log('Story data validation successful:', {
            totalParagraphs: storyData.paragraphs.length,
            firstParagraph: {
                text: storyData.paragraphs[0].text.substring(0, 50) + '...',
                hasImage: !!storyData.paragraphs[0].image_url,
                hasAudio: !!storyData.paragraphs[0].audio_url
            }
        });
    } catch (error) {
        console.error('Failed to parse story data:', error);
        console.error('Error details:', {
            name: error.name,
            message: error.message,
            stack: error.stack
        });
        showError('Failed to load story data. Please generate a story first.');
        return;
    }

    function showError(message) {
        container.innerHTML = `
            <div class="alert alert-warning text-center">
                <h4 class="alert-heading">Oops!</h4>
                <p>${message}</p>
                <hr>
                <p class="mb-0">You will be redirected to the story generation page...</p>
            </div>
        `;
        setTimeout(() => {
            window.location.href = '/';
        }, 3000);
    }

    // Check if we have valid story data
    if (!storyData || !storyData.paragraphs || !storyData.paragraphs.length) {
        showError('No story found. Please generate a story first.');
        return;
    }

    // Create root and render with ErrorBoundary
    const root = createRoot(container);
    root.render(
        <ErrorBoundary>
            <NodeEditor 
                story={storyData} 
                onStyleUpdate={(updatedParagraphs) => {
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
                    })
                    .catch(error => {
                        console.error('Error updating style:', error);
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
});
