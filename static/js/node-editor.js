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

const ParagraphNode = React.memo(({ data = {} }) => {
    const {
        index,
        text,
        imageUrl,
        audioUrl,
        imagePrompt,
        onGenerateImage,
        onGenerateAudio,
        onRegenerateImage,
        onRegenerateAudio,
        onExpandImage,
        isGeneratingImage,
        isGeneratingAudio,
        isRegenerating,
        isRegeneratingAudio,
        globalStyle
    } = data;
    return (
        <div className={`paragraph-node ${globalStyle || 'realistic'}-style`}>
            <Handle type="target" position={Position.Left} />
            <div className="node-header">Paragraph {index + 1}</div>
            <div className="node-content">{text}</div>
            <div className="node-controls">
                <div className="generation-controls mb-2">
                    <div className="generation-control">
                        <button 
                            className="btn btn-primary btn-sm w-100 mb-1" 
                            onClick={() => data.onGenerateImage(data.index)}
                            disabled={data.isGeneratingImage}>
                            <i className="bi bi-image"></i>
                            {data.isGeneratingImage ? ' Generating...' : ' Generate Image'}
                        </button>
                        {data.isGeneratingImage && (
                            <div className="progress" style={{ height: '3px' }}>
                                <div className="progress-bar progress-bar-striped progress-bar-animated" 
                                    role="progressbar" 
                                    style={{ width: `${data.imageProgress || 0}%` }}
                                    aria-valuenow={data.imageProgress || 0} 
                                    aria-valuemin="0" 
                                    aria-valuemax="100">
                                </div>
                            </div>
                        )}
                    </div>
                    <div className="generation-control mt-2">
                        <button 
                            className="btn btn-primary btn-sm w-100 mb-1" 
                            onClick={() => data.onGenerateAudio(data.index)}
                            disabled={data.isGeneratingAudio}>
                            <i className="bi bi-volume-up"></i>
                            {data.isGeneratingAudio ? ' Generating...' : ' Generate Audio'}
                        </button>
                        {data.isGeneratingAudio && (
                            <div className="progress" style={{ height: '3px' }}>
                                <div className="progress-bar progress-bar-striped progress-bar-animated" 
                                    role="progressbar" 
                                    style={{ width: `${data.audioProgress || 0}%` }}
                                    aria-valuenow={data.audioProgress || 0} 
                                    aria-valuemin="0" 
                                    aria-valuemax="100">
                                </div>
                            </div>
                        )}
                    </div>
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
            // Initialize generation state with progress
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {
                    ...node, 
                    data: {
                        ...node.data, 
                        isGeneratingImage: true,
                        imageProgress: 0
                    }
                } : node
            ));

            // Start progress animation
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress = Math.min(progress + 2, 90); // Don't reach 100% until complete
                setNodes(currentNodes => currentNodes.map(node =>
                    node.id === `p${index}` ? {
                        ...node,
                        data: {
                            ...node.data,
                            imageProgress: progress
                        }
                    } : node
                ));
            }, 100);

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

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Failed to generate image');
            }
            
            if (data.success) {
                clearInterval(progressInterval);
                setNodes(currentNodes => 
                    currentNodes.map(node => 
                        node.id === `p${index}` ? {
                            ...node, 
                            data: {
                                ...node.data,
                                imageUrl: data.image_url,
                                imagePrompt: data.image_prompt,
                                isGeneratingImage: false,
                                imageProgress: 100
                            }
                        } : node
                    )
                );
            } else {
                throw new Error(data.error || 'Failed to generate image');
            }
        } catch (error) {
            console.error('Error generating image:', error);
            clearInterval(progressInterval);
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {
                    ...node, 
                    data: {
                        ...node.data, 
                        isGeneratingImage: false,
                        imageProgress: 0
                    }
                } : node
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
            // Initialize generation state with progress
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {
                    ...node, 
                    data: {
                        ...node.data, 
                        isGeneratingAudio: true,
                        audioProgress: 0
                    }
                } : node
            ));

            // Start progress animation
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress = Math.min(progress + 2, 90); // Don't reach 100% until complete
                setNodes(currentNodes => currentNodes.map(node =>
                    node.id === `p${index}` ? {
                        ...node,
                        data: {
                            ...node.data,
                            audioProgress: progress
                        }
                    } : node
                ));
            }, 100);

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

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || 'Failed to generate audio');
            }
            
            if (data.success) {
                clearInterval(progressInterval);
                setNodes(currentNodes => 
                    currentNodes.map(node => 
                        node.id === `p${index}` ? {
                            ...node, 
                            data: {
                                ...node.data,
                                audioUrl: data.audio_url,
                                isGeneratingAudio: false,
                                audioProgress: 100
                            }
                        } : node
                    )
                );
            } else {
                throw new Error(data.error || 'Failed to generate audio');
            }
        } catch (error) {
            console.error('Error generating audio:', error);
            clearInterval(progressInterval);
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {
                    ...node, 
                    data: {
                        ...node.data, 
                        isGeneratingAudio: false,
                        audioProgress: 0
                    }
                } : node
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

        setNodes(paragraphNodes);
    }, [story?.paragraphs, selectedStyle, handleGenerateImage, handleGenerateAudio, handleRegenerateImage, handleRegenerateAudio, setNodes]);

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