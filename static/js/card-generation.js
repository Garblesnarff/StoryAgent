document.addEventListener('DOMContentLoaded', () => {
    const storyOutput = document.getElementById('story-output');
    const loadingCircle = document.querySelector('.loading-circle');
    const logContent = document.getElementById('log-content');
    let currentPage = 0;
    let totalPages = 0;
    
    function showLoading(show = true) {
        if (loadingCircle) {
            loadingCircle.style.display = show ? 'block' : 'none';
        }
    }
    
    function addLogMessage(message) {
        if (!logContent) return;
        const logEntry = document.createElement('div');
        logEntry.textContent = message;
        logContent.appendChild(logEntry);
        logContent.scrollTop = logContent.scrollHeight;
    }
    
    function createPageElement(paragraph, index) {
        if (!paragraph) return null;
        const pageDiv = document.createElement('div');
        pageDiv.className = 'book-page';
        pageDiv.dataset.index = index;
        
        pageDiv.innerHTML = `
            <div class="card h-100">
                ${paragraph.image_url ? `<img src="${paragraph.image_url}" class="card-img-top" alt="Paragraph image">` : ''}
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
                page.style.opacity = '1';
                page.style.transform = 'rotateY(0deg)';
            } else {
                page.style.display = 'none';
                page.style.opacity = '0';
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
    
    // Show loading at start
    if (storyOutput) {
        showLoading(true);
        storyOutput.style.display = 'none';
    }
    
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
                                    const pageElement = createPageElement(data.data, data.data.index);
                                    if (pageElement) {
                                        paragraphCards.appendChild(pageElement);
                                        updateNavigation();
                                    }
                                }
                                break;
                            case 'error':
                                addLogMessage('Error: ' + data.message);
                                showLoading(false);
                                break;
                            case 'complete':
                                addLogMessage(data.message);
                                showLoading(false);
                                if (storyOutput) {
                                    storyOutput.style.display = 'block';
                                }
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
