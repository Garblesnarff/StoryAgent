import React, { useCallback, useState } from 'react';
import ReactDOM from 'react-dom/client';
import ReactFlow, { 
  Background, 
  Controls, 
  MiniMap,
  useNodesState,
  useEdgesState
} from 'reactflow';
import 'reactflow/dist/style.css';
import ParagraphNode from './ParagraphNode';

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

  React.useEffect(() => {
    if (!storyData?.paragraphs) return;

    const initialNodes = storyData.paragraphs.map((para, index) => ({
      id: `paragraph-${index}`,
      type: 'paragraphNode',
      position: { x: 100, y: index * 200 },
      data: {
        ...para,
        index,
        onStyleChange,
      },
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
  }, [storyData]);

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
    <div style={{ width: '100%', height: '80vh' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
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
