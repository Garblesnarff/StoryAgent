document.addEventListener('DOMContentLoaded', () => {
    let saveTimeouts = {};
    
    document.querySelectorAll('.paragraph-container').forEach(container => {
        const index = container.dataset.index;
        const textArea = container.querySelector('.paragraph-text');
        const saveBtn = container.querySelector('.save-paragraph');
        
        // Show autosave status
        const statusDiv = document.createElement('div');
        statusDiv.className = 'save-status text-muted small mt-2';
        container.querySelector('.card-body').appendChild(statusDiv);
        
        // Auto-save functionality with debouncing
        textArea?.addEventListener('input', () => {
            statusDiv.textContent = 'Saving...';
            if (saveTimeouts[index]) {
                clearTimeout(saveTimeouts[index]);
            }
            
            saveTimeouts[index] = setTimeout(() => {
                saveParagraph(index, textArea.value, false, statusDiv);
            }, 1000);
        });
        
        // Manual save
        saveBtn?.addEventListener('click', () => {
            saveParagraph(index, textArea.value, false, statusDiv);
        });
    });
    
    async function saveParagraph(index, text, generateMedia = false, statusDiv = null) {
        try {
            const saveBtn = document.querySelector(`.paragraph-container[data-index="${index}"] .save-paragraph`);
            if (saveBtn) {
                saveBtn.disabled = true;
            }
            
            console.log('Saving changes...');
            
            const response = await fetch('/story/update_paragraph', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: text,
                    index: parseInt(index),
                    generate_media: generateMedia
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to save changes');
            }
            
            const data = await response.json();
            if (data.success) {
                if (statusDiv) {
                    statusDiv.textContent = 'Changes saved';
                    setTimeout(() => {
                        statusDiv.textContent = '';
                    }, 2000);
                }
            } else {
                throw new Error(data.error || 'Failed to save changes');
            }
            
        } catch (error) {
            console.error('Error:', error);
            if (statusDiv) {
                statusDiv.textContent = 'Error saving changes';
                statusDiv.style.color = 'var(--bs-danger)';
            }
            alert('Failed to save changes. Please try again.');
        } finally {
            if (saveBtn) {
                saveBtn.disabled = false;
            }
        }
    }
});
