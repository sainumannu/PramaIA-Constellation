# Sintesi modifiche Sistema Trigger Workflow PramaIA

## Architettura del Sistema

Il sistema PramaIA è basato su un'architettura a microservizi con le seguenti componenti principali:

1. **Backend**: Implementato in Python con FastAPI
   - API REST per la gestione dei workflow e trigger
   - Database SQLite per la persistenza dei dati
   - Gestione degli eventi tramite sistema di trigger

2. **PDK Server**: Node.js per la gestione dei plugin
   - Fornisce i nodi che possono essere utilizzati nei workflow

3. **Frontend**: React con Chakra UI (v2.8.2)
   - Interfaccia utente per la gestione dei workflow e trigger
   - Componenti modali per l'inserimento e modifica dei dati

4. **Sistema di Trigger Workflow**:
   - Permette l'associazione di eventi a workflow specifici
   - Supporta condizioni di filtro per affinare l'attivazione
   - Gestisce diverse sorgenti di eventi (pdf-monitor, scheduler, ecc.)

## Database Schema

Il sistema utilizza una tabella `workflow_triggers` con la seguente struttura:

```sql
CREATE TABLE IF NOT EXISTS workflow_triggers (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(100) NOT NULL,
    workflow_id VARCHAR(255) NOT NULL,
    conditions TEXT DEFAULT '{}',
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Con indici per ottimizzare le query più frequenti:
- `idx_trigger_event_source`
- `idx_trigger_active`
- `idx_trigger_workflow_id`

## File Modificati

### Backend
- `create_workflow_triggers_table.sql`: Schema di database per i trigger

### Frontend
1. **WorkflowTriggersPage.jsx**
   - Rimossi i `<Box>` contenitori con attributo `zIndex={9999}` che avvolgevano le modali
   - Le modali ora sono direttamente incorporate nel JSX della pagina

2. **TriggerFormModal.jsx**
   - Aumentato lo z-index della modale da 9999 a 10000
   - Aumentato lo z-index dell'overlay da 9998 a 9999
   - Rimosso l'attributo `zIndex={10000}` dal componente `<VStack>` all'interno della modale

3. **TriggerConditionsModal.jsx**
   - Aumentato lo z-index della modale da 9999 a 10000
   - Aumentato lo z-index dell'overlay da 9998 a 9999

## Modifiche Implementate

1. **Architettura Z-Index**
   - Rimossi contenitori nidificati che creavano contesti di impilamento conflittuali
   - Aumentati i valori di z-index delle modali a 10000
   - Migliorato il posizionamento degli overlay a z-index 9999

2. **Gestione Componenti UI**
   - Semplificata la struttura DOM delle modali
   - Corretti attributi di posizionamento relativi

## Problematica Rimanente

Nonostante le modifiche implementate, persiste un problema di sovrapposizione con l'icona informativa. In particolare:

1. **Problema specifico**: L'icona informativa nella pagina principale continua a sovrapporsi alle modali aperte, anche con i valori z-index aumentati.

2. **Comportamento osservato**: Quando si apre una modale (TriggerFormModal o TriggerConditionsModal), alcune parti della pagina sottostante, in particolare l'icona informativa, rimangono visibili sopra la modale.

3. **Tentativi effettuati**:
   - Aumentati gli z-index delle modali a 10000
   - Rimossi container nidificati con z-index
   - Semplificata la struttura DOM

4. **Possibili cause non ancora esplorate**:
   - Potrebbe esserci un componente di alto livello (come un portale o un tooltip) che imposta un z-index estremamente alto
   - Potrebbero esserci stili CSS globali che influenzano la visualizzazione
   - La struttura complessiva dei componenti potrebbe creare contesti di impilamento isolati

Una soluzione completa richiede un'analisi più approfondita della struttura DOM e dei componenti di alto livello nell'applicazione, oltre a un possibile refactoring più ampio dell'architettura dei componenti UI.
