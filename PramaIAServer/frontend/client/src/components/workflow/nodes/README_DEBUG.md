# Sistema di Debug Condizionale per Componenti Workflow

Questo sistema permette di controllare la verbosità dei log nel frontend del sistema di workflow PramaIA.

## Configurazione Debug

Ogni componente ha una variabile `DEBUG_MODE` che controlla la verbosità dei log:

```javascript
// Abilitare debug per visualizzare log dettagliati
const DEBUG_MODE = false;

// Helper per log condizionali
const debugLog = (...args) => {
  if (DEBUG_MODE) console.log(...args);
};
```

## Come Abilitare/Disabilitare i Log

Per abilitare i log dettagliati, modifica la costante `DEBUG_MODE` nei seguenti file:

1. `DynamicPDKNodes.js` - Per debug dei nodi PDK dinamici
2. `PDKNode.js` - Per debug del rendering dei nodi PDK
3. `index.js` - Per debug della selezione dei tipi di nodo

## Livelli di Log

I log sono stati organizzati su diversi livelli:

1. **Log Essenziali**: Sempre mostrati, indipendentemente da `DEBUG_MODE`
   - Conteggio nodi caricati
   - Errori critici

2. **Log di Debug**: Mostrati solo quando `DEBUG_MODE = true`
   - Dettagli delle richieste API
   - Trasformazione e mapping dei dati
   - Cache e performance

## Quando Usare Debug Mode

Attiva la modalità debug quando:

- Ci sono problemi nel caricamento dei nodi PDK
- I nodi non vengono visualizzati correttamente
- Ci sono problemi con le icone o le configurazioni
- Stai sviluppando nuovi tipi di nodi

## Note per gli Sviluppatori

1. Usa sempre `debugLog()` per i log di debug che non dovrebbero apparire in produzione
2. Mantieni i log essenziali brevi e informativi
3. Non disabilitare mai i log di errore critici

## Esempi

```javascript
// Log essenziale - sempre mostrato
console.log(`Caricati nodi PDK: ${nodes.length}`);

// Log di debug - mostrato solo in modalità debug
debugLog('[DynamicPDKNodes] Using cached PDK nodes');
debugLog('[DynamicPDKNodes] Filtered out test nodes, remaining:', filteredNodes.length);
```

## Console Browser

Per vedere più dettagli durante lo sviluppo, apri la console del browser e filtra per:

- "DynamicPDKNodes" - per log relativi al caricamento
- "PDKNode" - per log relativi al rendering
- "NodeTypes" - per log relativi alla selezione dei tipi di nodo
