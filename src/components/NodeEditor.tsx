import React, { useState, useCallback, useLayoutEffect } from 'react';
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
    ReactFlowProvider
} from 'reactflow';
import { Button } from '@/components/ui/button';
import 'reactflow/dist/style.css';

// Loading Component
const LoadingState = () => (
    <div className="flex items-center justify-center h-[600px] bg-background border rounded-lg">
        <div className="space-y-4 text-center">
            <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-muted-foreground">Loading story editor...</p>
        </div>
    </div>
);

interface NodeData {
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
    onStyleChange?: (index: number, style: string) => void;
    isGenerating: boolean;
    isRegenerating: boolean;
    isRegeneratingAudio: boolean;
}

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
    console.log('[NodeEditor] Props received:', { initialStory });
    
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [selectedStyle, setSelectedStyle] = useState('realistic');
    const [expandedImage, setExpandedImage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isInitialized, setIsInitialized] = useState(false);

    useLayoutEffect(() => {
        if (!initialStory?.paragraphs) {
            console.error('[NodeEditor] No story data available');
            setError('Story data is missing');
            setIsLoading(false);
            return;
        }

        try {
            console.log('[NodeEditor] Setting up nodes for story:', initialStory);
            const newNodes = initialStory.paragraphs.map((para, index) => ({
                id: `p${index}`,
                type: 'paragraph',
                position: { x: (index % 3) * 500 + 50, y: Math.floor(index / 3) * 450 + 50 },
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
            
            console.log('[NodeEditor] Setting up nodes:', newNodes);
            setNodes(newNodes);
            setIsInitialized(true);
        } catch (err) {
            console.error('[NodeEditor] Error setting up nodes:', err);
            setError('Failed to initialize story editor');
        } finally {
            setIsLoading(false);
        }
    }, [initialStory, selectedStyle]);

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
                    text: initialStory?.paragraphs[index].text,
                    style: selectedStyle
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
            console.error('[NodeEditor] Error regenerating image:', error);
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegenerating: false}} : node
            ));
        }
    }, [initialStory, selectedStyle]);

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
                    text: initialStory?.paragraphs[index].text
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
            console.error('[NodeEditor] Error regenerating audio:', error);
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isRegeneratingAudio: false}} : node
            ));
        }
    }, [initialStory]);

    const handleGenerateCard = useCallback(async (index: number) => {
        if (!initialStory?.paragraphs?.[index]?.text) {
            console.error('[NodeEditor] No text found for paragraph');
            return;
        }

        try {
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGenerating: true}} : node
            ));

            const response = await fetch('/story/generate_cards', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    index,
                    text: initialStory.paragraphs[index].text,
                    style: selectedStyle
                })
            });

            if (!response.ok) throw new Error('Failed to generate card');
            
            const data = await response.json();
            if (data.success) {
                setNodes(nodes => nodes.map(node => 
                    node.id === `p${index}` ? {
                        ...node, 
                        data: {
                            ...node.data,
                            imageUrl: data.image_url,
                            imagePrompt: data.image_prompt,
                            audioUrl: data.audio_url,
                            isGenerating: false
                        }
                    } : node
                ));
            }
        } catch (error) {
            console.error('[NodeEditor] Error generating card:', error);
            setNodes(nodes => nodes.map(node => 
                node.id === `p${index}` ? {...node, data: {...node.data, isGenerating: false}} : node
            ));
        }
    }, [initialStory, selectedStyle]);

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

        if (onStyleUpdate) {
            onStyleUpdate([{ index, image_style: newStyle }]);
        }
    }, [onStyleUpdate]);

    const onConnect = useCallback((params: Connection) => {
        const edge = {
            ...params,
            type: 'smoothstep',
            animated: true,
            style: { 
                stroke: 'var(--primary)',
                strokeWidth: 2,
            }
        };
        
        setEdges(edges => addEdge(edge, edges));
    }, [setEdges]);

    if (error) {
        return (
            <div className="flex items-center justify-center h-[600px] bg-background border rounded-lg">
                <div className="text-center space-y-4">
                    <p className="text-red-500">{error}</p>
                    <Button onClick={() => window.location.reload()}>
                        Retry
                    </Button>
                </div>
            </div>
        );
    }

    if (isLoading) {
        return <LoadingState />;
    }

    return (
        <div style={{ width: '100%', height: '600px' }} className="bg-background border rounded-lg">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                nodeTypes={nodeTypes}
                fitView
                minZoom={0.1}
                maxZoom={4}
                defaultViewport={{ x: 0, y: 0, zoom: 1 }}>
                <Background />
                <Controls />
            </ReactFlow>
            {expandedImage && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-background p-4 rounded-lg max-w-4xl max-h-[90vh] overflow-auto">
                        <img src={expandedImage} alt="Full preview" className="max-w-full h-auto" />
                        <Button onClick={() => setExpandedImage(null)} className="mt-4">
                            Close
                        </Button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default React.memo(NodeEditor);