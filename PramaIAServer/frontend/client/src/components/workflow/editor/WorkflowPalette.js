import React from 'react';
import NodePalette from './NodePalette';

const WorkflowPalette = () => {
  console.log('[WorkflowPalette] Rendering palette component...');
  
  return (
    <div className="w-80 min-w-80 max-w-80 border-r border-gray-200 bg-gray-50 overflow-y-auto overflow-x-hidden flex-shrink-0">
      {/* Usa il componente NodePalette per la gestione dinamica dei nodi */}
      <NodePalette onDragStart={(nodeType, nodeDefinition) => {
        console.log('[WorkflowPalette] Node dragged:', nodeType, nodeDefinition);
        // Il NodePalette gestisce già il drag start internamente
        // Questo callback è per compatibilità future se necessario
      }} />
    </div>
  );
};

export default WorkflowPalette;
