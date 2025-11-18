# PramaIA-PDK: Guida all'integrazione

## Indice
1. [Introduzione](#introduzione)
2. [Architettura generale](#architettura-generale)
3. [🏷️ Sistema di Tag](#sistema-di-tag)
4. [API di integrazione](#api-di-integrazione)
5. [Come utilizzare i nodi PDK](#come-utilizzare-i-nodi-pdk)
6. [Creazione di un plugin](#creazione-di-un-plugin)
7. [Interfacciamento con il frontend](#interfacciamento-con-il-frontend)
8. [Nodi PDK Avanzati](#nodi-pdk-avanzati)
9. [Best practices](#best-practices)
10. [PramaIA-PDK Studio: Roadmap](#pramaia-pdk-studio-roadmap-per-ambiente-di-sviluppo-visuale)
11. [Risoluzione problemi](#risoluzione-problemi)

## Introduzione

PramaIA-PDK (Plugin Development Kit) è un framework per la creazione e l'integrazione di nodi di elaborazione modulari che possono essere incorporati nei workflow di elaborazione dati. Il sistema è progettato per consentire una facile estensione delle funzionalità tramite plugin, con particolare attenzione all'elaborazione di documenti PDF e all'analisi semantica.

Questo documento fornisce le linee guida per integrare i nodi PDK in altri progetti, senza richiedere una conoscenza approfondita dell'architettura interna del sistema.

## Architettura generale

Il sistema PramaIA-PDK è organizzato in:

1. **Core**: Definisce le interfacce base e le classi astratte per i nodi e i plugin
2. **Plugin**: Moduli indipendenti che implementano funzionalità specifiche
3. **Workflow Engine**: Motore di esecuzione che orchestratra l'esecuzione dei nodi
4. **API**: Endpoint per la discovery dei nodi disponibili e l'esecuzione dei workflow

L'architettura è progettata per essere:
- **Modulare**: I plugin possono essere sviluppati e distribuiti indipendentemente
- **Estensibile**: Nuove funzionalità possono essere aggiunte senza modificare il core
- **Tipizzata**: Le interfacce sono definite con TypeScript per garantire robustezza

## 🏷️ Sistema di Tag

Il sistema di tag PDK fornisce un meccanismo avanzato per l'organizzazione e il filtraggio di plugin ed event sources attraverso una struttura gerarchica a 4 livelli.

### Architettura dei Tag

Il sistema supporta tag configurabili su 4 livelli:

1. **Plugin Level** - Tag applicati all'intero plugin
2. **Node Level** - Tag specifici per i singoli nodi di elaborazione  
3. **Event Source Level** - Tag per le sorgenti di eventi
4. **Event Type Level** - Tag per i tipi di eventi specifici

### Schema di Configurazione

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "tags": ["category", "type", "functionality"],
  "nodes": [
    {
      "id": "my_node",
      "name": "My Node",
      "tags": ["processing", "text", "utility"]
    }
  ],
  "eventTypes": [
    {
      "id": "my_event",
      "name": "My Event",
      "tags": ["trigger", "automation"]
    }
  ]
}
```

### Categorie Tag Predefinite

#### Plugin Categories
- `internal` - Plugin interni del sistema
- `core` - Funzionalità core
- `external` - Plugin esterni/community
- `utility` - Utilità generali
- `integration` - Plugin di integrazione

#### Processing Types
- `text-processing` - Elaborazione testo
- `document` - Gestione documenti
- `pdf` - Specifico per PDF
- `semantic` - Elaborazione semantica
- `ai` - Intelligenza artificiale

#### Event Source Types
- `monitoring` - Monitoraggio
- `file-system` - File system
- `database` - Database
- `api` - API/webhook
- `schedule` - Scheduling/cron

### API Tag System

Il PDK server espone endpoint specifici per il sistema di tag:

```bash
# Lista plugin con filtri tag
GET /api/plugins?tags=internal,core&mode=AND
GET /api/plugins?exclude_tags=deprecated

# Lista event sources con filtri
GET /api/event-sources?tags=monitoring

# Statistiche tag
GET /api/tags
```

**Parametri supportati:**
- `tags` - Lista tag da includere (separati da virgola)
- `exclude_tags` - Lista tag da escludere
- `mode` - Modalità filtro: `AND` (tutti i tag) o `OR` (almeno uno)

### Integrazione Frontend

Il sistema include componenti React per la gestione UI dei tag:

```jsx
import { PDKTagManagementPanel, PDKTagBadge } from './PDKTagManagement';
import { usePDKData } from './hooks/usePDKData';

const MyComponent = () => {
  const { plugins, updateFilters } = usePDKData();
  
  return (
    <PDKTagManagementPanel
      items={plugins}
      onItemsFilter={setFilteredItems}
      showStats={true}
      showCloud={true}
    />
  );
};
```

**Componenti disponibili:**
- `PDKTagBadge` - Badge visuali per tag singoli
- `PDKTagFilter` - Pannello di filtro interattivo
- `PDKTagCloud` - Visualizzazione cloud dei tag
- `PDKTagStats` - Statistiche utilizzo tag
- `PDKTagManagementPanel` - Pannello completo di gestione

## API di integrazione

### Endpoint principali

Per integrare i nodi PDK in un'applicazione esterna, sono disponibili i seguenti endpoint REST:

#### 1. Discovery dei nodi PDK

```
GET http://localhost:8000/api/workflows/pdk-nodes
```

Questo endpoint restituisce l'elenco completo dei nodi PDK disponibili nel sistema. La risposta è in formato JSON con la seguente struttura:

```json
{
  "nodes": [
    {
      "type": "pdk_plugin-name_node-id",
      "name": "Nome nodo",
      "display_name": "Nome visualizzato",
      "description": "Descrizione del nodo",
      "icon": "🧩",
      "pluginId": "plugin-name",
      "pluginName": "Nome del plugin",
      "pluginVersion": "1.0.0",
      "configSchema": { ... },
      "defaultConfig": { ... }
    },
    ...
  ]
}
```

Ogni nodo contiene:
- `type`: Identificativo univoco del nodo (formato: `pdk_plugin-name_node-id`)
- `name`: Nome tecnico del nodo
- `display_name`: Nome visualizzato nell'interfaccia utente
- `description`: Descrizione delle funzionalità
- `icon`: Icona rappresentativa (emoji o codice unicode)
- `configSchema`: Schema di configurazione per l'interfaccia utente
- `defaultConfig`: Valori predefiniti per la configurazione

#### 2. Esecuzione di un workflow

```
POST http://localhost:8000/api/workflows/execute
```

Richiede:
```json
{
  "workflowId": "workflow-id",
  "nodes": [
    {
      "id": "node1",
      "type": "pdk_plugin-name_node-id",
      "config": { ... }
    },
    ...
  ],
  "connections": [
    {
      "source": "node1",
      "sourceOutput": "output1",
      "target": "node2",
      "targetInput": "input1"
    },
    ...
  ]
}
```

Risposta:
```json
{
  "executionId": "exec-id",
  "status": "completed",
  "results": {
    "node1": { ... },
    "node2": { ... }
  }
}
```

#### 3. Documentazione dei nodi PDK

```
GET http://localhost:8000/api/workflows/pdk-node-documentation/{nodeType}
```

Questo endpoint restituisce la documentazione di un nodo PDK specifico. Il parametro `nodeType` deve essere l'identificativo completo del nodo nel formato `pdk_plugin-name_node-id`.

Risposta (formato default: markdown):
```json
{
  "nodeType": "pdk_plugin-name_node-id",
  "format": "markdown",
  "content": "# Documentazione del nodo\n\n..."
}
```

È possibile specificare il formato desiderato aggiungendo il parametro `format`:
```
GET http://localhost:8000/api/workflows/pdk-node-documentation/{nodeType}?format=text
```

Formati supportati:
- `markdown`: Documentazione completa in formato Markdown
- `text`: Documentazione concisa in formato testo

### Autenticazione

Le richieste API richiedono l'autenticazione tramite token JWT:

```javascript
const headers = {
  'Authorization': `Bearer ${token}`
};
```

## Come utilizzare i nodi PDK

### Integrazione in un frontend React

Per integrare i nodi PDK in un'applicazione React, è possibile utilizzare l'hook `usePDKNodes` fornito con il progetto:

```javascript
import { usePDKNodes } from './path/to/DynamicPDKNodes';

function MyComponent() {
  const { nodes, loading, error, fetchNodes } = usePDKNodes();

  // Forza un aggiornamento dei nodi disponibili
  const refreshNodes = () => {
    fetchNodes(true);
  };

  // Gestione stato di caricamento
  if (loading) return <div>Caricamento nodi PDK...</div>;
  
  // Gestione errori
  if (error) return <div>Errore: {error.message}</div>;

  return (
    <div>
      <button onClick={refreshNodes}>Aggiorna nodi</button>
      <ul>
        {nodes.map(node => (
          <li key={node.type}>
            {node.icon} {node.label} - {node.description}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

### Utilizzo dell'hook usePDKNodes

L'hook `usePDKNodes` fornisce:

- `nodes`: Array di nodi PDK disponibili
- `loading`: Stato di caricamento
- `error`: Eventuali errori durante il fetch
- `fetchNodes(forceRefresh)`: Funzione per aggiornare i nodi (opzionalmente forzando il refresh)

L'hook implementa:
- Caching dei risultati per ottimizzare le performance
- Gestione della concorrenza per evitare richieste multiple
- Fallback automatico in caso di errori

### Struttura di un nodo PDK

Ogni nodo PDK ha la seguente struttura:

```javascript
{
  type: "pdk_plugin-name_node-id",     // Identificativo univoco
  label: "Nome visualizzato",          // Nome per l'UI
  icon: "🧩",                          // Icona (emoji o unicode)
  description: "Descrizione del nodo", // Descrizione
  configSchema: { ... },               // Schema per configurazione UI
  defaultConfig: { ... },              // Valori predefiniti
  pluginId: "plugin-name",             // ID del plugin di appartenenza
  pluginName: "Nome Plugin",           // Nome del plugin
  pluginVersion: "1.0.0"               // Versione del plugin
}
```

## Creazione di un plugin

Per chi desidera estendere le funzionalità, è possibile creare un nuovo plugin PDK.

### Struttura di un plugin

Un plugin PDK ha la seguente struttura:

```
my-plugin/
├── plugin.json       # Manifesto del plugin
├── DOCUMENTATION.md  # Documentazione completa (formato Markdown)
├── DOCUMENTATION.txt # Documentazione concisa (formato testo)
├── src/              # Codice sorgente
│   ├── index.js      # Entry point
│   └── processors/   # Implementazione nodi
├── package.json      # Dipendenze
└── README.md         # Documentazione generale
```

### Documentazione integrata nei plugin

Per facilitare l'integrazione e l'utilizzo dei plugin, è consigliabile includere documentazione in due formati:

1. **DOCUMENTATION.md**: Documentazione completa in formato Markdown, con esempi dettagliati, spiegazioni e casi d'uso.
2. **DOCUMENTATION.txt**: Versione concisa in formato testo, facilmente trasmissibile insieme al plugin durante la distribuzione.

Questa documentazione viene trasmessa insieme al plugin al server che lo utilizza, permettendo agli sviluppatori di accedere rapidamente alle informazioni necessarie per l'integrazione.

Esempio di struttura della documentazione in formato testo:
```
NOME PLUGIN
===========
ID Plugin: plugin-id
Versione: 1.0.0
Tipo: processing
Categoria: Categoria

DESCRIZIONE
-----------
Breve descrizione della funzionalità del plugin.

INGRESSI/USCITE
--------------
- Ingresso1: Descrizione
- Uscita1: Descrizione

CONFIGURAZIONE
-------------
Parametri principali e loro utilizzo

ESEMPIO
-------
Esempio base di configurazione
```

Per facilitare la creazione della documentazione, PramaIA-PDK fornisce template predefiniti:
- `templates/plugin-documentation-template.md`: Template per documentazione completa in Markdown
- `templates/plugin-documentation-template.txt`: Template per documentazione concisa in formato testo

I file di documentazione possono essere referenziati nel manifest del plugin:

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Il mio plugin PDK",
  "author": "Nome Autore",
  "license": "MIT",
  "pdk_version": "^1.0.0",
  "engine_compatibility": "^1.0.0",
  "documentation": {
    "markdown": "DOCUMENTATION.md",
    "text": "DOCUMENTATION.txt"
  },
  "nodes": [
    // ...
  ]
}
```

Durante l'installazione del plugin, il server PDK può leggere questi file e renderli disponibili attraverso l'API.

### Manifesto del plugin (plugin.json)

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Il mio plugin PDK",
  "author": "Nome Autore",
  "license": "MIT",
  "pdk_version": "^1.0.0",
  "engine_compatibility": "^1.0.0",
  
  "tags": ["external", "processing", "utility"],
  
  "nodes": [
    {
      "id": "my_node",
      "name": "My Node",
      "type": "processing",
      "category": "My Category",
      "description": "Descrizione del nodo",
      "icon": "🔧",
      "color": "#FF8C00",
      "tags": ["transform", "data", "custom"],
      "inputs": [
        {
          "name": "input1",
          "type": "text",
          "required": true,
          "description": "Input principale"
        }
      ],
      "outputs": [
        {
          "name": "output1",
          "type": "json",
          "description": "Output elaborato"
        }
      ],
      "configSchema": {
        "title": "Configurazione",
        "type": "object",
        "properties": {
          "param1": {
            "type": "string",
            "title": "Parametro 1",
            "default": "valore"
          }
        }
      },
      "entry": "src/my_node_processor.js"
    }
  ]
}
```

### Creazione di un processore di nodo

```javascript
// src/my_node_processor.js
import { BaseNodeProcessor } from '@pramaia/plugin-development-kit';

export class MyNodeProcessor extends BaseNodeProcessor {
  async execute(nodeConfig, context) {
    // Recupera l'input
    const input = await this.getInput(context, nodeConfig.id, 'input1');
    
    // Recupera i parametri di configurazione
    const param1 = nodeConfig.config?.param1 || 'default';
    
    // Elaborazione
    const result = { processed: input, param: param1 };
    
    // Imposta l'output
    await this.setOutput(context, nodeConfig.id, 'output1', result);
    
    return result;
  }
  
  getConfigSchema() {
    return {
      title: "Configurazione",
      type: "object",
      properties: {
        param1: {
          type: "string",
          title: "Parametro 1",
          default: "valore"
        }
      }
    };
  }
}
```

### Registrazione del plugin

```javascript
// src/index.js
import { BaseNodePlugin, createPluginFactory } from '@pramaia/plugin-development-kit';
import { MyNodeProcessor } from './my_node_processor.js';
import manifest from '../plugin.json';

class MyPlugin extends BaseNodePlugin {
  manifest = manifest;
  
  async registerProcessors() {
    this.registerProcessor('my_node', new MyNodeProcessor());
  }
}

export default createPluginFactory(MyPlugin);
```

## Interfacciamento con il frontend

### Integrazione dei nodi nella UI

Per integrare i nodi PDK in un'interfaccia di workflow:

```javascript
import { usePDKNodes } from './path/to/DynamicPDKNodes';
import { useEffect } from 'react';

function WorkflowEditor() {
  const { nodes, loading, fetchNodes } = usePDKNodes();
  
  // Carica i nodi al montaggio del componente
  useEffect(() => {
    fetchNodes();
  }, [fetchNodes]);
  
  // Aggiungi un nodo al workflow
  const addNodeToWorkflow = (nodeType) => {
    const nodeTemplate = nodes.find(n => n.type === nodeType);
    if (!nodeTemplate) return;
    
    const newNode = {
      id: `node_${Date.now()}`,
      type: nodeTemplate.type,
      label: nodeTemplate.label,
      config: { ...nodeTemplate.defaultConfig }
    };
    
    // Aggiungi al workflow...
  };
  
  return (
    <div>
      {/* UI del workflow editor */}
      <div className="node-palette">
        {nodes.map(node => (
          <div 
            key={node.type} 
            className="node-item"
            onClick={() => addNodeToWorkflow(node.type)}
          >
            <span className="node-icon">{node.icon}</span>
            <span className="node-label">{node.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Generazione dinamica dei form di configurazione

Per generare form di configurazione basati sugli schemi dei nodi:

```javascript
import { useState } from 'react';
import Form from '@rjsf/core';

function NodeConfigForm({ node, onConfigChange }) {
  const [config, setConfig] = useState(node.config || {});
  
  const handleChange = ({ formData }) => {
    setConfig(formData);
    onConfigChange(formData);
  };
  
  return (
    <div className="node-config-form">
      <h3>{node.label} - Configurazione</h3>
      <Form
        schema={node.configSchema || {}}
        formData={config}
        onChange={handleChange}
      />
    </div>
  );
}
```

## Best practices

### Generali
1. **Caching**: Utilizza la cache implementata in `usePDKNodes` per evitare richieste multiple
2. **Gestione errori**: Implementa fallback appropriati in caso di errori di comunicazione
3. **Validazione**: Valida sempre i dati ricevuti dall'API prima di utilizzarli
4. **Refresh strategico**: Aggiorna i nodi solo quando necessario (cambio utente, notifica di nuovo plugin)
5. **Logging**: Mantieni log appropriati per il debugging, ma disabilitali in produzione

### 🏷️ Best Practices per i Tag

#### Creazione Tag Semantici
- **Consistenza**: Utilizza una nomenclatura coerente e descrittiva
- **Granularità**: Bilancia tra troppo generici e troppo specifici
- **Gerarchia**: Rispetta le categorie predefinite per compatibilità

```json
// ✅ Buon esempio
{
  "tags": ["external", "text-processing", "nlp", "utility"],
  "nodes": [
    {
      "tags": ["tokenize", "preprocessing", "text"]
    }
  ]
}

// ❌ Esempio da evitare
{
  "tags": ["stuff", "things", "plugin1", "misc"]
}
```

#### Convenzioni di Naming
- Usa kebab-case per tag composti: `text-processing`, `file-system`
- Evita caratteri speciali e spazi
- Preferisci termini in inglese per compatibilità internazionale
- Mantieni tag brevi ma descrittivi (2-20 caratteri)

#### Organizzazione Gerarchica
```json
{
  "tags": ["core", "text-processing"],        // Plugin level
  "nodes": [
    {
      "tags": ["tokenize", "nlp"],            // Node level - più specifico
      "inputs": [...],
      "outputs": [...]
    }
  ],
  "eventTypes": [
    {
      "tags": ["trigger", "text-change"]      // Event level - azione specifica
    }
  ]
}
```

#### Testing e Validazione Tag
- Testa filtri con combinazioni di tag prima del deployment
- Verifica che i tag siano semanticamente significativi
- Controlla compatibilità con tag system esistente
- Valida performance con molti tag

```bash
# Test filtri tag
curl "http://localhost:3001/api/plugins?tags=my-new-tag"
curl "http://localhost:3001/api/plugins?tags=processing,utility&mode=AND"
```

#### Mantenimento Tag
- Documenta i tag utilizzati nel README del plugin
- Evita tag ridondanti o duplicati
- Aggiorna tag quando cambia la funzionalità
- Considera impatto su filtri esistenti prima di rimuovere tag

## PramaIA-PDK Studio: Roadmap per ambiente di sviluppo visuale

Questa sezione delinea la roadmap per l'evoluzione di PramaIA-PDK in un ambiente di sviluppo visuale completo per la creazione e gestione di nodi e plugin.

### Fase 1: Fondamenta (3-4 mesi)

#### 1.1 Creazione dell'interfaccia base
- Sviluppo del layout principale dell'IDE con aree per esplorazione, editing e anteprima
- Integrazione dell'autenticazione esistente
- Componente di esplorazione dei plugin e nodi esistenti

#### 1.2 Editor di manifest visuale
- Interfaccia drag-and-drop per creare/modificare il file `plugin.json`
- Validazione in tempo reale dello schema
- Sistema di gestione degli input/output con suggerimenti sui tipi di dati compatibili

#### 1.3 Generatore di template
- Wizard per la creazione di plugin da zero
- Template predefiniti per diverse categorie di nodi (processamento, input/output, connettori)
- Generazione automatica della struttura di base del codice

#### 1.4 Gestione risorse
- UI per la gestione delle dipendenze nel `package.json`
- Editor di icone e risorse visive per i nodi
- Gestione centralizzata della documentazione

### Fase 2: Editing avanzato (2-3 mesi)

#### 2.1 Editor di codice integrato
- Integrazione di Monaco Editor o simile
- Evidenziazione sintassi e completamento per il framework PDK
- Debugging in-line con visualizzazione degli errori

#### 2.2 Anteprima documentazione
- Generazione e anteprima in tempo reale della documentazione in entrambi i formati
- Editor markdown con anteprima per `DOCUMENTATION.md`
- Strumento di consistenza per garantire la sincronizzazione tra codice e documentazione

#### 2.3 Gestione dei tipi di dati
- Definizione visuale di tipi di dati complessi
- Validatori di schema per input/output
- Libreria di tipi comuni riutilizzabili

### Fase 3: Testing e simulazione (3-4 mesi)

#### 3.1 Ambiente sandbox
- Creazione di un ambiente isolato per testare nodi singoli
- Generatore di dati di test basati sugli schemi di input
- Visualizzatore di output con formattazione basata sul tipo

#### 3.2 Simulatore di workflow
- Mini-editor di workflow per testare i nodi in contesto
- Simulazione del flusso di dati tra nodi
- Strumenti di analisi per verificare compatibilità e performance

#### 3.3 Strumenti di debugging
- Ispettore di stato per l'esecuzione
- Breakpoint e step-by-step execution
- Logger integrato con filtri per livello e componente

### Fase 4: Distribuzione e gestione (2-3 mesi)

#### 4.1 Packaging
- Strumenti per creare pacchetti distribuibili dei plugin
- Gestione delle versioni e delle dipendenze
- Controlli di qualità pre-distribuzione

#### 4.2 Marketplace interno
- Repository locale per i plugin sviluppati
- Sistema di versioning e compatibilità
- Metriche di utilizzo e feedback

#### 4.3 Integrazione con CI/CD
- Hook per sistemi di integrazione continua
- Test automatizzati per verificare compatibilità con nuove versioni del core
- Pipeline di aggiornamento automatico

### Fase 5: Collaborazione e ecosistema (3-4 mesi)

#### 5.1 Strumenti collaborativi
- Condivisione di plugin e nodi tra team
- Sistema di commenti e revisione
- Gestione di accessi e permessi

#### 5.2 Marketplace pubblico
- Piattaforma per la distribuzione di plugin a tutta la community
- Sistema di rating e recensioni
- Analytics per sviluppatori

#### 5.3 Estensibilità dell'IDE
- API per estendere l'IDE stesso con plugin
- Temi e personalizzazioni
- Integrazione con strumenti di terze parti

### Milestones principali

- **Milestone 1: MVP (Mese 4)** - Editor di manifest e template di base
- **Milestone 2: Alpha (Mese 7)** - Editor di codice completo e sandbox di testing
- **Milestone 3: Beta (Mese 11)** - Simulatore di workflow e strumenti di debugging
- **Milestone 4: Release (Mese 15)** - Marketplace interno e integrazione CI/CD
- **Milestone 5: Enterprise (Mese 18)** - Marketplace pubblico e sistema di estensioni

## Nodi PDK Avanzati

### Workflow Scheduler

Il nodo **Workflow Scheduler** è un componente avanzato che permette di programmare l'esecuzione dei workflow secondo vari criteri temporali.

#### Funzionalità principali

- **Schedulazione flessibile**: Supporta diverse modalità di schedulazione (intervalli, cron, date specifiche, eventi)
- **Controllo dell'esecuzione**: Limiti di esecuzione, date di inizio/fine, numero massimo di esecuzioni
- **Monitoraggio**: Tracciamento delle esecuzioni con notifiche opzionali
- **Integrazione**: Può essere posizionato in qualsiasi punto del workflow

#### Configurazione

Il nodo Scheduler supporta diverse modalità di configurazione:

```javascript
// Configurazione per esecuzione ogni 10 minuti
{
  "schedule_type": "interval",
  "interval": {
    "value": 10,
    "unit": "minutes"
  }
}

// Configurazione per esecuzione cron (lunedì alle 9:00)
{
  "schedule_type": "cron",
  "cron_expression": "0 9 * * 1",
  "timezone": "Europe/Rome"
}

// Configurazione per esecuzione a data specifica
{
  "schedule_type": "date",
  "specific_date": "2025-12-31T23:59:59"
}

// Configurazione per esecuzione basata su eventi
{
  "schedule_type": "event",
  "event_name": "nuovo_documento"
}
```

#### Integrazione nel workflow

```javascript
// Esempio di aggiunta del nodo Scheduler a un workflow
const schedulerNode = {
  id: "scheduler_node",
  type: "pdk_workflow-scheduler-plugin_workflow_scheduler",
  config: {
    schedule_type: "interval",
    interval: {
      value: 5,
      unit: "minutes"
    },
    max_executions: 10,
    execution_tracking: {
      store_history: true,
      notify_on_error: true
    }
  }
};

// Aggiungi il nodo al workflow
workflow.nodes.push(schedulerNode);

// Connetti il nodo scheduler ad altri nodi
workflow.connections.push({
  source: "scheduler_node",
  sourceOutput: "output",
  target: "process_node",
  targetInput: "input"
});
```

#### Output del nodo

Il nodo Scheduler produce due output:
- `output`: Dati da passare al nodo successivo
- `metadata`: Informazioni sulla schedulazione (stato, conteggio esecuzioni, timestamp, ecc.)

## Risoluzione problemi

### Nodi non visualizzati correttamente

**Problema**: I nodi PDK non vengono visualizzati o hanno icone corrotte.

**Soluzione**:
1. Verifica la connessione all'endpoint API `http://localhost:8000/api/workflows/pdk-nodes`
2. Controlla i log della console per errori di rete o parsing
3. Verifica che il token di autenticazione sia valido e presente
4. Prova a forzare il refresh con `fetchNodes(true)`

### Errori di autenticazione

**Problema**: Le richieste API falliscono con errori 401/403.

**Soluzione**:
1. Assicurati che l'utente sia autenticato
2. Verifica che il token sia ancora valido (non scaduto)
3. Rinnova il token se necessario
4. Controlla i permessi dell'utente per l'accesso ai nodi PDK

### Errori di esecuzione workflow

**Problema**: L'esecuzione del workflow fallisce.

**Soluzione**:
1. Controlla che tutte le connessioni tra nodi siano valide
2. Verifica che tutti i nodi abbiano configurazioni valide
3. Controlla i log del backend per errori specifici
4. Assicurati che i tipi di dati in input/output siano compatibili

### Problemi con lo Scheduler

**Problema**: Il nodo Scheduler non attiva il workflow come previsto.

**Soluzione**:
1. Verifica che la configurazione temporale sia corretta (formato data, espressione cron, ecc.)
2. Controlla il fuso orario impostato
3. Verifica che non siano state raggiunte le esecuzioni massime
4. Assicurati che la data corrente rientri nell'intervallo start_date/end_date
5. Per scheduler basati su eventi, verifica che l'evento venga effettivamente generato

---

Per ulteriori informazioni e supporto, consulta la documentazione completa del progetto o contatta il team di sviluppo PramaIA.
