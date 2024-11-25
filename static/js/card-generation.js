document.addEventListener('DOMContentLoaded', () => {
    const storyOutput = document.getElementById('story-output');
    let currentPage = 0;
    let totalPages = 0;
    let session = { story_data: { paragraphs: [] } };
    
    // Initialize tooltips for all elements
    function initTooltips(container = document) {
        const tooltipTriggerList = [].slice.call(container.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.forEach(tooltipTriggerEl => {
            new bootstrap.Tooltip(tooltipTriggerEl);
        });
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
                ${paragraph.image_url ? `
                <div class="card-image position-relative">
                    <img src="${paragraph.image_url}" 
                         class="card-img-top" 
                         data-bs-toggle="tooltip" 
                         data-bs-placement="top" 
                         title="${paragraph.image_prompt || 'Generated image'}" 
                         alt="Paragraph image">
                </div>` : ''}
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
                        <button class="btn btn-outline-secondary copy-prompt" data-bs-toggle="tooltip" data-bs-placement="top" title="Copy image prompt">
                            <div class="d-flex align-items-center">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" class="me-2">
                                    <path d="M4 1.5H3a2 2 0 0 0-2 2V14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V3.5a2 2 0 0 0-2-2h-1v1h1a1 1 0 0 1 1 1V14a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V3.5a1 1 0 0 1 1-1h1v-1z"/>
                                    <path d="M9.5 1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-3a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h3zm-3-1A1.5 1.5 0 0 0 5 1.5v1A1.5 1.5 0 0 0 6.5 4h3A1.5 1.5 0 0 0 11 2.5v-1A1.5 1.5 0 0 0 9.5 0h-3z"/>
                                </svg>
                                <span class="button-text">Copy Prompt</span>
                            </div>
                        </button>
                    </div>
                </div>
            </div>
            <div class="alert alert-danger mt-2 d-none" role="alert"></div>
        `;
        
        // Initialize tooltips for the new page
        initTooltips(pageDiv);
        
        // Add event listeners for regeneration buttons
        const generateImageBtn = pageDiv.querySelector('.generate-image');
        const generateAudioBtn = pageDiv.querySelector('.generate-audio');
        
        generateImageBtn?.addEventListener('click', async () => {
            await handleRegeneration('image', generateImageBtn, pageDiv, paragraph, index);
        });

        generateAudioBtn?.addEventListener('click', async () => {
            await handleRegeneration('audio', generateAudioBtn, pageDiv, paragraph, index);
        });

        const copyPromptBtn = pageDiv.querySelector('.copy-prompt');
        copyPromptBtn?.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(paragraph.image_prompt || '');
                const tooltip = bootstrap.Tooltip.getInstance(copyPromptBtn);
                const originalTitle = copyPromptBtn.getAttribute('data-bs-original-title');
                
                copyPromptBtn.setAttribute('data-bs-original-title', 'Copied!');
                tooltip?.show();
                
                setTimeout(() => {
                    copyPromptBtn.setAttribute('data-bs-original-title', originalTitle);
                    tooltip?.hide();
                }, 1500);
            } catch (err) {
                console.error('Failed to copy prompt:', err);
            }
        });
        
        return pageDiv;
    }
    
    async function handleRegeneration(type, button, pageDiv, paragraph, index, isInitialGeneration = false) {
        const spinner = button.querySelector('.spinner-border');
        const buttonText = button.querySelector('.button-text');
        const alert = pageDiv.querySelector('.alert');
        
        try {
            button.disabled = true;
            spinner.classList.remove('d-none');
            buttonText.textContent = isInitialGeneration ? `Generating ${type}...` : `Regenerating ${type}...`;
            alert.classList.add('d-none');
            
            const response = await fetch(`/story/regenerate_${type}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: paragraph.text,
                    index: parseInt(index),
                    style: paragraph.image_style || 'realistic'
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to regenerate ${type}`);
            }
            
            const data = await response.json();
            if (data.success) {
                if (type === 'image') {
                    const imgElement = pageDiv.querySelector('.card-img-top');
                    if (imgElement && data.image_url) {
                        const newImage = new Image();
                        newImage.onload = () => {
                            imgElement.src = data.image_url;
                            imgElement.title = data.image_prompt;
                            // Reinitialize tooltip with new content
                            const tooltip = bootstrap.Tooltip.getInstance(imgElement);
                            if (tooltip) {
                                tooltip.dispose();
                            }
                            new bootstrap.Tooltip(imgElement);
                        };
                        newImage.src = data.image_url;
                    }
                }
            } else {
                throw new Error(data.error || `Failed to regenerate ${type}`);
            }
            
        } catch (error) {
            console.error('Error:', error);
            alert.textContent = `Failed to regenerate ${type}. Please try again.`;
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
                                            pageElement.offsetHeight;
                                            pageElement.classList.add('visible');
                                        }
                                    } else {
                                        const newPage = createPageElement(data.data, index);
                                        if (newPage) {
                                            pageElement.innerHTML = newPage.innerHTML;
                                            // Initialize tooltips for updated content
                                            initTooltips(pageElement);
                                            
                                            // Reattach event listeners
                                            const regenerateImageBtn = pageElement.querySelector('.regenerate-image');
                                            regenerateImageBtn?.addEventListener('click', () => 
                                                handleRegeneration('image', regenerateImageBtn, pageElement, data.data, index));
                                            
                                            const copyPromptBtn = pageElement.querySelector('.copy-prompt');
                                            copyPromptBtn?.addEventListener('click', async () => {
                                                try {
                                                    await navigator.clipboard.writeText(data.data.image_prompt || '');
                                                    const tooltip = bootstrap.Tooltip.getInstance(copyPromptBtn);
                                                    const originalTitle = copyPromptBtn.getAttribute('data-bs-original-title');
                                                    
                                                    copyPromptBtn.setAttribute('data-bs-original-title', 'Copied!');
                                                    tooltip?.show();
                                                    
                                                    setTimeout(() => {
                                                        copyPromptBtn.setAttribute('data-bs-original-title', originalTitle);
                                                        tooltip?.hide();
                                                    }, 1500);
                                                } catch (err) {
                                                    console.error('Failed to copy prompt:', err);
                                                }
                                            });
                                        }
                                    }
                                    
                                    updateNavigation();
                                }
                                break;
                            case 'error':
                                console.error('Error:', data.message);
                                break;
                            case 'complete':
                                console.log(data.message);
                                break;
                        }
                    } catch (error) {
                        console.error('Error parsing message:', line, error);
                    }
                }
                buffer = lines[lines.length - 1];
            }
        } catch (error) {
            console.error('Error:', error.message || 'An unknown error occurred');
        }
    }
    
    // Initialize tooltips for initial content
    initTooltips();
    
    if (document.getElementById('paragraph-cards')) {
        generateCards();
    }
});