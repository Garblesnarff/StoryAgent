import React, { useCallback, useEffect, useState } from 'react';
import ReactFlow, { 
    useNodesState, 
    useEdgesState, 
    addEdge, 
    Handle, 
    Position,
    Background,
    Controls
} from 'reactflow';
import 'reactflow/dist/style.css';

const ParagraphNode = React.memo(({ data }) => {
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
        imageProgress,
        audioProgress,
        imageError,
        audioError,
        onDelete
    } = data;

    const nodeClass = `paragraph-node ${data.globalStyle || 'realistic'}-style`;
    return (
        <div className={nodeClass}>
            <Handle type="target" position={Position.Left} />
            <div className="node-content">
                <div className="text-content mb-2">
                    {text}
                </div>                
                <div className="generation-controls mb-2">
                    <div className="generation-control">
                        <button 
                            className="btn btn-primary btn-sm w-100 mb-1" 
                            onClick={() => onGenerateImage(index)}
                            disabled={isGeneratingImage || isRegenerating}>
                            <i className="bi bi-image me-1"></i>
                            {isGeneratingImage ? ' Generating...' : (isRegenerating ? ' Regenerating...' : ' Generate Image')}
                        </button>
                        {imageError && (
                            <div className="alert alert-danger p-2 mb-2">
                                <small>{imageError}</small>
                                <button 
                                    className="btn btn-sm btn-outline-danger w-100 mt-1"
                                    onClick={() => onGenerateImage(index, true)}>
                                    <i className="bi bi-arrow-clockwise me-1"></i>
                                    Retry
                                </button>
                            </div>
                        )}
                        <div className="progress mt-1" style={{ height: '4px', opacity: (isGeneratingImage || isRegenerating) ? 1 : 0, transition: 'opacity 0.3s ease' }}>
                            <div 
                                className="progress-bar progress-bar-striped progress-bar-animated bg-primary" 
                                role="progressbar" 
                                style={{ width: `${imageProgress || 0}%` }}
                                aria-valuenow={imageProgress || 0} 
                                aria-valuemin="0" 
                                aria-valuemax="100">
                            </div>
                        </div>
                    </div>                    
                    <div className="generation-control mt-2">
                        <button 
                            className="btn btn-primary btn-sm w-100 mb-1" 
                            onClick={() => onGenerateAudio(index)}
                            disabled={isGeneratingAudio || isRegeneratingAudio}>
                            <i className="bi bi-volume-up me-1"></i>
                            {isGeneratingAudio ? ' Generating...' : (isRegeneratingAudio ? ' Regenerating...' : ' Generate Audio')}
                        </button>
                        {audioError && (
                            <div className="alert alert-danger p-2 mb-2">
                                <small>{audioError}</small>
                                <button 
                                    className="btn btn-sm btn-outline-danger w-100 mt-1"
                                    onClick={() => onGenerateAudio(index, true)}>
                                    <i className="bi bi-arrow-clockwise me-1"></i>
                                    Retry
                                </button>
                            </div>
                        )}
                        <div className="progress mt-1" style={{ height: '4px', opacity: (isGeneratingAudio || isRegeneratingAudio) ? 1 : 0, transition: 'opacity 0.3s ease' }}>
                            <div 
                                className="progress-bar progress-bar-striped progress-bar-animated bg-primary" 
                                role="progressbar" 
                                style={{ width: `${audioProgress || 0}%` }}
                                aria-valuenow={audioProgress || 0} 
                                aria-valuemin="0" 
                                aria-valuemax="100">
                            </div>
                        </div>
                    </div>
                </div>                
                {imageUrl && !imageError && (
                    <>
                        <div className="node-preview mt-2">
                            <div className="image-container position-relative">
                                <img 
                                    src={imageUrl} 
                                    alt="Generated preview" 
                                    className="img-fluid rounded"
                                />
                                <div 
                                    className="expand-icon"
                                    onClick={() => onExpandImage(imageUrl)}
                                >
                                    <i className="bi bi-arrows-fullscreen"></i>
                                </div>
                                <div 
                                    className="copy-prompt-icon"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        navigator.clipboard.writeText(imagePrompt).then(() => {
                                            const toast = document.createElement('div');
                                            toast.className = 'toast-notification';
                                            toast.innerHTML = `
                                                <i class="bi bi-clipboard-check me-2"></i>
                                                Prompt copied to clipboard!
                                            `;
                                            document.body.appendChild(toast);                                            
                                            void toast.offsetHeight;                                            
                                            requestAnimationFrame(() => {
                                                toast.classList.add('show');
                                            });                                            
                                            const button = e.currentTarget;
                                            if (button) {
                                                button.innerHTML = '<i class="bi bi-check"></i>';
                                                button.style.background = 'rgba(40, 167, 69, 0.8)';                                                
                                                setTimeout(() => {
                                                    button.innerHTML = '<i class="bi bi-clipboard"></i>';
                                                    button.style.background = '';                                                    
                                                    toast.classList.remove('show');
                                                    setTimeout(() => {
                                                        toast.remove();
                                                    }, 300);
                                                }, 2000);
                                            }
                                        });
                                    }}
                                    title="Copy image prompt"
                                >
                                    <i className="bi bi-clipboard"></i>
                                </div>
                                <div className="image-prompt-overlay">
                                    {imagePrompt}
                                </div>
                            </div>
                        </div>
                        <div className="d-flex gap-2 mt-2">
                            <button 
                                className="btn btn-secondary btn-sm flex-grow-1"
                                onClick={() => onRegenerateImage(index)}
                                disabled={isRegenerating}>
                                <i className="bi bi-arrow-clockwise"></i> Regenerate Image
                            </button>
                        </div>
                    </>
                )}                
                {audioUrl && !audioError && (
                    <>
                        <div className="audio-player mt-2">
                            <audio controls className="w-100" key={audioUrl}>
                                <source src={audioUrl} type="audio/wav" />
                                Your browser does not support the audio element.
                            </audio>
                        </div>
                        <button 
                            className="btn btn-secondary btn-sm w-100 mt-2"
                            onClick={() => onRegenerateAudio(index)}
                            disabled={isRegeneratingAudio}>
                            <i className="bi bi-arrow-clockwise"></i> Regenerate Audio
                        </button>
                    </>
                )}
                <button onClick={() => onDelete(index)}>Delete</button>
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
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    const loadPage = async (pageNumber) => {
        try {
            setIsLoading(true);
            setError(null);
            const response = await fetch(`/story/get_chunks/${pageNumber}`);
            if (!response.ok) {
                throw new Error('Failed to load page');
            }

            const data = await response.json();
            setCurrentPage(data.current_page);
            setTotalPages(data.total_pages);

            const paragraphNodes = data.paragraphs.map((chunk, index) => ({
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
                    index: index + ((pageNumber - 1) * 10), 
                    text: chunk.text,
                    globalStyle: selectedStyle,
                    imageUrl: chunk.image_url,
                    imagePrompt: chunk.image_prompt,
                    audioUrl: chunk.audio_url,
                    onGenerateImage: handleGenerateImage,
                    onGenerateAudio: handleGenerateAudio,
                    onRegenerateImage: handleRegenerateImage,
                    onRegenerateAudio: handleRegenerateAudio,
                    onExpandImage: setExpandedImage,
                    isGeneratingImage: false,
                    isGeneratingAudio: false,
                    isRegenerating: false,
                    isRegeneratingAudio: false,
                    imageProgress: 0,
                    audioProgress: 0,
                    imageError: null,
                    audioError: null,
                    onDelete: handleDelete
                }
            }));

            setNodes(paragraphNodes);
            setEdges([]); 
        } catch (error) {
            console.error('Error loading page:', error);
            setError(error.message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = useCallback((index) => {
        setNodes(prevNodes => prevNodes.filter(node => node.data.index !== index));
    }, []);

    const handleRegenerateImage = useCallback(async (index) => {
        try {
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {
                    ...node, 
                    data: {
                        ...node.data, 
                        isRegenerating: true,
                        imageProgress: 0,
                        imageError: null
                    }
                } : node
            ));            
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress = Math.min(progress + 2, 90);
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
            clearInterval(progressInterval);            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to regenerate image');
            }            
            if (data.success) {
                setNodes(currentNodes => currentNodes.map(node => 
                    node.id === `p${index}` ? {
                        ...node, 
                        data: {
                            ...node.data,
                            imageUrl: data.image_url,
                            imagePrompt: data.image_prompt,
                            isRegenerating: false,
                            imageProgress: 100,
                            imageError: null
                        }
                    } : node
                ));
            } else {
                throw new Error(data.error || 'Failed to regenerate image');
            }
        } catch (error) {
            console.error('Error regenerating image:', error);
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {
                    ...node, 
                    data: {
                        ...node.data, 
                        isRegenerating: false,
                        imageProgress: 0,
                        imageError: error.message || 'Failed to regenerate image. Please try again.'
                    }
                } : node
            ));
        }
    }, [story?.paragraphs, selectedStyle, setNodes]);

    const handleRegenerateAudio = useCallback(async (index) => {
        try {
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {
                    ...node, 
                    data: {
                        ...node.data, 
                        isRegeneratingAudio: true,
                        audioProgress: 0,
                        audioError: null
                    }
                } : node
            ));            
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress = Math.min(progress + 2, 90);
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
            clearInterval(progressInterval);            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to regenerate audio');
            }            
            if (data.success) {
                setNodes(currentNodes => currentNodes.map(node => 
                    node.id === `p${index}` ? {
                        ...node, 
                        data: {
                            ...node.data,
                            audioUrl: data.audio_url,
                            isRegeneratingAudio: false,
                            audioProgress: 100,
                            audioError: null
                        }
                    } : node
                ));
            } else {
                throw new Error(data.error || 'Failed to regenerate audio');
            }
        } catch (error) {
            console.error('Error regenerating audio:', error);
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {
                    ...node, 
                    data: {
                        ...node.data, 
                        isRegeneratingAudio: false,
                        audioProgress: 0,
                        audioError: error.message || 'Failed to regenerate audio. Please try again.'
                    }
                } : node
            ));
        }
    }, [story?.paragraphs, setNodes]);

    const handleGenerateImage = useCallback(async (index, isRetry = false) => {
        if (!story?.paragraphs?.[index]?.text) {
            console.error('No text found for paragraph');
            return;
        }        
        try {
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {
                    ...node, 
                    data: {
                        ...node.data, 
                        isGeneratingImage: true,
                        imageProgress: 0,
                        imageError: null
                    }
                } : node
            ));            
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress = Math.min(progress + 2, 90);
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
                    style: selectedStyle,
                    is_retry: isRetry
                })
            });            
            const data = await response.json();
            clearInterval(progressInterval);            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to generate image');
            }            
            if (data.success) {
                const updatedNodes = [...nodes];
                const nodeIndex = updatedNodes.findIndex(n => n.id === `p${index}`);
                if (nodeIndex !== -1) {
                    updatedNodes[nodeIndex] = {
                        ...updatedNodes[nodeIndex],
                        data: {
                            ...updatedNodes[nodeIndex].data,
                            imageUrl: data.image_url,
                            imagePrompt: data.image_prompt,
                            isGeneratingImage: false,
                            imageProgress: 100,
                            imageError: null
                        }
                    };
                    setNodes(updatedNodes);
                }
            } else {
                throw new Error(data.error || 'Failed to generate image');
            }
        } catch (error) {
            console.error('Error generating image:', error);
            clearInterval(progressInterval);
            const errorMessage = error.response?.data?.error || error.message || 'Failed to generate image. Please try again.';
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {
                    ...node, 
                    data: {
                        ...node.data,
                        isGeneratingImage: false,
                        imageProgress: 0,
                        imageError: errorMessage
                    }
                } : node
            ));

            // Show error toast
            const toast = document.createElement('div');
            toast.className = 'toast-notification error';
            toast.innerHTML = `<i class="bi bi-exclamation-circle me-2"></i>${errorMessage}`;
            document.body.appendChild(toast);
            requestAnimationFrame(() => toast.classList.add('show'));
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, 5000);
        }
    }, [story?.paragraphs, selectedStyle, setNodes]);

    const handleGenerateAudio = useCallback(async (index, isRetry = false) => {
        if (!story?.paragraphs?.[index]?.text) {
            console.error('No text found for paragraph');
            return;
        }        
        let progressInterval;
        try {
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {
                    ...node, 
                    data: {
                        ...node.data, 
                        isGeneratingAudio: true,
                        audioProgress: 0,
                        audioError: null
                    }
                } : node
            ));            
            let progress = 0;
            progressInterval = setInterval(() => {
                progress = Math.min(progress + 2, 90);
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
                    text: story.paragraphs[index].text.trim(),
                    is_retry: isRetry
                })
            });            
            const data = await response.json();
            clearInterval(progressInterval);            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to generate audio');
            }            
            if (data.success) {
                setNodes(currentNodes => 
                    currentNodes.map(node => 
                        node.id === `p${index}` ? {
                            ...node, 
                            data: {
                                ...node.data,
                                audioUrl: data.audio_url,
                                isGeneratingAudio: false,
                                audioProgress: 100,
                                audioError: null
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
                        audioProgress: 0,
                        audioError: error.message || 'Failed to generate audio. Please try again.'
                    }
                } : node
            ));
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
        loadPage(1); //Initial Page Load
    }, [story?.paragraphs]); // Include setNodes in dependencies


    const handleNextPage = useCallback(() => {
        if (currentPage < totalPages) {
            loadPage(currentPage + 1);
        }
    }, [currentPage, totalPages]);

    const handlePrevPage = useCallback(() => {
        if (currentPage > 1) {
            loadPage(currentPage - 1);
        }
    }, [currentPage]);

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
            <div className="navigation-controls mb-3">
                <div className="d-flex justify-content-between align-items-center">
                    <button 
                        className="btn btn-primary" 
                        onClick={handlePrevPage}
                        disabled={currentPage <= 1 || isLoading}>
                        <i className="bi bi-chevron-left"></i> Previous Chapter
                    </button>
                    <span className="mx-3">
                        {isLoading ? (
                            <div className="spinner-border spinner-border-sm" role="status">
                                <span className="visually-hidden">Loading...</span>
                            </div>
                        ) : (
                            `Chapter ${currentPage} of ${totalPages}`
                        )}
                    </span>
                    <button 
                        className="btn btn-primary" 
                        onClick={handleNextPage}
                        disabled={currentPage >= totalPages || isLoading}>
                        Next Chapter <i className="bi bi-chevron-right"></i>
                    </button>
                </div>
                {error && (
                    <div className="alert alert-danger mt-2" role="alert">
                        {error}
                    </div>
                )}
            </div>
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
                    draggable={true}
                    nodesDraggable={true}
                    defaultEdgeOptions={{ type: 'smoothstep' }}
                    zoomOnDoubleClick={false}
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