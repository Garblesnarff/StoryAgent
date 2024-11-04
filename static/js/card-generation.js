document.addEventListener('DOMContentLoaded', () => {
    const storyOutput = document.getElementById('story-output');
    let currentPage = 0;
    let totalPages = 0;
    let session = { story_data: { paragraphs: [] } };
    
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
                            <div class="d-flex align-items-center">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" class="me-2">
                                    <path d="M11.534 7h3.932a.25.25 0 0 1 .192.41l-1.966 2.36a.25.25 0 0 1-.384 0l-1.966-2.36a.25.25 0 0 1 .192-.41zm-11 2h3.932a.25.25 0 0 0 .192-.41L2.692 6.23a.25.25 0 0 0-.384 0L.342 8.59A.25.25 0 0 0 .534 9z"/>
                                </svg>
                                <span class="button-text">Regenerate Image</span>
                            </div>
                            <div class="spinner-border spinner-border-sm ms-2 d-none" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                        </button>
                        <button class="btn btn-secondary regenerate-audio">
                            <div class="d-flex align-items-center">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" class="me-2">
                                    <path d="M11.536 14.01A8.473 8.473 0 0 0 14.026 8a8.473 8.473 0 0 0-2.49-6.01l-.708.707A7.476 7.476 0 0 1 13.025 8c0 2.071-.84 3.946-2.197 5.303l.708.707z"/>
                                    <path d="M10.121 12.596A6.48 6.48 0 0 0 12.025 8a6.48 6.48 0 0 0-1.904-4.596l-.707.707A5.483 5.483 0 0 1 11.025 8a5.483 5.483 0 0 1-1.61 3.89l.706.706z"/>
                                    <path d="M8.707 11.182A4.486 4.486 0 0 0 10.025 8a4.486 4.486 0 0 0-1.318-3.182L8 5.525A3.489 3.489 0 0 1 9.025 8 3.49 3.49 0 0 1 8 10.475l.707.707zM6.717 3.55A.5.5 0 0 1 7 4v8a.5.5 0 0 1-.812.39L3.825 10.5H1.5A.5.5 0 0 1 1 10V6a.5.5 0 0 1 .5-.5h2.325l2.363-1.89a.5.5 0 0 1 .529-.06z"/>
                                </svg>
                                <span class="button-text">Regenerate Audio</span>
                            </div>
                            <div class="spinner-border spinner-border-sm ms-2 d-none" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                        </button>
                    </div>
                </div>
                ${paragraph.audio_url ? `
                <div class="card-footer">
                    <audio controls src="${paragraph.audio_url}"></audio>
                </div>` : ''}
            </div>
            <div class="alert alert-danger mt-2 d-none" role="alert"></div>
        `;
        
        const regenerateImageBtn = pageDiv.querySelector('.regenerate-image');
        const regenerateAudioBtn = pageDiv.querySelector('.regenerate-audio');
        
        regenerateImageBtn?.addEventListener('click', async () => {
            await handleRegeneration('image', regenerateImageBtn, pageDiv, paragraph, index);
        });
        
        regenerateAudioBtn?.addEventListener('click', async () => {
            await handleRegeneration('audio', regenerateAudioBtn, pageDiv, paragraph, index);
        });
        
        return pageDiv;
    }
    
    async function handleRegeneration(type, button, pageDiv, paragraph, index) {
        const spinner = button.querySelector('.spinner-border');
        const buttonText = button.querySelector('.button-text');
        const alert = pageDiv.querySelector('.alert');
        
        try {
            button.disabled = true;
            spinner.classList.remove('d-none');
            buttonText.textContent = `Regenerating ${type}...`;
            alert.classList.add('d-none');
            
            const response = await fetch(`/story/regenerate_${type}`, {
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
                const errorData = await response.json();
                throw new Error(errorData.error || `Failed to regenerate ${type}`);
            }
            
            const data = await response.json();
            if (data.success) {
                console.log(`${type} regenerated successfully!`);
                
                if (type === 'image') {
                    const imgElement = pageDiv.querySelector('.card-img-top');
                    if (imgElement && data.image_url) {
                        const newImage = new Image();
                        newImage.onload = () => {
                            imgElement.src = data.image_url;
                        };
                        newImage.src = data.image_url;
                    }
                } else {
                    const audioElement = pageDiv.querySelector('audio');
                    if (audioElement && data.audio_url) {
                        audioElement.src = data.audio_url;
                        audioElement.load();
                    }
                }
            } else {
                throw new Error(data.error || `Failed to regenerate ${type}`);
            }
            
        } catch (error) {
            console.error('Error:', error.message || `Failed to regenerate ${type}`);
            alert.textContent = error.message || `Failed to regenerate ${type}. Please try again.`;
            alert.classList.remove('d-none');
        } finally {
            button.disabled = false;
            spinner.classList.add('d-none');
            buttonText.textContent = `Regenerate ${type.charAt(0).toUpperCase() + type.slice(1)}`;
        }
    }
    
    function updateNavigation() {
        const pages = document.querySelectorAll('.book-page');
        totalPages = pages.length;
        const prevButton = document.querySelector('.book-nav.prev');
        const nextButton = document.querySelector('.book-nav.next');
        
        if (!prevButton || !nextButton) return;
        
        prevButton.style.display = currentPage > 0 ? 'flex' : 'none';
        nextButton.style.display = currentPage < totalPages - 1 ? 'flex' : 'none';
        
        pages.forEach((page, index) => {
            page.style.display = index === currentPage ? 'block' : 'none';
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
            if (storyOutput) {
                storyOutput.style.display = 'block';
                storyOutput.classList.add('visible');
            }

            const response = await fetch('/story/generate_cards', {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
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
                                console.log(data.message);
                                break;
                            case 'paragraph':
                                const paragraphCards = document.getElementById('paragraph-cards');
                                if (paragraphCards && data.data) {
                                    const index = data.data.index;
                                    let pageElement = document.querySelector(`.book-page[data-index="${index}"]`);
                                    
                                    if (!pageElement) {
                                        pageElement = createPageElement(data.data, index);
                                        if (pageElement) {
                                            paragraphCards.appendChild(pageElement);
                                            pageElement.offsetHeight; // Force reflow
                                            pageElement.classList.add('visible');
                                        }
                                    } else {
                                        const newPage = createPageElement(data.data, index);
                                        if (newPage) {
                                            pageElement.innerHTML = newPage.innerHTML;
                                            const regenerateImageBtn = pageElement.querySelector('.regenerate-image');
                                            const regenerateAudioBtn = pageElement.querySelector('.regenerate-audio');
                                            regenerateImageBtn?.addEventListener('click', () => handleRegeneration('image', regenerateImageBtn, pageElement, data.data, index));
                                            regenerateAudioBtn?.addEventListener('click', () => handleRegeneration('audio', regenerateAudioBtn, pageElement, data.data, index));
                                        }
                                    }
                                    
                                    updateNavigation();
                                }
                                break;
                            case 'error':
                                console.error('Error:', data.message || 'An unknown error occurred');
                                throw new Error(data.message || 'An unknown error occurred');
                                break;
                            case 'complete':
                                console.log(data.message);
                                break;
                        }
                    } catch (error) {
                        console.error('Error parsing or handling message:', error.message, line);
                    }
                }
                buffer = lines[lines.length - 1];
            }
        } catch (error) {
            console.error('Error generating cards:', error.message || 'An unknown error occurred');
            const paragraphCards = document.getElementById('paragraph-cards');
            if (paragraphCards) {
                const errorAlert = document.createElement('div');
                errorAlert.className = 'alert alert-danger';
                errorAlert.textContent = error.message || 'Failed to generate cards. Please try again.';
                paragraphCards.appendChild(errorAlert);
            }
        }
    }
    
    if (document.getElementById('paragraph-cards')) {
        generateCards();
    }
    
    const saveStoryBtn = document.getElementById('save-story');
    saveStoryBtn?.addEventListener('click', async () => {
        try {
            const response = await fetch('/save_story', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to save story');
            }
            
            const data = await response.json();
            if (data.success) {
                console.log('Story saved successfully!');
                alert('Story saved successfully!');
            } else {
                throw new Error(data.error || 'Failed to save story');
            }
        } catch (error) {
            console.error('Error saving story:', error.message);
            alert('Failed to save story: ' + error.message);
        }
    });
});
