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
        
        // Calculate progress (20% per paragraph, split between image and audio)
        const progress = ((currentParagraph - 1) * 20 + (step === 'audio' ? 15 : step === 'image' ? 5 : 0));
        const percentage = Math.min(100, Math.round(progress));
        
        // Update circle progress
        const circumference = 283;
        const offset = circumference - (progress / 100) * circumference;
        if (progressCircle) {
            progressCircle.style.strokeDashoffset = offset;
        }
        
        // Update text
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
        pageDiv.className = 'book-page visible';  // Add visible class immediately
        pageDiv.dataset.index = index;
        pageDiv.style.display = 'block';  // Show immediately
        
        pageDiv.innerHTML = `
            <div class="card h-100">
                ${paragraph.image_url ? `
                    <img src="${paragraph.image_url}" class="card-img-top" alt="Paragraph image">
                ` : ''}
                <div class="card-body">
                    <p class="card-text">${paragraph.text || ''}</p>
                </div>
                ${paragraph.audio_url ? `
                <div class="card-footer">
                    <audio controls src="${paragraph.audio_url}"></audio>
                </div>` : ''}
            </div>
        `;
        
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
                page.style.transform = 'rotateY(0deg)';
            } else {
                page.style.display = 'none';
            }
        });
    }
    
    // Navigation event handlers
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
    
    // Generate cards
    async function generateCards() {
        try {
            showLoading(true);
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
                                    // Show story output container if hidden
                                    if (storyOutput && storyOutput.style.display === 'none') {
                                        storyOutput.style.display = 'block';
                                        storyOutput.classList.add('visible');
                                    }
                                    
                                    const index = data.data.index;
                                    let pageElement = document.querySelector(`.book-page[data-index="${index}"]`);
                                    
                                    if (!pageElement) {
                                        pageElement = createPageElement(data.data, index);
                                        if (pageElement) {
                                            paragraphCards.appendChild(pageElement);
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
    
    // Start card generation if we're on the generate page
    if (document.getElementById('paragraph-cards')) {
        generateCards();
    }
    
    // Save story functionality
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
