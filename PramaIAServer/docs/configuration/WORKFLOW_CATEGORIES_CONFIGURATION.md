# Configurazione delle Categorie di Workflow in PramaIA

## Panoramica

PramaIA supporta un sistema di categorizzazione personalizzabile per i workflow, implementato tramite una configurazione centralizzata. Questo approccio permette di gestire facilmente le categorie disponibili senza necessità di modificare il codice dell'applicazione.

## Architettura della configurazione

Le categorie dei workflow sono configurate nel file di configurazione centralizzato del frontend:

- **`frontend/client/src/config/appConfig.js`**: Configurazione centralizzata del frontend React

## Struttura della configurazione

### Array WORKFLOW_CATEGORIES

Nel file `frontend/client/src/config/appConfig.js` è presente un array denominato `WORKFLOW_CATEGORIES` che definisce tutte le categorie disponibili per i workflow:

```javascript
// Configurazione delle categorie di workflow
export const WORKFLOW_CATEGORIES = [
  { value: "processing", label: "Processing" },
  { value: "analysis", label: "Analysis" },
  { value: "extraction", label: "Extraction" },
  { value: "monitoring", label: "Monitoring" },
  { value: "integration", label: "Integration" },
  { value: "utility", label: "Utility" },
  { value: "other", label: "Other" }
];
```

Ogni categoria è rappresentata da un oggetto con due proprietà:
- **value**: Identificatore univoco della categoria (usato internamente dal sistema)
- **label**: Etichetta visualizzata nell'interfaccia utente

## Utilizzo nel componente WorkflowEditor

Il componente `WorkflowEditor.js` utilizza questa configurazione centralizzata per visualizzare le categorie disponibili nel menu a tendina durante la creazione o modifica di un workflow:

```javascript
import { WORKFLOW_CATEGORIES } from '../config/appConfig';

// All'interno del componente WorkflowEditor
const categoryOptions = WORKFLOW_CATEGORIES.map(category => ({
  value: category.value,
  label: category.label
}));
```

## Personalizzazione delle categorie

### Aggiungere nuove categorie

Per aggiungere nuove categorie, è sufficiente modificare l'array `WORKFLOW_CATEGORIES` nel file `frontend/client/src/config/appConfig.js`:

```javascript
export const WORKFLOW_CATEGORIES = [
  // Categorie esistenti...
  { value: "reporting", label: "Reporting" },  // Nuova categoria
  { value: "conversion", label: "Conversion" } // Nuova categoria
];
```

### Modificare categorie esistenti

Per modificare una categoria esistente, individuare la categoria nell'array `WORKFLOW_CATEGORIES` e aggiornarne il valore o l'etichetta:

```javascript
// Da:
{ value: "analysis", label: "Analysis" }
// A:
{ value: "analysis", label: "Advanced Analysis" }
```

### Rimuovere categorie

Per rimuovere una categoria, eliminare l'oggetto corrispondente dall'array `WORKFLOW_CATEGORIES`:

```javascript
// Rimuovere la categoria "monitoring"
export const WORKFLOW_CATEGORIES = WORKFLOW_CATEGORIES.filter(
  category => category.value !== "monitoring"
);
```

## Vantaggi dell'approccio

1. **Manutenibilità**: Centralizzazione della configurazione in un unico file
2. **Flessibilità**: Facile aggiunta, modifica o rimozione di categorie senza toccare la logica dell'applicazione
3. **Coerenza**: Garantisce che le stesse categorie siano utilizzate in tutti i componenti dell'applicazione
4. **Estensibilità**: La stessa struttura può essere estesa per supportare ulteriori metadati per le categorie

## Integrazione con il sistema di tag

Il sistema di categorizzazione dei workflow è progettato per lavorare in sinergia con il sistema di tag PDK, offrendo una soluzione completa per l'organizzazione e il filtraggio dei workflow e dei componenti correlati.

## Note tecniche

- Il sistema utilizza lo stesso approccio di configurazione centralizzata documentato in `CONFIG_CENTRALIZZATA.md`
- Questo sistema è stato implementato in linea con i principi SOLID, in particolare il principio Open/Closed (aperto per l'estensione, chiuso per la modifica)
- La configurazione supporta l'aggiunta dinamica di nuove categorie senza necessità di ricompilare l'applicazione
