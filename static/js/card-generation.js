document.addEventListener('DOMContentLoaded', () => {
    const storyOutput = document.getElementById('story-output');
    let currentPage = 0;
    let totalPages = 0;
    
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
                        <button class="btn btn-secondary generate-image">
                            <div class="d-flex align-items-center">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" class="me-2">
                                    <path d="M4 0h8a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2zm0 1a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H4z"/>
                                    <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/>
                                </svg>
                                <span class="button-text">Generate Image</span>
                            </div>
                            <div class="spinner-border spinner-border-sm ms-2 d-none" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                        </button>
                        <button class="btn btn-secondary generate-audio">
                            <div class="d-flex align-items-center">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" class="me-2">
                                    <path d="M11.536 14.01A8.473 8.473 0 0 0 14.026 8a8.473 8.473 0 0 0-2.49-6.01l-.708.707A7.476 7.476 0 0 1 13.025 8c0 2.071-.84 3.946-2.197 5.303l.708.707z"/>
                                    <path d="M10.121 12.596A6.48 6.48 0 0 0 12.025 8a6.48 6.48 0 0 0-1.904-4.596l-.707.707A5.483 5.483 0 0 1 11.025 8a5.483 5.483 0 0 1-1.61 3.89l.706.706z"/>
                                    <path d="M8.707 11.182A4.486 4.486 0 0 0 10.025 8a4.486 4.486 0 0 0-1.318-3.182L8 5.525A3.489 3.489 0 0 1 9.025 8 3.49 3.49 0 0 1 8 10.475l.707.707zM6.717 3.55A.5.5 0 0 1 7 4v8a.5.5 0 0 1-.812.39L3.825 10.5H1.5A.5.5 0 0 1 1 10V6a.5.5 0 0 1 .5-.5h2.325l2.363-1.89a.5.5 0 0 1 .529-.06z"/>
                                </svg>
                                <span class="button-text">Generate Audio</span>
                            </div>
                            <div class="spinner-border spinner-border-sm ms-2 d-none" role="status">
                                <span class="visually-hidden">Loading...</span>
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
    
    // Initialize tooltips and bind event listeners for initial content
    initTooltips();
    
    // Add event listeners to all generate buttons
    document.querySelectorAll('.generate-image, .generate-audio').forEach(button => {
        button.addEventListener('click', async (e) => {
            const type = button.classList.contains('generate-image') ? 'image' : 'audio';
            const pageDiv = button.closest('.book-page');
            const index = parseInt(pageDiv.dataset.index);
            const paragraph = {
                text: pageDiv.querySelector('.card-text').textContent,
                image_style: 'realistic'
            };
            await handleRegeneration(type, button, pageDiv, paragraph, index, true);
        });
    });
    
    // Initialize navigation
    updateNavigation();
});