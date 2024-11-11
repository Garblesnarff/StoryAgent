document.addEventListener('DOMContentLoaded', () => {
    const flowRoot = document.getElementById('reactflow-root');
    const saveButton = document.getElementById('save-customization');
    
    try {
        // Get story data and validate
        let storyData;
        try {
            storyData = JSON.parse(flowRoot.dataset.story || '{}');
            if (!storyData.paragraphs || !Array.isArray(storyData.paragraphs)) {
                throw new Error('Invalid story data format');
            }
        } catch (error) {
            console.error('Failed to load story data:', error);
            flowRoot.innerHTML = '<div class="alert alert-danger m-3">Failed to load story data. Please make sure you have a valid story selected.</div>';
            return;
        }

        // Create initial nodes from paragraphs with proper positioning
        const initialNodes = storyData.paragraphs.map((paragraph, index) => ({
            id: `paragraph-${index}`,
            type: 'customNode',
            position: { x: 250, y: index * 300 },
            data: {
                text: paragraph.text || '',
                imageStyle: paragraph.image_style || 'realistic',
                voiceStyle: paragraph.voice_style || 'neutral',
                index: index
            }
        }));

        // Create Custom Node Component
        function CustomNode({ data }) {
            const [styles, setStyles] = React.useState({
                imageStyle: data.imageStyle || 'realistic',
                voiceStyle: data.voiceStyle || 'neutral'
            });

            const handleStyleChange = (type, value) => {
                const newStyles = {
                    ...styles,
                    [type]: value
                };
                setStyles(newStyles);
                if (data) {
                    data[type] = value;
                }
            };

            return React.createElement('div', {
                className: 'paragraph-node'
            }, [
                React.createElement('div', {
                    key: 'header',
                    className: 'node-header'
                }, `Paragraph ${data.index + 1}`),
                
                React.createElement('div', {
                    key: 'content',
                    className: 'node-content'
                }, data.text || 'No content available'),
                
                React.createElement('div', {
                    key: 'controls',
                    className: 'node-controls'
                }, [
                    React.createElement('div', {
                        key: 'image-style',
                        className: 'node-select-group'
                    }, [
                        React.createElement('label', {
                            key: 'image-label',
                            className: 'node-select-label'
                        }, 'Image Style'),
                        React.createElement('select', {
                            key: 'image-select',
                            className: 'node-select',
                            value: styles.imageStyle,
                            onChange: (e) => handleStyleChange('imageStyle', e.target.value)
                        }, [
                            React.createElement('option', { value: 'realistic', key: 'realistic' }, 'Realistic'),
                            React.createElement('option', { value: 'artistic', key: 'artistic' }, 'Artistic'),
                            React.createElement('option', { value: 'fantasy', key: 'fantasy' }, 'Fantasy')
                        ])
                    ]),
                    
                    React.createElement('div', {
                        key: 'voice-style',
                        className: 'node-select-group'
                    }, [
                        React.createElement('label', {
                            key: 'voice-label',
                            className: 'node-select-label'
                        }, 'Voice Style'),
                        React.createElement('select', {
                            key: 'voice-select',
                            className: 'node-select',
                            value: styles.voiceStyle,
                            onChange: (e) => handleStyleChange('voiceStyle', e.target.value)
                        }, [
                            React.createElement('option', { value: 'neutral', key: 'neutral' }, 'Neutral'),
                            React.createElement('option', { value: 'dramatic', key: 'dramatic' }, 'Dramatic'),
                            React.createElement('option', { value: 'cheerful', key: 'cheerful' }, 'Cheerful')
                        ])
                    ])
                ])
            ]);
        }

        // Create Flow Component
        function Flow() {
            const [nodes, setNodes] = React.useState(initialNodes);
            const nodeTypes = React.useMemo(() => ({
                customNode: CustomNode
            }), []);

            const onNodesChange = React.useCallback(
                (changes) => setNodes((nds) => window.ReactFlow.applyNodeChanges(changes, nds)),
                []
            );

            return React.createElement(window.ReactFlow.default, {
                nodes: nodes,
                onNodesChange: onNodesChange,
                nodeTypes: nodeTypes,
                fitView: true,
                defaultViewport: { x: 0, y: 0, zoom: 1 },
                children: [
                    React.createElement(window.ReactFlow.Controls),
                    React.createElement(window.ReactFlow.Background, { color: '#aaa', gap: 16 })
                ]
            });
        }

        // Create and render main App component
        function App() {
            return React.createElement(window.ReactFlow.ReactFlowProvider, null,
                React.createElement(Flow)
            );
        }

        // Mount React application
        window.ReactDOM.render(
            React.createElement(App),
            flowRoot
        );
        
        // Save functionality
        if (saveButton) {
            saveButton.addEventListener('click', async () => {
                try {
                    saveButton.disabled = true;
                    saveButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving...';
                    
                    const nodes = document.querySelectorAll('.paragraph-node');
                    const styleData = {
                        paragraphs: Array.from(nodes).map((node, index) => ({
                            index: index,
                            image_style: node.querySelector('select[class*="node-select"]:first-child').value,
                            voice_style: node.querySelector('select[class*="node-select"]:last-child').value
                        }))
                    };
                    
                    const response = await fetch('/story/update_style', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(styleData)
                    });
                    
                    const data = await response.json();
                    
                    if (!response.ok) {
                        throw new Error(data.error || 'Failed to save customization');
                    }
                    
                    if (data.success) {
                        window.location.href = '/story/generate';
                    }
                } catch (error) {
                    console.error('Error saving customization:', error);
                    alert(error.message || 'Failed to save customization');
                } finally {
                    saveButton.disabled = false;
                    saveButton.innerHTML = 'Save Changes';
                }
            });
        }
    } catch (error) {
        console.error('Failed to initialize story customization:', error);
        flowRoot.innerHTML = '<div class="alert alert-danger m-3">An error occurred while initializing the customization interface.</div>';
    }
});
