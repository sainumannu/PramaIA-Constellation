# Scripts di Manutenzione PramaIA

**Script diagnostici per debug e validazione del sistema**

## 📋 Script Disponibili

### `check_schema.py`
**Funzione:** Validazione schema database
- Controlla struttura tabelle
- Verifica integrità referenziale
- Valida constraints e indici

### `check_system_status.py` 
**Funzione:** Status generale sistema
- Controllo servizi attivi
- Verifica connessioni database
- Monitoraggio risorse

### `check_triggers.py`
**Funzione:** Diagnostica trigger system
- Validazione trigger attivi
- Controllo mapping events
- Verifica configurazioni

### `check_workflow_ids.py`
**Funzione:** Controllo consistenza ID workflow
- Validazione ID univoci
- Controllo riferimenti
- Identificazione duplicati

### `check_workflow_structure.py`
**Funzione:** Validazione struttura workflow
- Controllo nodi validi
- Verifica connessioni
- Validazione JSON structure

## 🚀 Utilizzo

```bash
# Da root PramaIA
cd C:\PramaIA

# Esegui script singolo
python scripts/maintenance/check_schema.py

# Esegui controllo completo
python scripts/maintenance/check_system_status.py
```

## ⚡ Quando Usare

- **After deployment:** Validazione post-deploy
- **Debug issues:** Identificazione problemi
- **Maintenance:** Controlli periodici
- **Before updates:** Pre-migration checks

---
**Mantenuti per:** Debug futuro e validazione sistema  
**Data creazione:** 16 Novembre 2025