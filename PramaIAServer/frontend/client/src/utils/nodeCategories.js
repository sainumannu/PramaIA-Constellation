// Utility per la determinazione della categoria dei nodi
import { NODE_CATEGORIES, TAG_TO_CATEGORY_MAP } from '../config/appConfig';

/**
 * Determina la categoria di un nodo in base a vari criteri
 * @param {Object} node - Il nodo di cui determinare la categoria
 * @param {Object} plugin - Il plugin a cui appartiene il nodo (opzionale)
 * @param {Object} overrides - Sovrascritture di categoria configurate dall'amministratore (opzionale)
 * @returns {string} - Il valore della categoria determinata
 */
export const determineNodeCategory = (node, plugin = null, overrides = {}) => {
  const nodeFullId = plugin ? `${plugin.id}/${node.id}` : node.id;
  
  // 1. Verifica sovrascritture dell'amministratore (priorità massima)
  if (overrides && overrides[nodeFullId]) {
    return overrides[nodeFullId];
  }
  
  // 2. Verifica se il nodo ha una categoria esplicita
  if (node.category && NODE_CATEGORIES.some(c => c.value === node.category)) {
    return node.category;
  }
  
  // 3. Prova a inferire la categoria dai tag del nodo
  if (node.tags && node.tags.length > 0) {
    for (const tag of node.tags) {
      const tagLower = tag.toLowerCase();
      if (TAG_TO_CATEGORY_MAP[tagLower]) {
        return TAG_TO_CATEGORY_MAP[tagLower];
      }
    }
  }
  
  // 4. Usa la categoria del plugin se disponibile
  if (plugin && plugin.category && NODE_CATEGORIES.some(c => c.value === plugin.category)) {
    return plugin.category;
  }
  
  // 5. Default: categoria utility
  return 'utility';
};

/**
 * Carica le sovrascritture di categoria configurate dall'amministratore
 * @returns {Promise<Object>} - Oggetto con le sovrascritture di categoria
 */
export const loadCategoryOverrides = async () => {
  try {
    // Prima prova a caricare dal backend
    try {
      const response = await fetch('/api/config/node-categories-override');
      
      if (response.ok) {
        return await response.json();
      }
    } catch (backendError) {
      console.warn('Backend non disponibile per le sovrascritture, utilizzo localStorage', backendError);
    }
    
    // Fallback a localStorage se il backend non è disponibile
    const overridesJson = localStorage.getItem('nodeCategoryOverrides');
    return overridesJson ? JSON.parse(overridesJson) : {};
  } catch (error) {
    console.error('Errore nel caricamento delle sovrascritture delle categorie:', error);
    return {};
  }
};

/**
 * Salva una sovrascrittura di categoria per un nodo specifico
 * @param {string} nodeId - ID completo del nodo (plugin/node)
 * @param {string} categoryValue - Valore della categoria da assegnare
 * @returns {Promise<boolean>} - true se il salvataggio è riuscito, false altrimenti
 */
export const saveCategoryOverride = async (nodeId, categoryValue) => {
  try {
    // Prima prova a salvare sul backend
    let backendSuccess = false;
    
    try {
      const response = await fetch('/api/config/node-categories-override', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          nodeId,
          category: categoryValue
        }),
      });
      
      backendSuccess = response.ok;
    } catch (backendError) {
      console.warn('Backend non disponibile per salvare, utilizzo localStorage', backendError);
    }
    
    // Se il backend non è disponibile o fallisce, usa localStorage
    if (!backendSuccess) {
      // Carica le sovrascritture esistenti
      const overridesJson = localStorage.getItem('nodeCategoryOverrides');
      const overrides = overridesJson ? JSON.parse(overridesJson) : {};
      
      // Aggiorna con la nuova sovrascrittura
      overrides[nodeId] = categoryValue;
      
      // Salva nel localStorage
      localStorage.setItem('nodeCategoryOverrides', JSON.stringify(overrides));
    }
    
    return true;
  } catch (error) {
    console.error('Errore nel salvataggio della sovrascrittura della categoria:', error);
    return false;
  }
};

/**
 * Elimina una sovrascrittura di categoria per un nodo specifico
 * @param {string} nodeId - ID completo del nodo (plugin/node)
 * @returns {Promise<boolean>} - true se l'eliminazione è riuscita, false altrimenti
 */
export const resetCategoryOverride = async (nodeId) => {
  try {
    // Prima prova a eliminare dal backend
    let backendSuccess = false;
    
    try {
      const response = await fetch(`/api/config/node-categories-override/${nodeId}`, {
        method: 'DELETE',
      });
      
      backendSuccess = response.ok;
    } catch (backendError) {
      console.warn('Backend non disponibile per eliminare, utilizzo localStorage', backendError);
    }
    
    // Se il backend non è disponibile o fallisce, usa localStorage
    if (!backendSuccess) {
      // Carica le sovrascritture esistenti
      const overridesJson = localStorage.getItem('nodeCategoryOverrides');
      const overrides = overridesJson ? JSON.parse(overridesJson) : {};
      
      // Rimuovi la sovrascrittura
      if (overrides[nodeId]) {
        delete overrides[nodeId];
        
        // Salva nel localStorage
        localStorage.setItem('nodeCategoryOverrides', JSON.stringify(overrides));
      }
    }
    
    return true;
  } catch (error) {
    console.error('Errore nell\'eliminazione della sovrascrittura della categoria:', error);
    return false;
  }
};

/**
 * Organizza i nodi per categoria
 * @param {Array} nodes - Array di nodi da organizzare
 * @param {Object} plugins - Oggetto con i plugin a cui appartengono i nodi
 * @param {Object} overrides - Sovrascritture di categoria configurate dall'amministratore
 * @returns {Object} - Oggetto con i nodi organizzati per categoria
 */
export const organizeNodesByCategory = (nodes, plugins = {}, overrides = {}) => {
  const categorizedNodes = {};
  
  // Inizializza l'oggetto con tutte le categorie vuote
  NODE_CATEGORIES.forEach(category => {
    categorizedNodes[category.value] = [];
  });
  
  // Organizza i nodi nelle rispettive categorie
  nodes.forEach(node => {
    const plugin = node.pluginId ? plugins[node.pluginId] : null;
    const category = determineNodeCategory(node, plugin, overrides);
    
    // Assicurati che la categoria esista nell'oggetto
    if (!categorizedNodes[category]) {
      categorizedNodes[category] = [];
    }
    
    categorizedNodes[category].push(node);
  });
  
  return categorizedNodes;
};
