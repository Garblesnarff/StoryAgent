document.addEventListener('DOMContentLoaded', () => {
    const storyOutput = document.getElementById('story-output');
    let currentPage = 1;
    let totalPages = 1;
    let session = { story_data: { paragraphs: [] } };

    // Initialize tooltips for all elements
    function initTooltips(container = document) {
        const tooltipTriggerList = [].slice.call(container.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.forEach(tooltipTriggerEl => {
            new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    async function loadPage(pageNumber) {
        try {
            const response = await fetch(`/story/page/${pageNumber}`);
            if (!response.ok) {
                throw new Error('Failed to load page');
            }

            const data = await response.json();
            currentPage = data.current_page;
            totalPages = data.total_pages;

            const paragraphCards = document.getElementById('paragraph-cards');
            if (paragraphCards) {
                paragraphCards.innerHTML = '';
                data.chunks.forEach((chunk, index) => {
                    const pageElement = createPageElement(chunk, index);
                    if (pageElement) {
                        paragraphCards.appendChild(pageElement);
                        pageElement.offsetHeight;
                        pageElement.classList.add('visible');
                    }
                });
            }

            updateNavigation();

        } catch (error) {
            console.error('Error loading page:', error);
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
                    </div>
                </div>
            </div>
            <div class="alert alert-danger mt-2 d-none" role="alert"></div>
        `;

        // Initialize tooltips for the new page
        initTooltips(pageDiv);

        // Add event listeners for regeneration buttons
        const regenerateImageBtn = pageDiv.querySelector('.regenerate-image');
        regenerateImageBtn?.addEventListener('click', async () => {
            await handleRegeneration('image', regenerateImageBtn, pageDiv, paragraph, index);
        });

        return pageDiv;
    }

    function updateNavigation() {
        const prevButton = document.querySelector('.book-nav.prev');
        const nextButton = document.querySelector('.book-nav.next');

        if (!prevButton || !nextButton) return;

        prevButton.style.display = currentPage > 1 ? 'flex' : 'none';
        nextButton.style.display = currentPage < totalPages ? 'flex' : 'none';

        // Update page indicator if it exists
        const pageIndicator = document.querySelector('.page-indicator');
        if (pageIndicator) {
            pageIndicator.textContent = `Page ${currentPage} of ${totalPages}`;
        }
    }

    const nextButton = document.querySelector('.book-nav.next');
    const prevButton = document.querySelector('.book-nav.prev');

    nextButton?.addEventListener('click', () => {
        if (currentPage < totalPages) {
            loadPage(currentPage + 1);
        }
    });

    prevButton?.addEventListener('click', () => {
        if (currentPage > 1) {
            loadPage(currentPage - 1);
        }
    });

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
    

    // Initialize tooltips for initial content
    initTooltips();

    if (document.getElementById('paragraph-cards')) {
        loadPage(1);  // Load first page on initial load
    }
});