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

let currentPage = 1;
let totalPages = 1;

const updatePageControls = () => {
    const prevBtn = document.getElementById('prevPage');
    const nextBtn = document.getElementById('nextPage');
    const indicator = document.getElementById('pageIndicator');
    
    if (prevBtn && nextBtn && indicator) {
        prevBtn.disabled = currentPage <= 1;
        nextBtn.disabled = currentPage >= totalPages;
        indicator.textContent = `Page ${currentPage} of ${totalPages}`;
    }
};

const loadPage = async (pageNum) => {
    try {
        const response = await fetch(`/story/get_chunks/${pageNum}`);
        if (!response.ok) throw new Error('Failed to load page');
        
        const data = await response.json();
        currentPage = data.current_page;
        totalPages = data.total_pages;
        
        // Update node editor
        window.nodeEditor?.loadPage(pageNum);
        updatePageControls();
    } catch (error) {
        console.error('Error loading page:', error);
    }
};

document.addEventListener('DOMContentLoaded', () => {
    // Initialize page controls
    updatePageControls();
    const container = document.getElementById('node-editor');
    if (!container) {
        console.error('Node editor container not found');
        return;
    }

    // Parse story data
    let storyData;
    try {
        const storyAttr = container.getAttribute('data-story');
        if (!storyAttr) {
            throw new Error('No story data attribute found');
        }
        storyData = JSON.parse(storyAttr);
    } catch (error) {
        console.error('Failed to parse story data:', error);
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