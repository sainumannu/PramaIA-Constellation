# Quick Start Guide - Advanced Trigger System

## 🚀 Introduzione Rapida

Benvenuto nel nuovo sistema trigger avanzato di PramaIA! Questa guida ti aiuterà a iniziare rapidamente con le nuove funzionalità di routing intelligente dei trigger.

## ⚡ Setup Veloce

### 1. **Prerequisiti**
```bash
# Verifica versioni
python --version  # Python 3.9+
node --version    # Node.js 16+
sqlite3 --version # SQLite 3.35+
```

### 2. **Database**
Il sistema utilizza SQLite per la configurazione dei trigger. Il database è già inizializzato e contiene 3 trigger predefiniti in `backend/db/database.db`.

### 3. **Avvio Servizi**
```bash
# Dall'interno della directory PramaIA
.\start-all.ps1

# O manualmente:
# Terminal 1: Backend
cd PramaIAServer
python -m uvicorn backend.main:app --reload --port 8000

# Terminal 2: Frontend  
cd PramaIAServer/frontend/client
npm start  # port 3000

# Terminal 3: PDK Server
cd PramaIA-PDK/server
node plugin-api-server.js  # port 3001
```

## 🎯 Creazione del Primo Trigger Avanzato

### Passo 1: Apri Gestione Trigger
1. Vai su `http://localhost:3000`
2. Naviga in **Workflow → Gestione Trigger**
3. Clicca **"Nuovo Trigger"**

### Passo 2: Configura il Trigger
I trigger sono già predefiniti nel sistema:

```yaml
Trigger 1: "Trigger Aggiunta PDF"
  Workflow: PDF Document CREATE Pipeline (wf_bd11290f923b)
  Event Source: pdf-monitor-event-source
  Evento: pdf_file_added
  Nodo Target: pdf_input_validator
  Status: ✅ Abilitato

Trigger 2: "Trigger Eliminazione PDF"
  Workflow: PDF Document DELETE Pipeline (wf_b32ead12131c)
  Event Source: pdf-monitor-event-source
  Evento: pdf_file_deleted
  Nodo Target: pdf_input_validator
  Status: ✅ Abilitato

Trigger 3: "Trigger Aggiornamento PDF"
  Workflow: PDF Document UPDATE Pipeline (wf_055bf5029833)
  Event Source: pdf-monitor-event-source
  Evento: pdf_file_modified
  Nodo Target: pdf_input_validator
  Status: ✅ Abilitato
```
```

### Passo 3: Seleziona Nodo Target
- Il sistema mostrerà automaticamente i **nodi compatibili**
- Seleziona il nodo specifico che vuoi attivare
- Verifica lo stato di **compatibilità** (verde = compatibile)

### Passo 4: Configurazione Event Source
```json
{
  "monitor_path": "/path/to/pdf/folder",
  "recursive": true,
  "file_extensions": [".pdf"],
  "max_file_size": 50
}
```

### Passo 5: Salva e Attiva
1. Clicca **"Crea Trigger"**
2. Verifica che lo stato sia **"Attivo"**
3. Il trigger è pronto! 🎉

## 🔥 Funzionalità Principali

### 🎯 **Selezione Nodi Intelligente**
```javascript
// Il sistema rileva automaticamente nodi compatibili
const availableNodes = await getWorkflowInputNodes(workflowId);

// Mostra solo nodi compatibili con l'evento
const compatibleNodes = availableNodes.filter(node => 
  node.compatibility[eventType] === 'compatible'
);
```

### 📊 **Evento "File PDF Aggiunto"**
```json
{
  "eventType": "pdf_file_added",
  "data": {
    "file_path": "/path/to/file.pdf",
    "file_name": "documento.pdf",
    "file_size": 1024,
    "detected_at": "2025-11-19T10:30:00Z"
  }
}
```

### 📊 **Evento "File PDF Modificato"**
```json
{
  "eventType": "pdf_file_modified",
  "data": {
    "file_path": "/path/to/file.pdf",
    "change_type": "content_changed",
    "modified_at": "2025-11-19T10:30:00Z"
  }
}
```

### 📊 **Evento "File PDF Eliminato"**
```json
{
  "eventType": "pdf_file_deleted",
  "data": {
    "file_path": "/path/to/file.pdf",
    "file_name": "documento.pdf",
    "deleted_at": "2025-11-19T10:30:00Z"
  }
}
```

### 🔍 **Validazione Real-time**
- ✅ Compatibilità schemi automatica
- ⚠️ Warning per configurazioni subottimali  
- ❌ Errori per configurazioni invalide

## 📋 Esempi Pratici

### Esempio 1: Monitor PDF con CREATE
```yaml
Trigger: "Aggiunta PDF"
Workflow: "wf_bd11290f923b (PDF Document CREATE Pipeline)"
Event: "pdf_file_added"
Target Node: "pdf_input_validator"
Config:
  monitor_path: "/pdf-files"
  recursive: true
```

### Esempio 2: Monitor PDF con DELETE
```yaml
Trigger: "Eliminazione PDF"  
Workflow: "wf_b32ead12131c (PDF Document DELETE Pipeline)"
Event: "pdf_file_deleted"
Target Node: "pdf_input_validator"
Config:
  monitor_path: "/pdf-files"
```

### Esempio 3: Monitor PDF con UPDATE
```yaml
Trigger: "Modifica PDF"
Workflow: "wf_055bf5029833 (PDF Document UPDATE Pipeline)"
Event: "pdf_file_modified"
Target Node: "pdf_input_validator"
Config:
  monitor_path: "/pdf-files"
```

## 🛠️ Troubleshooting

### ❌ **Nessun nodo trovato**
```bash
# Verifica che il workflow abbia nodi senza connessioni
# Controlla i log del workflow engine
tail -f logs/workflow_engine.log
```

### ❌ **Evento non disponibile**
```bash
# Verifica PDK server
curl http://localhost:3001/api/event-sources/pdf-monitor-event-source/events

# Riavvia PDK server se necessario
cd PramaIA-PDK
node server/plugin-api-server.js
```

### ❌ **Validazione fallita**
```javascript
// Verifica compatibilità in console browser
console.log('Available nodes:', availableNodes);
console.log('Event type:', selectedEventType);
console.log('Compatibility:', node.compatibility[selectedEventType]);
```

## 🎨 Personalizzazione

### Configurazione Event Source Custom
```json
{
  "monitor_path": "/custom/path",
  "recursive": false,
  "file_extensions": [".pdf", ".docx"],
  "ignore_patterns": ["temp_*", "*.tmp"],
  "debounce_time": 5,
  "max_file_size": 200,
  "notification_webhook": "https://webhook.site/your-id"
}
```

### Validazione Nodi Custom
```javascript
// In InputNodeSelector, aggiungi validazione custom
const customValidation = (node, eventType) => {
  // Logica custom per validazione
  if (node.node_type === 'document_input_node' && eventType === 'pdf_file_added') {
    return 'compatible'; // Perfettamente compatibile
  }
  return 'compatible';
};
```

## 📈 Monitoring

### Dashboard Trigger
- **Stato trigger**: Attivo/Inattivo/Errore
- **Esecuzioni recenti**: Ultimi 10 trigger eseguiti  
- **Performance**: Tempo medio di esecuzione
- **Errori**: Log errori recenti

### Metriche Utili
```sql
-- Trigger più utilizzati
SELECT name, COUNT(*) as executions 
FROM trigger_executions 
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY trigger_id, name
ORDER BY executions DESC;

-- Nodi target più popolari
SELECT target_node_id, COUNT(*) as usage_count
FROM workflow_triggers 
WHERE is_active = true
GROUP BY target_node_id
ORDER BY usage_count DESC;
```

## 🎯 Best Practices

### ✅ **Do's**
- Usa nomi trigger descrittivi
- Seleziona sempre il nodo più specifico
- Configura debounce time appropriato
- Monitora le performance regolarmente
- Testa trigger in ambiente dev prima

### ❌ **Don'ts**  
- Non usare path troppo generici per monitor
- Non ignorare warning di compatibilità
- Non creare trigger duplicati
- Non usare nomi trigger troppo lunghi
- Non dimenticare di attivare trigger

### 🎨 **Convenzioni di Naming**
```
Formato: [Fonte]-[Azione]-[Target]
Esempi:
- "PDF-Monitor-Semantic"
- "API-Webhook-Processing" 
- "Email-Attachment-Analysis"
```

## 🚀 Prossimi Passi

1. **Esplora Advanced Features**: Trigger conditions, multi-node routing
2. **Crea Workflow Custom**: Progetta workflow specifici per i tuoi use case
3. **Integra Event Sources**: Connetti nuove fonti di eventi
4. **Ottimizza Performance**: Monitor e ottimizza trigger frequenti
5. **Scala il Sistema**: Configura cluster per carichi elevati

## 📚 Risorse

### Documentazione
- [Sistema Trigger Tecnico](./TRIGGER_SYSTEM_ADVANCED_DOCUMENTATION.md)
- [API Reference](./API_TRIGGER_SYSTEM_DOCUMENTATION.md)
- [Frontend Components](./FRONTEND_TRIGGER_COMPONENTS_DOCUMENTATION.md)
- [Database Schema](./DATABASE_TRIGGER_SCHEMA_DOCUMENTATION.md)

### Community
- **GitHub Issues**: Riporta bug e feature request
- **Discussions**: Community e Q&A
- **Examples**: Repository esempi pratici

---

**Happy Triggering! 🎯**

*Guida aggiornata per versione 2.0.0 - 2025-08-05*
