import React, { useCallback } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  Connection,
  Edge,
  NodeChange,
  EdgeChange,
  Node,
  addEdge,
  OnNodesChange,
  OnEdgesChange,
  OnConnect,
  NodePositionChange,
  NodeDimensionChange
} from 'reactflow';
import { ParagraphData } from '@/types/node';
import 'reactflow/dist/style.css';

/**
 * Props interface for the NodeEditor component
 * @interface NodeEditorProps
 * 
 * @property {Object} story - The story data containing paragraphs and metadata
 * @property {ParagraphData[]} story.paragraphs - Array of paragraph data for visualization
 * @property {Record<string, any>} [story.metadata] - Optional metadata for the story
 * @property {Function} [onStyleUpdate] - Optional callback for style update events
 */
interface NodeEditorProps {
  story: {
    paragraphs: ParagraphData[];
    metadata?: Record<string, any>;
  };
  onStyleUpdate?: (updates: ParagraphData[]) => void;
}

/** Type alias for story flow edges with proper typing */
type StoryEdge = Edge<ParagraphData>;

/**
 * NodeEditor Component
 * 
 * A visual editor for story nodes using ReactFlow.
 * Provides a drag-and-drop interface for arranging story paragraphs
 * and creating connections between them.
 * 
 * Features:
 * - Drag and drop node positioning
 * - Node connections with visual edges
 * - Background grid and controls
 * - Automatic layout adjustments
 * 
 * @component
 * @example
 * ```tsx
 * <NodeEditor
 *   story={{
 *     paragraphs: [{id: '1', content: 'Story begins...'}],
 *     metadata: { title: 'My Story' }
 *   }}
 *   onStyleUpdate={handleStyleUpdate}
 * />
 * ```
 */
const NodeEditor: React.FC<NodeEditorProps> = ({ story, onStyleUpdate }) => {
  // Initialize nodes from story paragraphs
  const initialNodes: Node<ParagraphData>[] = story.paragraphs.map((paragraph, index) => ({
    id: `node-${index}`,
    type: 'paragraph',
    position: { x: 250 * index, y: 100 },
    data: paragraph
  }));

  const [nodes, setNodes] = React.useState<Node<ParagraphData>[]>(initialNodes);
  const [edges, setEdges] = React.useState<Edge[]>([]);

  /**
   * Handles changes to node positions and dimensions
   * Updates the nodes state and triggers style updates if needed
   * 
   * @param changes - Array of node changes to apply
   */
  const onNodesChange = useCallback<OnNodesChange>((changes) => {
    setNodes((prevNodes) => {
      const updatedNodes = changes.reduce((acc, change) => {
        if (change.type === 'position' && 'position' in change) {
          return acc.map((node) => 
            node.id === change.id 
              ? { ...node, position: change.position } 
              : node
          );
        }
        if (change.type === 'dimensions' && 'dimensions' in change) {
          return acc.map((node) =>
            node.id === change.id
              ? { ...node, dimensions: change.dimensions }
              : node
          );
        }
        return acc;
      }, prevNodes);

      // Notify parent of updates if callback is provided
      if (onStyleUpdate) {
        const updatedData = updatedNodes.map(node => node.data);
        onStyleUpdate(updatedData);
      }

      return updatedNodes;
    });
  }, [onStyleUpdate]);

  /**
   * Handles changes to edge connections
   * Updates the edges state maintaining proper connections
   * 
   * @param changes - Array of edge changes to apply
   */
  const onEdgesChange = useCallback<OnEdgesChange>((changes) => {
    setEdges((prevEdges) => {
      return changes.reduce((acc, change) => {
        // Handle edge removal
        if (change.type === 'remove') {
          return acc.filter((edge) => edge.id !== change.id);
        }
        // Handle other edge changes (e.g., selection)
        return acc;
      }, prevEdges);
    });
  }, []);

  /**
   * Handles new connections between nodes
   * Creates a new edge with proper typing and styling
   * 
   * @param params - Connection parameters for the new edge
   */
  const onConnect = useCallback<OnConnect>((params) => {
    setEdges((prevEdges) => addEdge(
      { 
        ...params, 
        type: 'default',
        animated: true,
        style: { stroke: 'var(--bs-primary)' }
      }, 
      prevEdges
    ));
  }, []);

  return (
    <div className="w-full h-[calc(100vh-4rem)]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
};

export default NodeEditor;
