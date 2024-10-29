document.addEventListener('DOMContentLoaded', () => {
    const storyForm = document.getElementById('story-form');
    const paragraphsContainer = document.getElementById('paragraphs-container');
    const logContent = document.getElementById('log-content');
    const bringToLifeBtn = document.getElementById('bring-to-life');
    const editModal = new bootstrap.Modal(document.getElementById('editModal'));
    let currentEditingParagraph = null;
    let currentPage = 0;
    let totalPages = 0;
    let story_paragraphs = [];

    // Story generation form submission
    storyForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(storyForm);
        
        try {
            const response = await fetch('/generate_story', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error('Story generation failed');
            }

            // Process the response stream
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
                        if (data.type === 'paragraph') {
                            story_paragraphs.push(data.data.text);
                        }
                        if (data.type === 'complete') {
                            // Send a POST request to store data before redirecting
                            const storeResponse = await fetch('/store_story', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({
                                    paragraphs: story_paragraphs
                                })
                            });
                            
                            if (storeResponse.ok) {
                                window.location.href = '/review';
                            } else {
                                throw new Error('Failed to store story data');
                            }
                            return;
                        }
                    } catch (parseError) {
                        console.error('Error parsing message:', line);
                    }
                }
                buffer = lines[lines.length - 1];
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to generate story. Please try again.');
        }
    });

    // Function to add log messages
    function addLogMessage(message) {
        if (!logContent) return;
        const logEntry = document.createElement('div');
        logEntry.textContent = message;
        logContent.appendChild(logEntry);
        logContent.scrollTop = logContent.scrollHeight;
    }

    // Function to create paragraph card for review
    function createReviewParagraphCard(paragraph, index) {
        const card = document.createElement('div');
        card.className = 'paragraph-card';
        card.innerHTML = `
            <div class="paragraph-text">${paragraph}</div>
            <button class="btn btn-primary edit-paragraph" data-index="${index}">Edit</button>
        `;
        return card;
    }

    // Function to create display page card
    function createDisplayPageCard(paragraph, index) {
        const pageDiv = document.createElement('div');
        pageDiv.className = 'book-page';
        pageDiv.dataset.index = index;
        
        if (index === currentPage) {
            pageDiv.classList.add('active');
        } else if (index === currentPage + 1) {
            pageDiv.classList.add('next');
        } else if (index === currentPage - 1) {
            pageDiv.classList.add('prev');
        }
        
        pageDiv.innerHTML = `
            <div class="card h-100">
                <img src="${paragraph.image_url}" class="card-img-top" alt="Paragraph image">
                <div class="card-body">
                    <p class="card-text">${paragraph.text}</p>
                </div>
                <div class="card-footer">
                    <audio controls src="${paragraph.audio_url}" preload="none"></audio>
                </div>
            </div>
        `;
        return pageDiv;
    }

    // Review page functionality
    if (window.location.pathname === '/review') {
        // Process the generated story
        if (paragraphsContainer) {
            const paragraphs = JSON.parse(paragraphsContainer.dataset.paragraphs || '[]');
            paragraphs.forEach((paragraph, index) => {
                const card = createReviewParagraphCard(paragraph, index);
                paragraphsContainer.appendChild(card);
            });
        }

        // Edit paragraph functionality
        paragraphsContainer?.addEventListener('click', (e) => {
            if (e.target.classList.contains('edit-paragraph')) {
                const index = parseInt(e.target.dataset.index);
                const paragraphText = e.target.closest('.paragraph-card').querySelector('.paragraph-text').textContent;
                
                currentEditingParagraph = {
                    element: e.target.closest('.paragraph-card').querySelector('.paragraph-text'),
                    index: index
                };
                
                document.getElementById('editParagraphText').value = paragraphText;
                editModal.show();
            }
        });

        // Save edited paragraph
        document.getElementById('saveParagraphEdit')?.addEventListener('click', async () => {
            if (!currentEditingParagraph) return;

            const newText = document.getElementById('editParagraphText').value;
            
            try {
                const response = await fetch('/update_paragraph', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        text: newText,
                        index: currentEditingParagraph.index
                    })
                });

                if (!response.ok) {
                    throw new Error('Failed to update paragraph');
                }

                // Update local display
                currentEditingParagraph.element.textContent = newText;
                
                // Update session data
                story_paragraphs[currentEditingParagraph.index] = newText;
                
                editModal.hide();
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to update paragraph. Please try again.');
            }
        });

        // Bring to Life button
        bringToLifeBtn?.addEventListener('click', async () => {
            bringToLifeBtn.disabled = true;
            
            try {
                const response = await fetch('/bring_to_life', {
                    method: 'POST'
                });

                if (!response.ok) {
                    throw new Error('Failed to generate media');
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
                            if (data.type === 'complete') {
                                window.location.href = '/display';
                                return;
                            } else if (data.type === 'log') {
                                addLogMessage(data.message);
                            }
                        } catch (parseError) {
                            console.error('Error parsing message:', line);
                        }
                    }
                    buffer = lines[lines.length - 1];
                }
            } catch (error) {
                console.error('Error:', error);
                bringToLifeBtn.disabled = false;
                alert('Failed to generate media. Please try again.');
            }
        });
    }

    // Display page functionality
    if (window.location.pathname === '/display') {
        const paragraphCards = document.getElementById('paragraph-cards');
        const startOverBtn = document.getElementById('start-over');
        const saveStoryBtn = document.getElementById('save-story');

        function updateNavigation() {
            const pages = document.querySelectorAll('.book-page');
            totalPages = pages.length;
            const prevButton = document.querySelector('.book-nav.prev');
            const nextButton = document.querySelector('.book-nav.next');

            prevButton.style.display = currentPage > 0 ? 'flex' : 'none';
            nextButton.style.display = currentPage < totalPages - 1 ? 'flex' : 'none';

            pages.forEach((page, index) => {
                page.classList.remove('active', 'next', 'prev', 'turning', 'turning-forward', 'turning-backward');
                
                if (index === currentPage) {
                    page.classList.add('active');
                } else if (index === currentPage + 1) {
                    page.classList.add('next');
                } else if (index === currentPage - 1) {
                    page.classList.add('prev');
                }
                
                // Pause all other audio elements
                const audio = page.querySelector('audio');
                if (audio && index !== currentPage) {
                    audio.pause();
                    audio.currentTime = 0;
                }
            });
        }

        // Navigation event handlers
        document.querySelector('.book-nav.next')?.addEventListener('click', () => {
            if (currentPage < totalPages - 1) {
                const pages = document.querySelectorAll('.book-page');
                pages[currentPage].classList.add('turning', 'turning-forward');
                pages[currentPage + 1].classList.add('turning', 'turning-backward');
                
                setTimeout(() => {
                    currentPage++;
                    updateNavigation();
                }, 400);
            }
        });

        document.querySelector('.book-nav.prev')?.addEventListener('click', () => {
            if (currentPage > 0) {
                const pages = document.querySelectorAll('.book-page');
                pages[currentPage].classList.add('turning', 'turning-backward');
                pages[currentPage - 1].classList.add('turning', 'turning-forward');
                
                setTimeout(() => {
                    currentPage--;
                    updateNavigation();
                }, 400);
            }
        });

        // Start Over button
        startOverBtn?.addEventListener('click', () => {
            window.location.href = '/';
        });

        // Save Story button
        saveStoryBtn?.addEventListener('click', async () => {
            try {
                const response = await fetch('/save_story', {
                    method: 'POST'
                });

                if (!response.ok) {
                    throw new Error('Failed to save story');
                }

                const data = await response.json();
                if (data.success) {
                    alert('Story saved successfully!');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Failed to save story. Please try again.');
            }
        });

        // Process the media on page load
        processGeneratedMedia();
    }
});
