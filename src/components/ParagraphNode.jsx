import React from 'react';
import { Handle } from 'reactflow';

const ParagraphNode = ({ data, selected }) => {
  const handleStyleChange = (e) => {
    e.stopPropagation();
    if (data.onStyleChange) {
      data.onStyleChange(data.index, 'image', e.target.value);
    }
  };

  return (
    <div className={`paragraph-node ${selected ? 'selected' : ''}`}>
      <Handle 
        type="target" 
        position="top" 
        style={{ background: '#555' }}
        isConnectable={true}
      />
      <div className="node-content">
        <h4>Paragraph {data.index + 1}</h4>
        <p>{data.text?.substring(0, 100)}...</p>
        <div className="node-controls" onClick={e => e.stopPropagation()}>
          <select 
            value={data.imageStyle || 'realistic'} 
            onChange={handleStyleChange}
          >
            <option value="realistic">Realistic</option>
            <option value="artistic">Artistic</option>
            <option value="cartoon">Cartoon</option>
          </select>
        </div>
      </div>
      <Handle 
        type="source" 
        position="bottom" 
        style={{ background: '#555' }}
        isConnectable={true}
      />
    </div>
  );
};

export default ParagraphNode;