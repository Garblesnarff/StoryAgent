import React, { useState, useCallback, useEffect } from 'react';
import ReactFlow, { 
    Controls, 
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
    Handle,
    Position,
    Node,
    Edge
} from 'reactflow';
import 'reactflow/dist/style.css';

interface ParagraphData {
    index: number;
    text: string;
    globalStyle: string;
    imageUrl?: string;
    imagePrompt?: string;
    audioUrl?: string;
    onGenerateCard: (index: number) => void;
    onRegenerateImage: (index: number) => void;
    onRegenerateAudio: (index: number) => void;
    onExpandImage: (url: string) => void;
    isGenerating: boolean;
    isRegenerating: boolean;
    isRegeneratingAudio: boolean;
}

const ParagraphNode = React.memo(({ data }: { data: ParagraphData }) => {
    return (
        <div className="bg-card rounded-lg shadow-lg p-4 min-w-[400px] max-w-[400px] border border-border">
            <Handle type="target" position={Position.Left} className="!bg-primary" />
            <div className="text-lg font-bold mb-2 text-primary">Paragraph {data.index + 1}</div>
            <div className="text-sm text-card-foreground mb-4 max-h-[120px] overflow-y-auto">
                {data.text}
            </div>
            <div className="space-y-4">
                <button 
                    className="w-full bg-primary text-primary-foreground hover:bg-primary/90 px-4 py-2 rounded-md transition-colors"
                    onClick={() => data.onGenerateCard(data.index)}
                    disabled={data.isGenerating}>
                    {data.isGenerating ? (
                        <div className="flex items-center justify-center gap-2">
                            <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                            <span>Generating...</span>
                        </div>
                    ) : 'Generate Card'}
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
                                    onClick={() => data.onExpandImage(data.imageUrl!)}
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

interface Story {
    paragraphs: Array<{
        text: string;
        image_url?: string;
        image_prompt?: string;
        audio_url?: string;
    }>;
}

interface NodeEditorProps {
    story?: Story;
    onStyleUpdate?: (paragraphs: Array<{ index: number; image_style: string }>) => void;
}

const NodeEditor: React.FC<NodeEditorProps> = ({ story: initialStory, onStyleUpdate }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [selectedStyle, setSelectedStyle] = useState('realistic');
    const [expandedImage, setExpandedImage] = useState<string | null>(null);
    const [story, setStory] = useState(initialStory);
    const [isLoading, setIsLoading] = useState(!initialStory);

    useEffect(() => {
        if (!story?.paragraphs) {
            setIsLoading(false);
            return;
        }

        const paragraphNodes = story.paragraphs.map((para, index) => ({
            id: `p${index}`,
            type: 'paragraph',
            position: { 
                x: (index % 3) * 450 + 50, // Arrange in 3 columns
                y: Math.floor(index / 3) * 400 + 50 // More vertical spacing
            },
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
        setIsLoading(false);
    }, [story, selectedStyle, handleGenerateCard, handleRegenerateImage, handleRegenerateAudio]);

    // Rest of the component implementation remains the same, just with proper TypeScript types
    // ...

    if (isLoading) {
        return <div className="flex items-center justify-center h-96">Loading story data...</div>;
    }

    if (!story?.paragraphs?.length) {
        return <div className="flex items-center justify-center h-96">No story data available</div>;
    }

    return (
        <>
            <div style={{ width: '100%', height: '600px' }} className="node-editor-root">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    nodeTypes={nodeTypes}
                    fitView
                    style={{ background: 'var(--bs-dark)' }}
                    minZoom={0.1}
                    maxZoom={4}
                    defaultViewport={{ x: 0, y: 0, zoom: 1 }}
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
