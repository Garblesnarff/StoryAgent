document.addEventListener('DOMContentLoaded', () => {
    const storyForm = document.getElementById('story-form');
    const storyOutput = document.getElementById('story-output');
    const paragraphCards = document.getElementById('paragraph-cards');
    const saveStoryBtn = document.getElementById('save-story');
    const logContent = document.getElementById('log-content');
    const editModal = new bootstrap.Modal(document.getElementById('editModal'));
    let currentEditingCard = null;
    let currentPage = 0;
    let totalPages = 0;

    function addLogMessage(message) {
        const logEntry = document.createElement('div');
        logEntry.textContent = message;
        logContent.appendChild(logEntry);
        logContent.scrollTop = logContent.scrollHeight;
    }

    function createPageElement(paragraph, index, isCenter = false) {
        const pageDiv = document.createElement('div');
        pageDiv.className = `book-page ${isCenter ? 'center' : index % 2 === 0 ? 'left' : 'right'}`;
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
            </div>
        `;
        return pageDiv;
    }

    function addParagraphCard(paragraph, index) {
        // Remove existing page if it exists
        const existingPage = paragraphCards.querySelector(`[data-index="${index}"]`);
        if (existingPage) {
            existingPage.remove();
        }

        const isCenter = index === 0;
        const pageElement = createPageElement(paragraph, index, isCenter);
        paragraphCards.appendChild(pageElement);
        
        updateNavigation();
        storyOutput.style.display = 'block';
        setupAudioHover();
    }

    function updateNavigation() {
        const pages = document.querySelectorAll('.book-page');
        totalPages = Math.ceil((pages.length - 1) / 2); // Subtract 1 for center page
        const prevButton = document.querySelector('.book-nav.prev');
        const nextButton = document.querySelector('.book-nav.next');

        // Show/hide navigation buttons
        prevButton.style.display = currentPage > 0 ? 'block' : 'none';
        nextButton.style.display = currentPage < totalPages ? 'block' : 'none';

        // Update page visibility and positions
        pages.forEach((page, index) => {
            if (index === 0) {
                // Handle center page
                page.style.display = currentPage === 0 ? 'block' : 'none';
                if (currentPage > 0) {
                    page.classList.add('flipped');
                } else {
                    page.classList.remove('flipped');
                }
            } else {
                const pageNumber = Math.floor((index - 1) / 2);
                if (pageNumber === currentPage) {
                    page.style.display = 'block';
                    page.classList.remove('flipped');
                } else if (pageNumber < currentPage) {
                    page.style.display = 'block';
                    page.classList.add('flipped');
                } else {
                    page.style.display = 'none';
                    page.classList.remove('flipped');
                }
            }
        });
    }

    // Navigation event listeners
    document.querySelector('.book-nav.prev').addEventListener('click', () => {
        if (currentPage > 0) {
            currentPage--;
            updateNavigation();
        }
    });

    document.querySelector('.book-nav.next').addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            updateNavigation();
        }
    });

    function setupAudioHover() {
        const cards = document.querySelectorAll('.card');
        cards.forEach(card => {
            const audio = card.querySelector('audio');
            if (audio) {
                card.addEventListener('mouseenter', () => audio.play());
                card.addEventListener('mouseleave', () => {
                    audio.pause();
                    audio.currentTime = 0;
                });
            }
        });
    }

    // Handle edit button clicks
    paragraphCards.addEventListener('click', async (e) => {
        if (e.target.classList.contains('edit-paragraph')) {
            const index = e.target.dataset.index;
            const card = e.target.closest('.card');
            currentEditingCard = card;
            
            const paragraphText = card.querySelector('.card-text').textContent;
            document.getElementById('editParagraphText').value = paragraphText;
            editModal.show();
        }
    });

    // Handle paragraph edit save
    document.getElementById('saveParagraphEdit').addEventListener('click', async () => {
        if (!currentEditingCard) return;

        const newText = document.getElementById('editParagraphText').value;
        const paragraphElement = currentEditingCard.querySelector('.card-text');
        
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
                currentEditingCard.querySelector('.card-img-top').src = data.image_url;
            }
            if (data.audio_url) {
                currentEditingCard.querySelector('audio').src = data.audio_url;
            }

            editModal.hide();
            addLogMessage('Paragraph updated successfully!');
        } catch (error) {
            console.error('Error:', error);
            addLogMessage(`Error updating paragraph: ${error.message}`);
            alert('Failed to update paragraph. Please try again.');
        }
    });

    // Regenerate image button
    document.getElementById('regenerateImage').addEventListener('click', async () => {
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
            currentEditingCard.querySelector('.card-img-top').src = data.image_url;
            addLogMessage('Image regenerated successfully!');
        } catch (error) {
            console.error('Error:', error);
            addLogMessage(`Error regenerating image: ${error.message}`);
            alert('Failed to regenerate image. Please try again.');
        }
    });

    // Regenerate audio button
    document.getElementById('regenerateAudio').addEventListener('click', async () => {
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
            currentEditingCard.querySelector('audio').src = data.audio_url;
            addLogMessage('Audio regenerated successfully!');
        } catch (error) {
            console.error('Error:', error);
            addLogMessage(`Error regenerating audio: ${error.message}`);
            alert('Failed to regenerate audio. Please try again.');
        }
    });

    // Form submission handler
    storyForm.addEventListener('submit', async (e) => {
        e.preventDefault();  // Prevent form submission
        logContent.innerHTML = '';  // Clear previous logs
        paragraphCards.innerHTML = '';  // Clear previous story
        currentPage = 0;
        storyOutput.style.display = 'none';
        
        const formData = new FormData(storyForm);
        
        try {
            const response = await fetch('/generate_story', {
                method: 'POST',
                body: formData
            });

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
                                addParagraphCard(data.data, data.data.index);
                                setupAudioHover();
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
            addLogMessage('Error: ' + error.message);
        }
    });
});
