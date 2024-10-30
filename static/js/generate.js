document.addEventListener('DOMContentLoaded', async () => {
    const loadingOverlay = document.querySelector('.loading-overlay');
    if (loadingOverlay) {
        const progressBar = loadingOverlay.querySelector('.progress-bar');
        const currentProgress = loadingOverlay.querySelector('#current-progress');
        const totalParagraphs = loadingOverlay.querySelector('#total-paragraphs');
        
        try {
            const response = await fetch('/story/generate_media');
            const data = await response.json();
            
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
                            <img src="${card.image_url}" class="card-img-top" alt="Generated image">
                            <div class="card-body">
                                <p class="card-text">${card.text}</p>
                            </div>
                            <div class="card-footer">
                                <div class="audio-container">
                                    <button class="btn btn-sm btn-secondary play-audio-btn">
                                        <i class="bi bi-play-fill"></i> Play Audio
                                    </button>
                                    <audio src="${card.audio_url}" preload="none"></audio>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    paragraphCards.appendChild(pageDiv);
                });
                
                // Setup navigation and audio players
                setupNavigation();
                setupAudioPlayers();
                
                // Hide loading overlay
                loadingOverlay.style.display = 'none';
                
                // Show save button
                const saveBtn = document.getElementById('save-story');
                if (saveBtn) {
                    saveBtn.style.display = 'block';
                }
            } else {
                throw new Error(data.error || 'Failed to generate media');
            }
        } catch (error) {
            console.error('Error generating media:', error);
            loadingOverlay.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle-fill"></i>
                    Error generating story cards. Please try again.
                    <button class="btn btn-outline-danger mt-3" onclick="window.location.reload()">
                        Retry
                    </button>
                </div>
            `;
        }
    }
    
    function setupNavigation() {
        const pages = document.querySelectorAll('.book-page');
        if (pages.length > 0) {
            pages[0].classList.add('active');
            if (pages.length > 1) {
                document.querySelector('.book-nav.prev').style.display = 'flex';
                document.querySelector('.book-nav.next').style.display = 'flex';
            }
        }
    }
    
    function setupAudioPlayers() {
        document.querySelectorAll('.audio-container').forEach(container => {
            const playBtn = container.querySelector('.play-audio-btn');
            const audio = container.querySelector('audio');
            
            if (playBtn && audio) {
                playBtn.addEventListener('click', () => {
                    const allAudios = document.querySelectorAll('audio');
                    allAudios.forEach(a => {
                        if (a !== audio && !a.paused) {
                            a.pause();
                            a.currentTime = 0;
                            a.closest('.audio-container').querySelector('.play-audio-btn').innerHTML = 
                                '<i class="bi bi-play-fill"></i> Play Audio';
                        }
                    });
                    
                    if (audio.paused) {
                        audio.play().catch(() => {
                            console.log('Audio playback requires user interaction');
                        });
                        playBtn.innerHTML = '<i class="bi bi-pause-fill"></i> Pause';
                    } else {
                        audio.pause();
                        audio.currentTime = 0;
                        playBtn.innerHTML = '<i class="bi bi-play-fill"></i> Play Audio';
                    }
                });
                
                audio.addEventListener('ended', () => {
                    playBtn.innerHTML = '<i class="bi bi-play-fill"></i> Play Audio';
                });
            }
        });
    }
});
