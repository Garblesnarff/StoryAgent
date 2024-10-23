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

    // Rest of the code remains the same...
    // (Keep all the existing event handlers for editing, regenerating images/audio, and form submission)
});
