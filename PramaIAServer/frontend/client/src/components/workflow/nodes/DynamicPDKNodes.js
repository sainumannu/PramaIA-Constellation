// DynamicPDKNodes.js
// Utility per caricare i plugin PDK via API e trasformarli in nodi per la palette workflow

import axios from 'axios';
import { useState, useEffect, useCallback } from 'react';
import { API_BASE_URL } from '../../../config/appConfig';

// Usa l'endpoint FastAPI per la discovery - configurabile tramite appConfig
const PDK_DISCOVERY_API = `${API_BASE_URL}/api/workflows/pdk-nodes`;
// Aggiungiamo un endpoint di fallback diretto al PDK Server
const PDK_DIRECT_API = `http://localhost:3001/api/nodes`; // Endpoint diretto al PDK Server

// Abilitare debug per visualizzare log dettagliati
const DEBUG_MODE = true;

// Helper per log condizionali
const debugLog = (...args) => {
  if (DEBUG_MODE) console.log(...args);
};

// Cache globale per i nodi PDK - evita chiamate multiple all'API
let pdkNodesCache = null;
let fetchPromise = null;
let fetchInProgress = false;
let lastFetchTime = 0;
const CACHE_TTL = 60000; // 1 minuto di validità cache

// Hook per gestire i nodi PDK
export function usePDKNodes() {
  const [nodes, setNodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Funzione per fare il fetch manuale dei nodi - usa useCallback per stabilizzare il riferimento
  const fetchNodes = useCallback(async (forceRefresh = false) => {
    const id = Math.random().toString(36).substring(2, 8); // ID univoco per tracciamento
    debugLog(`[DynamicPDKNodes] fetchNodes called (ID: ${id})`);

    // Se abbiamo dati in cache validi e non è richiesto un refresh, usa quelli
    const now = Date.now();
    if (!forceRefresh && pdkNodesCache && (now - lastFetchTime) < CACHE_TTL) {
      debugLog('[DynamicPDKNodes] Using cached PDK nodes');
      setNodes(pdkNodesCache);
      setLoading(false);
      setError(null);
      return pdkNodesCache;
    }

    // Se c'è già un fetch in corso, aspetta quello invece di farne un altro
    if (fetchInProgress && fetchPromise) {
      debugLog('[DynamicPDKNodes] Fetch already in progress, waiting for it');
      try {
        const result = await fetchPromise;
        setNodes(result);
        setError(null);
        setLoading(false);
        return result;
      } catch (err) {
        setError(err);
        setLoading(false);
        throw err;
      }
    }

    // Altrimenti, esegui una nuova richiesta
    fetchInProgress = true;
    fetchPromise = fetchPDKNodes()
      .then(result => {
        pdkNodesCache = result;
        lastFetchTime = Date.now();
        setNodes(result);
        setError(null);
        setLoading(false);
        fetchInProgress = false;
        return result;
      })
      .catch(err => {
        console.error('Errore fetching PDK nodes:', err.message);
        
        // Usa fetch come fallback - ma solo se non c'è già stato un fallback
        if (!forceRefresh) {
          debugLog('[DynamicPDKNodes] Attempting fallback with direct fetch...');
          return fetch(PDK_DISCOVERY_API)
            .then(response => {
              if (!response.ok) {
                throw new Error(`API returned ${response.status}`);
              }
              return response.json();
            })
            .then(data => {
              const nodes = data.nodes || data;
              if (!nodes || nodes.length === 0) {
                throw new Error('No PDK nodes returned from API');
              }
              console.log(`Recovery successful! Caricati ${nodes.length} nodi`);
              pdkNodesCache = nodes;
              lastFetchTime = Date.now();
              setNodes(nodes);
              setError(null);
              return nodes;
            })
            .catch(retryError => {
              console.error('Recovery fallito:', retryError.message);
              setError(err);
              setNodes([]);
              throw err;
            })
            .finally(() => {
              fetchInProgress = false;
            });
        } else {
          setError(err);
          setNodes([]);
          fetchInProgress = false;
          throw err;
        }
      });

    try {
      return await fetchPromise;
    } catch (err) {
      throw err;
    }
  }, []); // Array vuoto - la funzione non dipende da niente

  // Nessun caricamento automatico per evitare chiamate duplicate
  // I componenti chiamano fetchNodes manualmente quando necessario
  useEffect(() => {
    debugLog('[DynamicPDKNodes] Init hook executed');
    setLoading(false);
  }, []); // Array vuoto = esegui solo al mount

  return { nodes, loading, error, fetchNodes };
}

// Funzione per il fetch dei nodi
async function fetchPDKNodes() {
  debugLog('\n🚀 [FRONTEND-PDK] ================== FETCH PDK NODES START ==================');
  debugLog('[FRONTEND-PDK] API URL (via backend):', PDK_DISCOVERY_API);
  debugLog('[FRONTEND-PDK] Direct API URL (fallback):', PDK_DIRECT_API);
  
  try {
    // Recupera il token dal localStorage
    const token = localStorage.getItem('token');
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    debugLog('[FRONTEND-PDK] Making request with auth header:', !!token);
    
    // Prima proviamo tramite il backend
    try {
      console.log('[FRONTEND-PDK] Tentativo via backend:', PDK_DISCOVERY_API);
      const res = await axios.get(PDK_DISCOVERY_API, { headers, timeout: 5000 });
      console.log(`[FRONTEND-PDK] Backend response status: ${res.status}`);
      
      // La risposta del backend ha la struttura {nodes: [...]}
      const nodes = res.data.nodes || res.data;
      
      if (nodes && nodes.length > 0) {
        // Log informativo sui nodi caricati - sempre mostrato ma ridotto
        console.log(`Caricati nodi PDK (via backend): ${nodes.length}`);
        return processNodes(nodes);
      } else {
        console.warn('[FRONTEND-PDK] Backend ha restituito zero nodi, provo chiamata diretta');
        throw new Error('Nessun nodo restituito dal backend');
      }
    } catch (backendError) {
      // Se il backend fallisce, prova chiamata diretta al PDK Server
      console.warn('[FRONTEND-PDK] Backend fallito:', backendError.message);
      console.log('[FRONTEND-PDK] Tentativo diretto al PDK Server:', PDK_DIRECT_API);
      
      const directRes = await axios.get(PDK_DIRECT_API, { timeout: 5000 });
      console.log(`[FRONTEND-PDK] Direct response status: ${directRes.status}`);
      
      // La risposta del PDK Server ha la struttura {nodes: [...]}
      const directNodes = directRes.data.nodes || directRes.data;
      
      if (directNodes && directNodes.length > 0) {
        console.log(`Caricati nodi PDK (diretti): ${directNodes.length}`);
        return processNodes(directNodes);
      } else {
        console.error('[FRONTEND-PDK] Anche il PDK Server diretto ha restituito zero nodi');
        throw new Error('Nessun nodo restituito anche dal PDK Server diretto');
      }
    }
  } catch (error) {
    // Log di errore - sempre mostrato ma semplificato
    console.error(`Errore durante il caricamento dei nodi PDK: ${error.message}`);
    
    if (DEBUG_MODE) {
      console.error('[FRONTEND-PDK] Dettagli errore:', error);
      if (error.response) {
        console.error('[FRONTEND-PDK] Response status:', error.response.status);
        console.error('[FRONTEND-PDK] Response headers:', error.response.headers);
        // Se è HTML, mostra i primi caratteri
        if (typeof error.response.data === 'string') {
          console.error('[FRONTEND-PDK] Response preview:', error.response.data.substring(0, 200));
        }
      }
    }
    
    throw error;
  }
}

// Funzione helper per processare i nodi (comune per entrambe le fonti)
function processNodes(nodes) {
  // Filtriamo i nodi di test - rimuoviamo qualsiasi nodo con 'test' nel nome o nel tipo (case insensitive)
  const filteredNodes = nodes.filter(node => {
    const nodeType = node.type?.toLowerCase() || '';
    const nodeName = node.name?.toLowerCase() || '';
    const nodeDisplayName = node.display_name?.toLowerCase() || '';
    
    // Consideriamo come test node solo quelli che hanno specificamente 'test' nel nome 
    // e non hanno il prefisso pdk_ standard
    const isExplicitTestNode = nodeType === 'pdk_test-plugin_test-node' || 
                              nodeType === 'test-plugin-node' ||
                              nodeType.includes('test-plugin');
    
    // Oppure il nodo contiene 'test' nel nome ma non è un nodo PDK valido
    const isImplicitTestNode = (nodeName.includes('test') || nodeDisplayName.includes('test')) && 
                              !nodeType.startsWith('pdk_');
    
    const isTestNode = isExplicitTestNode || isImplicitTestNode;
    
    if (isTestNode && DEBUG_MODE) {
      debugLog('[FRONTEND-PDK] Filtering out test node:', node.name, 'with type:', nodeType);
      return false;
    }
    return !isTestNode;
  });
  
  debugLog('[FRONTEND-PDK] Filtered out test nodes, remaining:', filteredNodes.length);
  
  // Sanifica solo icone corrotte o mancanti (nessun fallback deterministico)
  const safeIcon = (icon) => {
    if (!icon || typeof icon !== 'string') return '🧩';
    if (icon.includes('�')) return '🧩';
    return icon;
  };
  
  const mappedNodes = filteredNodes.map(node => {
    // Usa direttamente il tipo che arriva dal backend
    const nodeType = node.type;
    const originalIcon = node.icon || '🧩';
    
    return {
      type: nodeType,
      label: node.display_name || node.label || node.name,
      icon: safeIcon(originalIcon),
      description: node.description || '',
      configSchema: node.configSchema || node.config_schema || null,
      defaultConfig: node.defaultConfig || {},
      pluginId: node.plugin_id || node.pluginId,
      pluginName: node.plugin_name || node.pluginName,
      pluginDisplayName: node.plugin_display_name || node.pluginDisplayName || node.plugin_name || node.pluginName,
      category: node.category || node.group || '',
      pluginVersion: node.plugin_version || node.pluginVersion
    };
  });
  
  debugLog('\n📊 [FRONTEND-PDK] FINAL MAPPING RESULTS:');
  debugLog('[FRONTEND-PDK] Total mapped nodes:', mappedNodes.length);
  
  return mappedNodes;
}
