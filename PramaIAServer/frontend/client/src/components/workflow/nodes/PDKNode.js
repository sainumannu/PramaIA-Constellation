// PDKNode.js
// Componente generico per nodi PDK

import React from 'react';
import BaseNode from './BaseNode';

const PDKNode = ({ data, id, selected }) => {
  const {
    name = 'PDK Node',
    description = '',
    config = {},
    pluginName = '',
    pluginVersion = '',
    icon = '🧩',  // Usa l'icona dal plugin o fallback
    color = '#ffffff'  // Usa il colore dal plugin o fallback
  } = data;

  // Debug logs sono stati disabilitati
  // console.log('[PDKNode] Rendering node:', id);
  // console.log('[PDKNode] Final icon:', icon, 'for name:', name);

  // Usa l'icona che arriva (già processata nel WorkflowEditor)
  const finalIcon = icon || '🧩';

  // Pulsante di rimozione per il nodo
  const removeButton = (
    <button
      className="text-red-500 hover:text-red-700 hover:bg-red-50 rounded p-1 text-xs transition-colors"
      onClick={(e) => {
        e.stopPropagation();
        // Conferma prima di eliminare
        if (window.confirm(`Sei sicuro di voler eliminare questo nodo "${name}"?`)) {
          if (window.removeNode) {
            window.removeNode(id);
          }
        }
      }}
      title="Rimuovi nodo"
    >
      ✕
    </button>
  );

  // Contenuto aggiuntivo per il nodo PDK
  const nodeConfig = (
    <>
      {pluginName && (
        <div className="text-xs text-gray-500 mt-1">
          {pluginName} v{pluginVersion}
        </div>
      )}
      
      {/* Indicatore configurazione */}
      {Object.keys(config).length > 0 && (
        <div className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded mt-2">
          Configurato ({Object.keys(config).length} parametri)
        </div>
      )}
      
      {/* Pulsante rimozione */}
      <div className="flex justify-end mt-2">
        {removeButton}
      </div>
    </>
  );

  // Utilizziamo il BaseNode consolidato
  return (
    <BaseNode
      data={{
        name: name,
        description: description,
        config: config
      }}
      icon={finalIcon}
      selected={selected}
      bgColor="bg-white"
      borderColor={selected ? "border-blue-500" : "border-gray-300"}
      textColor="text-gray-800"
      nodeConfig={nodeConfig}
    />
  );
};

export default PDKNode;
