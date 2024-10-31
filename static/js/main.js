document.addEventListener('DOMContentLoaded', () => {
    const storyForm = document.getElementById('story-form');

    // Story generation form submission
    storyForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        try {
            const formData = new FormData(storyForm);
            const response = await fetch('/generate_story', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            
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
            alert('Error: ' + error.message);
        }
    });
});
