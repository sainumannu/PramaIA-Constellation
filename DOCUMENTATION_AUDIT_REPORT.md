# 📋 Audit Report: Documentazione vs Realtà del Database

**Data:** 19 novembre 2025  
**Stato:** ⚠️ **SIGNIFICATIVE DISCREPANZE TROVATE**

---

## 🔴 Problemi Principali

### 1. **Schema Database INCORRETTO in Documentazione**

#### Documentazione (sbagliata):
```sql
CREATE TABLE workflow_triggers (
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

#### Realtà nel Database (CORRETTO):
```sql
CREATE TABLE workflow_triggers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    source TEXT NOT NULL,
    workflow_id TEXT NOT NULL,
    conditions TEXT DEFAULT '{}',
    active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    target_node_id TEXT DEFAULT NULL
);
```

**Differenze:**
- ✅ SQLite usa TEXT/INTEGER, non VARCHAR/BOOLEAN
- ✅ Aggiunto `target_node_id` (PRESENTE nel database, MANCANTE dalla documentazione!)
- ✅ Nessun vincolo FOREIGN KEY nel database reale

---

### 2. **Workflow ID COMPLETAMENTE DIVERSI**

#### IDs nella Documentazione:
```
PDF Document CREATE Pipeline → wf_7af99caf311a
PDF Document READ Pipeline → wf_86ee1359f7f8
PDF Document UPDATE Pipeline → wf_fcad5d0befdb
PDF Document DELETE Pipeline → wf_04f5046263ff
```

#### IDs nel Database REALE:
```
PDF Document CREATE Pipeline (ID=2) → wf_bd11290f923b ❌
PDF Document READ Pipeline (ID=3) → wf_5008f60dc207 ❌
PDF Document UPDATE Pipeline (ID=4) → wf_055bf5029833 ❌
PDF Document DELETE Pipeline (ID=5) → wf_b32ead12131c ❌
PDF Semantic Processing Pipeline (ID=1) → wf_92eded45afde ❌
```

**⚠️ TUTTI gli ID sono SBAGLIATI nella documentazione!**

---

### 3. **Event Types SBAGLIATI**

#### Documentazione (sbagliata):
```
pdf_file_added, pdf_file_deleted, pdf_file_modified
```

#### Realtà nel Database (CORRETTO):
```
Trigger Aggiunta PDF → event_type: pdf_file_added ✓
Trigger Eliminazione PDF → event_type: pdf_file_deleted ✓
Trigger Aggiornamento PDF → event_type: pdf_file_modified ✓
```

**Nota:** Gli event types SONO corretti, solo gli IDs workflow sono sbagliati

---

### 4. **Target Node ID Mancante nella Documentazione**

#### Documentazione:
- Non menziona `target_node_id` nel database schema
- Pero lo menziona negli endpoint API (confusione!)

#### Realtà nel Database:
```
Tutti e 3 i trigger avevano:
  target_node_id = NULL (appena fixato a "pdf_input_validator")
```

**⚠️ Critico:** La documentazione non spiega come il trigger sa quale nodo del workflow ricevere i dati

---

### 5. **Numero di Nodi SBAGLIATO**

#### Documentazione:
```
PDF Document CREATE Pipeline | 10 nodi
PDF Document READ Pipeline | 10 nodi
PDF Document UPDATE Pipeline | 11 nodi
PDF Document DELETE Pipeline | 12 nodi
```

#### Realtà nel Database:
```
✓ PDF Document CREATE Pipeline: 10 nodi (CORRETTO)
✓ PDF Document READ Pipeline: 10 nodi (CORRETTO)
✓ PDF Document UPDATE Pipeline: 11 nodi (CORRETTO)
✓ PDF Document DELETE Pipeline: 12 nodi (CORRETTO)
✓ PDF Semantic Processing Pipeline: 11 nodi (MANCANTE DALLA DOCUMENTAZIONE!)
```

---

### 6. **Nodi Input Node MANCANTI DALLA DOCUMENTAZIONE**

#### Nel Database REALE:
Ogni workflow ha un nodo di input:
```
Nodo: pdf_input_validator
Tipo: PDFInputValidator
InputPorts: [] (vuoto - riceve dall'esterno)
OutputPorts: [validated_pdf, file_metadata, validation_result]
```

#### Nella Documentazione:
```
❌ Non menzionato!
❌ Non spiega come i dati del trigger raggiungono il workflow
```

---

## 📊 Tabella di Confronto

| Aspetto | Documentazione | Database Reale | Status |
|---------|---|---|---|
| Schema SQL | VARCHAR/BOOLEAN | TEXT/INTEGER | ❌ Sbagliato |
| Target Node ID | Menzionato API solo | Presente in DB | ❌ Incompleto |
| Workflow IDs | wf_7af99caf311a | wf_bd11290f923b | ❌ Tutti sbagliati |
| Event Types | pdf_file_* | pdf_file_* | ✅ Corretto |
| Nodi per workflow | Elencati | Corretti nel DB | ✅ Corretto |
| Nodi Input | Non documentati | pdf_input_validator | ❌ Non documentato |
| Trigger configurati | 3 menzionati | 3 nel DB | ✅ Corretto |
| Workflow totali | 4 documentati | 5 nel DB | ❌ Manca 1 |

---

## 🔧 Azioni Necessarie per Correggere la Documentazione

### 1. Aggiornare Schema Database
```markdown
PRIMA:
  id VARCHAR(36) PRIMARY KEY
DOPO:
  id TEXT PRIMARY KEY
  
PRIMA:
  active BOOLEAN DEFAULT 1
DOPO:
  active INTEGER DEFAULT 1
  
AGGIUNGERE:
  target_node_id TEXT DEFAULT NULL
```

### 2. Aggiornare Workflow IDs
```markdown
PDF Document CREATE Pipeline: wf_bd11290f923b (era: wf_7af99caf311a)
PDF Document READ Pipeline: wf_5008f60dc207 (era: wf_86ee1359f7f8)
PDF Document UPDATE Pipeline: wf_055bf5029833 (era: wf_fcad5d0befdb)
PDF Document DELETE Pipeline: wf_b32ead12131c (era: wf_04f5046263ff)
```

### 3. Documentare Nodi Input
```markdown
Ogni workflow deve avere un nodo di input:
- Node ID: pdf_input_validator
- Type: PDFInputValidator
- Purpose: Riceve i dati dal trigger (file PDF)
- Output: validated_pdf, file_metadata, validation_result
```

### 4. Spiegare Mappatura Trigger → Workflow → Nodo
```markdown
Flusso Completo:
1. Evento trigger: pdf_file_added
2. Ricerca trigger con event_type = pdf_file_added
3. Retrieve workflow_id dal trigger (es. wf_bd11290f923b)
4. Retrieve target_node_id dal trigger (es. pdf_input_validator)
5. Passa i dati dell'evento al nodo target_node_id del workflow
```

### 5. Aggiungere Workflow Mancante
```markdown
PDF Semantic Processing Pipeline (ID=1, workflow_id=wf_92eded45afde)
- 11 nodi
- Purpose: Elaborazione semantica di documenti PDF
- Non ha trigger associato
```

---

## 📝 Conclusioni

**La documentazione è SIGNIFICATIVAMENTE OBSOLETA:**

1. ✅ **Concettualmente corretta** - Il sistema funziona come descritto
2. ❌ **Dettagli tecnici obsoleti** - IDs e schema sono cambiati
3. ❌ **Informazioni incomplete** - Manca la spiegazione del `target_node_id`
4. ⚠️ **Fuori sincro con il database** - Non riflette lo stato attuale

**Raccomandazione:** Rigenerare tutta la documentazione dai database effettivi anziché da configurazioni statiche.

---

## 🎯 Fix Applicato Oggi

✅ **Risolto:** `target_node_id` aggiornato da NULL → `pdf_input_validator` per tutti i 3 trigger

**Prossimi passi:**
1. Aggiornare TUTTA la documentazione con i dati REALI dal database
2. Creare script di validazione per verificare coerenza documentation ↔️ database
3. Implementare un sistema di "single source of truth" per i dati di configurazione
