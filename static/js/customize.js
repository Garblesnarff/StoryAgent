document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded, checking dependencies...');
    
    // Check required dependencies
    if (!window.React) {
        console.error('React not loaded');
        return;
    }
    if (!window.ReactFlow) {
        console.error('ReactFlow not loaded');
        return;
    }

    const container = document.getElementById('node-editor');
    if (!container) {
        console.error('Node editor container not found');
        return;
    }

    // Use global ReactFlow namespace
    const { ReactFlow, Background, Controls } = window.ReactFlow;
    
    // Parse story data
    let storyData;
    try {
        const rawData = container.dataset.story;
        if (!rawData) {
            throw new Error('No story data found');
        }
        storyData = JSON.parse(rawData);
        if (!storyData || !Array.isArray(storyData.paragraphs)) {
            throw new Error('Invalid story data format');
        }
    } catch (error) {
        console.error('Failed to parse story data:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <h4 class="alert-heading">Failed to load story data</h4>
                <p>${error.message}</p>
            </div>
        `;
        return;
    }

    // Initialize nodes from paragraphs
    const initialNodes = storyData.paragraphs.map((paragraph, index) => ({
        id: `paragraph-${index}`,
        type: 'paragraphNode',
        position: { x: 250, y: index * 200 },
        data: {
            text: paragraph.text,
            imageStyle: paragraph.image_style || 'realistic',
            index: index,
            prompt: paragraph.prompt || ''
        }
    }));

    // Create edges connecting paragraphs sequentially
    const initialEdges = storyData.paragraphs.slice(1).map((_, index) => ({
        id: `edge-${index}`,
        source: `paragraph-${index}`,
        target: `paragraph-${index + 1}`,
        type: 'smoothstep'
    }));

    // Custom node type for paragraphs
    const ParagraphNode = React.memo(({ data }) => {
        return React.createElement('div', { className: 'paragraph-node' },
            React.createElement('div', { className: 'node-header' }, `Paragraph ${data.index + 1}`),
            React.createElement('div', { 
                className: 'node-content',
                title: 'Click to expand'
            }, `${data.text.substring(0, 100)}...`),
            React.createElement('div', { className: 'node-controls' },
                React.createElement('select', {
                    className: 'node-select',
                    value: data.imageStyle,
                    onChange: (e) => updateNodeStyle(data.index, e.target.value)
                },
                    React.createElement('option', { value: 'realistic' }, 'Realistic Photo'),
                    React.createElement('option', { value: 'artistic' }, 'Artistic Painting'),
                    React.createElement('option', { value: 'fantasy' }, 'Fantasy Illustration')
                ),
                React.createElement('div', {
                    className: 'prompt-display',
                    'data-prompt': data.prompt || `Style: ${data.imageStyle}`
                },
                    React.createElement('i', { className: 'fas fa-info-circle' })
                )
            )
        );
    });

    // Node types configuration
    const nodeTypes = {
        paragraphNode: ParagraphNode
    };

    // Initialize ReactFlow
    const flow = new ReactFlow({
        container,
        nodes: initialNodes,
        edges: initialEdges,
        nodeTypes: nodeTypes,
        fitView: true,
        defaultZoom: 1,
        minZoom: 0.5,
        maxZoom: 2,
        snapToGrid: true,
        snapGrid: [15, 15]
    });

    // Add background and controls
    flow.addPlugin(new Background({
        color: '#aaa',
        gap: 16,
        size: 1
    }));

    flow.addPlugin(new Controls());

    // Style update handler
    function updateNodeStyle(index, newStyle) {
        const node = flow.getNode(`paragraph-${index}`);
        if (node) {
            node.data = {
                ...node.data,
                imageStyle: newStyle
            };
            flow.setNodes([...flow.getNodes()]);
            
            // Update style data for saving
            window.styleData = {
                paragraphs: flow.getNodes().map(node => ({
                    index: node.data.index,
                    image_style: node.data.imageStyle
                }))
            };
        }
    }

    // Setup save functionality
    const saveButton = document.getElementById('save-customization');
    if (saveButton) {
        saveButton.addEventListener('click', async () => {
            try {
                saveButton.disabled = true;
                saveButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving...';

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
                }
            } catch (error) {
                console.error('Error:', error);
                alert(error.message || 'Failed to save customization');
            } finally {
                saveButton.disabled = false;
                saveButton.innerHTML = 'Generate Cards';
            }
        });
    }
});
