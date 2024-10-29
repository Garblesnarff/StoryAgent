document.addEventListener('DOMContentLoaded', () => {
    const storyForm = document.getElementById('story-form');
    const paragraphsContainer = document.getElementById('paragraphs-container');
    const logContent = document.getElementById('log-content');
    const bringToLifeBtn = document.getElementById('bring-to-life');
    const editModal = new bootstrap.Modal(document.getElementById('editModal'));
    let currentEditingParagraph = null;
    let currentPage = 0;
    let totalPages = 0;

    // Function to add log messages
    function addLogMessage(message) {
        if (!logContent) return;
        const logEntry = document.createElement('div');
        logEntry.textContent = message;
        logContent.appendChild(logEntry);
        logContent.scrollTop = logContent.scrollHeight;
    }

    // Story generation form submission
    storyForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(storyForm);
        
        try {
            const response = await fetch('/generate_story', {
                method: 'POST',
                body: formData,
                headers: {
                    'Accept': 'text/event-stream'
                }
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
                        if (data.type === 'complete') {
                            window.location.href = '/review';
                            return;
                        } else if (data.type === 'log') {
                            addLogMessage(data.message);
                        } else if (data.type === 'paragraph') {
                            // Store paragraph data if needed
                            addLogMessage(`Generated paragraph ${data.data.index + 1}`);
                        } else if (data.type === 'error') {
                            throw new Error(data.message);
                        }
                    } catch (parseError) {
                        console.error('Error parsing message:', line);
                    }
                }
                buffer = lines[lines.length - 1];
            }
        } catch (error) {
            console.error('Error:', error);
            addLogMessage(`Error: ${error.message}`);
            alert('Failed to generate story. Please try again.');
        }
    });

    // Function to create paragraph card for review
    function createReviewParagraphCard(paragraph, index) {
        const card = document.createElement('div');
        card.className = 'paragraph-card';
        card.innerHTML = `
            <div class="paragraph-text">${paragraph.text}</div>
            <div class="d-flex gap-2">
                <button class="btn btn-primary edit-paragraph" data-index="${index}">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-pencil me-1" viewBox="0 0 16 16">
                        <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/>
                    </svg>
                    Edit
                </button>
            </div>
        `;
        return card;
    }

    // Review page functionality
    if (window.location.pathname === '/review') {
        // Edit paragraph functionality
        paragraphsContainer?.addEventListener('click', (e) => {
            if (e.target.classList.contains('edit-paragraph') || e.target.closest('.edit-paragraph')) {
                const button = e.target.classList.contains('edit-paragraph') ? e.target : e.target.closest('.edit-paragraph');
                const index = button.dataset.index;
                const paragraphText = button.closest('.paragraph-card').querySelector('.paragraph-text').textContent;
                
                currentEditingParagraph = {
                    element: button.closest('.paragraph-card').querySelector('.paragraph-text'),
                    index: parseInt(index)
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
                    const data = await response.json();
                    throw new Error(data.error || 'Failed to update paragraph');
                }

                const data = await response.json();
                if (data.success) {
                    currentEditingParagraph.element.textContent = newText;
                    editModal.hide();
                    addLogMessage('Paragraph updated successfully');
                }
            } catch (error) {
                console.error('Error:', error);
                addLogMessage(`Error: ${error.message}`);
            }
        });

        // Bring to Life button
        bringToLifeBtn?.addEventListener('click', async () => {
            bringToLifeBtn.disabled = true;
            addLogMessage("Starting media generation...");
            
            try {
                const response = await fetch('/bring_to_life', {
                    method: 'POST',
                    headers: {
                        'Accept': 'text/event-stream'
                    }
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
                            if (data.type === 'error') {
                                throw new Error(data.message);
                            } else if (data.type === 'complete') {
                                window.location.href = '/display';
                                return;
                            } else if (data.type === 'log') {
                                addLogMessage(data.message);
                            } else if (data.type === 'paragraph') {
                                addLogMessage(`Generated media for paragraph ${data.data.index + 1}`);
                            }
                        } catch (parseError) {
                            console.error('Error parsing message:', line);
                        }
                    }
                    buffer = lines[lines.length - 1];
                }
            } catch (error) {
                console.error('Error:', error);
                addLogMessage(`Error: ${error.message}`);
                bringToLifeBtn.disabled = false;
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

            if (!prevButton || !nextButton) return;

            prevButton.style.display = currentPage > 0 ? 'block' : 'none';
            nextButton.style.display = currentPage < totalPages - 1 ? 'block' : 'none';

            pages.forEach((page, index) => {
                if (index === currentPage) {
                    page.style.display = 'block';
                    // Pause all other audio elements
                    pages.forEach((otherPage, otherIndex) => {
                        if (otherIndex !== currentPage) {
                            const audio = otherPage.querySelector('audio');
                            if (audio) {
                                audio.pause();
                                audio.currentTime = 0;
                            }
                        }
                    });
                } else {
                    page.style.display = 'none';
                }
            });
        }

        // Navigation event handlers
        document.querySelector('.book-nav.next')?.addEventListener('click', () => {
            if (currentPage < totalPages - 1) {
                currentPage++;
                updateNavigation();
            }
        });

        document.querySelector('.book-nav.prev')?.addEventListener('click', () => {
            if (currentPage > 0) {
                currentPage--;
                updateNavigation();
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
                    method: 'POST',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    }
                });

                if (!response.ok) {
                    throw new Error('Failed to save story');
                }

                const data = await response.json();
                if (data.success) {
                    addLogMessage('Story saved successfully!');
                }
            } catch (error) {
                console.error('Error:', error);
                addLogMessage(`Error: ${error.message}`);
            }
        });

        // Process the generated story with media on page load
        const processGeneratedMedia = async () => {
            try {
                const response = await fetch('/bring_to_life', {
                    method: 'POST',
                    headers: {
                        'Accept': 'text/event-stream'
                    }
                });

                if (!response.ok) {
                    throw new Error('Failed to load story media');
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
                            if (data.type === 'error') {
                                throw new Error(data.message);
                            } else if (data.type === 'paragraph') {
                                const pageElement = createDisplayPageCard(data.data, data.data.index);
                                paragraphCards.appendChild(pageElement);
                                updateNavigation();
                            }
                        } catch (parseError) {
                            console.error('Error parsing message:', line);
                        }
                    }
                    buffer = lines[lines.length - 1];
                }
            } catch (error) {
                console.error('Error:', error);
                addLogMessage(`Error: ${error.message}`);
            }
        };

        // Process the media on page load
        processGeneratedMedia();
    }
});
