document.addEventListener('DOMContentLoaded', () => {
    const storyOutput = document.getElementById('story-output');
    let currentPage = 0;
    let totalPages = 0;
    let session = { 
        story_data: { 
            paragraphs: [],
            story_context: ''
        } 
    };
    
    function initTooltips(container = document) {
        const tooltipTriggerList = [].slice.call(container.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.forEach(tooltipTriggerEl => {
            new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    async function handleGeneration(type, button) {
        const spinner = button.querySelector('.spinner-border');
        const buttonText = button.querySelector('.button-text');
        const card = button.closest('.card');
        const index = parseInt(button.dataset.index);
        const text = card.querySelector('.card-text').textContent;
        
        try {
            button.disabled = true;
            spinner.classList.remove('d-none');
            button.classList.add('processing');
            
            // Custom messages for each type
            if (type === 'image') {
                buttonText.textContent = 'Creating Scene...';
                button.title = 'Creating visual scene from the text...';
            } else {
                buttonText.textContent = 'Creating Voice...';
                button.title = 'Generating audio narration...';
            }
            
            const response = await fetch(`/story/generate_${type}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    index: index,
                    style: session.story_data.paragraphs[index]?.image_style || 'realistic',
                    story_context: session.story_data.story_context || ''
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: `Failed to generate ${type}` }));
                throw new Error(errorData.error || `Server error while generating ${type}`);
            }
            
            const data = await response.json();
            if (data.success) {
                if (type === 'image') {
                    updateImage(card, data);
                } else if (type === 'audio') {
                    updateAudio(card, data);
                }
            } else {
                throw new Error(data.error || `Failed to generate ${type}`);
            }
            
        } catch (error) {
            console.error('Error generating card:', error);
            const errorMessage = error.response ? await error.response.json().then(data => data.error) : error.message;
            showError(card, `Failed to generate ${type}. ${errorMessage || 'An unexpected error occurred. Please try again.'}`);
        } finally {
            button.disabled = false;
            spinner.classList.add('d-none');
            button.classList.remove('processing');
            buttonText.textContent = type === 'image' ? 'Generate Visual Scene' : 'Generate Narration';
        }
    }

    function updateImage(card, data) {
        const imgElement = card.querySelector('.card-img-top');
        const imgContainer = card.querySelector('.card-image');
        
        if (data.image_url) {
            if (!imgElement) {
                const newImgContainer = document.createElement('div');
                newImgContainer.className = 'card-image position-relative';
                newImgContainer.innerHTML = `
                    <img src="${data.image_url}" 
                         class="card-img-top" 
                         data-bs-toggle="tooltip" 
                         data-bs-placement="top" 
                         title="${data.image_prompt || ''}" 
                         alt="Generated image">
                `;
                card.insertBefore(newImgContainer, card.querySelector('.card-body'));
                initTooltips(newImgContainer);
            } else {
                imgElement.src = data.image_url;
                imgElement.title = data.image_prompt || '';
                const tooltip = bootstrap.Tooltip.getInstance(imgElement);
                if (tooltip) {
                    tooltip.dispose();
                }
                new bootstrap.Tooltip(imgElement);
            }
        }
    }

    function updateAudio(card, data) {
        if (data.audio_url) {
            let audioPlayer = card.querySelector('.audio-player');
            if (!audioPlayer) {
                audioPlayer = document.createElement('div');
                audioPlayer.className = 'audio-player mt-3';
                audioPlayer.innerHTML = `
                    <audio controls class="w-100">
                        <source src="${data.audio_url}" type="audio/mpeg">
                        Your browser does not support the audio element.
                    </audio>
                `;
                card.querySelector('.card-body').appendChild(audioPlayer);
            } else {
                const audioElement = audioPlayer.querySelector('audio');
                audioElement.src = data.audio_url;
            }
        }
    }

    function showError(card, message) {
        let alertDiv = card.querySelector('.alert');
        if (!alertDiv) {
            alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-danger mt-2';
            alertDiv.role = 'alert';
            const cardBody = card.querySelector('.card-body');
            cardBody.appendChild(alertDiv);
        }
        alertDiv.textContent = message;
        alertDiv.classList.remove('d-none');
        
        // Add a close button
        const closeButton = document.createElement('button');
        closeButton.type = 'button';
        closeButton.className = 'btn-close';
        closeButton.setAttribute('aria-label', 'Close');
        closeButton.onclick = () => alertDiv.classList.add('d-none');
        alertDiv.appendChild(closeButton);
    }

    function updateNavigation() {
        const pages = document.querySelectorAll('.story-card');
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

    // Event Listeners for generation buttons
    document.querySelectorAll('.generate-image').forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            await handleGeneration('image', button);
        });
    });

    document.querySelectorAll('.generate-audio').forEach(button => {
        button.addEventListener('click', async (e) => {
            e.preventDefault();
            await handleGeneration('audio', button);
        });
    });

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

    // Initialize
    async function init() {
        try {
            const response = await fetch('/story/get_data');
            if (!response.ok) {
                throw new Error('Failed to get story data');
            }
            
            const data = await response.json();
            if (data && data.paragraphs) {
                session.story_data = data;
            }
            
            if (storyOutput) {
                storyOutput.style.display = 'block';
                storyOutput.classList.add('visible');
            }
            
            initTooltips();
            updateNavigation();
            
        } catch (error) {
            console.error('Error:', error);
            if (storyOutput) {
                const alertDiv = document.createElement('div');
                alertDiv.className = 'alert alert-danger mt-3';
                alertDiv.textContent = 'Failed to initialize story data. Please refresh the page.';
                storyOutput.prepend(alertDiv);
            }
        }
    }

    if (document.getElementById('paragraph-cards')) {
        init();
    }
});
