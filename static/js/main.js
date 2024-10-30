document.addEventListener('DOMContentLoaded', () => {
    const paragraphsContainer = document.getElementById('paragraphs');
    
    if (paragraphsContainer) {
        paragraphsContainer.addEventListener('click', async (e) => {
            if (e.target.classList.contains('save-paragraph')) {
                const container = e.target.closest('.paragraph-container');
                await saveParagraph(container);
            }
        });
    }

    const generateCardsBtn = document.getElementById('generateCards');
    if (generateCardsBtn) {
        generateCardsBtn.addEventListener('click', async () => {
            try {
                window.location.href = '/story/generate';
            } catch (error) {
                console.error('Error:', error);
            }
        });
    }
});

async function saveParagraph(container) {
    if (!container) return;
    
    const text = container.querySelector('.paragraph-text')?.value;
    const index = parseInt(container.dataset.index);
    const saveButton = container.querySelector('.save-paragraph');
    const alert = container.querySelector('.alert');
    
    if (!text || isNaN(index) || !saveButton || !alert) {
        console.error('Required elements not found');
        return;
    }
    
    try {
        saveButton.disabled = true;
        const response = await fetch('/story/update_paragraph', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, index })
        });
        
        if (!response.ok) throw new Error('Failed to save');
        
        // Show success alert
        alert.classList.remove('alert-danger');
        alert.classList.add('alert-success');
        alert.innerHTML = `
            Changes saved successfully!
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        alert.style.display = 'block';
        alert.classList.add('show');
        
        setTimeout(() => {
            if (alert) {
                alert.classList.remove('show');
                alert.style.display = 'none';
            }
        }, 3000);
        
    } catch (error) {
        console.error('Error:', error);
        alert.classList.remove('alert-success');
        alert.classList.add('alert-danger');
        alert.innerHTML = `
            Failed to save changes. Please try again.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        alert.style.display = 'block';
        alert.classList.add('show');
    } finally {
        if (saveButton) saveButton.disabled = false;
    }
}
