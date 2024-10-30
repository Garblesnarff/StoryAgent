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
    try {
        if (!container) {
            console.error('No container found');
            return;
        }
        
        const textArea = container.querySelector('.paragraph-text');
        const index = container.dataset.index;
        const saveButton = container.querySelector('.save-paragraph');
        const alert = container.querySelector('.alert');
        
        if (!textArea) {
            throw new Error('Textarea not found');
        }
        if (index === undefined) {
            throw new Error('Paragraph index not found');
        }
        if (!saveButton) {
            throw new Error('Save button not found');
        }
        if (!alert) {
            throw new Error('Alert element not found');
        }

        const text = textArea.value;
        
        saveButton.disabled = true;
        const response = await fetch('/story/update_paragraph', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, index: parseInt(index) })
        });
        
        if (!response.ok) {
            throw new Error('Failed to save changes');
        }
        
        // Show success alert
        alert.classList.remove('alert-danger');
        alert.classList.add('alert-success');
        alert.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="bi bi-check-circle-fill me-2"></i>
                Changes saved successfully!
                <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
            </div>
        `;
        alert.style.display = 'block';
        alert.classList.add('show');
        
        setTimeout(() => {
            if (alert && alert.classList.contains('show')) {
                alert.classList.remove('show');
                setTimeout(() => {
                    alert.style.display = 'none';
                }, 150);
            }
        }, 3000);
        
    } catch (error) {
        console.error('Error:', error.message);
        if (!container) return;
        
        const alert = container.querySelector('.alert');
        if (alert) {
            alert.classList.remove('alert-success');
            alert.classList.add('alert-danger');
            alert.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    ${error.message}
                    <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
                </div>
            `;
            alert.style.display = 'block';
            alert.classList.add('show');
        }
    } finally {
        const saveButton = container?.querySelector('.save-paragraph');
        if (saveButton) {
            saveButton.disabled = false;
        }
    }
}
