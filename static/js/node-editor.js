import React, { useState, useCallback, useEffect } from 'react';
import ReactFlow, { 
    Controls, 
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
    Handle,
    Position
} from 'reactflow';
import 'reactflow/dist/style.css';

const ParagraphNode = React.memo(({ data }) => {
    const handleCopyPrompt = useCallback((e) => {
        e.stopPropagation();
        if (data.imagePrompt) {
            navigator.clipboard.writeText(data.imagePrompt)
                .then(() => {
                    // Could add a toast notification here
                    console.log('Prompt copied to clipboard');
                })
                .catch(err => console.error('Failed to copy prompt:', err));
        }
    }, [data.imagePrompt]);

    return (
        <div className={`paragraph-node ${data.globalStyle || 'realistic'}-style`}>
            <Handle type="target" position={Position.Left} />
            <div className="node-header">Paragraph {data.index + 1}</div>
            <div className="node-content">{data.text}</div>
            <div className="node-controls">
                <button 
                    className="btn btn-primary btn-sm w-100 mb-2" 
                    onClick={() => data.onGenerateCard(data.index)}
                    disabled={data.isGenerating}>
                    {data.isGenerating ? 'Generating...' : 'Generate Card'}
                </button>
                
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
                                    <button 
                                        className="copy-prompt-btn"
                                        onClick={handleCopyPrompt}
                                        title="Copy prompt to clipboard"
                                    >
                                        <i className="bi bi-clipboard"></i>
                                    </button>
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

            const response = await fetch('/story/regenerate_image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    index: index,
                    text: story.paragraphs[index].text.trim(),
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

    const handleGenerateCard = useCallback(async (index) => {
        if (!story?.paragraphs?.[index]?.text) {
            console.error('No text found for paragraph');
            return;
        }

        try {
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGenerating: true}} : node
            ));

            const storyContext = story.paragraphs
                .map(p => p.text)
                .join('\n\n');

            const response = await fetch('/story/generate_cards', {
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

            if (!response.ok) throw new Error('Failed to generate card');
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const {done, value} = await reader.read();
                if (done) break;
                
                buffer += decoder.decode(value, {stream: true});
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';
                
                for (const line of lines) {
                    if (!line.trim()) continue;
                    
                    try {
                        const data = JSON.parse(line);
                        if (data.type === 'paragraph') {
                            setNodes(currentNodes => 
                                currentNodes.map(node => 
                                    node.id === `p${index}` ? {
                                        ...node, 
                                        data: {
                                            ...node.data,
                                            imageUrl: data.data.image_url,
                                            imagePrompt: data.data.image_prompt,
                                            audioUrl: data.data.audio_url,
                                            isGenerating: false
                                        }
                                    } : node
                                )
                            );
                        } else if (data.type === 'error') {
                            throw new Error(data.message);
                        }
                    } catch (parseError) {
                        console.error('Error parsing JSON:', parseError);
                    }
                }
            }
        } catch (error) {
            console.error('Error generating card:', error);
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGenerating: false}} : node
            ));
            alert(error.message || 'Failed to generate card');
        }
    }, [story?.paragraphs, selectedStyle, setNodes]);

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
        if (!story?.paragraphs) {
            console.error('No story paragraphs found');
            return;
        }

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
                onGenerateCard: handleGenerateCard,
                onRegenerateImage: handleRegenerateImage,
                onRegenerateAudio: handleRegenerateAudio,
                onExpandImage: setExpandedImage,
                isGenerating: false,
                isRegenerating: false,
                isRegeneratingAudio: false
            }
        }));

        setNodes(paragraphNodes);
    }, [story?.paragraphs, selectedStyle, handleGenerateCard, handleRegenerateImage, handleRegenerateAudio, setNodes]);

    useEffect(() => {
        const radioButtons = document.querySelectorAll('input[name="imageStyle"]');
        const handler = (e) => handleStyleChange(e);
        
        radioButtons.forEach(radio => {
            radio.addEventListener('change', handler);
        });

        return () => {
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

    return (
        <>
            <div style={{ width: '100%', height: '600px' }} className="node-editor-root">
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
                >
                    <Background />
                    <Controls />
                </ReactFlow>
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