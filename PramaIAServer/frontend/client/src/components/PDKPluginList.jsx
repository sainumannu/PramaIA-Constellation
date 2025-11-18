

import React, { useEffect, useState } from 'react';
import { PDKTagManagementPanel, PDKTagBadge } from './PDKTagManagement';
import { usePDKPlugins } from '../hooks/usePDKData';
import NodeDetailsModal from './NodeDetailsModal';

const PDKPluginList = () => {
  const { 
    plugins, 
    allPlugins, 
    loading, 
    error, 
    updateFilters,
    resetFilters 
  } = usePDKPlugins();
  
  const [filteredNodes, setFilteredNodes] = useState([]);
  const [allNodes, setAllNodes] = useState([]);
  const [formError, setFormError] = useState('');
  const [showTagPanel, setShowTagPanel] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);
  const [showNodeModal, setShowNodeModal] = useState(false);

  // Estrae tutti i nodi da tutti i plugin
  useEffect(() => {
    const extractedNodes = [];
    plugins.forEach(plugin => {
      if (plugin.nodes && plugin.nodes.length > 0) {
        plugin.nodes.forEach(node => {
          extractedNodes.push({
            ...node,
            pluginId: plugin.id,
            pluginName: plugin.name,
            pluginTags: plugin.tags || [],
            plugin: plugin // Manteniamo il riferimento al plugin per il modal
          });
        });
      }
    });
    setAllNodes(extractedNodes);
    setFilteredNodes(extractedNodes);
  }, [plugins]);

  // Chiudi il modal del nodo se il nodo selezionato viene deselezionato
  useEffect(() => {
    if (!selectedNode && showNodeModal) {
      setShowNodeModal(false);
    }
  }, [selectedNode, showNodeModal]);

  // Non abbiamo più bisogno della funzione handleDetails per i plugin
  // Ora gestiamo direttamente i dettagli dei nodi
  const handleNodeDetails = (node) => {
    setSelectedNode(node);
    setShowNodeModal(true);
  };

  return (
    <div className="space-y-6">
      {/* Header con toggle per tag panel */}
      <div className="flex justify-between items-center">
        <div>
          <span className="text-xl font-semibold text-blue-800">🧩 Nodi PDK disponibili</span>
          <span className="ml-2 text-sm text-gray-600">
            ({filteredNodes.length} di {allNodes.length})
          </span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowTagPanel(!showTagPanel)}
            className={`px-4 py-2 rounded transition-colors ${
              showTagPanel 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {showTagPanel ? 'Nascondi Filtri' : 'Mostra Filtri Tag'}
          </button>
          <button
            onClick={resetFilters}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
          >
            Reset Filtri
          </button>
        </div>
      </div>

      {/* Tag Management Panel */}
      {showTagPanel && (
        <PDKTagManagementPanel
          items={allNodes}
          onItemsFilter={setFilteredNodes}
          showStats={true}
          showCloud={true}
        />
      )}

      {/* Loading and Error States */}
      {loading && (
        <div className="flex justify-center items-center py-8">
          <div className="text-blue-600">Caricamento plugins...</div>
        </div>
      )}
      
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Nodes Table */}
      {!loading && filteredNodes.length > 0 && (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white border border-gray-200 rounded-lg shadow">
            <thead>
              <tr className="bg-gray-100 text-gray-700 text-sm">
                <th className="px-4 py-3 text-left">Nome Nodo</th>
                <th className="px-4 py-3 text-left">Plugin</th>
                <th className="px-4 py-3 text-left">Descrizione</th>
                <th className="px-4 py-3 text-left">Categoria</th>
                <th className="px-4 py-3 text-left">Tags</th>
                <th className="px-4 py-3 text-left">Azioni</th>
              </tr>
            </thead>
            <tbody>
              {filteredNodes.map(node => (
                <tr key={`${node.pluginId}-${node.id}`} className="border-t hover:bg-gray-50">
                  <td className="px-4 py-3 font-semibold">
                    <div className="flex items-center gap-2">
                      <span>{node.icon || '🔧'}</span>
                      <span>{node.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500">{node.pluginName}</td>
                  <td className="px-4 py-3 text-sm max-w-xs">
                    <div className="truncate" title={node.description}>
                      {node.description}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm">
                    <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">
                      {node.category || node.type || 'General'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {((node.tags || []).concat(node.pluginTags || [])).slice(0, 3).map(tag => (
                        <PDKTagBadge key={tag} tag={tag} size="sm" />
                      ))}
                      {((node.tags || []).concat(node.pluginTags || [])).length > 3 && (
                        <span className="text-xs text-gray-500">
                          +{((node.tags || []).concat(node.pluginTags || [])).length - 3} more
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      <button 
                        className="text-blue-600 hover:text-blue-800 underline text-sm" 
                        onClick={() => handleNodeDetails(node)}
                      >
                        Dettagli
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* No Results */}
      {!loading && filteredNodes.length === 0 && allNodes.length > 0 && (
        <div className="text-center py-8 text-gray-500">
          <div className="text-lg mb-2">Nessun nodo trovato</div>
          <div className="text-sm">Prova a modificare i filtri di ricerca</div>
        </div>
      )}

      
      {/* Modal per i dettagli del nodo */}
      {showNodeModal && selectedNode && (
        <NodeDetailsModal 
          open={showNodeModal} 
          node={selectedNode} 
          plugin={selectedNode.plugin} 
          onClose={() => setShowNodeModal(false)} 
        />
      )}
    </div>
  );
};

export default PDKPluginList;
