document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('node-editor');
    const paragraphNodesContainer = document.getElementById('paragraph-nodes');
    
    if (!container || !paragraphNodesContainer) {
        console.error('Required containers not found');
        return;
    }

    // Parse story data and initialize style data storage
    let storyData;
    try {
        const rawData = container.dataset.story;
        if (!rawData) {
            throw new Error('No story data found');
        }
        storyData = JSON.parse(rawData);
        if (!storyData || !Array.isArray(storyData.paragraphs)) {
            throw new Error('Invalid story data format: Expected array of paragraphs');
        }

        // Initialize style data with proper structure for all paragraphs
        window.styleData = {
            paragraphs: storyData.paragraphs.map((paragraph, index) => ({
                index,
                image_style: paragraph.image_style || 'realistic'
            }))
        };
    } catch (error) {
        console.error('Failed to parse story data:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <h4 class="alert-heading">Failed to load story data</h4>
                <p>${error.message}</p>
                <hr>
                <p class="mb-0">Please make sure you have a valid story selected.</p>
            </div>
        `;
        return;
    }

    // Create paragraph nodes
    const paragraphNodes = storyData.paragraphs.map((paragraph, index) => {
        const card = document.createElement('div');
        card.className = 'card paragraph-node';
        card.innerHTML = `
            <div class="card-body">
                <div class="node-header">Paragraph ${index + 1}</div>
                <div class="node-content" title="Click to expand">${paragraph.text.substring(0, 100)}...</div>
                <div class="node-controls">
                    <select class="node-select" data-type="image_style" data-index="${index}">
                        <option value="realistic" ${(paragraph.image_style || 'realistic') === 'realistic' ? 'selected' : ''}>Realistic Photo</option>
                        <option value="artistic" ${(paragraph.image_style || 'realistic') === 'artistic' ? 'selected' : ''}>Artistic Painting</option>
                        <option value="fantasy" ${(paragraph.image_style || 'realistic') === 'fantasy' ? 'selected' : ''}>Fantasy Illustration</option>
                    </select>
                    <div class="prompt-display" data-prompt="${paragraph.prompt || 'Style: ' + (paragraph.image_style || 'realistic')}">
                        <i class="fas fa-info-circle"></i>
                    </div>
                </div>
            </div>
        `;

        // Add hover event listeners
        const content = card.querySelector('.node-content');
        content.addEventListener('click', () => {
            content.classList.toggle('expanded');
            content.textContent = content.classList.contains('expanded') ? 
                paragraph.text : 
                paragraph.text.substring(0, 100) + '...';
        });

        // Add event listeners to selects
        const select = card.querySelector('.node-select');
        select.addEventListener('change', (e) => {
            const index = parseInt(e.target.dataset.index);
            const type = e.target.dataset.type;
            const newStyle = e.target.value;
            
            // Update style data
            window.styleData.paragraphs[index] = {
                ...window.styleData.paragraphs[index],
                index,
                image_style: newStyle
            };
            
            console.log('Style updated:', window.styleData);
        });

        return card;
    });

    // Add nodes to container
    paragraphNodesContainer.append(...paragraphNodes);

    // Setup save functionality
    const saveButton = document.getElementById('save-customization');
    if (saveButton) {
        saveButton.addEventListener('click', async () => {
            try {
                saveButton.disabled = true;
                saveButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Saving...';

                if (!window.styleData?.paragraphs?.length) {
                    throw new Error('No style changes to save');
                }

                // Remove any null values from paragraphs array
                window.styleData.paragraphs = window.styleData.paragraphs.filter(p => p !== null);

                const response = await fetch('/story/update_style', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(window.styleData)
                });

                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Failed to save customization');
                }

                if (data.success) {
                    window.location.href = '/story/generate';
                } else {
                    throw new Error(data.error || 'Server returned unsuccessful response');
                }
            } catch (error) {
                console.error('Error saving customization:', error);
                alert(error.message || 'Failed to save customization');
            } finally {
                saveButton.disabled = false;
                saveButton.innerHTML = 'Generate Cards';
            }
        });
    }
});
