# Configurazione delle Categorie di Nodi nella Palette

## Panoramica

PramaIA supporta un sistema di categorizzazione funzionale unificato per tutti i nodi della palette, inclusi i nodi PDK. Questo approccio supera la precedente separazione tra nodi standard e nodi PDK, permettendo di organizzare tutti i componenti in base alla loro funzione reale anziché alla loro provenienza.

## Architettura della configurazione

Le categorie dei nodi sono configurate nel file di configurazione centralizzato del frontend:

- **`frontend/client/src/config/appConfig.js`**: Configurazione centralizzata del frontend React

## Struttura della configurazione

### Array NODE_CATEGORIES

Nel file `frontend/client/src/config/appConfig.js` è presente un array denominato `NODE_CATEGORIES` che definisce tutte le categorie funzionali disponibili per i nodi:

```javascript
// Configurazioni Node Palette - Categorie funzionali per tutti i nodi (inclusi PDK)
export const NODE_CATEGORIES = [
  { value: 'input', label: 'Input', description: 'Nodi per l\'acquisizione di dati' },
  { value: 'processing', label: 'Elaborazione', description: 'Nodi per l\'elaborazione generale dei dati' },
  { value: 'llm', label: 'LLM', description: 'Nodi per l\'integrazione con modelli linguistici' },
  { value: 'pdf', label: 'PDF', description: 'Nodi specifici per l\'elaborazione di documenti PDF' },
  { value: 'database', label: 'Database', description: 'Nodi per operazioni su database' },
  { value: 'output', label: 'Output', description: 'Nodi per l\'output e la visualizzazione' },
  { value: 'integration', label: 'Integrazione', description: 'Nodi per l\'integrazione con servizi esterni' },
  { value: 'utility', label: 'Utilità', description: 'Nodi di utilità generale' }
];
```

Ogni categoria è rappresentata da un oggetto con tre proprietà:
- **value**: Identificatore univoco della categoria (usato internamente dal sistema)
- **label**: Etichetta visualizzata nell'interfaccia utente
- **description**: Breve descrizione della categoria per aiutare l'utente a comprenderne lo scopo

## Utilizzo nel componente NodePalette

Il componente che gestisce la palette dei nodi utilizzerà questa configurazione centralizzata per organizzare e visualizzare i nodi disponibili, indipendentemente dalla loro provenienza (standard o PDK):

```javascript
import { NODE_CATEGORIES } from '../config/appConfig';

// All'interno del componente NodePalette
const renderNodeCategories = () => {
  return NODE_CATEGORIES.map(category => (
    <CategorySection 
      key={category.value}
      label={category.label}
      nodes={filterNodesByCategory(allNodes, category.value)}
      description={category.description}
    />
  ));
};
```

## Implementazione per i nodi PDK

### Metadati nei manifesti dei plugin

Per i nodi PDK, la categoria funzionale deve essere specificata nel manifesto del plugin:

```json
{
  "name": "pdf-processor-plugin",
  "version": "1.0.0",
  "nodes": [
    {
      "id": "pdf-extractor",
      "name": "PDF Text Extractor",
      "category": "pdf",
      "tags": ["extraction", "text"]
    },
    {
      "id": "pdf-metadata",
      "name": "PDF Metadata Reader",
      "category": "pdf",
      "tags": ["metadata", "document"]
    }
  ]
}
```

### Determinazione della categoria di un nodo

La categoria di un nodo viene determinata secondo il seguente ordine di priorità:

1. **Categoria esplicita** - Se il nodo specifica direttamente una categoria nel suo manifesto, questa viene utilizzata
2. **Inferenza dai tag** - Se il nodo non specifica una categoria ma ha tag correlati a una categoria (es. tag "pdf" → categoria "pdf")
3. **Categoria del plugin** - Se il plugin specifica una categoria a livello di plugin e il nodo non ha una categoria propria
4. **Categoria predefinita** - Se nessuna delle opzioni precedenti è applicabile, viene utilizzata la categoria "utility"

#### Implementazione della logica di inferenza

```javascript
// Funzione per determinare la categoria di un nodo
const determineNodeCategory = (node, plugin) => {
  // 1. Verifica se il nodo ha una categoria esplicita
  if (node.category && NODE_CATEGORIES.some(c => c.value === node.category)) {
    return node.category;
  }
  
  // 2. Prova a inferire la categoria dai tag del nodo
  if (node.tags && node.tags.length > 0) {
    // Mappa che associa tag a categorie
    const tagToCategoryMap = {
      'pdf': 'pdf',
      'database': 'database',
      'input': 'input',
      'output': 'output',
      'llm': 'llm',
      'ai': 'llm',
      'integration': 'integration',
      'api': 'integration'
    };
    
    // Cerca un tag che corrisponde a una categoria
    for (const tag of node.tags) {
      const tagLower = tag.toLowerCase();
      if (tagToCategoryMap[tagLower]) {
        return tagToCategoryMap[tagLower];
      }
    }
  }
  
  // 3. Usa la categoria del plugin se disponibile
  if (plugin && plugin.category) {
    return plugin.category;
  }
  
  // 4. Default: categoria utility
  return 'utility';
};
```

### Configurazione a livello di amministratore

Gli amministratori di sistema possono sovrascrivere le categorie dei nodi attraverso un file di configurazione JSON:

```json
{
  "nodeCategories": {
    "plugin-id/node-id": "custom-category",
    "another-plugin/another-node": "different-category"
  }
}
```

Questa configurazione ha la priorità più alta e consente di personalizzare le categorie dei nodi senza modificare i manifesti dei plugin.

### Integrazione con il sistema di tag

Il campo `category` è complementare ai `tags` esistenti. I tag forniscono una classificazione più granulare e multi-dimensionale, mentre la categoria rappresenta il gruppo funzionale principale.

## Personalizzazione delle categorie

### Aggiungere nuove categorie

Per aggiungere nuove categorie, è sufficiente modificare l'array `NODE_CATEGORIES` nel file `frontend/client/src/config/appConfig.js`:

```javascript
export const NODE_CATEGORIES = [
  // Categorie esistenti...
  { 
    value: 'ai-vision', 
    label: 'Visione AI', 
    description: 'Nodi per l\'elaborazione e l\'analisi di immagini tramite AI' 
  }
];
```

### Modificare categorie esistenti

Per modificare una categoria esistente, individuare la categoria nell'array `NODE_CATEGORIES` e aggiornarne le proprietà:

```javascript
// Da:
{ value: 'llm', label: 'LLM', description: 'Nodi per l\'integrazione con modelli linguistici' }
// A:
{ value: 'llm', label: 'AI Generativa', description: 'Nodi per l\'integrazione con modelli linguistici generativi' }
```

## Implementazione lato frontend

### Componente NodePalette aggiornato

Il componente NodePalette deve essere aggiornato per utilizzare il nuovo sistema di categorizzazione:

1. Eliminare la separazione tra nodi standard e nodi PDK
2. Raggruppare tutti i nodi in base alla loro categoria funzionale
3. Utilizzare le etichette e le descrizioni fornite in `NODE_CATEGORIES`
4. Implementare una visualizzazione coerente per tutti i nodi

### Supporto per la retrocompatibilità

Per supportare i plugin che non hanno ancora specificato una categoria, viene utilizzata la funzione `determineNodeCategory` descritta precedentemente:

```javascript
// Nel codice che elabora i nodi PDK
const getNodeCategory = (node, plugin) => {
  return determineNodeCategory(node, plugin);
};
```

### Interfaccia di amministrazione

Per facilitare la gestione delle categorie dei nodi, è consigliabile implementare un'interfaccia di amministrazione che consenta di:

1. Visualizzare tutti i nodi disponibili con le loro categorie attuali
2. Modificare la categoria di un nodo specifico
3. Impostare regole di categorizzazione automatica basate sui tag
4. Salvare queste configurazioni nel file di override delle categorie

```jsx
// Esempio di interfaccia di amministrazione per le categorie dei nodi
const NodeCategoryAdmin = () => {
  const [nodes, setNodes] = useState([]);
  const [categoryOverrides, setCategoryOverrides] = useState({});
  
  // Carica tutti i nodi e le sovrascritture di categoria
  useEffect(() => {
    fetchAllNodes().then(setNodes);
    fetchCategoryOverrides().then(setCategoryOverrides);
  }, []);
  
  // Gestisce il cambio di categoria per un nodo
  const handleCategoryChange = (nodeId, categoryValue) => {
    setCategoryOverrides(prev => ({
      ...prev,
      [nodeId]: categoryValue
    }));
    
    // Salva la modifica nel file di configurazione
    saveCategoryOverride(nodeId, categoryValue);
  };
  
  return (
    <div className="node-category-admin">
      <h2>Gestione Categorie Nodi</h2>
      
      <table>
        <thead>
          <tr>
            <th>Nome Nodo</th>
            <th>Plugin</th>
            <th>Categoria Originale</th>
            <th>Categoria Attuale</th>
            <th>Azioni</th>
          </tr>
        </thead>
        <tbody>
          {nodes.map(node => (
            <tr key={node.id}>
              <td>{node.name}</td>
              <td>{node.pluginName}</td>
              <td>{node.originalCategory}</td>
              <td>
                <select
                  value={categoryOverrides[node.id] || node.category}
                  onChange={(e) => handleCategoryChange(node.id, e.target.value)}
                >
                  {NODE_CATEGORIES.map(cat => (
                    <option key={cat.value} value={cat.value}>
                      {cat.label}
                    </option>
                  ))}
                </select>
              </td>
              <td>
                <button onClick={() => resetToDefaultCategory(node.id)}>
                  Reset
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

## Vantaggi dell'approccio unificato

1. **Organizzazione logica**: I nodi sono raggruppati in base alla loro funzione effettiva, non alla loro provenienza
2. **Coerenza nell'interfaccia utente**: Esperienza utente più intuitiva con categorie funzionali chiare
3. **Scalabilità**: Facilità nell'aggiungere nuove categorie funzionali al crescere del sistema
4. **Flessibilità per gli sviluppatori**: Gli sviluppatori di plugin possono categorizzare correttamente i loro nodi

## Note implementative

- Questa modifica richiede l'aggiornamento del componente NodePalette per utilizzare il nuovo sistema di categorizzazione
- È consigliabile aggiornare i manifesti dei plugin esistenti per specificare le categorie appropriate
- Il sistema di tag continua a funzionare in parallelo per fornire filtri più granulari
