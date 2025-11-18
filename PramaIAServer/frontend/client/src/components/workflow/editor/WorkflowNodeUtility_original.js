import { toast } from 'react-hot-toast';
import NodePropertyTracker from '../../../utils/NodePropertyTracker.js';

/**
 * Utility per arricchire i nodi con informazioni PDK
 * 
 * @param {Array} nodes - Array di nodi da arricchire
 * @param {Function} fetchNodes - Funzione per recuperare i nodi PDK
 * @returns {Array} - Array di nodi arricchiti
 */
export const enrichNodesWithPDKInfo = async (nodes, fetchNodes) => {
  console.log('🔍 [ENRICHING NODES] START - Function called with', nodes.length, 'nodes');
  console.log('[WorkflowEditor] enrichNodesWithPDKInfo - Input nodes:', nodes);
  console.log('[WorkflowEditor] Node types in workflow:', nodes.map(n => n.type));
  
  // DEBUGGING: Controlliamo se i nodi in input hanno già icon/color
  console.log('🚨 [ENRICHING NODES] INPUT NODE ANALYSIS:');
  nodes.forEach((node, index) => {
    console.log(`  Input Node ${index + 1}:`, {
      id: node.id,
      type: node.type,
      hasIcon: !!node.data?.icon,
      icon: node.data?.icon,
      hasColor: !!node.data?.color,
      color: node.data?.color,
      dataKeys: Object.keys(node.data || {}),
      fullDataObject: node.data
    });
  });
  
  // DEBUGGING: Chi ha chiamato questa funzione?
  console.log('🚨 [ENRICHING NODES] CALL STACK:');
  console.trace('enrichNodesWithPDKInfo called from:');
  
  try {
    // Usa l'hook per recuperare i nodi PDK
    console.log('[WorkflowEditor] Fetching PDK nodes...');
    const pdkNodes = await fetchNodes();
    console.log('[WorkflowEditor] 🔍 FETCH RESULT:', pdkNodes);
    console.log('[WorkflowEditor] 🔍 FETCH RESULT TYPE:', typeof pdkNodes);
    console.log('[WorkflowEditor] 🔍 FETCH RESULT LENGTH:', pdkNodes?.length);
    console.log('[WorkflowEditor] PDK nodes received:', pdkNodes);
    console.log('[WorkflowEditor] PDK node IDs available:', pdkNodes?.map(p => p.id) || 'NO PDK NODES');
    console.log('[WorkflowEditor] 📋 ALL PDK NODES DETAILS:');
    if (pdkNodes && pdkNodes.length > 0) { 
      pdkNodes.forEach((pdk, index) => {
        console.log(`  ${index + 1}. FULL NODE:`, pdk);
        console.log(`  ${index + 1}. ID: "${pdk.id}", Name: "${pdk.name}", Type: "${pdk.type}", Icon: "${pdk.icon}"`);
        console.log(`  ${index + 1}. Has configSchema:`, !!pdk.configSchema);
        if (pdk.configSchema) {
          console.log(`  ${index + 1}. ConfigSchema properties:`, Object.keys(pdk.configSchema.properties || {}));
        }
      });
    } else {
      console.log('  NO PDK NODES AVAILABLE');
    }
    
    if (!pdkNodes || pdkNodes.length === 0) {
      console.warn('[WorkflowEditor] No PDK nodes available');
      return nodes.map(node => ({
        ...node,
        data: {
          ...node.data,
          icon: '',  // Nessuna icona di fallback
          color: '#ffffff'
        }
      }));
    }
    
    const enrichedNodes = nodes.map(node => {
      console.log('[WorkflowEditor] Processing node:', node.type, node);
      console.log('[WorkflowEditor] 🔍 Looking for PDK node with ID matching:', node.type);
      
      // Trova il nodo PDK corrispondente - cerca per nome invece di ID
      let pdkNode = pdkNodes.find(pdk => {
        console.log('[WorkflowEditor] 🔍 TESTING MATCH for node.type:', node.type);
        console.log('[WorkflowEditor] 🔍   Against pdk.name:', pdk.name, '| pdk.type:', pdk.type);
        
        // PRIMA: Controlla se il tipo del PDK contiene il tipo del nodo
        if (pdk.type && pdk.type.includes(node.type)) {
          console.log('[WorkflowEditor] ✅ PDK type contains node type - MATCH!');
          return true;
        }
        
        // SECONDA: Prova a confrontare direttamente i tipi
        if (pdk.type === node.type) {
          console.log('[WorkflowEditor] ✅ Direct type match found!');
          return true;
        }
        
        // DEBUG: Log esatto delle stringhe
        console.log('[WorkflowEditor] 🔍 EXACT STRING COMPARISON:');
        console.log('[WorkflowEditor] 🔍   pdk.type length:', pdk.type?.length, 'content:', JSON.stringify(pdk.type));
        console.log('[WorkflowEditor] 🔍   node.type length:', node.type?.length, 'content:', JSON.stringify(node.type));
        console.log('[WorkflowEditor] 🔍   Are they equal?', pdk.type === node.type);
        console.log('[WorkflowEditor] 🔍   Does PDK include node?', pdk.type?.includes(node.type));
        
        // TERZA: Usa la mappa di corrispondenze tra tipi di nodo e nomi PDK
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
        const nameMatch = pdk.name === expectedName;
        if (expectedName) {
          console.log('[WorkflowEditor] 🔍 Name mapping test:', node.type, '->', expectedName, '| PDK name:', pdk.name, '| Match:', nameMatch);
        }
        if (nameMatch) {
          console.log('[WorkflowEditor] ✅ Name mapping match found!');
          return true;
        }
        
        // Nessun match trovato per questo PDK
        return false;
      });
      
      console.log('[WorkflowEditor] Found PDK node for', node.type, ':', pdkNode ? 'FOUND' : 'NOT FOUND');
      console.log('[WorkflowEditor] PDK node details:', pdkNode ? { name: pdkNode.name, icon: pdkNode.icon, color: pdkNode.color } : 'NOT FOUND');
      
      if (pdkNode) {
        console.log('[WorkflowEditor] 🔍 Found PDK node:', pdkNode.name);
        console.log('[WorkflowEditor] 🎨 Raw PDK icon:', pdkNode.icon);
        console.log('[WorkflowEditor] 🎨 Raw PDK icon charCodes:', pdkNode.icon ? Array.from(pdkNode.icon).map(char => char.charCodeAt(0)) : []);
        
        // Usa direttamente l'icona dal PDK senza alcun sistema di fallback statico
        const nodeIcon = pdkNode.icon || '';
        
        const enrichedNode = {
          ...node,
          data: {
            ...node.data,
            icon: nodeIcon,
            color: pdkNode.color || '#ffffff',
            pluginName: pdkNode.pluginName || '',
            pluginId: pdkNode.pluginId || '',
            configSchema: pdkNode.configSchema || null,
            defaultConfig: pdkNode.defaultConfig || {}
          }
        };
        console.log('[WorkflowEditor] Enriched node with PDK icon:', enrichedNode.data.icon);
        return enrichedNode;
      }
      
      // Fallback per nodi che non sono PDK
      const fallbackNode = {
        ...node,
        data: {
          ...node.data,
          icon: '',  // Nessuna icona di fallback, lasciamo vuoto
          color: '#ffffff'
        }
      };
      console.log('[WorkflowEditor] Node not found in PDK definitions, using no icon');
      return fallbackNode;
    });
    
    console.log('[WorkflowEditor] Final enriched nodes:', enrichedNodes);
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
  console.log('🚀 [LOAD WORKFLOW DATA] START - Loading workflow:', workflow?.name);
  console.log('[WorkflowEditor] Loading workflow data directly:', workflow);
  setCurrentWorkflow(workflow);
  setWorkflowName(workflow.name);
  setWorkflowDescription(workflow.description || '');
  setWorkflowTags(workflow.tags || []);
  setWorkflowCategory(workflow.category || 'General');
  
  // Controlliamo se il workflow ha uno stato del viewport salvato
  const savedViewState = workflow.view_state;
  console.log('[WorkflowEditor] Workflow has saved view state:', savedViewState);
  
  console.log('📋 [LOAD WORKFLOW DATA] Raw workflow nodes:', workflow.nodes);
  console.log('[WorkflowEditor] Loading nodes into editor:', workflow.nodes);
  
  // Aggiungiamo debug per vedere la struttura dei nodi
  if (workflow.nodes && workflow.nodes.length > 0) {
    console.log('🔍 [LOAD WORKFLOW DATA] First node structure:', workflow.nodes[0]);
    console.log('🔍 [LOAD WORKFLOW DATA] First node keys:', Object.keys(workflow.nodes[0]));
    console.log('🔍 [LOAD WORKFLOW DATA] First node node_config:', workflow.nodes[0].node_config);
  }
  
  let loadedNodes = workflow.nodes.map(node => ({
    id: node.node_id,
    type: node.node_type,
    position: { 
      // Rispetta esattamente le coordinate del nodo, anche se negative
      x: node.position?.x !== undefined ? node.position.x : (node.position_x || 100), 
      y: node.position?.y !== undefined ? node.position.y : (node.position_y || 100)
    },
    data: { 
      // I dati probabilmente sono in node_config, non a livello di root
      name: node.name || node.node_config?.name || node.node_config?.label || node.node_type,
      description: node.description || node.node_config?.description || '',
      config: node.config || node.node_config || {},
      // Preserva anche eventuali icone/colori già salvati nel database
      icon: node.node_config?.icon || '',
      color: node.node_config?.color || '#ffffff'
    }
  }));
  
  // Arricchisci i nodi con informazioni PDK
  console.log('[WorkflowEditor] Enriching nodes with PDK info...');
  loadedNodes = await enrichNodesWithPDKInfo(loadedNodes);
  
  console.log('🎯 [LOAD WORKFLOW DATA] After enrichment - loadedNodes:', loadedNodes);
  console.log('🎯 [LOAD WORKFLOW DATA] First enriched node icon:', loadedNodes[0]?.data?.icon);
  
  const loadedEdges = workflow.connections.map(conn => ({
    id: `${conn.source_node}-${conn.target_node}`,
    source: conn.source_node,
    target: conn.target_node,
    sourceHandle: conn.source_output,
    targetHandle: conn.target_input,
    type: 'default'
  }));
  
  console.log('[WorkflowEditor] Setting ENRICHED nodes:', loadedNodes);
  console.log('[WorkflowEditor] Setting edges:', loadedEdges);
  setNodes(loadedNodes);  // ← USANDO I NODI ARRICCHITI!
  setEdges(loadedEdges);
  
  // Centra la vista sui nodi caricati dopo un breve delay per permettere il render
  // ma solo se è un nuovo caricamento, non dopo un salvataggio
  if (!loadWorkflowData.hasBeenLoaded || loadedNodes.length > 0) {
    setTimeout(() => {
      if (reactFlowInstance && loadedNodes.length > 0) {
        // Se il workflow ha uno stato del viewport salvato nel database, usalo
        if (savedViewState && Object.keys(savedViewState).length > 0) {
          console.log('[WorkflowEditor] Restoring saved view state from database:', savedViewState);
          reactFlowInstance.setViewport(savedViewState);
        }
        // Altrimenti se abbiamo una viewport salvata dalla sessione corrente, usala
        else if (loadWorkflowData.lastViewport) {
          console.log('[WorkflowEditor] Restoring saved viewport from current session:', loadWorkflowData.lastViewport);
          reactFlowInstance.setViewport(loadWorkflowData.lastViewport);
        }
        // Se non abbiamo nessuno stato salvato, centra la vista
        else {
          console.log('[WorkflowEditor] No saved view state, fitting view to nodes');
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
