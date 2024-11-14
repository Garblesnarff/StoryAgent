import React from 'react';
import { createRoot } from 'react-dom/client';
import NodeEditor from './node-editor';

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('node-editor');
    if (!container) return;

    // Parse story data
    let storyData;
    try {
        storyData = JSON.parse(container.dataset.story || '{}');
    } catch (error) {
        console.error('Failed to parse story data:', error);
        showError('Failed to load story data. Please try again.');
        return;
    }

    // Check if we have valid story data
    if (!storyData.paragraphs || !storyData.paragraphs.length) {
        showError('No story found. Please generate a story first.');
        setTimeout(() => {
            window.location.href = '/';
        }, 3000);
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
    }

    // Create root and render
    const root = createRoot(container);
    root.render(
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
                            image_style: p.image_style || 'realistic',
                            voice_style: p.voice_style || 'neutral'
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
                        setTimeout(() => {
                            window.location.href = '/';
                        }, 3000);
                    } else {
                        alert(error.message || 'Failed to update style');
                    }
                });
            }}
        />
    );
});
