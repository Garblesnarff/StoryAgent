document.addEventListener('DOMContentLoaded', () => {
    // Wait for all scripts to load
    setTimeout(() => {
        const container = document.getElementById('node-editor');
        if (!container) return;

        try {
            // Parse story data
            const storyData = JSON.parse(container.dataset.story);
            
            // Create root element
            const root = document.createElement('div');
            root.style.width = '100%';
            root.style.height = '100%';
            container.appendChild(root);

            // Create node components
            function ParagraphNode({ data }) {
                return React.createElement('div', 
                    { className: 'paragraph-node' },
                    React.createElement('div', 
                        { className: 'node-header' }, 
                        `Paragraph ${data.index + 1}`
                    ),
                    React.createElement('div', 
                        { className: 'node-content' }, 
                        data.text.substring(0, 100) + '...'
                    )
                );
            }

            function EffectNode({ data }) {
                return React.createElement('div',
                    { className: 'effect-node' },
                    React.createElement('div',
                        { className: 'node-header' },
                        data.type
                    ),
                    React.createElement('select',
                        {
                            className: 'node-select',
                            onChange: (e) => data.onChange(e, data.index),
                            defaultValue: data.defaultValue
                        },
                        data.options.map(opt =>
                            React.createElement('option',
                                { key: opt.value, value: opt.value },
                                opt.label
                            )
                        )
                    )
                );
            }

            // Initialize nodes and edges
            const nodes = [];
            const edges = [];
            
            // Initialize style data
            window.styleData = { paragraphs: [] };

            // Create nodes for each paragraph
            storyData.paragraphs.forEach((p, i) => {
                window.styleData.paragraphs[i] = {
                    index: i,
                    image_style: p.image_style || 'realistic',
                    voice_style: p.voice_style || 'neutral'
                };

                // Add paragraph node
                nodes.push({
                    id: `p-${i}`,
                    type: 'paragraph',
                    position: { x: 100, y: i * 200 },
                    data: { index: i, text: p.text }
                });

                // Add effect nodes
                nodes.push({
                    id: `img-${i}`,
                    type: 'effect',
                    position: { x: 400, y: i * 200 },
                    data: {
                        type: 'Image Style',
                        index: i,
                        defaultValue: window.styleData.paragraphs[i].image_style,
                        options: [
                            { value: 'realistic', label: 'Realistic' },
                            { value: 'artistic', label: 'Artistic' },
                            { value: 'fantasy', label: 'Fantasy' }
                        ],
                        onChange: (e, index) => {
                            window.styleData.paragraphs[index].image_style = e.target.value;
                        }
                    }
                });

                nodes.push({
                    id: `voice-${i}`,
                    type: 'effect',
                    position: { x: 600, y: i * 200 },
                    data: {
                        type: 'Voice Style',
                        index: i,
                        defaultValue: window.styleData.paragraphs[i].voice_style,
                        options: [
                            { value: 'neutral', label: 'Neutral' },
                            { value: 'dramatic', label: 'Dramatic' },
                            { value: 'emotional', label: 'Emotional' }
                        ],
                        onChange: (e, index) => {
                            window.styleData.paragraphs[index].voice_style = e.target.value;
                        }
                    }
                });

                // Add edges
                edges.push(
                    {
                        id: `p${i}-img${i}`,
                        source: `p-${i}`,
                        target: `img-${i}`,
                        type: 'default'
                    },
                    {
                        id: `p${i}-voice${i}`,
                        source: `p-${i}`,
                        target: `voice-${i}`,
                        type: 'default'
                    }
                );
            });

            // Create the flow component
            const Flow = () => {
                const [reactNodes, setNodes] = React.useState(nodes);
                const [reactEdges, setEdges] = React.useState(edges);

                return React.createElement(ReactFlow.ReactFlowProvider, null,
                    React.createElement(ReactFlow.default, {
                        nodes: reactNodes,
                        edges: reactEdges,
                        nodeTypes: {
                            paragraph: ParagraphNode,
                            effect: EffectNode
                        },
                        fitView: true,
                        minZoom: 0.5,
                        maxZoom: 1.5,
                        nodesDraggable: true,
                        nodesConnectable: false,
                        elementsSelectable: true
                    },
                    React.createElement(ReactFlow.Background, {
                        color: '#aaa',
                        gap: 16,
                        size: 1
                    }),
                    React.createElement(ReactFlow.Controls))
                );
            };

            // Initialize the editor
            ReactDOM.render(
                React.createElement(Flow),
                root
            );

            // Setup save functionality
            const saveButton = document.getElementById('save-customization');
            if (saveButton) {
                saveButton.addEventListener('click', async () => {
                    try {
                        saveButton.disabled = true;
                        saveButton.innerHTML = 'Saving...';

                        const response = await fetch('/story/update_style', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(window.styleData)
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
                        saveButton.innerHTML = 'Generate Cards';
                    }
                });
            }

        } catch (error) {
            console.error('Failed to initialize node editor:', error);
            container.innerHTML = `<div class="alert alert-danger">
                <h4 class="alert-heading">Failed to initialize node editor</h4>
                <p>${error.message}</p>
                <hr>
                <p class="mb-0">Please try refreshing the page. If the problem persists, contact support.</p>
            </div>`;
        }
    }, 1000); // Wait 1 second for all scripts to load
});
