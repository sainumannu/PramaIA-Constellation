import { toast } from 'react-hot-toast';

/**
 * Utility per arricchire i nodi con informazioni PDK
 * 
 * @param {Array} nodes - Array di nodi da arricchire
 * @param {Function} fetchNodes - Funzione per recuperare i nodi PDK
 * @returns {Array} - Array di nodi arricchiti
 */
export const enrichNodesWithPDKInfo = async (nodes, fetchNodes) => {
  console.log('[WorkflowEditor] Enriching', nodes.length, 'nodes with PDK info');

  try {
    const pdkNodes = await fetchNodes();
    
    if (!pdkNodes || pdkNodes.length === 0) {
      console.warn('[WorkflowEditor] No PDK nodes available');
      return nodes.map(node => ({
        ...node,
        data: {
          ...node.data,
          icon: '',
          color: '#ffffff'
        }
      }));
    }

    const enrichedNodes = nodes.map(node => {
      // Trova il nodo PDK corrispondente
      let pdkNode = pdkNodes.find(pdk => {
        // Controlla se il tipo del PDK contiene il tipo del nodo
        if (pdk.type && pdk.type.includes(node.type)) {
          return true;
        }

        // Prova a confrontare direttamente i tipi
        if (pdk.type === node.type) {
          return true;
        }

        // Usa la mappa di corrispondenze tra tipi di nodo e nomi PDK
        const nameMap = {
          'pdf_input_node': 'PDF Input',
          'pdf_text_extractor': 'PDF Text Extractor',
          'text_chunker': 'Text Chunker',
          'text_embedder': 'Text Embedder',
          'chroma_vector_store': 'ChromaDB Writer',
          'query_input_node': 'Query Input',
          'chroma_retriever': 'ChromaDB Retriever',
          'llm_processor': 'LLM Processor',
          'pdf_results_formatter': 'Output Formatter',
          'text_joiner': 'Text Joiner',
          'text_filter': 'Text Filter',
          'user_context_provider': 'User Context Provider'
        };

        const expectedName = nameMap[node.type];
        return pdk.name === expectedName;
      });

      if (pdkNode) {
        // Preserva valori esistenti dal DB, usa PDK solo come fallback
        const existingIcon = node.data?.icon;
        const existingColor = node.data?.color;

        // Usa i valori esistenti se presenti e non vuoti, altrimenti fallback PDK
        const finalIcon = (existingIcon && existingIcon !== '') ? existingIcon : (pdkNode.icon || '');
        const finalColor = (existingColor && existingColor !== '' && existingColor !== '#ffffff') ? existingColor : (pdkNode.color || '#ffffff');

        const enrichedNode = {
          ...node,
          data: {
            ...node.data,
            icon: finalIcon,
            color: finalColor,
            pluginName: pdkNode.pluginName || '',
            pluginId: pdkNode.pluginId || '',
            configSchema: pdkNode.configSchema || null,
            defaultConfig: pdkNode.defaultConfig || {}
          }
        };

        return enrichedNode;
      }

      // Fallback per nodi che non sono PDK
      return {
        ...node,
        data: {
          ...node.data,
          icon: '',
          color: '#ffffff'
        }
      };
    });

    return enrichedNodes;

  } catch (error) {
    console.error('[WorkflowEditor] Error enriching nodes with PDK info:', error);
    // Ritorna i nodi originali senza icone
    return nodes.map(node => ({
      ...node,
      data: {
        ...node.data,
        icon: '',
        color: '#ffffff'
      }
    }));
  }
};

/**
 * Funzione per ottenere le informazioni sui tipi di dati collegati tra nodi
 *
 * @param {Object} edge - L'edge da analizzare
 * @param {Array} nodes - Array di nodi del workflow
 * @returns {Object|null} - Informazioni sull'edge o null se non è possibile determinarle
 */
export const getEdgeDataTypeInfo = (edge, nodes) => {
  if (!edge || !nodes.length) return null;

  // Trova il nodo sorgente e destinazione
  const sourceNode = nodes.find(n => n.id === edge.source);
  const targetNode = nodes.find(n => n.id === edge.target);

  if (!sourceNode || !targetNode) {
    console.warn('[WorkflowEditor] Cannot find source or target node for edge:', edge);
    return {
      sourceNode: sourceNode ? sourceNode.data.name : 'Nodo sconosciuto',
      targetNode: targetNode ? targetNode.data.name : 'Nodo sconosciuto',
      sourceOutput: edge.sourceHandle,
      targetInput: edge.targetHandle,
      dataType: 'Tipo di dato sconosciuto'
    };
  }

  // Struttura delle informazioni
  const info = {
    sourceNode: sourceNode.data.name,
    targetNode: targetNode.data.name,
    sourceOutput: edge.sourceHandle,
    targetInput: edge.targetHandle,
    dataType: 'Inferito dall\'editor'
  };

  // Inferisce il tipo di dato basandosi sui nomi dei nodi e dei handle
  // Questo è un sistema semplificato, in una versione più complessa
  // si potrebbe interrogare il server per avere informazioni precise

  // Mappa dei tipi di output comuni per ciascun tipo di nodo
  const outputTypeMap = {
    'pdf_input_node': 'PDF Document',
    'pdf_text_extractor': 'Text',
    'text_chunker': 'Text Chunks',
    'text_embedder': 'Embeddings',
    'text_joiner': 'Text',
    'text_filter': 'Filtered Text',
    'chroma_vector_store': 'Status',
    'query_input_node': 'Query Text',
    'chroma_retriever': 'Retrieved Documents',
    'llm_processor': 'LLM Response',
    'user_context_provider': 'User Context'
  };

  // Prende il tipo dal nodo sorgente
  info.dataType = outputTypeMap[sourceNode.type] || 'Dati generici';

  // Alcuni tipi specifici basati sulla combinazione di nodi
  if (sourceNode.type === 'text_chunker' && targetNode.type === 'text_embedder') {
    info.dataType = 'Chunks di testo';
  } else if (sourceNode.type === 'text_embedder' && targetNode.type === 'chroma_vector_store') {
    info.dataType = 'Vettori di embedding';
  } else if (sourceNode.type === 'chroma_retriever' && targetNode.type === 'llm_processor') {
    info.dataType = 'Documenti recuperati con punteggio di rilevanza';
  }

  return info;
};

/**
 * Funzione per caricare dati workflow già disponibili
 *
 * @param {Object} workflow - Dati del workflow da caricare
 * @param {Function} setCurrentWorkflow - Funzione per impostare il workflow corrente
 * @param {Function} setWorkflowName - Funzione per impostare il nome del workflow
 * @param {Function} setWorkflowDescription - Funzione per impostare la descrizione del workflow
 * @param {Function} setWorkflowTags - Funzione per impostare i tag del workflow
 * @param {Function} setWorkflowCategory - Funzione per impostare la categoria del workflow
 * @param {Function} setNodes - Funzione per impostare i nodi
 * @param {Function} setEdges - Funzione per impostare gli edges
 * @param {Function} enrichNodesWithPDKInfo - Funzione per arricchire i nodi con informazioni PDK
 * @param {Object} reactFlowInstance - Istanza di React Flow
 */
export const loadWorkflowData = async (
  workflow,
  setCurrentWorkflow,
  setWorkflowName,
  setWorkflowDescription,
  setWorkflowTags,
  setWorkflowCategory,
  setNodes,
  setEdges,
  enrichNodesWithPDKInfo,
  reactFlowInstance
) => {
  console.log('[WorkflowEditor] Loading workflow:', workflow?.name);

  setCurrentWorkflow(workflow);
  setWorkflowName(workflow.name);
  setWorkflowDescription(workflow.description || '');
  setWorkflowTags(workflow.tags || []);
  setWorkflowCategory(workflow.category || 'General');

  // Controlliamo se il workflow ha uno stato del viewport salvato
  const savedViewState = workflow.view_state;

  let loadedNodes = workflow.nodes.map(node => ({
    id: node.node_id,
    type: node.node_type,
    position: {
      // Rispetta esattamente le coordinate del nodo, anche se negative
      x: node.position?.x !== undefined ? node.position.x : (node.position_x || 100),
      y: node.position?.y !== undefined ? node.position.y : (node.position_y || 100)
    },
    data: {
      name: node.name || node.node_config?.name || node.node_config?.label || node.node_type,
      description: node.description || node.node_config?.description || '',
      config: node.config || node.node_config || {},
      // Preserva icon/color dal database se disponibili
      icon: node.icon || node.node_config?.icon || '',
      color: node.color || node.node_config?.color || '#ffffff'
    }
  }));

  // Arricchisci i nodi con informazioni PDK
  loadedNodes = await enrichNodesWithPDKInfo(loadedNodes);

  const loadedEdges = workflow.connections.map(conn => ({
    id: `${conn.source_node}-${conn.target_node}`,
    source: conn.source_node,
    target: conn.target_node,
    sourceHandle: conn.source_output,
    targetHandle: conn.target_input,
    type: 'default'
  }));

  setNodes(loadedNodes);
  setEdges(loadedEdges);

  // Centra la vista sui nodi caricati dopo un breve delay per permettere il render
  // ma solo se è un nuovo caricamento, non dopo un salvataggio
  if (!loadWorkflowData.hasBeenLoaded || loadedNodes.length > 0) {
    setTimeout(() => {
      if (reactFlowInstance && loadedNodes.length > 0) {
        // Se il workflow ha uno stato del viewport salvato nel database, usalo
        if (savedViewState && Object.keys(savedViewState).length > 0) {
          reactFlowInstance.setViewport(savedViewState);
        }
        // Altrimenti se abbiamo una viewport salvata dalla sessione corrente, usala
        else if (loadWorkflowData.lastViewport) {
          reactFlowInstance.setViewport(loadWorkflowData.lastViewport);
        }
        // Se non abbiamo nessuno stato salvato, centra la vista
        else {
          reactFlowInstance.fitView({ padding: 0.1 });
        }

        // Contrassegna che il workflow è stato caricato almeno una volta
        loadWorkflowData.hasBeenLoaded = true;
      }
    }, 100);
  }

  toast.success(`Workflow "${workflow.name}" caricato`);
};

// Esporta funzioni ausiliari
export default {
  enrichNodesWithPDKInfo,
  getEdgeDataTypeInfo,
  loadWorkflowData
};
