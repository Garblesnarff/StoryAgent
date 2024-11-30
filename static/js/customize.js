/**
 * Story Customization Module
 * 
 * Handles story customization interface initialization and error handling.
 * 
 * @module customize
 * @requires React
 * @requires ReactDOM
 * @requires NodeEditor
 * @requires ErrorBoundary
 */

import React from 'react';
import { createRoot } from 'react-dom/client';
import NodeEditor from '../../src/components/NodeEditor';

import { ErrorBoundary } from '../../src/components/ErrorBoundary';

/**
 * Initializes the story customization interface
 * 
 * Sets up the React application, parses story data, and handles
 * initialization errors with appropriate user feedback.
 */
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('node-editor');
    if (!container) {
        console.error('Node editor container not found');
        return;
    }

    /**
     * Parses story data from DOM attributes
     * @returns {Object} Parsed story data
     */
    const parseStoryData = () => {
        const storyAttr = container.getAttribute('data-story');
        if (!storyAttr) {
            throw new Error('Story data not found');
        }
        const data = JSON.parse(storyAttr);
        if (!data?.paragraphs?.length) {
            throw new Error('Invalid story format');
        }
        return data;
    };

    // Initialize story data
    let storyData;
    try {
        storyData = parseStoryData();
    } catch (error) {
        console.error('Failed to parse story data:', error);
        showError('Failed to load story data. Please generate a story first.');
        return;
    }

    /**
     * Displays error message and handles redirection
     * 
     * Renders a user-friendly error message and automatically redirects
     * to the home page after a specified delay. Uses Bootstrap alert
     * styling for consistent UI feedback.
     * 
     * @param {string} message - Error message to display to the user
     * @param {number} [delay=3000] - Delay in milliseconds before redirect
     * @param {string} [redirectUrl='/'] - URL to redirect to after delay
     * @throws {Error} If container element is not found in DOM
     */
    function showError(message, delay = 3000, redirectUrl = '/') {
        if (!container) {
            throw new Error('Error container element not found');
        }

        const alertHtml = `
            <div class="alert alert-warning text-center" role="alert">
                <h4 class="alert-heading">Oops!</h4>
                <p>${message}</p>
                <hr>
                <p class="mb-0">You will be redirected to the story generation page...</p>
            </div>
        `;
        
        container.innerHTML = alertHtml;
        setTimeout(() => {
            window.location.href = redirectUrl;
        }, delay);
    }

    /**
     * Updates paragraph styles on the server
     * 
     * @param {Array<Object>} updatedParagraphs - Paragraph style updates
     * @param {number} updatedParagraphs[].index - Paragraph index
     * @param {string} [updatedParagraphs[].image_style] - Style to apply
     * @returns {Promise<void>}
     */
    async function updateStoryStyles(updatedParagraphs) {
        if (!Array.isArray(updatedParagraphs)) {
            throw new TypeError('updatedParagraphs must be an array');
        }

        const requestBody = {
            paragraphs: updatedParagraphs.map((p, index) => ({
                index,
                image_style: p.image_style || 'realistic'
            }))
        };

        try {
            const response = await fetch('/story/update_style', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();

            if (!response.ok) {
                if (response.status === 403) {
                    const error = new Error('Session expired. Please generate a new story.');
                    error.code = 'SESSION_EXPIRED';
                    throw error;
                }
                throw new Error(data.error || `Server error: ${response.status}`);
            }

            if (!data.success) {
                throw new Error(data.error || 'Failed to update style');
            }
        } catch (error) {
            console.error('Error updating style:', error);
            
            if (error.code === 'SESSION_EXPIRED') {
                showError(error.message);
            } else {
                const errorMessage = error.message || 'Failed to update style';
                console.error(errorMessage);
                alert(errorMessage);
            }
            throw error;
        }
    }

    // Create root and render with ErrorBoundary
    const root = createRoot(container);
    root.render(
        <ErrorBoundary>
            <NodeEditor 
                story={storyData} 
                onStyleUpdate={updateStoryStyles}
            />
        </ErrorBoundary>
    );
});
