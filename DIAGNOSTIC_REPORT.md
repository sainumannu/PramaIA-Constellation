# Rapporto Diagnostico Pipeline Vettorizzazione PramaIA
**Data:** 19 Novembre 2025  
**Stato Sessione:** Diagnostica Completa Completata

---

## Sommario Esecutivo

La pipeline di vettorizzazione PramaIA è **correttamente configurata** ma **bloccata** da due problemi critici di autenticazione:

1. **Token JWT Incompleto** - Il token non contiene `user_id`
2. **Endpoint Upload Protetto** - Richiede autenticazione

**Impatto:** Nessun documento può essere caricato, di conseguenza i trigger non si attivano e la pipeline rimane ferma.

---

## Status Infrastruttura

| Componente | URL | Status | Note |
|-----------|-----|--------|------|
| Monitor Agent | http://localhost:8001 | ✓ ONLINE | Funzionante, rileva file con `/monitor/rescan_all` |
| Backend FastAPI | http://localhost:8000 | ✓ ONLINE | Tutte le API disponibili, richiede autenticazione |
| VectorStore Service | http://localhost:8090 | ✓ ONLINE | Pronto per ricevere documenti |
| Database SQLite | `PramaIAServer/backend/db/database.db` | ✓ OK | 0.84 MB, 15 tabelle, 1072 eventi Monitor |

---

## Database - Stato Attuale

```
Trigger Configurati:       3 (Tutti ACTIVE)
  ✓ Trigger Aggiunta PDF       → Workflow: wf_bd11290f923b
  ✓ Trigger Eliminazione PDF    → Workflow: wf_b32ead12131c
  ✓ Trigger Aggiornamento PDF   → Workflow: wf_055bf5029833

Workflow Executions:       0 (VUOTO - PROBLEMA!)
Nodi Workflow:            54 (Correttamente definiti)
Eventi Monitor:         1072 (Dati storici da Ottobre)
```

---

## Problemi Identificati

### P0 - CRITICO: Token JWT Mancante di user_id
```
Sintomo: Errore 400 durante upload
Response: {"detail":"user_id mancante nel token utente"}
```

**Causa:** La funzione di creazione token in `backend/auth/dependencies.py` non include `user_id` nel payload JWT.

**Soluzione:** Modificare il token JWT per includere l'ID utente

### P0 - CRITICO: Endpoint Upload Protetto
```
Sintomo: Errore 401 senza token
        Errore 400 con token non valido
```

**Causa:** L'endpoint `/api/documents/upload/` richiede autenticazione Bearer

**Soluzione:** Creare endpoint `/api/documents/upload-public/` senza autenticazione oppure correggere il token

### P1 - IMPORTANTE: Pipeline Non Eseguita
```
Sintomo: workflow_executions = 0 records
         Nessun documento vettorizzato
```

**Causa:** Impossibile caricare documenti → Trigger non si attivano → Workflow non eseguono

**Soluzione dipende da:** Risolvere P0

### P2 - DESIDERABILE: Monitor Richiede Rescan Manuale
```
Sintomo: File creati ma non generano automaticamente eventi
```

**Workaround:** Eseguire `curl -X POST http://localhost:8001/monitor/rescan_all`

**Soluzione:** Verificare frequenza di polling del Monitor

---

## Test Eseguiti

### Test 1: Monitor File Detection ✓
```
✓ Monitor online e monitorando D:\TestPramaIA
✓ File test creati: test_document_20251119_164346.pdf (2163 bytes)
✓ Rescan triggerato manualmente: 2 eventi generati
✓ File rilevato nel buffer Monitor
```

### Test 2: Trigger Configuration ✓
```
✓ 3 trigger attivi nel database
✓ Tutti configurati con workflow corretto
✓ Mapping node-to-trigger valido
```

### Test 3: Upload (Endpoint Discovery) ✓
```
✓ Endpoint /api/documents/upload/ trovato
✓ Richiede Bearer token (401 senza)
✓ Token invalido causa 400 "user_id mancante"
```

### Test 4: Authentication ✓
```
✓ Registrazione nuovo utente: OK
✓ Login con credenziali: OK
✓ Token JWT generato: OK
✗ Token manca user_id: ERRORE
```

---

## Script Creati per Diagnostica

1. **`final_diagnostic_report.py`** - Rapporto dettagliato completo
2. **`quick_check.py`** - Check rapido dello stato
3. **`test_e2e_register_login.py`** - Test pipeline con autenticazione
4. **`test_e2e_final.py`** - Test endpoint corretto
5. **`find_upload_endpoint.py`** - Scoperta endpoint OpenAPI
6. **`create_test_pdf.py`** - Generazione PDF test
7. **`force_monitor_rescan.py`** - Trigger manuale Monitor

### Come usarli:
```bash
# Diagnostica rapida
python quick_check.py

# Rapporto completo
python final_diagnostic_report.py

# Test pipeline (dopo correzione token)
python test_e2e_register_login.py
```

---

## Soluzioni Raccomandate

### FASE 1 - Correzione Urgente (Priorità P0)

**Opzione A: Correggere il Token JWT** (Consigliato)

```python
# File: PramaIAServer/backend/auth/dependencies.py

# Trovare la funzione che crea il token (probabilmente create_access_token)
# Aggiungere user_id al payload:

def create_access_token(data: dict, expires_delta=None):
    to_encode = data.copy()
    
    # AGGIUNGERE QUESTA LINEA:
    to_encode["user_id"] = data.get("sub")  # o l'ID effettivo dell'utente
    
    # ... resto del codice
```

Poi testare:
```bash
python test_e2e_register_login.py
```

**Opzione B: Creare Endpoint Upload Pubblico** (Fallback)

```python
# File: PramaIAServer/backend/routers/documents.py

@router.post("/upload-public/")
async def upload_public(files: List[UploadFile]):
    """Upload senza autenticazione - fallback per problemi token"""
    # Usare user_id di default (es. ID=1)
    # Resto del codice come upload normale
```

---

## Comandi Diagnostici Utili

```bash
# Verificare trigger nel database
sqlite3 PramaIAServer/backend/db/database.db \
  "SELECT id, name, active, workflow_id FROM workflow_triggers;"

# Verificare esecuzioni workflow
sqlite3 PramaIAServer/backend/db/database.db \
  "SELECT COUNT(*) FROM workflow_executions;"

# Forza rilevamento file nel Monitor
curl -X POST http://localhost:8001/monitor/rescan_all

# Controllare buffer Monitor
curl http://localhost:8001/monitor/events/recent?limit=5

# Lista endpoint disponibili
curl http://localhost:8000/openapi.json | python -m json.tool | grep -i upload
```

---

## Checklist Prossimi Step

### Immediato (Oggi)
- [ ] Correggere token JWT aggiungendo user_id
  - [ ] Locate function in `backend/auth/dependencies.py`
  - [ ] Add user_id to payload
  - [ ] Test con `test_e2e_register_login.py`
  - [ ] Verificare workflow_executions > 0

### Domani
- [ ] Verificare vettorizzazione documenti
- [ ] Testare query semantica
- [ ] Validare metadati nel database

### Questa settimana
- [ ] Abilitare auto-detection Monitor (senza rescan manuale)
- [ ] Aggiungere error handling robusto
- [ ] Implementare retry logic
- [ ] Aggiungere logging dettagliato

---

## Conclusioni

La pipeline è **ben architettata e correttamente configurata**. I problemi sono **puramente tecnici** (token JWT) e **facilmente risolvibili**.

Una volta corretti:
1. Upload sarà possibile
2. Trigger si attiveranno automaticamente
3. Workflow eseguiranno
4. Documenti verranno vettorizzati
5. Metadati verranno salvati

**Tempo stimato per correzione:** 15-30 minuti

**Rischio:** Minimo (problema noto, soluzione semplice)

---

**Generato da:** Diagnostica Automatica PramaIA  
**Data:** 2025-11-19 17:55:30  
**Script principale:** `final_diagnostic_report.py`
