document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('node-editor');
    if (!container) return;

    try {
        // Parse story data with error handling
        let storyData;
        try {
            storyData = JSON.parse(container.dataset.story);
            if (!storyData || !storyData.paragraphs) {
                throw new Error('Invalid story data format');
            }
        } catch (parseError) {
            throw new Error(`Failed to parse story data: ${parseError.message}`);
        }

        // Create root element
        const root = document.createElement('div');
        root.style.width = '100%';
        root.style.height = '100%';
        container.appendChild(root);

        // Initialize ReactFlow
        const reactFlowInstance = window.ReactFlow;
        if (!reactFlowInstance) {
            throw new Error('ReactFlow not properly loaded');
        }

        // Create nodes
        const nodes = [];
        const edges = [];

        // Add paragraph nodes
        storyData.paragraphs.forEach((paragraph, index) => {
            nodes.push({
                id: `p${index}`,
                type: 'default',
                position: { x: 100, y: index * 150 },
                data: { 
                    label: React.createElement('div', { className: 'paragraph-node' },
                        React.createElement('div', { className: 'node-header' }, 
                            `Paragraph ${index + 1}`
                        ),
                        React.createElement('div', { className: 'node-content' }, 
                            paragraph.text.substring(0, 100) + '...'
                        )
                    )
                }
            });

            // Add style nodes
            nodes.push({
                id: `style${index}`,
                type: 'default',
                position: { x: 400, y: index * 150 },
                data: {
                    label: React.createElement('div', { className: 'effect-node' },
                        React.createElement('div', { className: 'node-header' }, 'Styles'),
                        React.createElement('select', {
                            className: 'node-select',
                            defaultValue: paragraph.image_style || 'realistic',
                            onChange: (e) => {
                                if (!window.styleData) window.styleData = { paragraphs: [] };
                                if (!window.styleData.paragraphs[index]) {
                                    window.styleData.paragraphs[index] = { index };
                                }
                                window.styleData.paragraphs[index].image_style = e.target.value;
                            }
                        }, [
                            React.createElement('option', { value: 'realistic' }, 'Realistic'),
                            React.createElement('option', { value: 'artistic' }, 'Artistic'),
                            React.createElement('option', { value: 'fantasy' }, 'Fantasy')
                        ])
                    )
                }
            });

            // Add connecting edge
            edges.push({
                id: `e${index}`,
                source: `p${index}`,
                target: `style${index}`,
                type: 'smoothstep'
            });
        });

        // Create and render the flow
        const Flow = () => {
            const [flowInstance, setFlowInstance] = React.useState(null);

            return React.createElement(reactFlowInstance.ReactFlowProvider, null,
                React.createElement(reactFlowInstance.ReactFlow, {
                    nodes: nodes,
                    edges: edges,
                    onInit: setFlowInstance,
                    fitView: true,
                    minZoom: 0.5,
                    maxZoom: 1.5
                },
                React.createElement(reactFlowInstance.Background, {
                    color: '#aaa',
                    gap: 16,
                    size: 1
                }),
                React.createElement(reactFlowInstance.Controls))
            );
        };

        // Render the flow
        ReactDOM.render(React.createElement(Flow), root);

        // Setup save button handler
        const saveButton = document.getElementById('save-customization');
        if (saveButton) {
            saveButton.addEventListener('click', async () => {
                try {
                    if (!window.styleData || !window.styleData.paragraphs) {
                        throw new Error('No style data available');
                    }

                    saveButton.disabled = true;
                    saveButton.textContent = 'Saving...';

                    const response = await fetch('/story/update_style', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(window.styleData)
                    });

                    if (!response.ok) {
                        throw new Error('Failed to save customization');
                    }

                    const data = await response.json();
                    if (data.success) {
                        window.location.href = '/story/generate';
                    } else {
                        throw new Error(data.error || 'Failed to save customization');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert(error.message);
                } finally {
                    saveButton.disabled = false;
                    saveButton.textContent = 'Generate Cards';
                }
            });
        }

    } catch (error) {
        console.error('Failed to initialize node editor:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <h4 class="alert-heading">Failed to initialize node editor</h4>
                <p>${error.message}</p>
                <hr>
                <p class="mb-0">Please try refreshing the page. If the problem persists, contact support.</p>
            </div>
        `;
    }
});
