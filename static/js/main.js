document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded event triggered');
    
    // Helper function to show error messages
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger mt-3';
        errorDiv.textContent = message;
        document.querySelector('.content-wrapper').prepend(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => errorDiv.remove(), 5000);
    }

    // Story form initialization and handling
    const storyForm = document.getElementById('story-form');
    console.log('Story form found:', !!storyForm);
    
    if (storyForm) {
        storyForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const submitButton = storyForm.querySelector('button[type="submit"]');
            const originalButtonText = submitButton.textContent;
            
            try {
                submitButton.disabled = true;
                submitButton.innerHTML = `
                    <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                    Generating Story...
                `;
                
                const formData = new FormData(storyForm);
                const response = await fetch('/story/generate', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error('Failed to generate story');
                }
                
                const data = await response.json();
                if (data.success) {
                    window.location.href = '/story/edit';
                } else {
                    throw new Error(data.error || 'Failed to generate story');
                }
            } catch (error) {
                console.error('Story generation error:', error);
                showError(error.message || 'Failed to generate story. Please try again.');
            } finally {
                submitButton.disabled = false;
                submitButton.textContent = originalButtonText;
            }
        });
    }

    // Upload form initialization and handling
    const uploadForm = document.getElementById('upload-form');
    console.log('Upload form found:', !!uploadForm);
    
    if (uploadForm) {
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const submitButton = uploadForm.querySelector('button[type="submit"]');
            const spinner = submitButton.querySelector('.spinner-border');
            const buttonText = submitButton.querySelector('.button-text');
            const uploadProgress = document.getElementById('upload-progress');
            const progressBar = uploadProgress.querySelector('.progress-bar');
            const uploadStatus = document.getElementById('upload-status');
            
            try {
                submitButton.disabled = true;
                spinner.classList.remove('d-none');
                uploadProgress.classList.remove('d-none');
                uploadStatus.innerHTML = '';
                
                const formData = new FormData(uploadForm);
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    uploadStatus.innerHTML = `<span class="text-success">File uploaded and processed successfully!</span>`;
                    setTimeout(() => {
                        window.location.href = '/story/edit';
                    }, 1000);
                } else {
                    throw new Error(data.error || 'Failed to upload file');
                }
            } catch (error) {
                console.error('Upload error:', error);
                let errorMessage = 'Failed to upload file. Please try again.';
                
                if (error.name === 'TypeError') {
                    errorMessage = 'Network error. Please check your connection.';
                } else if (error.message.includes('unsupported')) {
                    errorMessage = 'Unsupported file type. Please upload PDF, EPUB, or HTML files only.';
                } else if (error.message) {
                    errorMessage = error.message;
                }
                
                uploadStatus.innerHTML = `<span class="text-danger"><strong>Error:</strong> ${errorMessage}</span>`;
                progressBar.style.width = '0%';
                progressBar.style.transition = 'none';
            } finally {
                submitButton.disabled = false;
                spinner.classList.add('d-none');
            }
        });
    }
});
