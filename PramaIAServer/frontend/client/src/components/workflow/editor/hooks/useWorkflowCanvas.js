import { useState, useCallback, useRef, useMemo, useEffect } from 'react';
import { addEdge, useNodesState, useEdgesState } from 'reactflow';
import { nodeTypes as baseNodeTypes } from '../../nodes';
import PDKNode from '../../nodes/PDKNode';
import { usePDKNodes } from '../../nodes/DynamicPDKNodes';
import toast from 'react-hot-toast';

// Initial empty state for new workflows
const emptyNodes = [];
const emptyEdges = [];

// Funzione per ottenere icone di fallback basate sul tipo di nodo
const getIconForNodeType = (nodeType) => {
  if (nodeType.includes('pdf') || nodeType.includes('PDF')) return '📄';
  if (nodeType.includes('text') || nodeType.includes('Text')) return '📝';
  if (nodeType.includes('query') || nodeType.includes('Query')) return '❓';
  if (nodeType.includes('chroma') || nodeType.includes('vector')) return '🗄️';
  if (nodeType.includes('llm') || nodeType.includes('LLM')) return '🤖';
  if (nodeType.includes('input') || nodeType.includes('Input')) return '📥';
  if (nodeType.includes('output') || nodeType.includes('Output')) return '📤';
  if (nodeType.includes('embed') || nodeType.includes('Embed')) return '🧠';
  if (nodeType.includes('chunk') || nodeType.includes('Chunk')) return '✂️';
  if (nodeType.includes('filter') || nodeType.includes('Filter')) return '🔍';
  if (nodeType.includes('join') || nodeType.includes('Join')) return '🔗';
  return '🧩'; // default
};

/**
 * Custom hook per la gestione del canvas ReactFlow
 */
export const useWorkflowCanvas = () => {
  // Stati principali ReactFlow
  const [nodes, setNodes, onNodesChange] = useNodesState(emptyNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(emptyEdges);
  
  // Ref per il container React Flow
  const reactFlowWrapper = useRef(null);
  const [reactFlowInstance, setReactFlowInstance] = useState(null);

  // Hook per i nodi PDK 
  const { nodes: pdkNodes, loading: pdkLoading, error: pdkError, fetchNodes } = usePDKNodes();

  // Converti i nodi PDK in tipi di nodo per il mapping
  const pdkNodeTypes = useMemo(() => {
    const types = {};
    if (pdkNodes && Array.isArray(pdkNodes)) {
      pdkNodes.forEach(node => {
        if (node.type) {
          types[node.type] = PDKNode;
        }
      });
    }
    return types;
  }, [pdkNodes]);

  // Memoizza i nodeTypes per evitare ricreazione ad ogni render e usa un proxy 
  // per supportare anche tipi di nodi PDK che potrebbero non essere stati registrati esplicitamente
  const dynamicNodeTypes = useMemo(() => {
    console.log('[useWorkflowCanvas] Creating dynamic node types with PDK nodes:', Object.keys(pdkNodeTypes));
    const newNodeTypes = { ...baseNodeTypes };

    // Registra tutti i tipi di nodi PDK conosciuti
    Object.keys(pdkNodeTypes).forEach(nodeType => {
      newNodeTypes[nodeType] = PDKNode;
      console.log(`[useWorkflowCanvas] 📝 Registered PDK node type: "${nodeType}"`);
    });

    // Crea un proxy per intercettare richieste per qualsiasi tipo che inizia con pdk_
    // In questo modo supportiamo nodi che potrebbero essere stati aggiunti dopo il caricamento iniziale
    // o che non sono stati correttamente registrati
    return new Proxy(newNodeTypes, {
      get: (target, prop) => {
        // Se il tipo è già registrato, usalo
        if (target[prop]) {
          return target[prop];
        }
        
        // Se è un tipo PDK non ancora registrato, usa il componente PDKNode generico
        if (typeof prop === 'string' && prop.startsWith('pdk_')) {
          console.log(`[useWorkflowCanvas] 🔄 Dynamic PDK node requested: "${prop}"`);
          return PDKNode;
        }
        
        return target[prop];
      }
    });
  }, [pdkNodeTypes]);

  // Carica i nodi PDK al primo avvio se necessario
  useEffect(() => {
    if (!pdkLoading && (!pdkNodes || pdkNodes.length === 0)) {
      console.log('[useWorkflowCanvas] Loading PDK nodes on mount...');
      fetchNodes(false);
    }
  }, [pdkLoading, pdkNodes, fetchNodes]);

  // Debug: monitora i cambiamenti nei nodi
  useEffect(() => {
    console.log('[useWorkflowCanvas] Nodes state changed:', nodes);
    console.log('[useWorkflowCanvas] Current nodes count:', nodes.length);
  }, [nodes]);

  // Gestione drop di nuovi nodi
  const onDrop = useCallback((event) => {
    event.preventDefault();
    
    const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
    const type = event.dataTransfer.getData('application/reactflow');
    const nodeDefinition = JSON.parse(event.dataTransfer.getData('nodeDefinition') || '{}');
    
    if (typeof type === 'undefined' || !type) {
      return;
    }
    
    const position = reactFlowInstance.project({
      x: event.clientX - reactFlowBounds.left,
      y: event.clientY - reactFlowBounds.top,
    });
    
    const newNode = {
      id: `${type}_${Date.now()}`,
      type,
      position,
      data: {
        name: nodeDefinition.label || type,
        description: nodeDefinition.description || '',
        config: nodeDefinition.defaultConfig || {},
        icon: nodeDefinition.icon,
        color: nodeDefinition.color
      }
    };
    
    console.log('[useWorkflowCanvas] Adding new node:', newNode);
    setNodes((nds) => nds.concat(newNode));
  }, [reactFlowInstance, setNodes]);

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onConnect = useCallback((params) => {
    console.log('[useWorkflowCanvas] Connecting nodes:', params);
    setEdges((eds) => addEdge(params, eds));
  }, [setEdges]);

  // Funzione per rimuovere un nodo (chiamata dal pulsante delete nel PDKNode)
  const removeNode = useCallback((nodeId) => {
    console.log('[useWorkflowCanvas] Removing node:', nodeId);
    setNodes((nds) => nds.filter((node) => node.id !== nodeId));
    setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
    toast.success('Nodo rimosso');
  }, [setNodes, setEdges]);

  // Gestione eliminazione nodi con tasto delete
  const onNodesDelete = useCallback((nodesToDelete) => {
    const nodeIds = nodesToDelete.map(node => node.id);
    console.log('[useWorkflowCanvas] Deleting nodes:', nodeIds);
    setNodes((nds) => nds.filter((node) => !nodeIds.includes(node.id)));
    setEdges((eds) => eds.filter((edge) => !nodeIds.includes(edge.source) && !nodeIds.includes(edge.target)));
    toast.success(`${nodeIds.length} nodo/i eliminato/i`);
  }, [setNodes, setEdges]);

  // Rendi la funzione removeNode disponibile globalmente per PDKNode
  useEffect(() => {
    window.removeNode = removeNode;
    return () => {
      delete window.removeNode;
    };
  }, [removeNode]);

  // Carica dati del workflow nel canvas
  const loadWorkflowIntoCanvas = useCallback(async (workflowData) => {
    if (!workflowData) {
      console.log('[useWorkflowCanvas] No workflow data provided');
      return;
    }
    
    console.log('[useWorkflowCanvas] Loading workflow into canvas:', workflowData);
    console.log('[useWorkflowCanvas] Workflow nodes:', workflowData.nodes);
    console.log('[useWorkflowCanvas] Available PDK nodes for enrichment:', pdkNodes);
    
    try {
      // Carica nodi
      if (workflowData.nodes && workflowData.nodes.length > 0) {
        const loadedNodes = workflowData.nodes.map(node => {
          console.log('[useWorkflowCanvas] Processing node:', node);
          
          // Cerca le informazioni del nodo nei dati PDK per arricchire con icona e colore
          let nodeIcon = '🧩';  // default
          let nodeColor = '#3B82F6'; // default
          
          if (pdkNodes && pdkNodes.length > 0) {
            // MODIFICA BUGFIX: Sistema migliorato per gestire le icone dei nodi PDK
            const pdkNodeInfo = pdkNodes.find(pdkNode => pdkNode.type === node.node_type);
            
            // Verifica se il nodo ha già un'icona salvata e se è valida
            const hasSavedValidIcon = node.icon && node.icon.length > 0 && !node.icon.includes('?') && !node.icon.includes('�');
            
            if (hasSavedValidIcon) {
              // Se il nodo ha già un'icona valida, la utilizziamo direttamente
              nodeIcon = node.icon;
              nodeColor = node.color || '#3B82F6';
              console.log(`[useWorkflowCanvas] Using saved icon for ${node.node_type}:`, { icon: nodeIcon, color: nodeColor });
            } else if (pdkNodeInfo) {
              // Altrimenti, utilizziamo l'icona dal pdkNodeInfo se disponibile
              nodeIcon = pdkNodeInfo.icon && pdkNodeInfo.icon.length > 0 && !pdkNodeInfo.icon.includes('�') 
                ? pdkNodeInfo.icon 
                : getIconForNodeType(node.node_type);
              nodeColor = pdkNodeInfo.color || '#3B82F6';
              console.log(`[useWorkflowCanvas] Found PDK info for ${node.node_type}:`, { icon: nodeIcon, color: nodeColor });
            } else {
              // Se non c'è né un'icona salvata né info dal PDK, usiamo il fallback
              nodeIcon = getIconForNodeType(node.node_type);
              console.log(`[useWorkflowCanvas] No PDK info found for node type: ${node.node_type}, using fallback icon: ${nodeIcon}`);
            }
          } else {
            nodeIcon = getIconForNodeType(node.node_type);
          }
          
          return {
            id: node.node_id,
            type: node.node_type,
            position: node.position || { x: 100, y: 100 },
            data: {
              name: node.name,
              description: node.description,
              config: node.config || {},
              icon: nodeIcon,
              color: nodeColor
            }
          };
        });
        
        console.log('[useWorkflowCanvas] Setting enriched nodes:', loadedNodes);
        setNodes(loadedNodes);
        
        // Verifica immediata se i nodi sono stati settati
        setTimeout(() => {
          console.log('[useWorkflowCanvas] Nodes after setting (delayed check):');
        }, 100);
      } else {
        console.log('[useWorkflowCanvas] No nodes to load, clearing canvas');
        setNodes([]);
      }

      // Carica connessioni
      if (workflowData.connections && workflowData.connections.length > 0) {
        const loadedEdges = workflowData.connections.map((conn, index) => ({
          id: `edge-${index}`,
          source: conn.source_node,
          target: conn.target_node,
          sourceHandle: conn.source_output,
          targetHandle: conn.target_input
        }));
        
        console.log('[useWorkflowCanvas] Setting edges:', loadedEdges);
        setEdges(loadedEdges);
      } else {
        console.log('[useWorkflowCanvas] No connections to load, clearing edges');
        setEdges([]);
      }
      
    } catch (error) {
      console.error('[useWorkflowCanvas] Error loading workflow into canvas:', error);
      toast.error('Errore nel caricamento del workflow nel canvas');
    }
  }, [setNodes, setEdges, pdkNodes]);

  // Aggiorna configurazione di un nodo
  const updateNodeConfig = useCallback((nodeId, newConfig) => {
    console.log('[useWorkflowCanvas] Updating node config:', nodeId, newConfig);
    setNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, config: newConfig } }
          : node
      )
    );
  }, [setNodes]);

  return {
    // Stati ReactFlow
    nodes,
    edges,
    setNodes,
    setEdges,
    onNodesChange,
    onEdgesChange,
    
    // Ref e istanza
    reactFlowWrapper,
    reactFlowInstance,
    setReactFlowInstance,
    
    // Node types e PDK
    dynamicNodeTypes,
    pdkNodes,
    pdkLoading,
    
    // Event handlers
    onDrop,
    onDragOver,
    onConnect,
    onNodesDelete,
    removeNode,
    
    // Funzioni di utilità
    loadWorkflowIntoCanvas,
    updateNodeConfig
  };
};
