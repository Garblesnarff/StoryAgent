document.addEventListener('DOMContentLoaded', () => {
    // Initialize UI elements only if they exist
    const storyForm = document.getElementById('story-form');
    const storyOutput = document.getElementById('story-output');
    const paragraphCards = document.getElementById('paragraph-cards');
    const logContent = document.getElementById('log-content');
    const saveStoryBtn = document.getElementById('save-story');
    
    // Hide save button by default if it exists
    if (saveStoryBtn) {
        saveStoryBtn.style.display = 'none';
    }

    function addLogMessage(message) {
        if (logContent) {
            const logEntry = document.createElement('div');
            logEntry.textContent = message;
            logContent.appendChild(logEntry);
            logContent.scrollTop = logContent.scrollHeight;
        }
    }

    function setupAudioControls() {
        const audioElements = document.querySelectorAll('audio');
        audioElements.forEach(audio => {
            const container = audio.closest('.card');
            if (container) {
                // Replace autoplay with manual play button
                const playButton = document.createElement('button');
                playButton.className = 'btn btn-sm btn-secondary mt-2';
                playButton.innerHTML = '<i class="bi bi-play-fill"></i> Play Audio';
                
                playButton.addEventListener('click', () => {
                    if (audio.paused) {
                        // Stop all other audio first
                        audioElements.forEach(a => {
                            if (a !== audio && !a.paused) {
                                a.pause();
                                a.currentTime = 0;
                            }
                        });
                        audio.play().catch(() => {
                            console.log('Audio playback requires user interaction');
                        });
                        playButton.innerHTML = '<i class="bi bi-pause-fill"></i> Pause';
                    } else {
                        audio.pause();
                        audio.currentTime = 0;
                        playButton.innerHTML = '<i class="bi bi-play-fill"></i> Play Audio';
                    }
                });
                
                audio.parentNode.insertBefore(playButton, audio.nextSibling);
            }
        });
    }

    // Story editing functionality
    const paragraphsContainer = document.getElementById('paragraphs');
    if (paragraphsContainer) {
        paragraphsContainer.addEventListener('click', async (e) => {
            if (e.target.classList.contains('save-paragraph')) {
                const container = e.target.closest('.paragraph-container');
                const index = container.dataset.index;
                const text = container.querySelector('.paragraph-text').value;
                const mediaPreview = container.querySelector('.media-preview');
                const saveButton = e.target;
                const originalText = saveButton.innerHTML;
                
                try {
                    saveButton.disabled = true;
                    saveButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Saving...';
                    
                    const response = await fetch('/story/update_paragraph', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ text, index: parseInt(index) })
                    });

                    if (!response.ok) throw new Error('Failed to update paragraph');
                    
                    const data = await response.json();
                    
                    // Update preview
                    if (data.image_url) {
                        const img = mediaPreview.querySelector('img');
                        img.src = data.image_url;
                        img.style.display = 'block';
                    }
                    if (data.audio_url) {
                        const audio = mediaPreview.querySelector('audio');
                        audio.src = data.audio_url;
                        audio.style.display = 'block';
                        setupAudioControls();
                    }
                    mediaPreview.style.display = 'block';
                    
                    // Show success message
                    const alert = document.createElement('div');
                    alert.className = 'alert alert-success mt-2';
                    alert.textContent = 'Paragraph updated successfully!';
                    container.appendChild(alert);
                    setTimeout(() => alert.remove(), 3000);
                    
                } catch (error) {
                    console.error('Error:', error);
                    const alert = document.createElement('div');
                    alert.className = 'alert alert-danger mt-2';
                    alert.textContent = 'Failed to update paragraph. Please try again.';
                    container.appendChild(alert);
                    setTimeout(() => alert.remove(), 3000);
                } finally {
                    saveButton.disabled = false;
                    saveButton.innerHTML = originalText;
                }
            }
        });
    }
});
