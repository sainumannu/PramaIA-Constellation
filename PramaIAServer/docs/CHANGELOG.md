# PramaIA - Changelog

## [1.2.0] - 2025-08-04

### 📚 MAJOR: Riorganizzazione Documentazione e Sistema Nodi

#### ✨ Nuove Funzionalità

**Riorganizzazione Documentazione**
- Creata cartella `docs/` con struttura organizzata per categoria
- Sottocartelle: `architecture/`, `configuration/`, `development/`, `implementation/`
- Nuovo sistema di documentazione centralizzata con indice navigabile
- Migrazione di tutti i file `.md` nella nuova struttura

**Sistema di Visualizzazione Nodi PDK**
- Refactoring completo di `PDKPluginList.jsx` per mostrare singoli nodi
- Estrazione automatica dei nodi dai plugin container
- Visualizzazione diretta dei componenti utilizzabili nel canvas
- Miglioramento UX con accesso diretto ai dettagli dei nodi

#### 🔧 Miglioramenti

**NodeDetailsModal**
- Modal avanzato con tab: Info, Category, Schema, Plugin, Debug
- Gestione categorie con sistema di override
- Panel di debug integrato per sviluppatori

**PDKPluginList Interface**
- Tabella ottimizzata con colonne: Nome, Plugin, Descrizione, Categoria, Tags, Azioni
- Filtri avanzati per tag combinati (nodo + plugin)
- Stati dell'interfaccia migliorati (loading, error, empty state)

#### 📁 Struttura Documentazione

```
docs/
├── README.md                    # Indice principale
├── architecture/               # Architettura sistema
├── configuration/             # Guide configurazione
├── development/               # Risorse sviluppatori
└── implementation/            # Implementazioni specifiche
```

#### 🎯 Benefici

**Per Utenti**
- Visibilità diretta dei nodi utilizzabili
- Accesso rapido ai dettagli e configurazione
- Ricerca efficace con filtri combinati

**Per Sviluppatori**
- Documentazione organizzata e navigabile
- Separazione chiara tra logica e visualizzazione
- Facilità di manutenzione e estensione

---

## [1.1.0] - 2025-08-03

### 🏷️ MAJOR: Sistema di Tag PDK Implementato

#### ✨ Nuove Funzionalità

**Sistema di Tag Gerarchico**
- Implementato sistema di tag configurabili a 4 livelli
- Supporto per tag su: Plugin → Node → Event Source → Event Type
- Schema TypeScript con validazione Zod
- Retrocompatibilità completa con plugin esistenti

**API Extensions**
- Nuovo endpoint `GET /api/plugins` con filtri tag avanzati
- Nuovo endpoint `GET /api/event-sources` con supporto tag
- Nuovo endpoint `GET /api/tags` per statistiche e analytics
- Parametri di filtro: `tags`, `exclude_tags`, `mode` (AND/OR)

**Frontend Components**
- Nuovi componenti React per gestione tag UI
- `PDKTagManagementPanel` - Pannello completo di gestione
- `PDKTagBadge` - Badge visuali per tag
- `PDKTagFilter` - Filtri interattivi
- `PDKTagCloud` - Visualizzazione cloud
- `PDKTagStats` - Dashboard statistiche

**Custom Hooks**
- `usePDKData` - Hook principale per data management
- `usePDKPlugins` - Hook specifico per plugin con tag
- `usePDKEventSources` - Hook per event sources
- Supporto per stati loading/error e fallback API

#### 🔧 Miglioramenti

**UI/UX**
- Interfaccia tag responsive con Tailwind CSS
- Toggle panels per filtri avanzati
- Stati di caricamento e gestione errori
- Visualizzazione tag con badge colorati
- Statistiche in tempo reale

**Performance**
- Caching intelligente per richieste API
- Lazy loading per dataset grandi
- Debouncing per filtri real-time
- Ottimizzazioni query database

**Developer Experience**
- TypeScript interfaces complete per tag system
- Documentazione comprensiva
- Template e esempi pratici
- Test suite per validazione

#### 📊 Tag Semantici Predefiniti

**Plugin Categories**
- `internal`, `core`, `external`, `utility`, `integration`

**Processing Types** 
- `text-processing`, `document`, `pdf`, `semantic`, `ai`

**Event Source Types**
- `monitoring`, `file-system`, `database`, `api`, `schedule`

**Automation & Control**
- `automation`, `trigger`, `cron`, `recurring`, `timer`

#### 🛠️ Modifiche Tecniche

**Backend**
- Esteso `plugin-api-server.js` con logica filtri tag
- Implementata validazione input e sanitizzazione
- Aggiunto rate limiting e logging dettagliato
- Supporto per statistiche tag aggregate

**Frontend**
- Creato sistema di componenti modulari
- Implementati hook personalizzati per data fetching
- Aggiunta gestione stati complessa
- UI responsiva e accessibile

**Configurazione**
- Aggiornati manifest plugin con tag semantici
- Schema configurazione esteso
- Backward compatibility mantenuta
- Validazione configurazioni

#### 📁 File Aggiunti/Modificati

**Nuovi File**
```
src/core/interfaces.ts                      # Interfacce TypeScript estese
src/components/PDKTagManagement.jsx         # Componenti React tag
src/components/PDKEventSourcesList.jsx      # Lista event sources
src/components/PDKDashboard.jsx             # Dashboard principale
src/hooks/usePDKData.js                     # Custom hooks
pdk-tag-system-test.html                    # Test interface standalone
SISTEMA_TAG_PDK_DOCUMENTAZIONE.md           # Documentazione completa
README.md                                   # README principale progetto
```

**File Modificati**
```
server/plugin-api-server.js                # API server con tag support
components/PDKPluginList.jsx               # Lista plugin migliorata
plugins/*/plugin.json                      # Manifesti con tag
PramaIA-PDK-Guida-Integrazione.md          # Guida aggiornata
```

#### 🧪 Testing

**API Testing**
- Endpoint `/api/plugins?tags=internal` testato
- Filtri AND/OR verificati
- Performance con 40+ tag validata
- Backward compatibility confermata

**Frontend Testing**
- Componenti React testati standalone
- Integrazione UI validata
- Responsive design verificato
- Accessibility compliance

**Integration Testing**
- Server PDK (localhost:3001) operativo
- API endpoints funzionanti
- Tag system end-to-end testato
- Database queries ottimizzate

#### 🚀 Impatto

**Per Sviluppatori**
- Organizzazione plugin semplificata
- Discovery migliorata
- Filtraggio avanzato
- Best practices definite

**Per Utenti**
- Interfaccia più intuitiva
- Ricerca semantica
- Categorizzazione chiara
- Performance migliorate

**Per Sistema**
- Scalabilità aumentata
- Manutenibilità migliorata
- Estensibilità garantita
- Monitoring avanzato

#### 📈 Metriche

- **8 plugin** configurati con tag
- **5 event sources** taggate
- **40+ tag semantici** definiti
- **100% backward compatibility** mantenuta
- **0 breaking changes** introdotti

#### 🔮 Roadmap Prossime Versioni

**v1.2 (Q4 2025)**
- Tag autocomplete e suggestions ML
- GraphQL API per query complesse
- Advanced analytics dashboard
- Plugin marketplace integration

**v1.3 (Q1 2026)**
- Tag validation rules
- Bulk tag operations
- Export/import configurazioni
- Mobile responsive optimization

---

### 📝 Note per Sviluppatori

Il sistema di tag è completamente operativo e pronto per l'uso in produzione. Tutti i plugin esistenti sono retrocompatibili e funzionano senza modifiche. I nuovi plugin dovrebbero includere tag semantici appropriati per beneficiare del sistema di organizzazione.

### 🆘 Breaking Changes

**Nessuno** - Il sistema è progettato per essere completamente retrocompatibile.

### 🔧 Migration Guide

Non sono richieste migrazioni. I plugin esistenti continueranno a funzionare normalmente. Per beneficiare del tag system, aggiungere semplicemente campi `tags` nei manifesti plugin.

---

## [1.0.0] - 2025-07-01

### Initial Release
- PramaIA PDK framework base
- Plugin system modulare
- Event sources support
- Workflow engine
- Frontend React interface
- API server

---

**Legenda:**
- ✨ Nuove funzionalità
- 🔧 Miglioramenti
- 🐛 Bug fixes
- 💥 Breaking changes
- 📝 Documentazione
- 🧪 Testing
