document.addEventListener('DOMContentLoaded', () => {
    const storyForm = document.getElementById('story-form');
    const uploadForm = document.getElementById('upload-form');

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

    uploadForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(uploadForm);
        const submitButton = uploadForm.querySelector('button[type="submit"]');
        const buttonText = submitButton.querySelector('.button-text');
        const spinner = submitButton.querySelector('.spinner-border');
        const progressBar = document.querySelector('#upload-progress .progress-bar');
        const uploadProgress = document.getElementById('upload-progress');
        const uploadStatus = document.getElementById('upload-status');
        
        // Reset and show progress elements
        uploadProgress.classList.remove('d-none');
        progressBar.style.width = '0%';
        uploadStatus.textContent = '';
        submitButton.disabled = true;
        spinner.classList.remove('d-none');
        
        try {
            // File upload phase
            uploadStatus.innerHTML = '<strong>Phase 1/3:</strong> Uploading file...';
            progressBar.style.width = '0%';
            
            const response = await fetch('/story/upload', {
                method: 'POST',
                body: formData
            });
            
            // Processing phase
            uploadStatus.innerHTML = '<strong>Phase 2/3:</strong> Processing document...';
            progressBar.style.width = '33%';
            
            let data;
            try {
                data = await response.json();
            } catch (parseError) {
                throw new Error('Server returned an invalid response');
            }
            
            if (!response.ok) {
                throw new Error(data.error || 'Upload failed');
            }
            
            // Text extraction phase
            uploadStatus.innerHTML = '<strong>Phase 3/3:</strong> Extracting text...';
            progressBar.style.width = '66%';
            
            // Complete
            uploadStatus.innerHTML = '<strong>Complete!</strong> Redirecting to editor...';
            progressBar.style.width = '100%';
            
            // Redirect to edit page
            if (data.redirect) {
                window.location.href = data.redirect;
            }
            
        } catch (error) {
            console.error('Error:', error);
            uploadStatus.innerHTML = `<span class="text-danger"><strong>Error:</strong> ${error.message}</span>`;
            progressBar.style.width = '0%';
        } finally {
            submitButton.disabled = false;
            spinner.classList.add('d-none');
        }
    });
});
