# PramaIA - AI-Powered Document Processing Platform

![PramaIA Logo](https://img.shields.io/badge/PramaIA-v1.1.0-blue) ![PDK](https://img.shields.io/badge/PDK-Plugin_System-green) ![Tags](https://img.shields.io/badge/Tags-System-orange)

## 🚀 Panoramica

**PramaIA** è una piattaforma avanzata per l'elaborazione di documenti basata su intelligenza artificiale, progettata con un'architettura modulare e scalabile. Il sistema combina potenti capacità di elaborazione PDF semantica con un framework di plugin estensibile (PDK - Plugin Development Kit).

### ✨ Caratteristiche Principali

- **🔌 Plugin Development Kit (PDK)** - Sistema modulare per estendere le funzionalità
- **🏷️ Sistema di Tag Avanzato** - Organizzazione intelligente di plugin ed event sources
- **📄 Elaborazione PDF Semantica** - Estrazione e analisi avanzata di documenti
- **⚡ Event Sources** - Monitoraggio automatico e trigger personalizzabili
- **🤖 AI Integration** - Supporto per LLM e modelli di embedding
- **💾 Vector Database** - ChromaDB per ricerca semantica
- **🔄 Workflow Engine** - Orchestrazione di pipeline complesse

## 🏗️ Architettura

```
PramaIA/
├── PramaIAServer/          # Server principale e backend
│   ├── backend/            # API FastAPI
│   └── frontend/           # Interface React
├── PramaIA-PDK/            # Plugin Development Kit
│   ├── server/             # PDK API Server
│   ├── plugins/            # Plugin disponibili
│   └── src/                # Core PDK (TypeScript)
├── PramaIA-Plugins/        # Plugin esterni
└── PramaIA-EventSources/   # Event sources personalizzate
```

### Componenti Principali

1. **PramaIA Server** - Core dell'applicazione con API REST
2. **PDK System** - Framework per plugin modulari
3. **Event Sources** - Sistema di eventi e trigger
4. **Tag System** - Organizzazione gerarchica di componenti
5. **Frontend** - Interfaccia utente React

## 📚 Documentazione

La documentazione completa è organizzata nella cartella [`docs/`](./docs/):

- **[Architecture](./docs/architecture/)** - Architettura del sistema e guide di integrazione
- **[Configuration](./docs/configuration/)** - Guide di configurazione
- **[Development](./docs/development/)** - Risorse per sviluppatori
- **[Implementation](./docs/implementation/)** - Documentazione implementazioni specifiche

### Guide Rapide
- [Guida di Integrazione PDK](./docs/architecture/PramaIA-PDK-Guida-Integrazione.md)
- [Sistema di Visualizzazione Nodi](./docs/implementation/PDK_NODE_VISUALIZATION_SYSTEM.md)
- [Configurazione Event Sources](./docs/architecture/ARCHITETTURA_EVENT_SOURCES.md)

## 🏷️ Sistema di Tag

Il sistema di tag PDK fornisce organizzazione avanzata attraverso 4 livelli gerarchici:

### Livelli di Tag
- **Plugin Level** - Categorizzazione dei plugin
- **Node Level** - Tag per singoli nodi di elaborazione  
- **Event Source Level** - Organizzazione delle sorgenti eventi
- **Event Type Level** - Tipologie specifiche di eventi

### Funzionalità
- ✅ Filtri avanzati (AND/OR, inclusione/esclusione)
- ✅ Statistiche tag in tempo reale
- ✅ Interfaccia UI con badge e pannelli interattivi
- ✅ API REST per integrazione esterna
- ✅ Retrocompatibilità completa

```bash
# Esempi API con tag system
GET /api/plugins?tags=internal,core&mode=AND
GET /api/event-sources?tags=monitoring
GET /api/tags  # Statistiche complete
```

## 🚀 Quick Start

### 1. Avvio PDK Server
```powershell
cd PramaIA-PDK/server
node plugin-api-server.js
# Server disponibile: http://localhost:3001
```

### 2. Avvio Server Principale
```powershell
cd PramaIAServer
python -m uvicorn backend.main:app --reload
# API disponibile: http://localhost:8000
```

### 3. Avvio Frontend
```powershell
cd PramaIAServer/frontend/client
npm start
# UI disponibile: http://localhost:3000
```

## 📋 Plugin Disponibili

### Core Plugins
- **internal-processors-plugin** `[internal, core, text-processing]`
  - Text Joiner, Text Filter, User Context Provider
  
- **pdf-semantic-complete-plugin** `[pdf, semantic, document, ai]`
  - Pipeline completa PDF → Embedding → ChromaDB → Query

### Event Sources
- **pdf-monitor-event-source** `[monitoring, file-system, pdf]`
- **webhook-event-source** `[api, http, webhook]`
- **scheduler-event-source** `[automation, cron, timer]`
- **database-triggers-event-source** `[database, monitoring, trigger]`
- **email-monitor-event-source** `[monitoring, email, automation]`

### Workflow Control
- **workflow-scheduler-plugin** `[automation, schedule, control]`

## 🔧 Configurazione

### Environment Variables
```bash
PDK_SERVER_PORT=3001
PRAMAIA_SERVER_PORT=8000
CHROMA_DB_PATH=./chroma_db
FRONTEND_PORT=3000
```

### Database Setup
```powershell
# PostgreSQL per metadata
# ChromaDB per vettori (auto-configurazione)
```

## 📚 Documentazione

- **[Sistema Tag PDK](SISTEMA_TAG_PDK_DOCUMENTAZIONE.md)** - Guida completa al sistema di tag
- **[Guida Integrazione PDK](PramaIA-PDK-Guida-Integrazione.md)** - Come integrare e sviluppare plugin
- **[Workflow PDF Semantico](WORKFLOW_PDF_SEMANTIC_DOCUMENTATION.md)** - Pipeline di elaborazione documenti
- **[Sistema Trigger](WORKFLOW_TRIGGER_SYSTEM.md)** - Event sources e automazione

## 🛠️ Sviluppo

### Creazione Plugin
```bash
cd PramaIA-PDK/plugins
mkdir my-new-plugin
# Copia template e configura plugin.json con tag appropriati
```

### Tag System Usage
```javascript
// Configura tag nel plugin.json
{
  "name": "my-plugin",
  "tags": ["external", "processing", "utility"],
  "nodes": [
    {
      "id": "my_node",
      "tags": ["transform", "data"]
    }
  ]
}
```

### Frontend Integration
```jsx
import { PDKTagManagementPanel } from './components/PDKTagManagement';
import { usePDKPlugins } from './hooks/usePDKData';

const MyComponent = () => {
  const { plugins, updateFilters } = usePDKPlugins();
  return <PDKTagManagementPanel items={plugins} />;
};
```

## 🔍 Testing

```powershell
# Test PDK API
curl http://localhost:3001/api/plugins?tags=internal

# Test sistema completo
node test_workflow_api.py

# Test frontend standalone
# Apri: pdk-tag-system-test.html
```

## 📊 Monitoring & Logging

- **PDK Server**: Logging dettagliato delle operazioni plugin
- **Tag System**: Statistiche utilizzo e performance
- **Event Sources**: Monitoring lifecycle e eventi
- **API Metrics**: Rate limiting e analytics

## 🤝 Contributing

1. Fork del repository
2. Crea feature branch con tag semantici appropriati
3. Sviluppa seguendo le convenzioni PDK
4. Aggiungi test per nuove funzionalità
5. Aggiorna documentazione
6. Submit pull request

### Convenzioni Tag
- Usa tag semantici consistenti
- Segui le categorie predefinite
- Documenta nuovi tag nel sistema
- Testa filtri e compatibilità

## 📜 License

MIT License - Vedi [LICENSE](LICENSE) per dettagli.

## 🏆 Roadmap

### v1.1 (Q4 2025)
- [ ] Tag autocomplete e suggestions ML
- [ ] GraphQL API per query complesse
- [ ] Plugin marketplace integrato
- [ ] Advanced analytics dashboard

### v1.2 (Q1 2026)
- [ ] Multi-tenant support
- [ ] Cloud deployment tools
- [ ] Real-time collaboration
- [ ] Mobile responsive UI

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/sainumannu/PramaIA/issues)
- **Documentazione**: Vedi cartella docs/
- **Community**: [Discussions](https://github.com/sainumannu/PramaIA/discussions)

---

**PramaIA** - *Empowering Document Processing with AI* 🚀

[![Built with](https://img.shields.io/badge/Built_with-TypeScript-blue)](https://www.typescriptlang.org/)
[![Backend](https://img.shields.io/badge/Backend-FastAPI-green)](https://fastapi.tiangolo.com/)
[![Frontend](https://img.shields.io/badge/Frontend-React-blue)](https://reactjs.org/)
[![AI](https://img.shields.io/badge/AI-LLM_Ready-purple)](https://www.anthropic.com/)
[![Database](https://img.shields.io/badge/Vector_DB-ChromaDB-orange)](https://www.trychroma.com/)
