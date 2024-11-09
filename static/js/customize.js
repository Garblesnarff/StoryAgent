document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('node-editor');
    if (!container) return;

    try {
        // Parse story data
        const storyData = JSON.parse(container.dataset.story);
        if (!storyData || !storyData.paragraphs) {
            throw new Error('Invalid story data format');
        }

        // Initialize React components
        const { ReactFlowProvider, ReactFlow, Background, Controls } = window.ReactFlow;

        // Create nodes array
        const nodes = storyData.paragraphs.flatMap((paragraph, index) => [
            {
                id: `p${index}`,
                type: 'default',
                position: { x: 100, y: index * 200 },
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
            },
            {
                id: `style${index}`,
                type: 'default',
                position: { x: 400, y: index * 200 },
                data: {
                    label: React.createElement('div', { className: 'effect-node' },
                        React.createElement('div', { className: 'node-header' },
                            'Style Options'
                        ),
                        React.createElement('select', {
                            className: 'node-select',
                            defaultValue: 'realistic',
                            onChange: (e) => {
                                if (!window.styleData) {
                                    window.styleData = { paragraphs: [] };
                                }
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
            }
        ]);

        // Create edges array
        const edges = storyData.paragraphs.map((_, index) => ({
            id: `e${index}`,
            source: `p${index}`,
            target: `style${index}`,
            type: 'smoothstep',
            animated: true
        }));

        // Create Flow component
        function Flow() {
            return React.createElement(ReactFlowProvider, null,
                React.createElement(ReactFlow, {
                    nodes: nodes,
                    edges: edges,
                    fitView: true,
                    nodesDraggable: true,
                    nodesConnectable: false
                },
                React.createElement(Background, {
                    color: '#aaa',
                    gap: 16,
                    size: 1
                }),
                React.createElement(Controls))
            );
        }

        // Mount the component
        ReactDOM.render(
            React.createElement(Flow),
            container
        );

        // Setup save button
        const saveButton = document.getElementById('save-customization');
        if (saveButton) {
            saveButton.addEventListener('click', async () => {
                try {
                    saveButton.disabled = true;
                    saveButton.textContent = 'Saving...';

                    const response = await fetch('/story/update_style', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(window.styleData || { paragraphs: [] })
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
