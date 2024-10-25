document.addEventListener('DOMContentLoaded', () => {
    const storyForm = document.getElementById('story-form');
    const storyOutput = document.getElementById('story-output');
    const paragraphCards = document.getElementById('paragraph-cards');
    const logContent = document.getElementById('log-content');
    const editModal = new bootstrap.Modal(document.getElementById('editModal'));
    const socket = io();
    let currentEditingCard = null;
    let currentPage = 0;
    let totalPages = 0;

    // Hide save button by default
    document.getElementById('save-story').style.display = 'none';

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
                    <button class="btn btn-primary edit-paragraph" data-index="${index}">Edit</button>
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

    function addParagraphCard(paragraph, index) {
        const existingPage = paragraphCards.querySelector(`[data-index="${index}"]`);
        if (existingPage) {
            existingPage.remove();
        }

        const pageElement = createPageElement(paragraph, index);
        paragraphCards.appendChild(pageElement);
        
        updateNavigation();
        storyOutput.style.display = 'block';
        setupAudioHover();
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
            page.classList.remove('active', 'next', 'prev', 'turning', 'turning-forward', 'turning-backward');
            
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
                const pages = document.querySelectorAll('.book-page');
                const currentPageEl = pages[currentPage];
                const nextPageEl = pages[currentPage + 1];
                
                if (currentPageEl && nextPageEl) {
                    currentPageEl.classList.add('turning', 'turning-forward');
                    nextPageEl.classList.add('turning', 'turning-backward');
                    
                    setTimeout(() => {
                        currentPage++;
                        updateNavigation();
                    }, 800);
                }
            }
        });
    }

    if (prevButton) {
        prevButton.addEventListener('click', () => {
            if (currentPage > 0) {
                const pages = document.querySelectorAll('.book-page');
                const currentPageEl = pages[currentPage];
                const prevPageEl = pages[currentPage - 1];
                
                if (currentPageEl && prevPageEl) {
                    currentPageEl.classList.add('turning', 'turning-backward');
                    prevPageEl.classList.add('turning', 'turning-forward');
                    
                    setTimeout(() => {
                        currentPage--;
                        updateNavigation();
                    }, 800);
                }
            }
        });
    }

    function setupAudioHover() {
        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            const audio = card.querySelector('audio');
            if (audio) {
                card.addEventListener('mouseenter', () => {
                    try {
                        audio.play().catch(err => console.log('Audio autoplay prevented'));
                    } catch (err) {
                        console.log('Audio playback error:', err);
                    }
                });
                card.addEventListener('mouseleave', () => {
                    try {
                        audio.pause();
                        audio.currentTime = 0;
                    } catch (err) {
                        console.log('Audio pause error:', err);
                    }
                });
            }
        });
    }

    // Edit paragraph functionality
    paragraphCards.addEventListener('click', async (e) => {
        if (e.target.classList.contains('edit-paragraph')) {
            const index = e.target.dataset.index;
            const card = e.target.closest('.card');
            if (!card) return;
            
            currentEditingCard = card;
            const paragraphText = card.querySelector('.card-text')?.textContent || '';
            document.getElementById('editParagraphText').value = paragraphText;
            editModal.show();
        }
    });

    // Save edited paragraph
    document.getElementById('saveParagraphEdit')?.addEventListener('click', async () => {
        if (!currentEditingCard) return;

        const newText = document.getElementById('editParagraphText').value;
        const paragraphElement = currentEditingCard.querySelector('.card-text');
        if (!paragraphElement) return;
        
        try {
            addLogMessage('Updating paragraph...');
            const response = await fetch('/update_paragraph', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: newText
                })
            });

            if (!response.ok) {
                throw new Error('Failed to update paragraph');
            }

            const data = await response.json();
            paragraphElement.textContent = newText;

            if (data.image_url) {
                const imgElement = currentEditingCard.querySelector('.card-img-top');
                if (imgElement) imgElement.src = data.image_url;
            }
            if (data.audio_url) {
                const audioElement = currentEditingCard.querySelector('audio');
                if (audioElement) audioElement.src = data.audio_url;
            }

            editModal.hide();
            addLogMessage('Paragraph updated successfully!');
        } catch (error) {
            console.error('Error:', error);
            addLogMessage(`Error updating paragraph: ${error.message}`);
            alert('Failed to update paragraph. Please try again.');
        }
    });

    // Regenerate image
    document.getElementById('regenerateImage')?.addEventListener('click', async () => {
        if (!currentEditingCard) return;

        try {
            addLogMessage('Regenerating image...');
            const text = document.getElementById('editParagraphText').value;
            const response = await fetch('/regenerate_image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });

            if (!response.ok) {
                throw new Error('Failed to regenerate image');
            }

            const data = await response.json();
            const imgElement = currentEditingCard.querySelector('.card-img-top');
            if (imgElement && data.image_url) {
                imgElement.src = data.image_url;
                addLogMessage('Image regenerated successfully!');
            }
        } catch (error) {
            console.error('Error:', error);
            addLogMessage(`Error regenerating image: ${error.message}`);
            alert('Failed to regenerate image. Please try again.');
        }
    });

    // Regenerate audio
    document.getElementById('regenerateAudio')?.addEventListener('click', async () => {
        if (!currentEditingCard) return;

        try {
            addLogMessage('Regenerating audio...');
            const text = document.getElementById('editParagraphText').value;
            const response = await fetch('/regenerate_audio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ text })
            });

            if (!response.ok) {
                throw new Error('Failed to regenerate audio');
            }

            const data = await response.json();
            const audioElement = currentEditingCard.querySelector('audio');
            if (audioElement && data.audio_url) {
                audioElement.src = data.audio_url;
                addLogMessage('Audio regenerated successfully!');
            }
        } catch (error) {
            console.error('Error:', error);
            addLogMessage(`Error regenerating audio: ${error.message}`);
            alert('Failed to regenerate audio. Please try again.');
        }
    });

    // Story generation form submission
    storyForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        logContent.innerHTML = '';
        paragraphCards.innerHTML = '';
        currentPage = 0;
        storyOutput.style.display = 'none';
        document.getElementById('save-story').style.display = 'none';
        
        const formData = new FormData(storyForm);
        const data = {
            prompt: formData.get('prompt'),
            genre: formData.get('genre'),
            mood: formData.get('mood'),
            target_audience: formData.get('target_audience'),
            paragraphs: formData.get('paragraphs')
        };
        
        // Emit the event to generate story
        socket.emit('generate_story', data);
    });

    // Socket event listeners
    socket.on('log', (data) => {
        addLogMessage(data.message);
    });

    socket.on('paragraph', (data) => {
        addParagraphCard(data.data, data.data.index);
        updateProgress(data.data.index, parseInt(data.data.index) + 1);
    });

    socket.on('complete', (data) => {
        addLogMessage(data.message);
        storyOutput.style.display = 'block';
        document.getElementById('save-story').style.display = 'block';
    });

    socket.on('error', (data) => {
        console.error('Error:', data);
        addLogMessage('Error: ' + data.message);
    });

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
