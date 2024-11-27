import React, { useState, useCallback, useEffect, useRef, ErrorInfo } from 'react';
import ReactFlow, { 
    Controls, 
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
    Handle,
    Position,
    Node,
    Edge,
    Connection
} from 'reactflow';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import 'reactflow/dist/style.css';

/**
 * Interface definitions for story and component data structures
 */
interface ParagraphData {
    index: number;
    text: string;
    globalStyle: string;
    imageUrl?: string;
    imagePrompt?: string;
    audioUrl?: string;
    onGenerateCard: (index: number) => Promise<void>;
    onRegenerateImage: (index: number) => Promise<void>;
    onRegenerateAudio: (index: number) => Promise<void>;
    onExpandImage: (url: string) => void;
    onStyleChange?: (index: number, style: string) => void;
    isGenerating: boolean;
    isRegenerating: boolean;
    isRegeneratingAudio: boolean;
    error?: string;
}

interface StoryData {
    paragraphs: Array<{
        text: string;
        image_url?: string;
        image_prompt?: string;
        audio_url?: string;
        style?: string;
    }>;
    metadata?: {
        title?: string;
        created_at?: string;
        modified_at?: string;
    };
}

interface NodeEditorProps {
    story?: StoryData;
    onStyleUpdate?: (paragraphs: Array<{ index: number; image_style: string }>) => void;
}

interface ErrorBoundaryState {
    hasError: boolean;
    error?: Error;
}

interface ErrorBoundaryProps {
    children: React.ReactNode;
}

/**
 * ErrorBoundary Component
 * Catches and handles errors in the component tree
 */
class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
        console.error('Error caught by boundary:', error, errorInfo);
    }

    render(): React.ReactNode {
        if (this.state.hasError) {
            return (
                <div className="alert alert-danger">
                    <h4>Something went wrong</h4>
                    <p>{this.state.error?.message}</p>
                    <button 
                        className="btn btn-primary mt-2"
                        onClick={() => this.setState({ hasError: false })}
                    >
                        Try again
                    </button>
                </div>
            );
        }
        return this.props.children;
    }
}

/**
 * ParagraphNode Component
 * Represents a single paragraph node in the story flow
 */
const ParagraphNode = React.memo(({ data }: { data: ParagraphData }) => {
    const [showPrompt, setShowPrompt] = useState<boolean>(false);
    const [localStyle, setLocalStyle] = useState<string>(data.globalStyle || 'realistic');

    return (
        <div className={`paragraph-node ${localStyle}-style`}>
            <Handle type="target" position={Position.Left} className="!bg-primary" />
            <div className="text-lg font-bold mb-2 text-primary">
                Paragraph {data.index + 1}
            </div>
            <div className="text-sm text-card-foreground mb-4 max-h-[120px] overflow-y-auto">
                {data.text}
            </div>
            {/* Controls section */}
            <div className="space-y-4">
                <Button 
                    className="w-full"
                    onClick={() => data.onGenerateCard(data.index)}
                    disabled={data.isGenerating}
                >
                    {data.isGenerating ? (
                        <div className="flex items-center justify-center gap-2">
                            <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                            <span>Generating...</span>
                        </div>
                    ) : 'Generate Card'}
                </Button>
                
                {/* Style selection */}
                <div className="mt-4 mb-2">
                    <RadioGroup
                        value={localStyle}
                        onValueChange={(value: string) => {
                            setLocalStyle(value);
                            data.onStyleChange?.(data.index, value);
                        }}
                        className="flex gap-4 justify-center"
                    >
                        {['realistic', 'artistic', 'fantasy'].map((style) => (
                            <div key={style} className="flex items-center space-x-2">
                                <RadioGroupItem value={style} id={`${style}-${data.index}`} />
                                <Label htmlFor={`${style}-${data.index}`}>
                                    {style.charAt(0).toUpperCase() + style.slice(1)}
                                </Label>
                            </div>
                        ))}
                    </RadioGroup>
                </div>
                
                {/* Image preview and controls */}
                {data.imageUrl && (
                    <>
                        <div className="relative rounded-lg overflow-hidden border border-border">
                            <img 
                                src={data.imageUrl} 
                                alt="Generated preview" 
                                className="w-full h-auto object-cover"
                                onError={(e: React.SyntheticEvent<HTMLImageElement>) => {
                                    console.error('Image failed to load:', data.imageUrl);
                                    e.currentTarget.src = '/static/placeholder.png';
                                }}
                            />
                            {showPrompt && (
                                <div className="absolute inset-0 bg-black/75 p-4 text-white overflow-y-auto transition-all duration-200">
                                    <p className="text-sm">{data.imagePrompt}</p>
                                </div>
                            )}
                        </div>
                        
                        {/* Image control buttons */}
                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                size="sm"
                                className="flex-1"
                                onClick={() => data.onRegenerateImage(data.index)}
                                disabled={data.isRegenerating}
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                                    <path d="M3 3v5h5" />
                                    <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
                                    <path d="M16 16h5v5" />
                                </svg>
                                Regenerate
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setShowPrompt(!showPrompt)}
                            >
                                {showPrompt ? 'Hide Prompt' : 'Show Prompt'}
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => data.onExpandImage(data.imageUrl!)}
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" />
                                </svg>
                            </Button>
                        </div>
                    </>
                )}
                
                {/* Audio player and controls */}
                {data.audioUrl && (
                    <>
                        <div className="audio-player mt-4">
                            <audio
                                controls
                                className="w-full"
                                key={data.audioUrl}
                                onError={() => console.error('Audio failed to load:', data.audioUrl)}
                            >
                                <source src={data.audioUrl} type="audio/wav" />
                                Your browser does not support the audio element.
                            </audio>
                        </div>
                        <Button 
                            variant="outline"
                            size="sm"
                            className="w-full mt-2"
                            onClick={() => data.onRegenerateAudio(data.index)}
                            disabled={data.isRegeneratingAudio}
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
                                <path d="M3 3v5h5" />
                                <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
                                <path d="M16 16h5v5" />
                            </svg>
                            Regenerate Audio
                        </Button>
                    </>
                )}
            </div>
            <Handle type="source" position={Position.Right} className="!bg-primary" />
        </div>
    );
});

ParagraphNode.displayName = 'ParagraphNode';

const nodeTypes = {
    paragraph: ParagraphNode
};

/**
 * NodeEditor Component
 * Main component for the story editor interface
 */
const NodeEditor: React.FC<NodeEditorProps> = ({ story: initialStory, onStyleUpdate }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [selectedStyle, setSelectedStyle] = useState<string>('realistic');
    const [expandedImage, setExpandedImage] = useState<string | null>(null);
    const [story, setStory] = useState<StoryData | undefined>(initialStory);
    const [isLoading, setIsLoading] = useState<boolean>(!initialStory);
    const [error, setError] = useState<string | null>(null);
    const nodesInitializedRef = useRef<boolean>(false);

    // Error handling and loading state management
    useEffect(() => {
        const errorContainer = document.getElementById('error-container');
        const loadingContainer = document.getElementById('loading-container');
        
        if (errorContainer && loadingContainer) {
            if (error) {
                errorContainer.textContent = error;
                errorContainer.classList.remove('d-none');
                loadingContainer.classList.add('d-none');
            } else {
                errorContainer.classList.add('d-none');
                loadingContainer.classList.toggle('d-none', !isLoading);
            }
        }
    }, [error, isLoading]);

    // Handle image regeneration
    const handleRegenerateImage = useCallback(async (index: number) => {
        try {
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegenerating: true}} : node
            ));

            const response = await fetch('/story/regenerate_image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    index,
                    text: story?.paragraphs[index].text,
                    style: nodes.find(n => n.id === `p${index}`)?.data.globalStyle || 'realistic',
                    regenerate_prompt: true
                })
            });

            const data = await response.json();
            if (data.success) {
                setNodes(nodes => nodes.map(node => 
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
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegenerating: false}} : node
            ));
        }
    }, [story, nodes]);

    // Handle style changes
    const handleStyleChange = useCallback((index: number, newStyle: string) => {
        setNodes(nodes => nodes.map(node => 
            node.id === `p${index}` ? {
                ...node,
                data: {
                    ...node.data,
                    globalStyle: newStyle
                }
            } : node
        ));
        
        onStyleUpdate?.([{
            index,
            image_style: newStyle
        }]);
    }, [onStyleUpdate]);

    const handleGenerateCard = useCallback(async (index: number) => {
        try {
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGenerating: true}} : node
            ));

            const response = await fetch('/story/generate_cards', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    index,
                    text: story?.paragraphs[index].text,
                    style: nodes.find(n => n.id === `p${index}`)?.data.globalStyle || 'realistic'
                })
            });

            if (!response.ok) throw new Error('Failed to generate card');

            const reader = response.body?.getReader();
            if (!reader) throw new Error('Failed to get reader');

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
                            setNodes(nodes => nodes.map(node => 
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
                            ));
                        }
                    } catch (error) {
                        console.error('Error parsing JSON:', error);
                    }
                }
            }
        } catch (error) {
            console.error('Error generating card:', error);
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGenerating: false}} : node
            ));
        }
    }, [story, nodes]);

    const handleRegenerateAudio = useCallback(async (index: number) => {
        try {
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegeneratingAudio: true}} : node
            ));

            const response = await fetch('/story/regenerate_audio', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    index,
                    text: story?.paragraphs[index].text
                })
            });

            const data = await response.json();
            if (data.success) {
                setNodes(nodes => nodes.map(node => 
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
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegeneratingAudio: false}} : node
            ));
        }
    }, [story]);

    // Initialize nodes from story data
    useEffect(() => {
        if (!story?.paragraphs || nodesInitializedRef.current) return;
        
        const paragraphNodes = story.paragraphs.map((para, index) => ({
            id: `p${index}`,
            type: 'paragraph' as const,
            position: { 
                x: (index % 2) * 300 + 50,
                y: Math.floor(index / 2) * 250 + 50
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
                onStyleChange: handleStyleChange,
                isGenerating: false,
                isRegenerating: false,
                isRegeneratingAudio: false
            }
        }));

        setNodes(paragraphNodes);
        nodesInitializedRef.current = true;
    }, [story, selectedStyle, handleRegenerateImage, handleRegenerateAudio, handleStyleChange, setNodes]);

    // Handle node connections
    const onConnect = useCallback((params: Connection) => {
        if (params.source === params.target) return;
        
        setEdges(edges => addEdge({
            ...params,
            type: 'smoothstep',
            animated: true,
            style: { 
                stroke: 'var(--bs-primary)',
                strokeWidth: 2,
            }
        }, edges));
    }, [setEdges]);

    return (
        <ErrorBoundary>
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
                <div 
                    className="modal-backdrop" 
                    onClick={() => setExpandedImage(null)}
                >
                    <div 
                        className="preview-modal" 
                        onClick={e => e.stopPropagation()}
                    >
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
        </ErrorBoundary>
    );
};

export default React.memo(NodeEditor);