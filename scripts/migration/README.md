# Scripts Migration e Rebuild

**Script per migrazione database e rebuild completo sistema**

## 📋 Script Disponibili

### `run_rebuild.py`
**Funzione:** Rebuild completo sistema
- Rebuild completo database
- Recreazione workflow
- Validazione post-rebuild

### `run_rebuild_simple.py`
**Funzione:** Rebuild semplificato
- Rebuild solo componenti essenziali
- Modalità veloce per testing
- Skip validazioni non critiche

### `run_rebuild_verbose.py`
**Funzione:** Rebuild con logging esteso
- Output dettagliato di ogni step
- Debug completo del processo
- Log di tutti gli errori

### File SQL

#### `rebuild_all_workflows.sql`
- **Funzione:** Script SQL completo rebuild
- Drop e recreate tutte le tabelle workflow
- Reset completo dati

#### `rebuild_workflows_corrected.sql`
- **Funzione:** Versione corretta rebuild
- Fix per problemi noti versione precedente
- Validazioni aggiuntive

#### `rebuild_workflows_v2.sql`
- **Funzione:** Rebuild versione 2.0
- Schema aggiornato per nuova architettura
- Compatibilità PDK

## 🚀 Utilizzo

```bash
# Rebuild completo (ATTENZIONE: cancella tutto)
python scripts/migration/run_rebuild.py

# Rebuild veloce per testing
python scripts/migration/run_rebuild_simple.py

# Rebuild con debug completo
python scripts/migration/run_rebuild_verbose.py

# Esecuzione SQL diretta
sqlcmd -i scripts/migration/rebuild_workflows_v2.sql
```

## ⚠️ **ATTENZIONE**

### 🚨 **BACKUP OBBLIGATORIO**
- **SEMPRE** fare backup completo prima di rebuild
- **Testare** su ambiente di sviluppo prima
- **Verificare** restore funzionante

### 🔒 **Solo Sviluppo**
- **MAI** usare in produzione senza supervisione
- **Coordinare** con team prima dell'uso
- **Documentare** ogni modifica

## 📋 Checklist Pre-Rebuild

- [ ] ✅ Backup completo database
- [ ] ✅ Backup file di configurazione  
- [ ] ✅ Test restore funzionante
- [ ] ✅ Ambiente di test validato
- [ ] ✅ Coordinamento team
- [ ] ✅ Finestra di manutenzione programmata

---
**Categoria:** Migration e Rebuild  
**Rischio:** 🔴 ALTO - Backup obbligatorio  
**Data organizzazione:** 16 Novembre 2025