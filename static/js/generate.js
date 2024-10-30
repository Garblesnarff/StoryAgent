document.addEventListener('DOMContentLoaded', async () => {
    const loadingOverlay = document.querySelector('.loading-overlay');
    if (loadingOverlay) {
        const progressBar = loadingOverlay.querySelector('.progress-bar');
        const currentProgress = loadingOverlay.querySelector('#current-progress');
        const totalParagraphs = loadingOverlay.querySelector('#total-paragraphs');
        
        try {
            console.log('Starting media generation...');
            const response = await fetch('/story/generate_media');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log('Media generation response:', data);
            
            if (data.success && data.story_media) {
                // Create story cards
                const paragraphCards = document.getElementById('paragraph-cards');
                data.story_media.forEach((card, index) => {
                    // Update progress
                    const progress = ((index + 1) / data.story_media.length) * 100;
                    progressBar.style.width = `${progress}%`;
                    currentProgress.textContent = index + 1;
                    
                    const pageDiv = document.createElement('div');
                    pageDiv.className = 'book-page';
                    pageDiv.dataset.index = index;
                    
                    pageDiv.innerHTML = `
                        <div class="card h-100">
                            <img src="${card.image_url}" class="card-img-top" alt="Generated image" 
                                 onerror="this.src='/static/img/placeholder.png'">
                            <div class="card-body">
                                <p class="card-text">${card.text}</p>
                            </div>
                            <div class="card-footer">
                                <audio controls src="${card.audio_url}" 
                                       onerror="this.closest('.card-footer').innerHTML = 'Audio failed to load'">
                                </audio>
                            </div>
                        </div>
                    `;
                    
                    paragraphCards.appendChild(pageDiv);
                });
                
                // Setup navigation
                const pages = document.querySelectorAll('.book-page');
                if (pages.length > 0) {
                    pages[0].classList.add('active');
                    if (pages.length > 1) {
                        document.querySelector('.book-nav.prev').style.display = 'flex';
                        document.querySelector('.book-nav.next').style.display = 'flex';
                    }
                }
                
                // Hide loading overlay
                loadingOverlay.style.display = 'none';
                
                // Show story output and save button
                document.getElementById('story-output').style.display = 'block';
                const saveBtn = document.getElementById('save-story');
                if (saveBtn) saveBtn.style.display = 'block';
                
            } else {
                throw new Error(data.error || 'Failed to generate media');
            }
        } catch (error) {
            console.error('Error generating media:', error);
            loadingOverlay.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle-fill"></i>
                    Error generating story cards: ${error.message}
                    <button class="btn btn-outline-danger mt-3" onclick="window.location.reload()">
                        Retry
                    </button>
                </div>
            `;
        }
    }
});
