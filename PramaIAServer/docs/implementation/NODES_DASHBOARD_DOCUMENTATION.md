# Gestione Centralizzata dei Nodi in PramaIA

## Panoramica

PramaIA introduce un sistema unificato di gestione dei nodi nella dashboard di amministrazione, integrando sia i nodi core che i nodi PDK in un'unica interfaccia. Questo sistema permette di visualizzare, categorizzare e gestire tutti i nodi disponibili nell'ecosistema PramaIA.

## Architettura dell'interfaccia

### Dashboard dei Nodi

La scheda "Nodi" nella dashboard di amministrazione è stata ampliata per includere:

1. **Visualizzazione unificata** - Tutti i nodi disponibili nell'ecosistema
2. **Gestione delle categorie** - Assegnazione e modifica delle categorie funzionali
3. **Sezione PDK dedicata** - Area specifica per i nodi provenienti dal PDK
4. **Filtri e ricerca** - Strumenti per trovare rapidamente nodi specifici

## Implementazione dell'Interfaccia

### Componenti Principali

#### NodesDashboard

Componente principale che integra la gestione di tutti i nodi:

```jsx
// Componente unificato per la gestione dei nodi
const NodesDashboard = () => {
  const [activeTab, setActiveTab] = useState('all');
  const [categoryOverrides, setCategoryOverrides] = useState({});
  
  return (
    <div className="nodes-dashboard">
      <h2>Gestione Nodi</h2>
      
      <Tabs value={activeTab} onChange={setActiveTab}>
        <Tab value="all" label="Tutti i Nodi" />
        <Tab value="core" label="Nodi Core" />
        <Tab value="pdk" label="Nodi PDK" />
        <Tab value="categories" label="Gestione Categorie" />
      </Tabs>
      
      {activeTab === 'all' && <AllNodesView />}
      {activeTab === 'core' && <CoreNodesView />}
      {activeTab === 'pdk' && <PDKNodesView />}
      {activeTab === 'categories' && <NodeCategoriesManager />}
    </div>
  );
};
```

#### NodeItem

Componente che rappresenta un singolo nodo nella lista, con funzionalità di visualizzazione dettagli:

```jsx
// Componente per un elemento nodo nella lista
const NodeItem = ({ node, plugin, categoryOverrides = {} }) => {
  const [detailsOpen, setDetailsOpen] = useState(false);
  
  // Determina la categoria del nodo
  const nodeId = plugin ? `${plugin.id}/${node.id}` : node.id;
  const overriddenCategory = categoryOverrides[nodeId];
  const computedCategory = determineNodeCategory(node, plugin);
  const nodeCategory = overriddenCategory || computedCategory;
  
  // Gestisce l'apertura del modal dei dettagli
  const handleOpenDetails = () => {
    setDetailsOpen(true);
  };
  
  return (
    <>
      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6">{node.name}</Typography>
          {node.description && (
            <Typography variant="body2" color="text.secondary">
              {node.description}
            </Typography>
          )}
          <Box sx={{ mt: 1 }}>
            <Chip 
              label={categoryInfo.label} 
              size="small" 
              color="primary" 
            />
            <Chip 
              label={plugin ? 'PDK' : 'Core'} 
              size="small" 
              variant="outlined"
            />
          </Box>
        </CardContent>
        <CardActions>
          <Button size="small" onClick={handleOpenDetails}>
            Dettagli
          </Button>
        </CardActions>
      </Card>
      
      <NodeDetailsModal 
        open={detailsOpen} 
        node={node} 
        plugin={plugin} 
        onClose={() => setDetailsOpen(false)} 
      />
    </>
  );
};
```

#### NodeDetailsModal

Modal che mostra i dettagli completi di un nodo quando si clicca sul pulsante "Dettagli":

```jsx
// Modal per visualizzare i dettagli di un nodo
const NodeDetailsModal = ({ open, node, plugin, onClose }) => {
  const [activeTab, setActiveTab] = useState('info');
  
  return (
    <Modal open={open} onClose={onClose}>
      <Paper sx={{ /* stili */ }}>
        <Typography variant="h5">{node.name}</Typography>
        
        <Tabs value={activeTab} onChange={(e, val) => setActiveTab(val)}>
          <Tab label="Informazioni" value="info" />
          <Tab label="Categoria" value="category" />
          {node.schema && <Tab label="Schema" value="schema" />}
        </Tabs>
        
        {activeTab === 'info' && (
          <Box>
            <Typography>ID: {node.id}</Typography>
            <Typography>Descrizione: {node.description}</Typography>
            <Typography>Tipo: {plugin ? 'PDK' : 'Core'}</Typography>
            {plugin && <Typography>Plugin: {plugin.name}</Typography>}
            <Typography>Tag: {renderTags(node.tags)}</Typography>
          </Box>
        )}
        
        {activeTab === 'category' && (
          <Box>
            <Typography variant="h6">{categoryInfo.label}</Typography>
            <Typography>{categoryInfo.description}</Typography>
            
            <Typography variant="subtitle2">
              Come viene determinata la categoria
            </Typography>
            {/* Dettagli sulla determinazione della categoria */}
          </Box>
        )}
        
        {activeTab === 'schema' && node.schema && (
          <Box>
            <pre>{JSON.stringify(node.schema, null, 2)}</pre>
          </Box>
        )}
        
        <Button onClick={onClose}>Chiudi</Button>
      </Paper>
    </Modal>
  );
};
```

### NodeCategoriesManager

Componente specifico per la gestione delle categorie:

```jsx
// Componente per la gestione delle categorie dei nodi
const NodeCategoriesManager = () => {
  const [nodes, setNodes] = useState([]);
  const [categoryOverrides, setCategoryOverrides] = useState({});
  const [loading, setLoading] = useState(true);
  
  // Carica tutti i nodi e le sovrascritture di categoria
  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchAllNodes(),
      loadCategoryOverrides()
    ]).then(([nodesData, overridesData]) => {
      setNodes(nodesData);
      setCategoryOverrides(overridesData);
      setLoading(false);
    });
  }, []);
  
  // Gestisce il cambio di categoria per un nodo
  const handleCategoryChange = async (nodeId, categoryValue) => {
    // Aggiorna localmente
    setCategoryOverrides(prev => ({
      ...prev,
      [nodeId]: categoryValue
    }));
    
    // Salva la modifica nel file di configurazione
    await saveCategoryOverride(nodeId, categoryValue);
  };
  
  // Ripristina la categoria predefinita
  const handleResetCategory = async (nodeId) => {
    // Aggiorna localmente
    setCategoryOverrides(prev => {
      const newOverrides = { ...prev };
      delete newOverrides[nodeId];
      return newOverrides;
    });
    
    // Elimina la sovrascrittura
    await resetCategoryOverride(nodeId);
  };
  
  if (loading) {
    return <div>Caricamento in corso...</div>;
  }
  
  return (
    <div className="node-categories-manager">
      <div className="category-manager-header">
        <h3>Gestione Categorie dei Nodi</h3>
        <p>
          Questa interfaccia permette di modificare la categoria di ciascun nodo.
          Le modifiche avranno effetto su come i nodi vengono visualizzati nella palette durante la creazione dei workflow.
        </p>
      </div>
      
      <div className="filters">
        <input type="text" placeholder="Filtra nodi..." />
        <select>
          <option value="">Tutte le categorie</option>
          {NODE_CATEGORIES.map(cat => (
            <option key={cat.value} value={cat.value}>{cat.label}</option>
          ))}
        </select>
        <select>
          <option value="">Tutti i tipi</option>
          <option value="core">Core</option>
          <option value="pdk">PDK</option>
        </select>
      </div>
      
      <table className="categories-table">
        <thead>
          <tr>
            <th>Nome Nodo</th>
            <th>Tipo</th>
            <th>Origine</th>
            <th>Categoria Originale</th>
            <th>Categoria Attuale</th>
            <th>Azioni</th>
          </tr>
        </thead>
        <tbody>
          {nodes.map(node => {
            const originalCategory = determineNodeCategory(node, node.plugin);
            const currentCategory = categoryOverrides[node.id] || originalCategory;
            
            return (
              <tr key={node.id}>
                <td>{node.name}</td>
                <td>{node.pluginId ? 'PDK' : 'Core'}</td>
                <td>{node.pluginId ? node.plugin.name : 'Sistema'}</td>
                <td>{NODE_CATEGORIES.find(c => c.value === originalCategory)?.label || originalCategory}</td>
                <td>
                  <select
                    value={currentCategory}
                    onChange={(e) => handleCategoryChange(node.id, e.target.value)}
                    className={currentCategory !== originalCategory ? 'category-modified' : ''}
                  >
                    {NODE_CATEGORIES.map(cat => (
                      <option key={cat.value} value={cat.value}>
                        {cat.label}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  {currentCategory !== originalCategory && (
                    <button 
                      onClick={() => handleResetCategory(node.id)}
                      className="reset-button"
                    >
                      Ripristina
                    </button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
```

## Implementazione Backend

### API per la gestione delle categorie

Il backend è stato esteso con endpoint dedicati alla gestione delle categorie dei nodi:

```javascript
// Endpoint per gestire le sovrascritture delle categorie
app.get('/api/config/node-categories-override', (req, res) => {
  // Leggi il file di configurazione
  fs.readFile(NODE_CATEGORIES_OVERRIDE_PATH, 'utf8', (err, data) => {
    if (err) {
      // Se il file non esiste, restituisci un oggetto vuoto
      if (err.code === 'ENOENT') {
        return res.json({});
      }
      return res.status(500).json({ error: 'Errore nella lettura delle sovrascritture delle categorie' });
    }
    
    try {
      const overrides = JSON.parse(data);
      res.json(overrides);
    } catch (parseErr) {
      res.status(500).json({ error: 'Errore nel parsing delle sovrascritture delle categorie' });
    }
  });
});

// Endpoint per salvare una sovrascrittura
app.post('/api/config/node-categories-override', (req, res) => {
  const { nodeId, category } = req.body;
  
  if (!nodeId || !category) {
    return res.status(400).json({ error: 'nodeId e category sono richiesti' });
  }
  
  // Leggi il file esistente
  fs.readFile(NODE_CATEGORIES_OVERRIDE_PATH, 'utf8', (err, data) => {
    let overrides = {};
    
    if (!err) {
      try {
        overrides = JSON.parse(data);
      } catch (parseErr) {
        // Se c'è un errore di parsing, inizializza un nuovo oggetto
      }
    }
    
    // Aggiorna l'override
    overrides[nodeId] = category;
    
    // Salva il file aggiornato
    fs.writeFile(NODE_CATEGORIES_OVERRIDE_PATH, JSON.stringify(overrides, null, 2), writeErr => {
      if (writeErr) {
        return res.status(500).json({ error: 'Errore nel salvataggio della sovrascrittura' });
      }
      
      res.json({ success: true, nodeId, category });
    });
  });
});

// Endpoint per eliminare una sovrascrittura
app.delete('/api/config/node-categories-override/:nodeId', (req, res) => {
  const { nodeId } = req.params;
  
  // Leggi il file esistente
  fs.readFile(NODE_CATEGORIES_OVERRIDE_PATH, 'utf8', (err, data) => {
    if (err) {
      return res.status(404).json({ error: 'File di configurazione non trovato' });
    }
    
    try {
      const overrides = JSON.parse(data);
      
      // Rimuovi l'override
      if (overrides[nodeId]) {
        delete overrides[nodeId];
        
        // Salva il file aggiornato
        fs.writeFile(NODE_CATEGORIES_OVERRIDE_PATH, JSON.stringify(overrides, null, 2), writeErr => {
          if (writeErr) {
            return res.status(500).json({ error: 'Errore nell\'eliminazione della sovrascrittura' });
          }
          
          res.json({ success: true, nodeId });
        });
      } else {
        res.status(404).json({ error: 'Sovrascrittura non trovata' });
      }
    } catch (parseErr) {
      res.status(500).json({ error: 'Errore nel parsing del file di configurazione' });
    }
  });
});
```

## Integrazione con la NodePalette

La NodePalette è stata aggiornata per utilizzare il nuovo sistema di categorizzazione:

```jsx
// Componente per la palette dei nodi
const NodePalette = () => {
  const [nodes, setNodes] = useState([]);
  const [plugins, setPlugins] = useState({});
  const [categoryOverrides, setCategoryOverrides] = useState({});
  const [loading, setLoading] = useState(true);
  
  // Carica tutti i dati necessari
  useEffect(() => {
    Promise.all([
      fetchAllNodes(),
      fetchPlugins(),
      loadCategoryOverrides()
    ]).then(([nodesData, pluginsData, overridesData]) => {
      setNodes(nodesData);
      setPlugins(pluginsData);
      setCategoryOverrides(overridesData);
      setLoading(false);
    });
  }, []);
  
  if (loading) {
    return <div>Caricamento palette...</div>;
  }
  
  // Organizza i nodi per categoria
  const categorizedNodes = organizeNodesByCategory(nodes, plugins, categoryOverrides);
  
  return (
    <div className="node-palette">
      {NODE_CATEGORIES.map(category => {
        const nodesInCategory = categorizedNodes[category.value] || [];
        
        // Salta le categorie senza nodi
        if (nodesInCategory.length === 0) {
          return null;
        }
        
        return (
          <div key={category.value} className="node-category">
            <h3>{category.label}</h3>
            <p>{category.description}</p>
            
            <div className="node-list">
              {nodesInCategory.map(node => (
                <NodeItem 
                  key={node.id} 
                  node={node} 
                  isPdk={!!node.pluginId}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
};
```

## Vantaggi dell'approccio unificato

1. **Interfaccia centralizzata**: Tutti i nodi gestiti da un'unica interfaccia
2. **Flessibilità di categorizzazione**: Possibilità di organizzare i nodi in modo coerente
3. **Esperienza utente migliorata**: Palette dei nodi più intuitiva durante la creazione dei workflow
4. **Manutenibilità**: Gestione semplificata delle categorie dei nodi
5. **Coerenza visiva**: Presentazione uniforme dei nodi core e PDK
