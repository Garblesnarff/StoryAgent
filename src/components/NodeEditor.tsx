import React, { useState, useCallback, useEffect, useRef } from 'react';
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
    Connection,
    NodeProps,
    NodeTypes
} from 'reactflow';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import 'reactflow/dist/style.css';

/**
 * Type definitions for story and node data structures
 */
interface ParagraphData {
    index: number;
    text: string;
    style: string;
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

/**
 * Calculate optimal node position to prevent overlapping
 * @param index Node index in the story
 * @param totalNodes Total number of nodes
 * @returns Calculated x,y coordinates
 */
const calculateNodePosition = (index: number, totalNodes: number) => {
    const SPACING_X = 350; // Horizontal spacing between nodes
    const SPACING_Y = 300; // Vertical spacing between rows
    const NODES_PER_ROW = Math.ceil(Math.sqrt(totalNodes)); // Dynamic row size

    const row = Math.floor(index / NODES_PER_ROW);
    const col = index % NODES_PER_ROW;

    return {
        x: col * SPACING_X + 50,
        y: row * SPACING_Y + 50
    };
};

/**
 * ErrorBoundary Component
 * Handles runtime errors in the node editor and provides recovery options
 */
class ErrorBoundary extends React.Component<
    { children: React.ReactNode },
    { hasError: boolean; error?: Error }
> {
    constructor(props: { children: React.ReactNode }) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error: Error) {
        return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error('NodeEditor error:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="alert alert-danger">
                    <h4>Something went wrong</h4>
                    <p>{this.state.error?.message}</p>
                    <Button 
                        onClick={() => this.setState({ hasError: false })}
                        variant="secondary"
                        className="mt-2"
                    >
                        Try again
                    </Button>
                </div>
            );
        }
        return this.props.children;
    }
}

/**
 * ParagraphNode Component
 * Renders individual story paragraph nodes with media controls
 */
const ParagraphNode = React.memo<NodeProps<ParagraphData>>(({ data }) => {
    const [showPrompt, setShowPrompt] = useState(false);
    const [localStyle, setLocalStyle] = useState(data.style || 'realistic');

    const handleImageError = (e: React.SyntheticEvent<HTMLImageElement>) => {
        console.error('Image failed to load:', data.imageUrl);
        e.currentTarget.src = '/static/placeholder.png';
    };

    return (
        <div className={`paragraph-node ${localStyle}-style`}>
            <Handle type="target" position={Position.Left} className="!bg-primary" />
            
            <div className="text-lg font-bold mb-2 text-primary">
                Paragraph {data.index + 1}
            </div>
            
            <div className="text-sm text-card-foreground mb-4 max-h-[120px] overflow-y-auto">
                {data.text}
            </div>

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

                {data.error && (
                    <div className="alert alert-danger mb-4">
                        {data.error}
                    </div>
                )}

                {data.imageUrl && (
                    <>
                        <div className="relative rounded-lg overflow-hidden border border-border">
                            <img 
                                src={data.imageUrl} 
                                alt="Generated preview" 
                                className="w-full h-auto object-cover"
                                onError={handleImageError}
                            />
                            {showPrompt && (
                                <div className="absolute inset-0 bg-black/75 p-4 text-white overflow-y-auto">
                                    <p className="text-sm">{data.imagePrompt}</p>
                                </div>
                            )}
                        </div>

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

                {data.audioUrl && (
                    <>
                        <div className="audio-player mt-4">
                            <audio
                                controls
                                className="w-full"
                                key={data.audioUrl}
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

const nodeTypes: NodeTypes = {
    paragraph: ParagraphNode
};

/**
 * NodeEditor Component
 * Main component for the story flow editor interface
 * 
 * Features:
 * - Interactive node-based story visualization
 * - Media generation and regeneration capabilities
 * - Style customization for each paragraph
 * - Error boundaries and loading states
 * - Responsive layout with dynamic node positioning
 */
const NodeEditor: React.FC<NodeEditorProps> = ({ story: initialStory, onStyleUpdate }) => {
    // State management
    const [nodes, setNodes, onNodesChange] = useNodesState<Node<ParagraphData>[]>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState<Edge[]>([]);
    const [selectedStyle, setSelectedStyle] = useState('realistic');
    const [expandedImage, setExpandedImage] = useState<string | null>(null);
    const [story, setStory] = useState<StoryData | undefined>(initialStory);
    const [isLoading, setIsLoading] = useState(!initialStory);
    const [error, setError] = useState<string | null>(null);
    const nodesInitializedRef = useRef(false);

    // Initialize nodes from story data
    useEffect(() => {
        if (!story?.paragraphs || nodesInitializedRef.current) return;

        try {
            const totalNodes = story.paragraphs.length;
            const paragraphNodes: Node<ParagraphData>[] = story.paragraphs.map((para, index) => {
                const position = calculateNodePosition(index, totalNodes);
                return {
                    id: `p${index}`,
                    type: 'paragraph',
                    position,
                    data: {
                        index,
                        text: para.text,
                        style: selectedStyle,
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
                };
            });

            setNodes(paragraphNodes);
            nodesInitializedRef.current = true;
            setIsLoading(false);
        } catch (error) {
            console.error('Error initializing nodes:', error);
            setError('Failed to initialize story nodes');
            setIsLoading(false);
        }
    }, [story?.paragraphs, selectedStyle]);

    // Handle image regeneration
    const handleRegenerateImage = useCallback(async (index: number) => {
        try {
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegenerating: true, error: null}} : node
            ));

            const response = await fetch('/story/regenerate_image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    index,
                    text: story?.paragraphs[index].text,
                    style: selectedStyle
                })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Failed to regenerate image');

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
        } catch (error) {
            console.error('Error regenerating image:', error);
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {
                    ...node,
                    data: {
                        ...node.data,
                        isRegenerating: false,
                        error: error instanceof Error ? error.message : 'Failed to regenerate image'
                    }
                } : node
            ));
        }
    }, [story, selectedStyle]);

    // Handle audio regeneration
    const handleRegenerateAudio = useCallback(async (index: number) => {
        try {
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegeneratingAudio: true, error: null}} : node
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
            if (!response.ok) throw new Error(data.error || 'Failed to regenerate audio');

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
        } catch (error) {
            console.error('Error regenerating audio:', error);
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {
                    ...node,
                    data: {
                        ...node.data,
                        isRegeneratingAudio: false,
                        error: error instanceof Error ? error.message : 'Failed to regenerate audio'
                    }
                } : node
            ));
        }
    }, [story]);

    // Handle card generation
    const handleGenerateCard = useCallback(async (index: number) => {
        try {
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGenerating: true, error: null}} : node
            ));

            const response = await fetch('/story/generate_cards', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    index,
                    text: story?.paragraphs[index].text,
                    style: selectedStyle
                })
            });

            if (!response.ok) throw new Error('Failed to generate card');

            const reader = response.body?.getReader();
            if (!reader) throw new Error('Failed to read response');

            const decoder = new TextDecoder();
            let buffer = '';
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
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
                        throw new Error('Invalid response format');
                    }
                }
            }
        } catch (error) {
            console.error('Error generating card:', error);
            setNodes(currentNodes => currentNodes.map(node => 
                node.id === `p${index}` ? {
                    ...node,
                    data: {
                        ...node.data,
                        isGenerating: false,
                        error: error instanceof Error ? error.message : 'Failed to generate card'
                    }
                } : node
            ));
        }
    }, [story, selectedStyle]);

    // Handle style changes
    const handleStyleChange = useCallback((index: number, newStyle: string) => {
        setNodes(currentNodes => currentNodes.map(node => ({
            ...node,
            data: node.id === `p${index}` ? {
                ...node.data,
                style: newStyle
            } : node.data
        })));

        onStyleUpdate?.([{ index, image_style: newStyle }]);
    }, [onStyleUpdate]);

    // Handle node connections
    const onConnect = useCallback((params: Connection) => {
        if (params.source === params.target) return;
        
        setEdges(currentEdges => addEdge({
            ...params,
            type: 'smoothstep',
            animated: true,
            style: { 
                stroke: 'var(--bs-primary)',
                strokeWidth: 2,
            }
        }, currentEdges));
    }, [setEdges]);

    if (error) {
        return (
            <div className="alert alert-danger">
                <h4>Error</h4>
                <p>{error}</p>
                <Button onClick={() => setError(null)} variant="secondary">
                    Try Again
                </Button>
            </div>
        );
    }

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-[600px]">
                <div className="spinner-border text-primary" role="status">
                    <span className="visually-hidden">Loading...</span>
                </div>
            </div>
        );
    }

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
        </ErrorBoundary>
    );
};

export default React.memo(NodeEditor);
