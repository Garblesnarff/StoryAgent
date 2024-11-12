import React, { useCallback, useState } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  MiniMap,
  useNodesState,
  useEdgesState,
  Handle,
  useReactFlow
} from 'reactflow';
import 'reactflow/dist/style.css';
import ParagraphNode from './ParagraphNode';
import LibraryPanel from './LibraryPanel';

const nodeTypes = {
  paragraphNode: ParagraphNode,
};

function StoryFlow({ storyData }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [history, setHistory] = useState({ past: [], present: null, future: [] });
  const { setViewport } = useReactFlow();

  // Function to save current state to history
  const saveToHistory = useCallback((currentNodes) => {
    setHistory(prev => ({
      past: [...prev.past, prev.present || nodes],
      present: currentNodes,
      future: []
    }));
  }, [nodes]);

  // Undo function
  const undo = useCallback(() => {
    setHistory(prev => {
      if (prev.past.length === 0) return prev;
      
      const newPast = prev.past.slice(0, -1);
      const newPresent = prev.past[prev.past.length - 1];
      
      return {
        past: newPast,
        present: newPresent,
        future: [prev.present, ...prev.future]
      };
    });
  }, []);

  // Redo function
  const redo = useCallback(() => {
    setHistory(prev => {
      if (prev.future.length === 0) return prev;
      
      const newFuture = prev.future.slice(1);
      const newPresent = prev.future[0];
      
      return {
        past: [...prev.past, prev.present],
        present: newPresent,
        future: newFuture
      };
    });
  }, []);

  // Effect to update nodes when history changes
  React.useEffect(() => {
    if (history.present !== null) {
      setNodes(history.present);
    }
  }, [history.present, setNodes]);

  // Handle keyboard shortcuts
  React.useEffect(() => {
    const handleKeyPress = (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key === 'z') {
        if (event.shiftKey) {
          redo();
        } else {
          undo();
        }
      }
    };
    
    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, [undo, redo]);

  const onStyleChange = useCallback((index, type, value) => {
    setNodes((nds) => {
      const newNodes = nds.map((node) => {
        if (node.id === `paragraph-${index}`) {
          return {
            ...node,
            data: {
              ...node.data,
              [type === 'image' ? 'imageStyle' : 'voiceStyle']: value,
            },
          };
        }
        return node;
      });
      saveToHistory(newNodes);
      return newNodes;
    });
  }, [saveToHistory]);

  const onNodeDragStop = useCallback((event, node) => {
    saveToHistory(nodes);
  }, [nodes, saveToHistory]);

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback((event) => {
    event.preventDefault();
    const effect = JSON.parse(event.dataTransfer.getData('application/json'));
    
    const reactFlowBounds = document.querySelector('.react-flow').getBoundingClientRect();
    const position = {
      x: event.clientX - reactFlowBounds.left,
      y: event.clientY - reactFlowBounds.top,
    };

    const droppedNode = nodes.find(node => {
      const nodeRect = document.querySelector(`[data-id="${node.id}"]`)?.getBoundingClientRect();
      if (!nodeRect) return false;
      return (
        position.x >= nodeRect.left - reactFlowBounds.left &&
        position.x <= nodeRect.right - reactFlowBounds.left &&
        position.y >= nodeRect.top - reactFlowBounds.top &&
        position.y <= nodeRect.bottom - reactFlowBounds.top
      );
    });

    if (droppedNode) {
      const index = droppedNode.data.index;
      onStyleChange(index, effect.category, effect.id);
    }
  }, [nodes, onStyleChange]);

  React.useEffect(() => {
    if (!storyData?.paragraphs) return;

    const initialNodes = storyData.paragraphs.map((para, index) => ({
      id: `paragraph-${index}`,
      type: 'paragraphNode',
      position: { x: 250, y: index * 250 },
      data: {
        ...para,
        index,
        onStyleChange,
        imageStyle: para.image_style || 'realistic',
        voiceStyle: para.voice_style || 'neutral'
      },
      draggable: true,
      selectable: true
    }));

    const initialEdges = storyData.paragraphs
      .slice(0, -1)
      .map((_, index) => ({
        id: `edge-${index}`,
        source: `paragraph-${index}`,
        target: `paragraph-${index + 1}`,
        type: 'smoothstep',
      }));

    setNodes(initialNodes);
    setEdges(initialEdges);
    setHistory({ past: [], present: initialNodes, future: [] });
  }, [storyData, onStyleChange]);

  const onSave = useCallback(() => {
    const styleData = {
      paragraphs: nodes.map((node) => ({
        index: node.data.index,
        image_style: node.data.imageStyle || 'realistic',
        voice_style: node.data.voiceStyle || 'neutral',
      })),
    };

    fetch('/story/update_style', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(styleData),
    })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        window.location.href = '/story/generate';
      } else {
        console.error('Failed to save styles:', data.error);
      }
    })
    .catch((error) => {
      console.error('Error saving styles:', error);
    });
  }, [nodes]);

  return (
    <div className="story-flow-container">
      <LibraryPanel />
      <div className="flow-wrapper">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          onDragOver={onDragOver}
          onDrop={onDrop}
          onNodeDragStop={onNodeDragStop}
          fitView
          defaultViewport={{ x: 0, y: 0, zoom: 1 }}
          minZoom={0.1}
          maxZoom={4}
          nodesDraggable={true}
          nodesConnectable={true}
          elementsSelectable={true}
          proOptions={{ hideAttribution: true }}
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
        <div className="editor-controls">
          <button onClick={undo} disabled={history.past.length === 0}>Undo</button>
          <button onClick={redo} disabled={history.future.length === 0}>Redo</button>
        </div>
        <div className="save-controls">
          <button onClick={onSave}>Save and Generate</button>
        </div>
      </div>
    </div>
  );
}

export default StoryFlow;
