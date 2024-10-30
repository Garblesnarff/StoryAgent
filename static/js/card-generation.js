document.addEventListener('DOMContentLoaded', () => {
    const storyOutput = document.getElementById('story-output');
    const paragraphCards = document.getElementById('paragraph-cards');
    const logContent = document.getElementById('log-content');
    let currentPage = 0;
    let totalPages = 0;
    
    function addLogMessage(message) {
        const logEntry = document.createElement('div');
        logEntry.textContent = message;
        logContent.appendChild(logEntry);
        logContent.scrollTop = logContent.scrollHeight;
    }
    
    function createPageElement(paragraph, index) {
        const pageDiv = document.createElement('div');
        pageDiv.className = 'book-page';
        pageDiv.dataset.index = index;
        
        pageDiv.innerHTML = `
            <div class="card h-100">
                <img src="${paragraph.image_url}" class="card-img-top" alt="Paragraph image">
                <div class="card-body">
                    <p class="card-text">${paragraph.text}</p>
                </div>
                <div class="card-footer">
                    <audio controls src="${paragraph.audio_url}"></audio>
                </div>
                <div class="progress-indicator"></div>
            </div>
        `;
        return pageDiv;
    }
    
    function updateProgress(currentIndex, totalParagraphs) {
        const cards = document.querySelectorAll('.book-page');
        cards.forEach((card, index) => {
            const indicator = card.querySelector('.progress-indicator');
            if (indicator && index === currentIndex) {
                const progress = ((index + 1) / totalParagraphs) * 100;
                indicator.style.background = `conic-gradient(var(--apple-accent) ${progress}%, transparent ${progress}%)`;
            }
        });
    }
    
    function updateNavigation() {
        const pages = document.querySelectorAll('.book-page');
        totalPages = pages.length;
        const prevButton = document.querySelector('.book-nav.prev');
        const nextButton = document.querySelector('.book-nav.next');
        
        if (!prevButton || !nextButton) return;
        
        prevButton.style.display = currentPage > 0 ? 'block' : 'none';
        nextButton.style.display = currentPage < totalPages - 1 ? 'block' : 'none';
        
        pages.forEach((page, index) => {
            page.classList.remove('active', 'next', 'prev', 'turning');
            
            if (index === currentPage) {
                page.classList.add('active');
                page.style.display = 'block';
            } else if (index === currentPage + 1) {
                page.classList.add('next');
                page.style.display = 'block';
            } else if (index === currentPage - 1) {
                page.classList.add('prev');
                page.style.display = 'block';
            } else {
                page.style.display = 'none';
            }
        });
    }
    
    // Navigation event handlers
    const nextButton = document.querySelector('.book-nav.next');
    const prevButton = document.querySelector('.book-nav.prev');
    
    if (nextButton) {
        nextButton.addEventListener('click', () => {
            if (currentPage < totalPages - 1) {
                currentPage++;
                updateNavigation();
            }
        });
    }
    
    if (prevButton) {
        prevButton.addEventListener('click', () => {
            if (currentPage > 0) {
                currentPage--;
                updateNavigation();
            }
        });
    }
    
    // Generate cards
    async function generateCards() {
        try {
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
                                const pageElement = createPageElement(data.data, data.data.index);
                                paragraphCards.appendChild(pageElement);
                                updateProgress(data.data.index, totalPages);
                                updateNavigation();
                                break;
                            case 'error':
                                addLogMessage('Error: ' + data.message);
                                break;
                            case 'complete':
                                addLogMessage(data.message);
                                storyOutput.style.display = 'block';
                                break;
                        }
                    } catch (parseError) {
                        console.error('Error parsing message:', line);
                    }
                }
                buffer = lines[lines.length - 1];
            }
        } catch (error) {
            console.error('Error:', error);
            addLogMessage('Error: ' + error.message);
        }
    }
    
    // Start card generation when page loads
    generateCards();
    
    // Save story functionality
    document.getElementById('save-story')?.addEventListener('click', async () => {
        try {
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
                alert('Story saved successfully!');
            } else {
                throw new Error('Failed to save story');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to save story. Please try again.');
        }
    });
});
