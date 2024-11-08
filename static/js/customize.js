// Node editor components
const NodeEditor = React.createClass({
    getInitialState() {
        return {
            nodes: [],
            edges: []
        };
    },

    componentDidMount() {
        const paragraphs = this.props.paragraphs;
        
        // Create paragraph nodes
        const paragraphNodes = paragraphs.map((p, i) => ({
            id: `p-${i}`,
            type: 'paragraph',
            position: { x: 100, y: i * 200 },
            data: { index: i, text: p.text }
        }));

        // Create effect nodes
        const effectNodes = paragraphs.map((p, i) => [
            {
                id: `img-${i}`,
                type: 'effect',
                position: { x: 400, y: i * 200 },
                data: {
                    type: 'Image Style',
                    options: [
                        { value: 'realistic', label: 'Realistic' },
                        { value: 'artistic', label: 'Artistic' },
                        { value: 'fantasy', label: 'Fantasy' }
                    ],
                    onChange: (e) => this.handleStyleChange(i, 'image_style', e.target.value)
                }
            },
            {
                id: `voice-${i}`,
                type: 'effect',
                position: { x: 600, y: i * 200 },
                data: {
                    type: 'Voice Style',
                    options: [
                        { value: 'neutral', label: 'Neutral' },
                        { value: 'dramatic', label: 'Dramatic' },
                        { value: 'emotional', label: 'Emotional' }
                    ],
                    onChange: (e) => this.handleStyleChange(i, 'voice_style', e.target.value)
                }
            }
        ]).flat();

        // Create edges
        const edges = paragraphs.map((p, i) => [
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
        ]).flat();

        this.setState({
            nodes: [...paragraphNodes, ...effectNodes],
            edges: edges
        });
    },

    handleStyleChange(index, styleType, value) {
        window.styleData = window.styleData || { paragraphs: [] };
        if (!window.styleData.paragraphs[index]) {
            window.styleData.paragraphs[index] = { index };
        }
        window.styleData.paragraphs[index][styleType] = value;
    },

    render() {
        return React.createElement('div', 
            { style: { width: '100%', height: '400px' } },
            React.createElement(ReactFlow, {
                nodes: this.state.nodes,
                edges: this.state.edges,
                nodeTypes: {
                    paragraph: ParagraphNode,
                    effect: EffectNode
                },
                fitView: true
            })
        );
    }
});

const ParagraphNode = React.createClass({
    render() {
        const { data } = this.props;
        return React.createElement('div', 
            { className: 'paragraph-node' },
            React.createElement('div', 
                { className: 'node-header' },
                `Paragraph ${data.index + 1}`
            ),
            React.createElement('div', 
                { className: 'node-content' },
                `${data.text.substring(0, 100)}...`
            )
        );
    }
});

const EffectNode = React.createClass({
    render() {
        const { data } = this.props;
        return React.createElement('div',
            { className: 'effect-node' },
            React.createElement('div',
                { className: 'node-header' },
                data.type
            ),
            React.createElement('select',
                {
                    className: 'node-select',
                    onChange: data.onChange
                },
                data.options.map(opt =>
                    React.createElement('option',
                        {
                            key: opt.value,
                            value: opt.value
                        },
                        opt.label
                    )
                )
            )
        );
    }
});

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('node-editor');
    const storyData = JSON.parse(container.dataset.story);
    
    ReactDOM.render(
        React.createElement(NodeEditor, { paragraphs: storyData.paragraphs }),
        container
    );
    
    // Handle save and generation
    const saveButton = document.getElementById('save-customization');
    saveButton?.addEventListener('click', async () => {
        try {
            saveButton.disabled = true;
            const response = await fetch('/story/update_style', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(window.styleData || { paragraphs: [] })
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
        }
    });
});
