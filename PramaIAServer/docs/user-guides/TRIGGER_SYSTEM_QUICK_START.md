# Quick Start Guide - Advanced Trigger System

## 🚀 Introduzione Rapida

Benvenuto nel nuovo sistema trigger avanzato di PramaIA! Questa guida ti aiuterà a iniziare rapidamente con le nuove funzionalità di routing intelligente dei trigger.

## ⚡ Setup Veloce

### 1. **Prerequisiti**
```bash
# Verifica versioni
python --version  # Python 3.9+
node --version    # Node.js 16+
psql --version    # PostgreSQL 12+
```

### 2. **Migrazione Database**
```bash
cd PramaIAServer
python -m alembic upgrade head
```

### 3. **Avvio Servizi**
```bash
# Terminal 1: Backend
cd PramaIAServer
python -m uvicorn backend.main:app --reload

# Terminal 2: Frontend  
cd PramaIAServer/frontend/client
npm start

# Terminal 3: PDK Server
cd PramaIA-PDK
node server/plugin-api-server.js
```

## 🎯 Creazione del Primo Trigger Avanzato

### Passo 1: Apri Gestione Trigger
1. Vai su `http://localhost:3000`
2. Naviga in **Workflow → Gestione Trigger**
3. Clicca **"Nuovo Trigger"**

### Passo 2: Configura il Trigger
```yaml
Nome: "Monitor PDF Intelligente"
Descrizione: "Monitora cartella PDF con routing specifico"
Workflow: [Seleziona il tuo workflow]
Event Source: "pdf-monitor-event-source"
Evento: "Qualsiasi Modifica"  # 🆕 Nuovo evento!
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

### 📊 **Evento "Qualsiasi Modifica"**
```json
{
  "eventType": "any_change",
  "data": {
    "file_path": "/path/to/file.pdf",
    "change_type": "created",  // created|modified|deleted
    "detected_at": "2025-08-05T10:30:00Z",
    "file_size": 1024
  }
}
```

### 🔍 **Validazione Real-time**
- ✅ Compatibilità schemi automatica
- ⚠️ Warning per configurazioni subottimali  
- ❌ Errori per configurazioni invalide

## 📋 Esempi Pratici

### Esempio 1: Monitor PDF con Analisi Semantica
```yaml
Trigger: "PDF Semantico"
Workflow: "Analisi Documentale"
Event: "any_change"
Target Node: "semantic-analyzer-node"
Config:
  monitor_path: "/documents/incoming"
  recursive: true
```

### Esempio 2: Trigger Multi-Step
```yaml
Trigger: "Pipeline PDF Completa"  
Workflow: "PDF Complete Pipeline"
Event: "pdf_file_added"
Target Node: "pdf-metadata-extractor"
Config:
  monitor_path: "/inbox"
  max_file_size: 100
```

### Esempio 3: Trigger con Filtraggio
```yaml
Trigger: "Solo PDF Grandi"
Workflow: "Heavy Processing"
Event: "pdf_file_added"
Target Node: "batch-processor"
Config:
  monitor_path: "/large-docs"
  min_file_size: 10  # MB
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
  if (node.node_type === 'heavy-processor' && eventType === 'any_change') {
    return 'warning'; // Potrebbe essere lento
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
