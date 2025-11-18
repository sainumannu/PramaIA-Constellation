import React, { useState, useEffect } from 'react';
import workflowService from '../services/workflowService';

const InputNodeSelector = ({ 
  workflowId, 
  selectedNodeId, 
  onNodeSelect, 
  triggerEventType,
  disabled = false,
  className = ""
}) => {
  const [inputNodes, setInputNodes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Carica i nodi di input disponibili per il workflow
  useEffect(() => {
    const loadInputNodes = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await workflowService.getWorkflowInputNodes(workflowId);
        setInputNodes(response.input_nodes || []);
        
        console.log('InputNodeSelector - Nodi caricati:', response.input_nodes);
        console.log('InputNodeSelector - selectedNodeId corrente:', selectedNodeId);
        
        // Verifica se il nodo selezionato è nella lista
        if (selectedNodeId && response.input_nodes?.length > 0) {
          const selectedNodeExists = response.input_nodes.some(node => node.node_id === selectedNodeId);
          console.log('InputNodeSelector - Nodo selezionato esiste nella lista:', selectedNodeExists);
          
          if (!selectedNodeExists) {
            console.warn('InputNodeSelector - Il nodo selezionato non è presente nella lista dei nodi disponibili');
          }
        }
        
        // Se c'è solo un nodo disponibile, selezionalo automaticamente
        if (response.input_nodes?.length === 1 && !selectedNodeId) {
          onNodeSelect(response.input_nodes[0].node_id);
        }
        
      } catch (err) {
        console.error('Errore nel caricamento dei nodi di input:', err);
        setError('Errore nel caricamento dei nodi di input disponibili');
      } finally {
        setLoading(false);
      }
    };

    if (workflowId) {
      loadInputNodes();
    } else {
      setInputNodes([]);
    }
  }, [workflowId, selectedNodeId, onNodeSelect]);

  const getNodeRecommendationBadge = (node) => {
    const isRecommended = node.is_recommended_for?.includes(triggerEventType);
    if (!isRecommended || !triggerEventType) return null;
    
    return (
      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 ml-2">
        ⭐ Raccomandato
      </span>
    );
  };

  const getCompatibilityInfo = (node) => {
    if (!node.supported_input_types?.length) return null;
    
    const types = node.supported_input_types.map(type => type.type).join(', ');
    return (
      <div className="text-xs text-gray-500 mt-1">
        Tipi supportati: {types}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="animate-pulse">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Nodo di Ingresso
        </label>
        <div className="space-y-2">
          <div className="h-16 bg-gray-200 rounded"></div>
          <div className="h-16 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Nodo di Ingresso
        </label>
        <div className="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
          {error}
        </div>
      </div>
    );
  }

  if (!workflowId) {
    return (
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Nodo di Ingresso
        </label>
        <div className="text-sm text-gray-500 italic">
          Seleziona prima un workflow per vedere i nodi di input disponibili
        </div>
      </div>
    );
  }

  if (inputNodes.length === 0) {
    return (
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-700">
          Nodo di Ingresso
        </label>
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 px-3 py-2 rounded text-sm">
          ⚠️ Nessun nodo di input disponibile in questo workflow
        </div>
      </div>
    );
  }

  // Controllo se il nodo selezionato esiste nella lista
  const selectedNodeExists = selectedNodeId ? inputNodes.some(node => node.node_id === selectedNodeId) : true;

  return (
    <div className={`space-y-3 ${className}`}>
      <div className="flex items-center justify-between">
        <label className="block text-sm font-medium text-gray-700">
          Nodo di Ingresso
        </label>
        {triggerEventType && (
          <span className="text-xs text-gray-500">
            Evento: {triggerEventType}
          </span>
        )}
      </div>
      
      {/* Messaggio di avviso se il nodo selezionato non esiste più */}
      {selectedNodeId && !selectedNodeExists && (
        <div className="bg-orange-50 border border-orange-200 text-orange-700 px-3 py-2 rounded text-sm">
          ⚠️ Il nodo selezionato "{selectedNodeId}" non è più disponibile in questo workflow. 
          Seleziona un altro nodo dall'elenco sottostante.
        </div>
      )}
      
      <div className="space-y-3">
        {inputNodes.map(node => (
          <div 
            key={node.node_id} 
            className={`relative flex items-start space-x-3 p-3 border rounded-lg hover:bg-gray-50 transition-colors ${
              selectedNodeId === node.node_id 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-200'
            } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            onClick={() => !disabled && onNodeSelect(node.node_id)}
          >
            <input
              type="radio"
              id={node.node_id}
              name="inputNode"
              value={node.node_id}
              checked={selectedNodeId === node.node_id}
              onChange={() => !disabled && onNodeSelect(node.node_id)}
              disabled={disabled}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 mt-1"
            />
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center">
                <label 
                  htmlFor={node.node_id} 
                  className={`font-medium text-sm ${disabled ? 'cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  {node.name}
                </label>
                {getNodeRecommendationBadge(node)}
              </div>
              
              <div className="text-sm text-gray-600 mt-1">
                {node.description}
              </div>
              
              <div className="text-xs text-gray-500 mt-1">
                Tipo: <code className="bg-gray-100 px-1 rounded">{node.node_type}</code>
              </div>
              
              {getCompatibilityInfo(node)}
            </div>
          </div>
        ))}
      </div>
      
      {inputNodes.length > 1 && (
        <div className="text-xs text-gray-500 bg-blue-50 p-2 rounded border border-blue-200">
          💡 <strong>Suggerimento:</strong> I nodi marcati come "Raccomandato" sono ottimizzati per il tipo di evento selezionato.
        </div>
      )}
    </div>
  );
};

export default InputNodeSelector;
