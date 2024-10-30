document.addEventListener('DOMContentLoaded', () => {
    const logContent = document.getElementById('log-content');
    
    function addLogMessage(message) {
        const logEntry = document.createElement('div');
        logEntry.textContent = message;
        logContent.appendChild(logEntry);
        logContent.scrollTop = logContent.scrollHeight;
    }
    
    // Handle paragraph updates with debouncing
    let saveTimeouts = {};
    
    document.querySelectorAll('.paragraph-container').forEach(container => {
        const index = container.dataset.index;
        const textArea = container.querySelector('.paragraph-text');
        const saveBtn = container.querySelector('.save-paragraph');
        const regenerateImageBtn = container.querySelector('.regenerate-image');
        const regenerateAudioBtn = container.querySelector('.regenerate-audio');
        
        // Auto-save functionality with debouncing
        textArea.addEventListener('input', () => {
            if (saveTimeouts[index]) {
                clearTimeout(saveTimeouts[index]);
            }
            
            saveTimeouts[index] = setTimeout(() => {
                saveParagraph(index, textArea.value, false);
            }, 1000);
        });
        
        // Manual save with media regeneration
        saveBtn.addEventListener('click', () => {
            saveParagraph(index, textArea.value, true);
        });
        
        // Regenerate image
        regenerateImageBtn.addEventListener('click', async () => {
            try {
                regenerateImageBtn.disabled = true;
                addLogMessage('Regenerating image...');
                
                const response = await fetch('/story/regenerate_image', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        text: textArea.value,
                        index: parseInt(index)
                    })
                });
                
                if (!response.ok) {
                    throw new Error('Failed to regenerate image');
                }
                
                const data = await response.json();
                if (data.success) {
                    addLogMessage('Image regenerated successfully!');
                    // Update image in UI if needed
                } else {
                    throw new Error(data.error || 'Failed to regenerate image');
                }
                
            } catch (error) {
                console.error('Error:', error);
                addLogMessage(`Error regenerating image: ${error.message}`);
                alert('Failed to regenerate image. Please try again.');
            } finally {
                regenerateImageBtn.disabled = false;
            }
        });
        
        // Regenerate audio
        regenerateAudioBtn.addEventListener('click', async () => {
            try {
                regenerateAudioBtn.disabled = true;
                addLogMessage('Regenerating audio...');
                
                const response = await fetch('/story/regenerate_audio', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        text: textArea.value,
                        index: parseInt(index)
                    })
                });
                
                if (!response.ok) {
                    throw new Error('Failed to regenerate audio');
                }
                
                const data = await response.json();
                if (data.success) {
                    addLogMessage('Audio regenerated successfully!');
                    // Update audio in UI if needed
                } else {
                    throw new Error(data.error || 'Failed to regenerate audio');
                }
                
            } catch (error) {
                console.error('Error:', error);
                addLogMessage(`Error regenerating audio: ${error.message}`);
                alert('Failed to regenerate audio. Please try again.');
            } finally {
                regenerateAudioBtn.disabled = false;
            }
        });
    });
    
    async function saveParagraph(index, text, generateMedia = false) {
        try {
            const saveBtn = document.querySelector(`.paragraph-container[data-index="${index}"] .save-paragraph`);
            if (saveBtn) {
                saveBtn.disabled = true;
            }
            
            addLogMessage('Saving changes...');
            
            const response = await fetch('/story/update_paragraph', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    index: parseInt(index),
                    generate_media: generateMedia
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to save changes');
            }
            
            const data = await response.json();
            if (data.success) {
                addLogMessage('Changes saved successfully!');
                if (generateMedia) {
                    // Update UI with new media URLs if provided
                    if (data.image_url) {
                        // Update image in UI
                    }
                    if (data.audio_url) {
                        // Update audio in UI
                    }
                }
            } else {
                throw new Error(data.error || 'Failed to save changes');
            }
            
        } catch (error) {
            console.error('Error:', error);
            addLogMessage(`Error saving changes: ${error.message}`);
            alert('Failed to save changes. Please try again.');
        } finally {
            if (saveBtn) {
                saveBtn.disabled = false;
            }
        }
    }
});
