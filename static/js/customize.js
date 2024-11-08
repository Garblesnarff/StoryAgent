document.addEventListener('DOMContentLoaded', () => {
    const saveButton = document.getElementById('save-customization');
    const paragraphStyles = document.querySelectorAll('.paragraph-style');
    
    // Initialize style data
    const styleData = {
        paragraphs: Array.from(paragraphStyles).map((container) => {
            const index = parseInt(container.dataset.index);
            return {
                index,
                image_style: container.querySelector('.image-style').value,
                voice_style: container.querySelector('.voice-style').value,
                mood_enhancement: container.querySelector('.mood-enhancement').value
            };
        })
    };
    
    // Add change listeners to all style selects
    paragraphStyles.forEach((container) => {
        const selects = container.querySelectorAll('select');
        const index = parseInt(container.dataset.index);
        
        selects.forEach((select) => {
            select.addEventListener('change', () => {
                styleData.paragraphs[index][select.className.replace('-', '_')] = select.value;
            });
        });
    });
    
    // Handle save and generation
    saveButton?.addEventListener('click', async () => {
        try {
            saveButton.disabled = true;
            const response = await fetch('/story/update_style', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(styleData)
            });
            
            if (!response.ok) {
                throw new Error('Failed to save style customization');
            }
            
            const data = await response.json();
            if (data.success) {
                window.location.href = '/story/generate';
            } else {
                throw new Error(data.error || 'Failed to save customization');
            }
            
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to save customization. Please try again.');
        } finally {
            saveButton.disabled = false;
        }
    });
});
