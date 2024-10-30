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
        
        // Show autosave status
        const statusDiv = document.createElement('div');
        statusDiv.className = 'save-status text-muted small mt-2';
        container.querySelector('.card-body').appendChild(statusDiv);
        
        // Auto-save functionality with debouncing
        textArea?.addEventListener('input', () => {
            statusDiv.textContent = 'Saving...';
            if (saveTimeouts[index]) {
                clearTimeout(saveTimeouts[index]);
            }
            
            saveTimeouts[index] = setTimeout(() => {
                saveParagraph(index, textArea.value, false, statusDiv);
            }, 1000);
        });
        
        // Manual save with media regeneration
        saveBtn?.addEventListener('click', () => {
            saveParagraph(index, textArea.value, true, statusDiv);
        });
        
        // Regenerate image
        regenerateImageBtn?.addEventListener('click', async () => {
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
                    const imgElement = container.querySelector('.card-img-top');
                    if (imgElement && data.image_url) {
                        imgElement.src = data.image_url;
                    }
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
        regenerateAudioBtn?.addEventListener('click', async () => {
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
                    const audioElement = container.querySelector('audio');
                    if (audioElement && data.audio_url) {
                        audioElement.src = data.audio_url;
                    }
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
    
    async function saveParagraph(index, text, generateMedia = false, statusDiv = null) {
        try {
            const saveBtn = document.querySelector(`.paragraph-container[data-index="${index}"] .save-paragraph`);
            if (saveBtn) {
                saveBtn.disabled = true;
            }
            
            if (!generateMedia) {
                addLogMessage('Saving changes...');
            }
            
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
                if (statusDiv) {
                    statusDiv.textContent = 'Changes saved';
                    setTimeout(() => {
                        statusDiv.textContent = '';
                    }, 2000);
                }
                if (generateMedia) {
                    addLogMessage('Changes saved successfully!');
                    const container = document.querySelector(`.paragraph-container[data-index="${index}"]`);
                    // Update UI with new media URLs if provided
                    if (data.image_url && container) {
                        const imgElement = container.querySelector('.card-img-top');
                        if (imgElement) {
                            imgElement.src = data.image_url;
                        }
                    }
                    if (data.audio_url && container) {
                        const audioElement = container.querySelector('audio');
                        if (audioElement) {
                            audioElement.src = data.audio_url;
                        }
                    }
                }
            } else {
                throw new Error(data.error || 'Failed to save changes');
            }
            
        } catch (error) {
            console.error('Error:', error);
            if (statusDiv) {
                statusDiv.textContent = 'Error saving changes';
                statusDiv.style.color = 'var(--bs-danger)';
            }
            addLogMessage(`Error saving changes: ${error.message}`);
            alert('Failed to save changes. Please try again.');
        } finally {
            if (saveBtn) {
                saveBtn.disabled = false;
            }
        }
    }
});
