document.addEventListener('DOMContentLoaded', () => {
    const storyOutput = document.getElementById('story-output');
    const logContent = document.getElementById('log-content');
    let currentPage = 0;
    let totalPages = 0;
    let session = { story_data: { paragraphs: [] } };
    
    function showLoading(show = true) {
        const loadingContainer = document.querySelector('.loading-container');
        if (loadingContainer) {
            loadingContainer.style.display = show ? 'flex' : 'none';
        }
    }
    
    function addLogMessage(message) {
        if (!logContent) return;
        const logEntry = document.createElement('div');
        logEntry.textContent = message;
        logContent.appendChild(logEntry);
        logContent.scrollTop = logContent.scrollHeight;
    }

    function updateProgress(currentParagraph, totalParagraphs, step) {
        const progressCircle = document.querySelector('.progress-circle');
        const percentageText = document.querySelector('.progress-percentage');
        const stepText = document.querySelector('.progress-step');
        
        const progress = ((currentParagraph - 1) * 20 + (step === 'audio' ? 15 : step === 'image' ? 5 : 0));
        const percentage = Math.min(100, Math.round(progress));
        
        const circumference = 283;
        const offset = circumference - (progress / 100) * circumference;
        if (progressCircle) {
            progressCircle.style.strokeDashoffset = offset;
        }
        
        if (percentageText) {
            percentageText.textContent = `${percentage}%`;
        }
        if (stepText) {
            const stepMessage = step === 'image' ? 'Generating Image' : 
                              step === 'audio' ? 'Generating Audio' :
                              step === 'complete' ? 'Complete' : 'Processing';
            stepText.textContent = `${stepMessage} - Paragraph ${currentParagraph}/${totalParagraphs}`;
        }
    }
    
    function createPageElement(paragraph, index) {
        if (!paragraph) return null;
        const pageDiv = document.createElement('div');
        pageDiv.className = 'book-page';
        pageDiv.dataset.index = index;
        pageDiv.style.opacity = '1';
        pageDiv.style.display = 'block';
        
        pageDiv.innerHTML = `
            <div class="card h-100">
                ${paragraph.image_url ? `<img src="${paragraph.image_url}" class="card-img-top" alt="Paragraph image">` : ''}
                <div class="card-body">
                    <p class="card-text">${paragraph.text || ''}</p>
                    <div class="d-flex gap-2 mt-3">
                        <button class="btn btn-secondary regenerate-image">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" class="me-2">
                                <path d="M11.534 7h3.932a.25.25 0 0 1 .192.41l-1.966 2.36a.25.25 0 0 1-.384 0l-1.966-2.36a.25.25 0 0 1 .192-.41zm-11 2h3.932a.25.25 0 0 0 .192-.41L2.692 6.23a.25.25 0 0 0-.384 0L.342 8.59A.25.25 0 0 0 .534 9z"/>
                            </svg>
                            Regenerate Image
                        </button>
                        <button class="btn btn-secondary regenerate-audio">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" class="me-2">
                                <path d="M11.536 14.01A8.473 8.473 0 0 0 14.026 8a8.473 8.473 0 0 0-2.49-6.01l-.708.707A7.476 7.476 0 0 1 13.025 8c0 2.071-.84 3.946-2.197 5.303l.708.707z"/>
                                <path d="M10.121 12.596A6.48 6.48 0 0 0 12.025 8a6.48 6.48 0 0 0-1.904-4.596l-.707.707A5.483 5.483 0 0 1 11.025 8a5.483 5.483 0 0 1-1.61 3.89l.706.706z"/>
                                <path d="M8.707 11.182A4.486 4.486 0 0 0 10.025 8a4.486 4.486 0 0 0-1.318-3.182L8 5.525A3.489 3.489 0 0 1 9.025 8 3.49 3.49 0 0 1 8 10.475l.707.707zM6.717 3.55A.5.5 0 0 1 7 4v8a.5.5 0 0 1-.812.39L3.825 10.5H1.5A.5.5 0 0 1 1 10V6a.5.5 0 0 1 .5-.5h2.325l2.363-1.89a.5.5 0 0 1 .529-.06z"/>
                            </svg>
                            Regenerate Audio
                        </button>
                    </div>
                </div>
                ${paragraph.audio_url ? `
                <div class="card-footer">
                    <audio controls src="${paragraph.audio_url}"></audio>
                </div>` : ''}
            </div>
        `;
        
        // Add event listeners for regeneration buttons
        const regenerateImageBtn = pageDiv.querySelector('.regenerate-image');
        const regenerateAudioBtn = pageDiv.querySelector('.regenerate-audio');
        
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
                        text: paragraph.text,
                        index: parseInt(index)
                    })
                });
                
                if (!response.ok) {
                    throw new Error('Failed to regenerate image');
                }
                
                const data = await response.json();
                if (data.success) {
                    addLogMessage('Image regenerated successfully!');
                    const imgElement = pageDiv.querySelector('.card-img-top');
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
                        text: paragraph.text,
                        index: parseInt(index)
                    })
                });
                
                if (!response.ok) {
                    throw new Error('Failed to regenerate audio');
                }
                
                const data = await response.json();
                if (data.success) {
                    addLogMessage('Audio regenerated successfully!');
                    const audioElement = pageDiv.querySelector('audio');
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
        
        return pageDiv;
    }
    
    function updateNavigation() {
        const pages = document.querySelectorAll('.book-page');
        totalPages = pages.length;
        const prevButton = document.querySelector('.book-nav.prev');
        const nextButton = document.querySelector('.book-nav.next');
        
        if (!prevButton || !nextButton) return;
        
        if (totalPages > 1) {
            prevButton.style.display = currentPage > 0 ? 'flex' : 'none';
            nextButton.style.display = currentPage < totalPages - 1 ? 'flex' : 'none';
        } else {
            prevButton.style.display = 'none';
            nextButton.style.display = 'none';
        }
        
        pages.forEach((page, index) => {
            if (index === currentPage) {
                page.style.display = 'block';
            } else {
                page.style.display = 'none';
            }
        });
    }
    
    const nextButton = document.querySelector('.book-nav.next');
    const prevButton = document.querySelector('.book-nav.prev');
    
    nextButton?.addEventListener('click', () => {
        if (currentPage < totalPages - 1) {
            currentPage++;
            updateNavigation();
        }
    });
    
    prevButton?.addEventListener('click', () => {
        if (currentPage > 0) {
            currentPage--;
            updateNavigation();
        }
    });
    
    async function generateCards() {
        try {
            showLoading(true);
            // Show story output container at start
            if (storyOutput) {
                storyOutput.style.display = 'block';
                storyOutput.classList.add('visible');
            }

            const response = await fetch('/story/generate_cards', {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error('Failed to generate cards');
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const {done, value} = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, {stream: true});
                const lines = buffer.split('\n');
                
                for (let i = 0; i < lines.length - 1; i++) {
                    const line = lines[i].trim();
                    if (!line) continue;
                    
                    try {
                        const data = JSON.parse(line);
                        switch (data.type) {
                            case 'log':
                                addLogMessage(data.message);
                                break;
                            case 'paragraph':
                                const paragraphCards = document.getElementById('paragraph-cards');
                                if (paragraphCards && data.data) {
                                    // Show story output container immediately
                                    if (storyOutput) {
                                        storyOutput.style.display = 'block';
                                        storyOutput.classList.add('visible');
                                    }
                                    
                                    const index = data.data.index;
                                    let pageElement = document.querySelector(`.book-page[data-index="${index}"]`);
                                    
                                    if (!pageElement) {
                                        pageElement = createPageElement(data.data, index);
                                        if (pageElement) {
                                            paragraphCards.appendChild(pageElement);
                                            // Force reflow to trigger animation
                                            pageElement.offsetHeight;
                                            pageElement.classList.add('visible');
                                        }
                                    } else {
                                        // Update existing page
                                        pageElement.innerHTML = createPageElement(data.data, index).innerHTML;
                                    }
                                    
                                    updateProgress(
                                        index + 1,
                                        session.story_data.paragraphs.length,
                                        data.step || 'complete'
                                    );
                                    
                                    updateNavigation();
                                }
                                break;
                            case 'error':
                                addLogMessage('Error: ' + data.message);
                                showLoading(false);
                                break;
                            case 'complete':
                                addLogMessage(data.message);
                                showLoading(false);
                                break;
                        }
                    } catch (error) {
                        console.error('Error parsing message:', line, error);
                    }
                }
                buffer = lines[lines.length - 1];
            }
        } catch (error) {
            showLoading(false);
            addLogMessage('Error: ' + (error.message || 'An unknown error occurred'));
        }
    }
    
    if (document.getElementById('paragraph-cards')) {
        generateCards();
    }
    
    const saveStoryBtn = document.getElementById('save-story');
    saveStoryBtn?.addEventListener('click', async () => {
        try {
            addLogMessage('Saving story...');
            const response = await fetch('/save_story', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to save story');
            }
            
            const data = await response.json();
            if (data.success) {
                addLogMessage('Story saved successfully!');
            } else {
                throw new Error(data.error || 'Failed to save story');
            }
        } catch (error) {
            console.error('Error:', error);
            addLogMessage('Error: ' + (error.message || 'Failed to save story'));
            alert('Failed to save story. Please try again.');
        }
    });
});
