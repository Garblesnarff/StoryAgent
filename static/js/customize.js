// Error boundary component for React
class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error('Node Editor Error:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return React.createElement('div', { className: 'alert alert-danger' },
                React.createElement('h4', { className: 'alert-heading' }, 'Error Loading Node Editor'),
                React.createElement('p', null, this.state.error?.message || 'An unknown error occurred'),
                React.createElement('hr'),
                React.createElement('p', { className: 'mb-0' }, 'Please try refreshing the page')
            );
        }
        return this.props.children;
    }
}

// Node editor component
function NodeEditor({ storyData }) {
    const [nodes, setNodes] = React.useState([]);
    const [edges, setEdges] = React.useState([]);

    React.useEffect(() => {
        const paragraphNodes = storyData.paragraphs.map((paragraph, index) => ({
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
        }));

        const styleNodes = storyData.paragraphs.map((paragraph, index) => ({
            id: `style${index}`,
            type: 'default',
            position: { x: 500, y: index * 200 },
            data: {
                label: React.createElement('div', { className: 'effect-node' },
                    React.createElement('div', { className: 'node-header' }, 'Style Options'),
                    React.createElement('div', null, [
                        React.createElement('div', { key: 'image-style', className: 'node-select-group' }, [
                            React.createElement('label', { className: 'node-select-label' }, 'Image Style'),
                            React.createElement('select', {
                                className: 'node-select',
                                defaultValue: paragraph.image_style || 'realistic',
                                onChange: (e) => {
                                    window.styleData = window.styleData || { paragraphs: [] };
                                    window.styleData.paragraphs[index] = window.styleData.paragraphs[index] || { index };
                                    window.styleData.paragraphs[index].image_style = e.target.value;
                                }
                            }, [
                                React.createElement('option', { value: 'realistic' }, 'Realistic'),
                                React.createElement('option', { value: 'artistic' }, 'Artistic'),
                                React.createElement('option', { value: 'fantasy' }, 'Fantasy')
                            ])
                        ]),
                        React.createElement('div', { key: 'voice-style', className: 'node-select-group' }, [
                            React.createElement('label', { className: 'node-select-label' }, 'Voice Style'),
                            React.createElement('select', {
                                className: 'node-select',
                                defaultValue: paragraph.voice_style || 'neutral',
                                onChange: (e) => {
                                    window.styleData = window.styleData || { paragraphs: [] };
                                    window.styleData.paragraphs[index] = window.styleData.paragraphs[index] || { index };
                                    window.styleData.paragraphs[index].voice_style = e.target.value;
                                }
                            }, [
                                React.createElement('option', { value: 'neutral' }, 'Neutral'),
                                React.createElement('option', { value: 'dramatic' }, 'Dramatic'),
                                React.createElement('option', { value: 'cheerful' }, 'Cheerful')
                            ])
                        ]),
                        React.createElement('div', { key: 'mood-enhancement', className: 'node-select-group' }, [
                            React.createElement('label', { className: 'node-select-label' }, 'Mood Enhancement'),
                            React.createElement('select', {
                                className: 'node-select',
                                defaultValue: paragraph.mood_enhancement || 'none',
                                onChange: (e) => {
                                    window.styleData = window.styleData || { paragraphs: [] };
                                    window.styleData.paragraphs[index] = window.styleData.paragraphs[index] || { index };
                                    window.styleData.paragraphs[index].mood_enhancement = e.target.value;
                                }
                            }, [
                                React.createElement('option', { value: 'none' }, 'None'),
                                React.createElement('option', { value: 'intense' }, 'Intense'),
                                React.createElement('option', { value: 'subtle' }, 'Subtle'),
                                React.createElement('option', { value: 'dreamy' }, 'Dreamy')
                            ])
                        ])
                    ])
                )
            }
        }));

        const newEdges = storyData.paragraphs.map((_, index) => ({
            id: `e${index}`,
            source: `p${index}`,
            target: `style${index}`,
            type: 'smoothstep',
            animated: true
        }));

        setNodes([...paragraphNodes, ...styleNodes]);
        setEdges(newEdges);
    }, [storyData]);

    return React.createElement(window.ReactFlow.ReactFlowProvider, null,
        React.createElement(window.ReactFlow.ReactFlow, {
            nodes,
            edges,
            fitView: true,
            nodesDraggable: true,
            nodesConnectable: false,
            defaultViewport: { x: 0, y: 0, zoom: 0.75 }
        },
        React.createElement(window.ReactFlow.Background, {
            color: '#aaa',
            gap: 16,
            size: 1
        }),
        React.createElement(window.ReactFlow.Controls))
    );
}

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('node-editor');
    if (!container) {
        console.error('Node editor container not found');
        return;
    }

    // Create root element
    const root = document.createElement('div');
    root.style.width = '100%';
    root.style.height = '100%';
    container.appendChild(root);

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

                const response = await fetch('/story/update_style', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
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
                saveButton.innerHTML = 'Generate Cards';
            }
        });
    }

    // Parse story data
    let storyData;
    try {
        storyData = JSON.parse(container.dataset.story);
        if (!storyData || !storyData.paragraphs) {
            throw new Error('Invalid story data format');
        }
    } catch (error) {
        console.error('Failed to parse story data:', error);
        root.innerHTML = `
            <div class="alert alert-danger">
                <h4 class="alert-heading">Failed to load story data</h4>
                <p>${error.message}</p>
            </div>
        `;
        return;
    }

    // Initialize editor with proper error handling
    const initializeEditor = () => {
        try {
            ReactDOM.render(
                React.createElement(ErrorBoundary, null,
                    React.createElement(NodeEditor, { storyData })
                ),
                root
            );
        } catch (error) {
            console.error('Failed to initialize node editor:', error);
            root.innerHTML = `
                <div class="alert alert-danger">
                    <h4 class="alert-heading">Failed to initialize node editor</h4>
                    <p>${error.message}</p>
                </div>
            `;
        }
    };

    // Check for ReactFlow with timeout
    let attempts = 0;
    const maxAttempts = 50;
    const checkInterval = 100;

    const checkReactFlow = setInterval(() => {
        attempts++;
        if (window.ReactFlow) {
            clearInterval(checkReactFlow);
            console.log('ReactFlow loaded successfully');
            initializeEditor();
        } else if (attempts >= maxAttempts) {
            clearInterval(checkReactFlow);
            console.error('ReactFlow failed to load');
            root.innerHTML = `
                <div class="alert alert-danger">
                    <h4 class="alert-heading">Failed to load ReactFlow</h4>
                    <p>The required library could not be loaded. Please check your internet connection and try again.</p>
                </div>
            `;
        }
    }, checkInterval);
});
