import React from 'react';
import { Handle } from 'reactflow';

const ParagraphNode = ({ data, selected }) => {
  const handleStyleChange = (type, value) => {
    if (data.onStyleChange) {
      data.onStyleChange(data.index, type, value);
    }
  };

  return (
    <div className={`paragraph-node ${selected ? 'selected' : ''}`}>
      <Handle type="target" position="top" />
      <div className="node-header">Paragraph {data.index + 1}</div>
      <div className="node-content">
        <p>{data.text.substring(0, 100)}...</p>
        <div className="node-controls">
          <select 
            value={data.imageStyle || 'realistic'} 
            onChange={(e) => handleStyleChange('image', e.target.value)}
          >
            <option value="realistic">Realistic</option>
            <option value="artistic">Artistic</option>
            <option value="cartoon">Cartoon</option>
          </select>
        </div>
      </div>
      <Handle type="source" position="bottom" />
    </div>
  );
};

export default ParagraphNode;
