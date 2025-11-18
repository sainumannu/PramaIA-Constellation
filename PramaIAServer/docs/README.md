# Documentazione PramaIA

Benvenuti nella documentazione ufficiale di PramaIA, la piattaforma AI per l'elaborazione avanzata di documenti con architettura modulare basata su Plugin Development Kit (PDK).

## 🎯 **Trigger System v2.0.0** ⭐ **NUOVO**
- **[📖 Documentazione Completa Trigger System](./TRIGGER_SYSTEM_DOCUMENTATION_INDEX.md)**
  - Sistema trigger-to-node routing intelligente
  - Selezione automatica dei nodi
  - Evento "qualsiasi modifica" per PDF monitoring
  - Guide utente e riferimenti sviluppatori

## Struttura della Documentazione

### 📁 Architecture
Documentazione dell'architettura del sistema e dei componenti principali.

- [Event Sources Architecture](./architecture/ARCHITETTURA_EVENT_SOURCES.md) - Architettura degli event sources
- [PDK Integration Guide](./architecture/PramaIA-PDK-Guida-Integrazione.md) - Guida completa all'integrazione PDK

### 📁 Configuration
Guide di configurazione per vari componenti del sistema.

- [Centralized Configuration](./configuration/CONFIG_CENTRALIZZATA.md) - Sistema di configurazione centralizzata
- [Node Categories Configuration](./configuration/NODE_CATEGORIES_CONFIGURATION.md) - Configurazione categorie nodi
- [Workflow Categories Configuration](./configuration/WORKFLOW_CATEGORIES_CONFIGURATION.md) - Configurazione categorie workflow

### 📁 Development
Risorse per sviluppatori e contributori.

- [Copilot Instructions](./development/COPILOT_INSTRUCTIONS.md) - Istruzioni per GitHub Copilot
- [Copilot Prompt Guidelines](./development/COPILOT_PROMPT.md) - Linee guida per prompting
- [Development Notes](./development/NOTES.md) - Note di sviluppo

### 📁 Implementation
Documentazione dettagliata delle implementazioni specifiche.

- [PDK Node Visualization System](./implementation/PDK_NODE_VISUALIZATION_SYSTEM.md) - Sistema di visualizzazione nodi PDK
- [Nodes Dashboard Documentation](./implementation/NODES_DASHBOARD_DOCUMENTATION.md) - Documentazione dashboard nodi
- [PDK Tagging System](./implementation/SISTEMA_TAG_PDK_DOCUMENTAZIONE.md) - Sistema di tagging PDK
- [Workflow Trigger System](./implementation/WORKFLOW_TRIGGER_SYSTEM.md) - Sistema di trigger workflow
- [PDF Semantic Workflow](./implementation/WORKFLOW_PDF_SEMANTIC_DOCUMENTATION.md) - Workflow semantico PDF
- [Trigger System Changes](./implementation/sintesi_modifiche_trigger_system.md) - Sintesi modifiche sistema trigger

## Guide Rapide

### Per Iniziare
1. Leggi il [README principale](../README.md) per una panoramica generale
2. Consulta la [guida di integrazione PDK](./architecture/PramaIA-PDK-Guida-Integrazione.md)
3. Configura il tuo ambiente seguendo le [istruzioni di configurazione](./configuration/)

### Per Sviluppatori
1. Familiarizza con le [istruzioni Copilot](./development/COPILOT_INSTRUCTIONS.md)
2. Studia l'[architettura degli event sources](./architecture/ARCHITETTURA_EVENT_SOURCES.md)
3. Consulta la [documentazione del sistema di nodi](./implementation/PDK_NODE_VISUALIZATION_SYSTEM.md)

### Per Utenti Avanzati
1. Esplora la [configurazione delle categorie](./configuration/NODE_CATEGORIES_CONFIGURATION.md)
2. Comprendi il [sistema di trigger](./implementation/WORKFLOW_TRIGGER_SYSTEM.md)
3. Personalizza i [workflow PDF semantici](./implementation/WORKFLOW_PDF_SEMANTIC_DOCUMENTATION.md)

## Changelog e Storia

- [CHANGELOG](../CHANGELOG.md) - Storia completa delle modifiche

## Struttura del Progetto

```
PramaIA/
├── docs/                          # Documentazione (questa cartella)
│   ├── architecture/              # Architettura del sistema
│   ├── configuration/             # Guide di configurazione
│   ├── development/               # Risorse per sviluppatori
│   └── implementation/            # Implementazioni specifiche
├── PramaIA-PDK/                   # Plugin Development Kit
├── PramaIA-EventSources/          # Event Sources
├── PramaIA-Agents/                # Agenti esterni autonomi
└── PramaIAServer/                 # Server principale
    ├── backend/                   # API backend (FastAPI)
    └── frontend/                  # Frontend React
```

## Contribuire alla Documentazione

Quando aggiungi nuova documentazione:

1. **Architecture**: Per documentazione di design e architettura
2. **Configuration**: Per guide di configurazione e setup
3. **Development**: Per risorse e guide per sviluppatori
4. **Implementation**: Per documentazione di implementazioni specifiche

Segui le convenzioni di naming:
- Usa `UPPERCASE_WITH_UNDERSCORES.md` per documentazione generale
- Usa `PascalCase.md` per guide e tutorial
- Includi sempre data di creazione/modifica
- Aggiungi riferimenti incrociati quando appropriato

## Contatti e Supporto

Per domande specifiche sulla documentazione o per suggerimenti di miglioramento, consulta le note di sviluppo o contatta il team di sviluppo.

---

**Ultimo Aggiornamento**: Agosto 2025  
**Versione Documentazione**: 2.0  
**Maintainer**: Team PramaIA
