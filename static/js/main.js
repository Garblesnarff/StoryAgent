document.addEventListener('DOMContentLoaded', () => {
    // Handle paragraph editing
    const paragraphsContainer = document.getElementById('paragraphs');
    if (paragraphsContainer) {
        paragraphsContainer.addEventListener('click', async (e) => {
            if (e.target.classList.contains('save-paragraph')) {
                const container = e.target.closest('.paragraph-container');
                if (container) {
                    await saveParagraph(container);
                }
            }
        });

        // Auto-save on textarea change after delay
        let saveTimeout;
        paragraphsContainer.addEventListener('input', (e) => {
            if (e.target.classList.contains('paragraph-text')) {
                const container = e.target.closest('.paragraph-container');
                if (container) {
                    clearTimeout(saveTimeout);
                    saveTimeout = setTimeout(() => {
                        saveParagraph(container);
                    }, 2000); // Auto-save after 2 seconds of no typing
                }
            }
        });
    }
});

async function generateCards() {
    try {
        // Redirect to generate page
        window.location.href = '/story/generate';
    } catch (error) {
        console.error('Error:', error);
    }
}

async function saveParagraph(container) {
    const textArea = container.querySelector('.paragraph-text');
    const index = container.dataset.index;
    const saveButton = container.querySelector('.save-paragraph');
    const alert = container.querySelector('.alert');
    
    if (!textArea || index === undefined || !saveButton || !alert) {
        console.error('Missing required elements:', {
            textArea: !!textArea,
            index: !!index,
            saveButton: !!saveButton,
            alert: !!alert
        });
        return;
    }

    try {
        saveButton.disabled = true;
        
        const response = await fetch('/story/update_paragraph', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                text: textArea.value,
                index: parseInt(index)
            })
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
        
        // Hide alert after 3 seconds
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
        
        // Show error alert
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
    } finally {
        if (saveButton) {
            saveButton.disabled = false;
        }
    }
}
