import React from 'react';
import { Handle, Position, NodeResizer } from 'reactflow';

/**
 * BaseNode - Componente base per tutti i tipi di nodi nel workflow
 * 
 * Supporta tre modalità:
 * 1. 'simple' - Solo visualizzazione senza handle
 * 2. 'default' - Con handle in/out
 * 3. 'resizable' - Con handle e possibilità di ridimensionamento
 */
const BaseNode = ({ 
  data, 
  type = 'default',
  icon,
  bgColor = 'bg-white',
  borderColor = 'border-gray-300',
  textColor = 'text-gray-900',
  selected = false,
  mode = 'default', // 'simple', 'default', 'resizable'
  nodeConfig
}) => {
  // Rendering condizionale delle handle in base alla modalità
  const renderHandles = mode !== 'simple';

  return (
    <div className={`px-4 py-2 shadow-lg rounded-md ${bgColor} ${borderColor} ${textColor} border-2 min-w-[200px] ${mode === 'resizable' ? 'relative' : ''}`}>
      {/* Node Resizer - appare solo quando selezionato e in modalità resizable */}
      {mode === 'resizable' && selected && (
        <NodeResizer 
          color="#ff0071" 
          isVisible={selected}
          minWidth={200}
          minHeight={80}
          handleStyle={{
            width: '8px',
            height: '8px',
            backgroundColor: '#ff0071',
            border: '2px solid #fff',
            borderRadius: '50%'
          }}
          lineStyle={{
            borderColor: '#ff0071',
            borderWidth: '1px'
          }}
        />
      )}
      
      {/* Input Handle - solo in modalità default o resizable */}
      {renderHandles && (
        <Handle
          type="target"
          position={Position.Left}
          className="w-3 h-3 bg-gray-400 border-2 border-white"
          id="input"
          style={mode === 'resizable' ? { left: -6 } : undefined}
        />
      )}
      
      <div className="flex items-center space-x-2">
        {icon && <div className="text-lg">{icon}</div>}
        <div>
          <div className="font-bold text-sm">{data?.name || 'Node'}</div>
          <div className="text-xs text-gray-500">{data?.description || 'Description'}</div>
        </div>
      </div>
      
      {data?.config && Object.keys(data.config).length > 0 && (
        <div className="mt-2 text-xs">
          <div className="text-gray-400">Config:</div>
          <div className="bg-gray-50 p-1 rounded text-gray-600 max-h-20 overflow-y-auto">
            {JSON.stringify(data.config, null, 1)}
          </div>
        </div>
      )}
      
      {/* Configurazione aggiuntiva del nodo se fornita */}
      {nodeConfig && (
        <div className="mt-2 border-t border-gray-200 pt-2">
          {nodeConfig}
        </div>
      )}
      
      {/* Output Handle - solo in modalità default o resizable */}
      {renderHandles && (
        <Handle
          type="source"
          position={Position.Right}
          className="w-3 h-3 bg-gray-400 border-2 border-white"
          id="output"
          style={mode === 'resizable' ? { right: -6 } : undefined}
        />
      )}
    </div>
  );
};

export default BaseNode;
