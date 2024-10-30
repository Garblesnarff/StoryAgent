document.addEventListener('DOMContentLoaded', () => {
    const logContent = document.getElementById('log-content');
    
    function addLogMessage(message) {
        const logEntry = document.createElement('div');
        logEntry.textContent = message;
        logContent.appendChild(logEntry);
        logContent.scrollTop = logContent.scrollHeight;
    }
    
    // Handle paragraph updates
    document.querySelectorAll('.paragraph-container').forEach(container => {
        const index = container.dataset.index;
        const textArea = container.querySelector('.paragraph-text');
        const saveBtn = container.querySelector('.save-paragraph');
        const regenerateImageBtn = container.querySelector('.regenerate-image');
        const regenerateAudioBtn = container.querySelector('.regenerate-audio');
        
        // Save paragraph changes
        saveBtn.addEventListener('click', async () => {
            try {
                addLogMessage('Updating paragraph...');
                const response = await fetch('/story/update_paragraph', {
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
                    throw new Error('Failed to update paragraph');
                }
                
                const data = await response.json();
                addLogMessage('Paragraph updated successfully!');
                
            } catch (error) {
                console.error('Error:', error);
                addLogMessage(`Error updating paragraph: ${error.message}`);
                alert('Failed to update paragraph. Please try again.');
            }
        });
        
        // Regenerate image
        regenerateImageBtn.addEventListener('click', async () => {
            try {
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
                addLogMessage('Image regenerated successfully!');
                
            } catch (error) {
                console.error('Error:', error);
                addLogMessage(`Error regenerating image: ${error.message}`);
                alert('Failed to regenerate image. Please try again.');
            }
        });
        
        // Regenerate audio
        regenerateAudioBtn.addEventListener('click', async () => {
            try {
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
                addLogMessage('Audio regenerated successfully!');
                
            } catch (error) {
                console.error('Error:', error);
                addLogMessage(`Error regenerating audio: ${error.message}`);
                alert('Failed to regenerate audio. Please try again.');
            }
        });
    });
});
