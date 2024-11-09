document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('node-editor');
    if (!container) {
        console.error('Node editor container not found');
        return;
    }

    try {
        // Parse story data
        const storyData = JSON.parse(container.dataset.story);
        
        // Create root element
        const root = document.createElement('div');
        root.style.width = '100%';
        root.style.height = '100%';
        container.appendChild(root);

        // Wait for ReactFlow to be fully loaded
        if (!window.ReactFlow) {
            throw new Error('ReactFlow not loaded. Please ensure all dependencies are loaded correctly.');
        }

        const { ReactFlow, Background, Controls, ReactFlowProvider } = window.ReactFlow;
        
        // Create simple components
        function ParagraphNode(props) {
            return React.createElement('div', 
                { className: 'paragraph-node' },
                React.createElement('div', 
                    { className: 'node-header' },
                    `Paragraph ${props.data.index + 1}`
                ),
                React.createElement('div', 
                    { className: 'node-content' },
                    props.data.text.substring(0, 100) + '...'
                )
            );
        }

        function EffectNode(props) {
            return React.createElement('div',
                { className: 'effect-node' },
                React.createElement('div',
                    { className: 'node-header' },
                    props.data.type
                ),
                React.createElement('select',
                    {
                        className: 'node-select',
                        onChange: props.data.onChange,
                        defaultValue: props.data.defaultValue
                    },
                    props.data.options.map(opt =>
                        React.createElement('option',
                            { key: opt.value, value: opt.value },
                            opt.label
                        )
                    )
                )
            );
        }

        // Initialize nodes and edges
        const initialNodes = [];
        const initialEdges = [];

        // Add paragraph nodes
        storyData.paragraphs.forEach((p, i) => {
            // Paragraph node
            initialNodes.push({
                id: `p-${i}`,
                type: 'paragraph',
                position: { x: 100, y: i * 200 },
                data: { index: i, text: p.text }
            });

            // Image style node
            initialNodes.push({
                id: `img-${i}`,
                type: 'effect',
                position: { x: 400, y: i * 200 },
                data: {
                    type: 'Image Style',
                    defaultValue: p.image_style || 'realistic',
                    options: [
                        { value: 'realistic', label: 'Realistic' },
                        { value: 'artistic', label: 'Artistic' },
                        { value: 'fantasy', label: 'Fantasy' }
                    ],
                    onChange: (e) => {
                        window.styleData = window.styleData || { paragraphs: [] };
                        window.styleData.paragraphs[i] = window.styleData.paragraphs[i] || { index: i };
                        window.styleData.paragraphs[i].image_style = e.target.value;
                    }
                }
            });

            // Voice style node
            initialNodes.push({
                id: `voice-${i}`,
                type: 'effect',
                position: { x: 600, y: i * 200 },
                data: {
                    type: 'Voice Style',
                    defaultValue: p.voice_style || 'neutral',
                    options: [
                        { value: 'neutral', label: 'Neutral' },
                        { value: 'dramatic', label: 'Dramatic' },
                        { value: 'emotional', label: 'Emotional' }
                    ],
                    onChange: (e) => {
                        window.styleData = window.styleData || { paragraphs: [] };
                        window.styleData.paragraphs[i] = window.styleData.paragraphs[i] || { index: i };
                        window.styleData.paragraphs[i].voice_style = e.target.value;
                    }
                }
            });

            // Add edges
            initialEdges.push(
                {
                    id: `p${i}-img${i}`,
                    source: `p-${i}`,
                    target: `img-${i}`,
                    type: 'smoothstep'
                },
                {
                    id: `p${i}-voice${i}`,
                    source: `p-${i}`,
                    target: `voice-${i}`,
                    type: 'smoothstep'
                }
            );
        });

        // Create the flow component
        function Flow() {
            const [nodes, setNodes] = React.useState(initialNodes);
            const [edges, setEdges] = React.useState(initialEdges);

            return React.createElement(ReactFlowProvider, null,
                React.createElement(ReactFlow, {
                    nodes: nodes,
                    edges: edges,
                    nodeTypes: {
                        paragraph: ParagraphNode,
                        effect: EffectNode
                    },
                    fitView: true,
                    minZoom: 0.5,
                    maxZoom: 1.5,
                    nodesDraggable: true,
                    nodesConnectable: false,
                    elementsSelectable: true,
                    onNodesChange: (changes) => {
                        setNodes((nds) => ReactFlow.applyNodeChanges(changes, nds));
                    },
                    onEdgesChange: (changes) => {
                        setEdges((eds) => ReactFlow.applyEdgeChanges(changes, eds));
                    }
                },
                React.createElement(Background, {
                    color: '#aaa',
                    gap: 16,
                    size: 1
                }),
                React.createElement(Controls))
            );
        }

        // Initialize styles from existing data
        window.styleData = {
            paragraphs: storyData.paragraphs.map((p, index) => ({
                index,
                image_style: p.image_style || 'realistic',
                voice_style: p.voice_style || 'neutral'
            }))
        };

        // Render the flow
        ReactDOM.render(
            React.createElement(Flow),
            root
        );

        // Setup save button handler
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
        container.innerHTML = `
            <div class="alert alert-danger">
                <h4 class="alert-heading">Failed to initialize node editor</h4>
                <p>${error.message}</p>
                <hr>
                <p class="mb-0">Please try refreshing the page. If the problem persists, contact support.</p>
            </div>`;
    }
});
