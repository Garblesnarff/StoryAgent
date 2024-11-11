import React, { useCallback, useState } from 'react';
import ReactDOM from 'react-dom/client';
import ReactFlow, { 
  Background, 
  Controls, 
  MiniMap,
  useNodesState,
  useEdgesState,
  Handle
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

  const onStyleChange = useCallback((index, type, value) => {
    setNodes((nds) =>
      nds.map((node) => {
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
      })
    );
  }, []);

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback((event) => {
    event.preventDefault();
    const effect = JSON.parse(event.dataTransfer.getData('application/json'));
    
    // Get the drop position relative to the viewport
    const reactFlowBounds = document.querySelector('.react-flow').getBoundingClientRect();
    const position = {
      x: event.clientX - reactFlowBounds.left,
      y: event.clientY - reactFlowBounds.top,
    };

    // Update the node that was dropped on
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
          defaultViewport={{ x: 0, y: 0, zoom: 1 }}
          nodesDraggable={true}
          nodesConnectable={true}
          elementsSelectable={true}
          fitView
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
        <div className="save-controls">
          <button onClick={onSave} className="btn btn-primary">
            Save and Generate
          </button>
        </div>
      </div>
    </div>
  );
}

document.addEventListener('DOMContentLoaded', () => {
  const container = document.getElementById('node-editor');
  if (!container) return;
  
  try {
    const storyData = JSON.parse(container.dataset.story);
    const root = ReactDOM.createRoot(container);
    root.render(
      <React.StrictMode>
        <StoryFlow storyData={storyData} />
      </React.StrictMode>
    );
  } catch (error) {
    console.error('Failed to initialize React app:', error);
    container.innerHTML = '<div class="alert alert-danger">Failed to load story customization</div>';
  }
});
