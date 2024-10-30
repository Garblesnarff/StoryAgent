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
});

async function saveParagraph(container) {
    const text = container.querySelector('.paragraph-text').value;
    const index = container.dataset.index;
    const saveButton = container.querySelector('.save-paragraph');
    const alert = container.querySelector('.alert');
    
    try {
        saveButton.disabled = true;
        const response = await fetch('/story/update_paragraph', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, index })
        });
        
        if (!response.ok) throw new Error('Failed to save');
        
        alert.classList.add('show');
        alert.style.display = 'block';
        setTimeout(() => {
            alert.classList.remove('show');
            alert.style.display = 'none';
        }, 3000);
        
    } catch (error) {
        console.error('Error:', error);
        alert.className = 'alert alert-danger alert-dismissible fade';
        alert.innerHTML = `
            Failed to save changes. Please try again.
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        alert.style.display = 'block';
    } finally {
        saveButton.disabled = false;
    }
}
