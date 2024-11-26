import React, { useState, useCallback, useEffect, Component } from 'react';
import ReactFlow, { 
    Controls, 
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
    Handle,
    Position,
    ReactFlowProvider
} from 'reactflow';
import 'reactflow/dist/style.css';

// Error Boundary Component
class ErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error('ReactFlow Error:', error);
        console.error('Error Info:', errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="error-boundary p-4 text-center">
                    <h3>Something went wrong</h3>
                    <p>{this.state.error?.message}</p>
                    <button 
                        className="btn btn-primary"
                        onClick={() => this.setState({ hasError: false })}
                    >
                        Try Again
                    </button>
                </div>
            );
        }
        return this.props.children;
    }
}

const ParagraphNode = React.memo(({ data }) => {
    return (
        <div className={`paragraph-node ${data.globalStyle || 'realistic'}-style`}>
            <Handle type="target" position={Position.Left} />
            <div className="node-header">Paragraph {data.index + 1}</div>
            <div className="node-content">{data.text}</div>
            <div className="node-controls">
                <div className="d-flex gap-2 mb-2">
                    <button 
                        className="btn btn-primary btn-sm flex-grow-1" 
                        onClick={() => data.onGenerateImage(data.index)}
                        disabled={data.isGeneratingImage}>
                        <i className="bi bi-image me-1"></i>
                        {data.isGeneratingImage ? 'Generating...' : 'Generate Image'}
                    </button>
                    <button 
                        className="btn btn-primary btn-sm flex-grow-1" 
                        onClick={() => data.onGenerateAudio(data.index)}
                        disabled={data.isGeneratingAudio}>
                        <i className="bi bi-volume-up me-1"></i>
                        {data.isGeneratingAudio ? 'Generating...' : 'Generate Audio'}
                    </button>
                </div>
                
                {data.imageUrl && (
                    <>
                        <div className="node-preview mt-2">
                            <div className="image-container position-relative">
                                <img 
                                    src={data.imageUrl} 
                                    alt="Generated preview" 
                                    className="img-fluid rounded"
                                />
                                <div 
                                    className="expand-icon"
                                    onClick={() => data.onExpandImage(data.imageUrl)}
                                >
                                    <i className="bi bi-arrows-fullscreen"></i>
                                </div>
                                <div className="image-prompt-overlay">
                                    {data.imagePrompt}
                                </div>
                            </div>
                        </div>
                        <div className="d-flex gap-2 mt-2">
                            <button 
                                className="btn btn-secondary btn-sm flex-grow-1"
                                onClick={() => data.onRegenerateImage(data.index)}
                                disabled={data.isRegenerating}>
                                <i className="bi bi-arrow-clockwise"></i> Regenerate Image
                            </button>
                        </div>
                    </>
                )}
                
                {data.audioUrl && (
                    <>
                        <div className="audio-player mt-2">
                            <audio controls className="w-100" key={data.audioUrl}>
                                <source src={data.audioUrl} type="audio/wav" />
                                Your browser does not support the audio element.
                            </audio>
                        </div>
                        <button 
                            className="btn btn-secondary btn-sm w-100 mt-2"
                            onClick={() => data.onRegenerateAudio(data.index)}
                            disabled={data.isRegeneratingAudio}>
                            <i className="bi bi-arrow-clockwise"></i> Regenerate Audio
                        </button>
                    </>
                )}
            </div>
            <Handle type="source" position={Position.Right} />
        </div>
    );
});

const nodeTypes = {
    paragraph: ParagraphNode
};

const NodeEditor = ({ story, onStyleUpdate }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [selectedStyle, setSelectedStyle] = useState('realistic');
    const [expandedImage, setExpandedImage] = useState(null);

    const handleRegenerateImage = useCallback(async (index) => {
        try {
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegenerating: true}} : node
            ));

            // Build context from previous paragraphs and their image prompts
            const storyContext = story.paragraphs
                .slice(0, index)
                .map(p => `Text: ${p.text}\n${p.image_prompt ? `Previous Image Prompt: ${p.image_prompt}\n` : ''}`)
                .join('\n\n');

            const response = await fetch('/story/regenerate_image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    index: index,
                    text: story.paragraphs[index].text.trim(),
                    story_context: storyContext,
                    style: selectedStyle
                })
            });

            const data = await response.json();
            if (data.success) {
                setNodes(currentNodes => currentNodes.map(node => 
                    node.id === `p${index}` ? {
                        ...node, 
                        data: {
                            ...node.data,
                            imageUrl: data.image_url,
                            imagePrompt: data.image_prompt,
                            isRegenerating: false
                        }
                    } : node
                ));
            }
        } catch (error) {
            console.error('Error regenerating image:', error);
            alert('Failed to regenerate image');
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegenerating: false}} : node
            ));
        }
    }, [story?.paragraphs, selectedStyle, setNodes]);

    const handleRegenerateAudio = useCallback(async (index) => {
        try {
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegeneratingAudio: true}} : node
            ));

            const response = await fetch('/story/regenerate_audio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    index: index,
                    text: story.paragraphs[index].text.trim()
                })
            });

            const data = await response.json();
            if (data.success) {
                setNodes(currentNodes => currentNodes.map(node => 
                    node.id === `p${index}` ? {
                        ...node, 
                        data: {
                            ...node.data,
                            audioUrl: data.audio_url,
                            isRegeneratingAudio: false
                        }
                    } : node
                ));
            }
        } catch (error) {
            console.error('Error regenerating audio:', error);
            alert('Failed to regenerate audio');
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegeneratingAudio: false}} : node
            ));
        }
    }, [story?.paragraphs, setNodes]);

    const handleGenerateImage = useCallback(async (index) => {
        if (!story?.paragraphs?.[index]?.text) {
            console.error('No text found for paragraph');
            return;
        }

        try {
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGeneratingImage: true}} : node
            ));

            const storyContext = story.paragraphs
                .slice(0, index)
                .map(p => `Text: ${p.text}\n${p.image_prompt ? `Previous Image Prompt: ${p.image_prompt}\n` : ''}`)
                .join('\n\n');

            const response = await fetch('/story/generate_image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    index: index,
                    text: story.paragraphs[index].text.trim(),
                    story_context: storyContext,
                    style: selectedStyle
                })
            });

            if (!response.ok) throw new Error('Failed to generate image');
            
            const data = await response.json();
            if (data.success) {
                setNodes(currentNodes => 
                    currentNodes.map(node => 
                        node.id === `p${index}` ? {
                            ...node, 
                            data: {
                                ...node.data,
                                imageUrl: data.image_url,
                                imagePrompt: data.image_prompt,
                                isGeneratingImage: false
                            }
                        } : node
                    )
                );
            }
        } catch (error) {
            console.error('Error generating image:', error);
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGeneratingImage: false}} : node
            ));
            alert(error.message || 'Failed to generate image');
        }
    }, [story?.paragraphs, selectedStyle, setNodes]);

    const handleGenerateAudio = useCallback(async (index) => {
        if (!story?.paragraphs?.[index]?.text) {
            console.error('No text found for paragraph');
            return;
        }

        try {
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGeneratingAudio: true}} : node
            ));

            const response = await fetch('/story/generate_audio', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    index: index,
                    text: story.paragraphs[index].text.trim()
                })
            });

            if (!response.ok) throw new Error('Failed to generate audio');
            
            const data = await response.json();
            if (data.success) {
                setNodes(currentNodes => 
                    currentNodes.map(node => 
                        node.id === `p${index}` ? {
                            ...node, 
                            data: {
                                ...node.data,
                                audioUrl: data.audio_url,
                                isGeneratingAudio: false
                            }
                        } : node
                    )
                );
            }
        } catch (error) {
            console.error('Error generating audio:', error);
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGeneratingAudio: false}} : node
            ));
            alert(error.message || 'Failed to generate audio');
        }
    }, [story?.paragraphs, setNodes]);

    const handleStyleChange = useCallback((event) => {
        const newStyle = event.target.value;
        setSelectedStyle(newStyle);
        
        setNodes(currentNodes => currentNodes.map(node => ({
            ...node,
            data: {
                ...node.data,
                globalStyle: newStyle
            }
        })));
        
        const updatedParagraphs = story?.paragraphs?.map((p, index) => ({
            index,
            image_style: newStyle
        })) || [];
        
        onStyleUpdate(updatedParagraphs);
    }, [setNodes, story?.paragraphs, onStyleUpdate]);

    useEffect(() => {
        console.log('Initializing nodes from story data');
        if (!story?.paragraphs) {
            console.error('No story paragraphs found');
            return;
        }
        
        try {

        const paragraphNodes = story.paragraphs.map((para, index) => ({
            id: `p${index}`,
            type: 'paragraph',
            position: { 
                x: (index % 2) * 300 + 50,
                y: Math.floor(index / 2) * 250 + 50
            },
            sourcePosition: 'right',
            targetPosition: 'left',
            connectable: true,
            data: {
                index,
                text: para.text,
                globalStyle: selectedStyle,
                imageUrl: para.image_url,
                imagePrompt: para.image_prompt,
                audioUrl: para.audio_url,
                onGenerateImage: handleGenerateImage,
                onGenerateAudio: handleGenerateAudio,
                onRegenerateImage: handleRegenerateImage,
                onRegenerateAudio: handleRegenerateAudio,
                onExpandImage: setExpandedImage,
                isGeneratingImage: false,
                isGeneratingAudio: false,
                isRegenerating: false,
                isRegeneratingAudio: false
            }
        }));

        console.log('Setting nodes:', paragraphNodes.length);
            setNodes(paragraphNodes);
        } catch (error) {
            console.error('Error initializing nodes:', error);
        }
    }, [story?.paragraphs, selectedStyle, handleGenerateImage, handleGenerateAudio, handleRegenerateImage, handleRegenerateAudio, setNodes]);

    useEffect(() => {
        console.log('Setting up style change event listeners');
        let mounted = true;
        const radioButtons = document.querySelectorAll('input[name="imageStyle"]');
        const handler = (e) => {
            if (mounted) {
                console.log('Style changed to:', e.target.value);
                handleStyleChange(e);
            }
        };
        
        radioButtons.forEach(radio => {
            radio.addEventListener('change', handler);
        });

        return () => {
            console.log('Cleaning up style change event listeners');
            mounted = false;
            radioButtons.forEach(radio => {
                radio.removeEventListener('change', handler);
            });
        };
    }, [handleStyleChange]);

    const onConnect = useCallback((params) => {
        if (params.source === params.target) return;
        
        const edge = {
            ...params,
            type: 'smoothstep',
            animated: true,
            style: { 
                stroke: 'var(--bs-primary)',
                strokeWidth: 2,
            }
        };
        
        setEdges(currentEdges => addEdge(edge, currentEdges));
    }, [setEdges]);

    console.log('Initializing NodeEditor with:', { 
        nodesCount: nodes.length, 
        edgesCount: edges.length,
        selectedStyle 
    });

    return (
        <>
            <div style={{ width: '100%', height: '600px' }} className="node-editor-root">
                <ErrorBoundary>
                    <ReactFlowProvider>
                        <ReactFlow
                            nodes={nodes}
                            edges={edges}
                            onNodesChange={onNodesChange}
                            onEdgesChange={onEdgesChange}
                            onConnect={onConnect}
                            nodeTypes={nodeTypes}
                            fitView
                            style={{ background: 'var(--bs-dark)' }}
                            minZoom={0.1}
                            maxZoom={4}
                            defaultViewport={{ x: 0, y: 0, zoom: 1 }}
                            connectOnClick={true}
                            onError={(error) => console.error('ReactFlow Error:', error)}
                        >
                            <Background />
                            <Controls />
                        </ReactFlow>
                    </ReactFlowProvider>
                </ErrorBoundary>
            </div>
            
            {expandedImage && (
                <div className="modal-backdrop" onClick={() => setExpandedImage(null)}>
                    <div className="preview-modal" onClick={e => e.stopPropagation()}>
                        <button 
                            type="button" 
                            className="close-button"
                            onClick={() => setExpandedImage(null)}
                        >
                            ×
                        </button>
                        <div className="preview-content">
                            <img src={expandedImage} alt="Full preview" />
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default React.memo(NodeEditor);