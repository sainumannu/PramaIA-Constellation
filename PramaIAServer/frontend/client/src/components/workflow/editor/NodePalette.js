import React, { useState, useEffect, useMemo } from 'react';
import { usePDKNodes } from '../nodes/DynamicPDKNodes';
import { API_BASE_URL } from '../../../config/appConfig';
import axios from 'axios';

// Debug flag
const DEBUG_MODE = true;
const PDK_DISCOVERY_API = `${API_BASE_URL}/api/workflows/pdk-nodes`;
// Aggiungiamo un endpoint diretto al PDK Server come fallback
const PDK_DIRECT_API = `http://localhost:3001/api/nodes`;

const NodePalette = ({ onDragStart }) => {
  console.log('[NodePalette] Component mounting in ' + (DEBUG_MODE ? 'DEBUG' : 'NORMAL') + ' mode');
  
  const [expandedCategories, setExpandedCategories] = useState({
    Input: true,
    Processing: true,
    LLM: true,
    Output: true,
    'Debug': true
  });

  const [pdkNodes, setPDKNodes] = useState([]);
  const [rawPdkNodes, setRawPdkNodes] = useState([]);
  const { fetchNodes } = usePDKNodes();
  
  // Stato per il filtro di ricerca
  const [searchFilter, setSearchFilter] = useState('');

  useEffect(() => {
    // ID univoco per tracciare questo effetto
    const effectId = Math.random().toString(36).substring(2, 8);
    console.log(`[NodePalette] Effect initializing (ID: ${effectId})`);
    
    let isMounted = true; // Flag per prevenire aggiornamenti su componenti smontati
    
    // Sanifica solo icone corrotte o mancanti (nessun fallback deterministico)
    const safeIcon = (icon) => {
      if (!icon || typeof icon !== 'string') return '🧩';
      if (icon.includes('�')) return '🧩';
      return icon;
    };

    async function fetchDirectPDKNodes() {
      console.log('[NodePalette] DEBUG: Fetching PDK nodes directly from API');
      try {
        // Prima prova con l'endpoint del backend
        try {
          // Recupera il token dal localStorage
          const token = localStorage.getItem('token');
          const headers = token ? { Authorization: `Bearer ${token}` } : {};
          console.log('[NodePalette] Making request with auth header:', !!token);
          
          console.log('[NodePalette] DEBUG: Trying backend endpoint:', PDK_DISCOVERY_API);
          const response = await axios.get(PDK_DISCOVERY_API, { headers, timeout: 5000 });
          console.log('[NodePalette] DEBUG: Backend API response status:', response.status);
          const nodes = response.data.nodes || [];
          
          if (nodes && nodes.length > 0) {
            if (isMounted) {
              console.log('[NodePalette] DEBUG: Setting raw PDK nodes from backend:', nodes.length);
              setRawPdkNodes(nodes);
              
              // Mappa i nodi nel formato richiesto dalla palette
              const mappedNodes = nodes.map(node => ({
                type: node.type,
                label: node.display_name || node.name,
                icon: safeIcon(node.icon),
                description: node.description || '',
                configSchema: node.configSchema || {},  // Ora usiamo camelCase
                defaultConfig: node.defaultConfig || {},
                pluginId: node.plugin_id || node.pluginId,
                pluginName: node.plugin_name || node.pluginName,
                pluginDisplayName: node.plugin_display_name || node.plugin_name,
                category: node.category || node.group || '',
                pluginVersion: node.plugin_version
              }));
              
              setPDKNodes(mappedNodes);
              return true; // Successo
            }
          } else {
            console.warn('[NodePalette] DEBUG: Backend returned zero nodes, trying direct PDK API');
            throw new Error('Backend returned zero nodes');
          }
        } catch (backendError) {
          // Se l'endpoint del backend fallisce, prova l'endpoint diretto
          console.warn('[NodePalette] DEBUG: Backend fetch failed:', backendError.message);
          console.log('[NodePalette] DEBUG: Trying direct PDK endpoint:', PDK_DIRECT_API);
          
          const directResponse = await axios.get(PDK_DIRECT_API, { timeout: 5000 });
          console.log('[NodePalette] DEBUG: Direct PDK API response status:', directResponse.status);
          const directNodes = directResponse.data.nodes || [];
          
          if (directNodes && directNodes.length > 0 && isMounted) {
            console.log('[NodePalette] DEBUG: Setting raw PDK nodes from direct API:', directNodes.length);
            setRawPdkNodes(directNodes);
            
            // Mappa i nodi nel formato richiesto dalla palette
            const mappedNodes = directNodes.map(node => ({
              type: node.type,
              label: node.display_name || node.name,
              icon: safeIcon(node.icon),
              description: node.description || '',
              configSchema: node.configSchema || {},
              defaultConfig: node.defaultConfig || {},
              pluginId: node.pluginId,
              pluginName: node.pluginName,
              pluginDisplayName: node.pluginDisplayName || node.pluginName,
              category: node.category || node.group || '',
              pluginVersion: node.pluginVersion
            }));
            
            setPDKNodes(mappedNodes);
            return true; // Successo
          } else {
            console.error('[NodePalette] DEBUG: Direct PDK API returned zero nodes or component unmounted');
            throw new Error('Direct PDK API returned zero nodes');
          }
        }
      } catch (err) {
        console.error('[NodePalette] DEBUG: All attempts to fetch PDK nodes failed:', err);
        if (isMounted) setRawPdkNodes([]);
        return false; // Fallimento
      }
    }
    
    // Nuova logica: carichiamo i nodi PDK anche se non esiste token
    // Questo evita palette vuote quando l'utente non ha ancora effettuato il login
    async function fetchInitialNodes() {
      console.log(`[NodePalette] Fetching initial PDK nodes (Effect ID: ${effectId})`);
      try {
        // Forza un refresh iniziale per evitare cache stantia delle icone
        const nodes = await fetchNodes(true);

        // Previene aggiornamenti se il componente è stato smontato
        if (!isMounted) {
          console.log(`[NodePalette] Component unmounted, not updating (Effect ID: ${effectId})`);
          return;
        }

        console.log(`[NodePalette] PDK nodes received (Effect ID: ${effectId}):`, nodes.length);
        if (DEBUG_MODE) {
          console.log(`[NodePalette] PDK nodes types:`, nodes.map(n => n.type));
        }
        
        // Applica safeIcon anche qui (percorso cache/fetchNodes)
        const mapped = nodes.map(n => ({ ...n, icon: safeIcon(n.icon) }));
        setPDKNodes(mapped);
      } catch (error) {
        console.warn(`[NodePalette] fetchNodes failed, attempting direct fetch (Effect ID: ${effectId}):`, error.message || error);
        // Fallback diretto
        const success = await fetchDirectPDKNodes();
        
        // Se anche il direct fetch fallisce, usa i nodi di fallback definiti in index.js
        if (pdkNodes.length === 0) {
          console.warn('[NodePalette] Tutti i tentativi di fetch falliti, usando nodi di fallback');
          
          // Importa i nodeDefinitions da index.js
          try {
            const { nodeDefinitions } = await import('../nodes/index.js');
            console.log('[NodePalette] Nodi di fallback caricati:', nodeDefinitions);
            
            if (nodeDefinitions && nodeDefinitions.length > 0) {
              if (isMounted) {
                setPDKNodes(nodeDefinitions);
              }
            } else {
              console.error('[NodePalette] Nodi di fallback non disponibili');
            }
          } catch (importErr) {
            console.error('[NodePalette] Errore nel caricamento dei nodi di fallback:', importErr);
          }
        }
      }
    }
    
    // Utilizziamo un timeout per consentire al WorkflowEditor di caricare i nodi PDK prima
    // Questo riduce le chiamate multiple al backend
    const timer = setTimeout(() => {
      fetchInitialNodes();
    }, 500); // Ritardo di 500ms
    
    // Aggiorna se il token cambia in un'altra tab
    window.addEventListener('storage', fetchInitialNodes);
    
    // Cleanup
    return () => {
      console.log(`[NodePalette] Effect cleanup (ID: ${effectId})`);
      clearTimeout(timer);
      isMounted = false;
      window.removeEventListener('storage', fetchInitialNodes);
    };
  }, []); // fetchNodes è stabilizzato con useCallback, non serve includerlo

  const toggleCategory = (category) => {
    setExpandedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }));
  };

  const onDragStartHandler = (event, nodeType, nodeDefinition) => {
    console.log('[NodePalette] Drag start - nodeType:', nodeType);
    console.log('[NodePalette] Drag start - nodeDefinition:', nodeDefinition);
    
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.setData('nodeDefinition', JSON.stringify(nodeDefinition));
    event.dataTransfer.effectAllowed = 'move';
    
    if (onDragStart) {
      onDragStart(event, nodeType, nodeDefinition);
    }
  };

  // Funzione per filtrare i nodi in base alla ricerca
  const filterNodes = (nodes, searchTerm) => {
    if (!searchTerm) return nodes;
    
    const lowerSearch = searchTerm.toLowerCase();
    return nodes.filter(node => 
      node.label.toLowerCase().includes(lowerSearch) || 
      node.description.toLowerCase().includes(lowerSearch)
    );
  };
  
  // Raggruppa i nodi PDK per categoria (se presente) altrimenti per display name del plugin
  const pdkNodesByPlugin = useMemo(() => {
    // Se non ci sono nodi PDK, ritorna un oggetto vuoto
    if (!pdkNodes.length) return {};
    
    // Raggruppa i nodi per categoria o per display name del plugin
    const groupedNodes = {};
    pdkNodes.forEach(node => {
      const groupKey = node.category || node.pluginDisplayName || node.pluginName || 'Altri Plugin';
      if (!groupedNodes[groupKey]) {
        groupedNodes[groupKey] = [];
      }
      groupedNodes[groupKey].push(node);
    });
    
    return groupedNodes;
  }, [pdkNodes]);
  
  return (
    <div className="bg-white h-full overflow-y-auto">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Node Library</h2>
        <p className="text-sm text-gray-500 mt-1">Trascina i nodi nell'editor</p>
        
        {/* Campo di ricerca */}
        <div className="mt-3">
          <input
            type="text"
            placeholder="Cerca nodi..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
          />
        </div>
      </div>

      <div className="p-2">
        {/* Nodi nativi rimossi: la palette mostra solo i nodi PDK */}

        {/* Sezione di debug */}
        {DEBUG_MODE && (
          <div className="mb-4">
            <button
              onClick={() => toggleCategory('Debug')}
              className="w-full flex items-center justify-between px-3 py-2 text-left bg-red-50 hover:bg-red-100 rounded-lg transition-colors"
            >
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <span className="font-medium text-red-900">DEBUG PDK</span>
                <span className="text-xs text-red-500">({rawPdkNodes.length})</span>
              </div>
              <div className={`transform transition-transform ${expandedCategories['Debug'] ? 'rotate-90' : ''}`}>
                ▶
              </div>
            </button>
            {expandedCategories['Debug'] && (
              <div className="mt-2">
                <div>Debug mode enabled</div>
              </div>
            )}
          </div>
        )}

        {/* Plugin PDK Categories - Dynamic */}
        {Object.entries(pdkNodesByPlugin).map(([pluginName, pluginNodes]) => {
          // Filtra i nodi per la ricerca
          const filteredPluginNodes = filterNodes(pluginNodes, searchFilter);
          
          // Non mostrare plugin vuoti quando c'è un filtro attivo
          if (searchFilter && filteredPluginNodes.length === 0) return null;
          
          // Genera colori personalizzati per ciascun plugin
          // Prende l'hash del nome del plugin per generare un colore coerente
          const hashCode = Array.from(pluginName).reduce(
            (hash, char) => char.charCodeAt(0) + ((hash << 5) - hash), 0
          );
          const hue = Math.abs(hashCode % 360);
          const bgColor = `hsl(${hue}, 70%, 85%)`;  // Colore pastello
          
          return (
            <div key={pluginName} className="mb-4">
              <button
                onClick={() => toggleCategory(pluginName)}
                className="w-full flex items-center justify-between px-3 py-2 text-left bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <div className="flex items-center space-x-2">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: bgColor }}
                  />
                  <span className="font-medium text-gray-900">
                    {pluginName}
                  </span>
                  <span className="text-xs text-gray-500">
                    ({filteredPluginNodes.length})
                  </span>
                </div>
                <div className={`transform transition-transform ${
                  expandedCategories[pluginName] ? 'rotate-90' : ''
                }`}>
                  ▶
                </div>
              </button>
              
              {/* Plugin Nodes */}
              {expandedCategories[pluginName] && (
                <div className="mt-2 space-y-1">
                  {filteredPluginNodes.length === 0 ? (
                    <div className="text-center py-4 text-sm text-gray-500">
                      Nessun nodo disponibile.
                      {DEBUG_MODE && <div className="text-xs mt-1">Controlla la sezione Debug.</div>}
                    </div>
                  ) : (
                    filteredPluginNodes.map((node) => (
                      <div
                        key={node.type}
                        draggable
                        onDragStart={(e) => onDragStartHandler(e, node.type, node)}
                        className="cursor-move bg-white border border-indigo-200 rounded-lg p-3 hover:border-indigo-300 hover:shadow-sm transition-all"
                      >
                        <div className="flex items-center space-x-3">
                          <div className="text-lg">{node.icon}</div>
                          <div className="flex-1 min-w-0">
                            <div className="font-medium text-sm text-gray-900">{node.label}</div>
                            <div className="text-xs text-gray-500 truncate">{node.description}</div>
                          </div>
                        </div>
                        
                        {/* ConfigSchema preview */}
                        {node.configSchema && node.configSchema.properties && (
                          <div className="mt-2 text-xs">
                            <div className="text-gray-400 mb-1">Parametri configurabili:</div>
                            <div className="bg-gray-50 p-2 rounded text-gray-600 max-h-16 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent">
                              {Object.entries(node.configSchema.properties).slice(0, 3).map(([key, prop]) => (
                                <div key={key} className="truncate mb-1">
                                  <span className="text-blue-600 font-medium">{prop.title || key}</span>
                                  {prop.type && (
                                    <span className="text-gray-400 ml-1">({prop.type})</span>
                                  )}
                                  {prop.default && (
                                    <span className="text-gray-500 ml-1">= {String(prop.default)}</span>
                                  )}
                                </div>
                              ))}
                              {Object.keys(node.configSchema.properties).length > 3 && (
                                <div className="text-gray-400 italic">
                                  +{Object.keys(node.configSchema.properties).length - 3} altri parametri...
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Help Section */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <h3 className="text-sm font-medium text-gray-900 mb-2">💡 Come usare:</h3>
        <ul className="text-xs text-gray-600 space-y-1">
          <li>• Trascina i nodi nell'editor</li>
          <li>• Collega i nodi dalle porte</li>
          <li>• Doppio click per configurare</li>
          <li>• Salva il workflow quando pronto</li>
        </ul>
      </div>
    </div>
  );
};

export default NodePalette;
