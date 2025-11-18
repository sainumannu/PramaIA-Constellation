import React from 'react';
import TagEditor from '../../TagEditor';
import WorkflowSelectModal from '../../WorkflowSelectModal';
import NodeConfigForm from './NodeConfigForm';
import toast from 'react-hot-toast';

/**
 * Componente per la visualizzazione delle informazioni sui collegamenti tra nodi
 * 
 * @param {boolean} showEdgeInfoModal - Flag per mostrare/nascondere il modale
 * @param {Object} selectedEdge - Edge selezionato
 * @param {Function} getEdgeDataTypeInfo - Funzione per ottenere le informazioni sull'edge
 * @param {Function} setShowEdgeInfoModal - Funzione per impostare la visibilità del modale
 * @param {Array} nodes - Array di nodi del workflow
 * @returns {JSX.Element|null} - Componente React o null se il modale non è visibile
 */
export const EdgeInfoModal = ({ 
  showEdgeInfoModal, 
  selectedEdge, 
  getEdgeDataTypeInfo, 
  setShowEdgeInfoModal,
  nodes
}) => {
  if (!showEdgeInfoModal || !selectedEdge) return null;
  
  const edgeInfo = getEdgeDataTypeInfo(selectedEdge, nodes);
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">
            Informazioni Collegamento
          </h3>
          <button
            onClick={() => setShowEdgeInfoModal(false)}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>
        
        {edgeInfo ? (
          <div className="space-y-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-lg mb-2">Tipo di Dato</h4>
              <div className="px-3 py-2 bg-blue-100 text-blue-800 rounded-md font-medium">
                {edgeInfo.dataType}
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-gray-700 mb-1">Da Nodo</h4>
                <div className="px-3 py-2 bg-gray-100 rounded-md">
                  {edgeInfo.sourceNode}
                </div>
                <p className="mt-1 text-sm text-gray-500">Output: {edgeInfo.sourceOutput}</p>
              </div>
              <div>
                <h4 className="font-medium text-gray-700 mb-1">A Nodo</h4>
                <div className="px-3 py-2 bg-gray-100 rounded-md">
                  {edgeInfo.targetNode}
                </div>
                <p className="mt-1 text-sm text-gray-500">Input: {edgeInfo.targetInput}</p>
              </div>
            </div>
            
            <div className="mt-4 border-t pt-4">
              <p className="text-sm text-gray-500 italic">
                I tipi di dato sono inferiti in base al tipo di nodo e alle connessioni.
              </p>
            </div>
          </div>
        ) : (
          <div className="text-center p-4">
            <p className="text-gray-600">Nessuna informazione disponibile per questo collegamento.</p>
          </div>
        )}
        
        <div className="mt-6 flex justify-end">
          <button
            onClick={() => setShowEdgeInfoModal(false)}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            Chiudi
          </button>
        </div>
      </div>
    </div>
  );
};

/**
 * Componente per la configurazione dei nodi
 * 
 * @param {boolean} showNodeConfig - Flag per mostrare/nascondere il modale
 * @param {Object} selectedNode - Nodo selezionato
 * @param {Function} setShowNodeConfig - Funzione per impostare la visibilità del modale
 * @param {Function} removeNode - Funzione per rimuovere un nodo
 * @param {Function} setNodes - Funzione per aggiornare i nodi
 * @returns {JSX.Element|null} - Componente React o null se il modale non è visibile
 */
export const NodeConfigModal = ({ 
  showNodeConfig, 
  selectedNode, 
  setShowNodeConfig, 
  removeNode, 
  setNodes 
}) => {
  if (!showNodeConfig || !selectedNode) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">
            Configurazione Nodo: {selectedNode.data.name}
          </h3>
          <button
            onClick={() => setShowNodeConfig(false)}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>
        
        <div className="space-y-4">
          {/* Informazioni nodo */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
            <div className="text-sm text-gray-600">{selectedNode.type}</div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Descrizione</label>
            <div className="text-sm text-gray-600">{selectedNode.data.description || 'Nessuna descrizione'}</div>
          </div>
          
          <hr className="my-4" />
          
          {/* Pulsante di eliminazione */}
          <div className="flex justify-end mb-4">
            <button
              onClick={() => {
                if (window.confirm(`Sei sicuro di voler eliminare questo nodo "${selectedNode.data.name}"?`)) {
                  removeNode(selectedNode.id);
                  setShowNodeConfig(false);
                }
              }}
              className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors"
            >
              Elimina nodo
            </button>
          </div>
          
          {/* Form di configurazione dinamico */}
          <NodeConfigForm
            node={selectedNode}
            onSave={(newConfig) => {
              console.log('[WorkflowEditor] Saving node config:', newConfig);
              
              // Aggiorna la configurazione del nodo
              setNodes(prevNodes => 
                prevNodes.map(node => 
                  node.id === selectedNode.id 
                    ? { 
                        ...node, 
                        data: { 
                          ...node.data, 
                          config: newConfig 
                        } 
                      }
                    : node
                )
              );
              
              toast.success('Configurazione salvata!');
              setShowNodeConfig(false);
            }}
            onCancel={() => setShowNodeConfig(false)}
          />
        </div>
      </div>
    </div>
  );
};

/**
 * Componente per i modali dell'editor di workflow
 * 
 * @param {Object} props - Proprietà del componente
 * @returns {JSX.Element} - Componente React
 */
export const WorkflowEditorModals = ({
  showSelectModal,
  showTagEditor,
  showNodeConfig,
  showEdgeInfoModal,
  workflowTags,
  selectedNode,
  selectedEdge,
  setShowSelectModal,
  setShowTagEditor,
  setShowNodeConfig,
  setShowEdgeInfoModal,
  setWorkflowTags,
  setNodes,
  loadWorkflow,
  removeNode,
  getEdgeDataTypeInfo,
  nodes
}) => {
  return (
    <>
      {/* Modale selezione workflow */}
      {showSelectModal && (
        <WorkflowSelectModal
          onSelect={(workflow) => {
            loadWorkflow(workflow.workflow_id);
            setShowSelectModal(false);
          }}
          onClose={() => setShowSelectModal(false)}
        />
      )}
      
      {/* Modale configurazione nodo */}
      <NodeConfigModal 
        showNodeConfig={showNodeConfig}
        selectedNode={selectedNode}
        setShowNodeConfig={setShowNodeConfig}
        removeNode={removeNode}
        setNodes={setNodes}
      />
      
      {/* Modale informazioni collegamento */}
      <EdgeInfoModal
        showEdgeInfoModal={showEdgeInfoModal}
        selectedEdge={selectedEdge}
        getEdgeDataTypeInfo={getEdgeDataTypeInfo}
        setShowEdgeInfoModal={setShowEdgeInfoModal}
        nodes={nodes}
      />
      
      {/* Tag Editor come componente controllato */}
      {showTagEditor && (
        <div className="border-b border-gray-200 p-4 bg-white shadow-md">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-lg font-semibold">Gestione Tag Workflow</h3>
            <button
              onClick={() => setShowTagEditor(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          <TagEditor
            tags={workflowTags}
            onSave={(tags) => {
              setWorkflowTags(tags);
              setShowTagEditor(false);
            }}
            onClose={() => setShowTagEditor(false)}
            className="max-h-64 overflow-y-auto"
          />
        </div>
      )}
    </>
  );
};

export default WorkflowEditorModals;
