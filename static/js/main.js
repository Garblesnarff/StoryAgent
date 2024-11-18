document.addEventListener('DOMContentLoaded', () => {
    const storyForm = document.getElementById('story-form');

    storyForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Show loading state
        const submitButton = storyForm.querySelector('button[type="submit"]');
        const originalText = submitButton.textContent;
        submitButton.disabled = true;
        submitButton.textContent = 'Generating...';
        
        try {
            const formData = new FormData(storyForm);
            const response = await fetch('/generate_story', {
                method: 'POST',
                body: formData
            });

            let data;
            try {
                data = await response.json();
            } catch (parseError) {
                console.error('Failed to parse JSON response:', parseError);
                throw new Error('Server returned an invalid response');
            }
            
            if (!response.ok) {
                throw new Error(data.error || 'Story generation failed');
            }

            if (data.success && data.redirect) {
                window.location.href = data.redirect;
            } else {
                throw new Error(data.error || 'Invalid response from server');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error: ' + (error.message || 'An unexpected error occurred'));
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = originalText;
        }
    });
});
