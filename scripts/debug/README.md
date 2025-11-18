# Scripts Debug e Analisi

**Script per debugging, analisi e risoluzione problemi**

## 📋 Script Disponibili

### `analyze_triggers.py`
**Funzione:** Analisi sistema trigger
- Analizza configurazioni trigger attive
- Identifica trigger malfunzionanti
- Report dettagliato performance

### `analyze_view_state.py` 
**Funzione:** Analisi stato views database
- Controlla views materializzate
- Verifica refresh automatici
- Identifica views corrotte

### `debug_database.py`
**Funzione:** Debug completo database
- Controllo connessioni
- Analisi performance query
- Identificazione deadlock

### `patch_sqlalchemy.py`
**Funzione:** Patch temporanee SQLAlchemy
- Fix temporanei per bug noti
- Workaround per limitazioni
- Patch di compatibilità

### `run_sql.py`
**Funzione:** Esecuzione SQL manuale
- Esecuzione query ad-hoc
- Testing SQL prima del deploy
- Analisi dati diretta

## 🚀 Utilizzo

```bash
# Da root PramaIA
cd C:\PramaIA

# Debug generale
python scripts/debug/debug_database.py

# Analisi trigger
python scripts/debug/analyze_triggers.py

# Esecuzione SQL
python scripts/debug/run_sql.py --query "SELECT * FROM workflows LIMIT 10"
```

## ⚠️ Attenzione

- **Solo per debugging:** Non usare in produzione
- **Backup obbligatorio:** Prima di patch o modifiche
- **Log completo:** Tutti gli script loggano in `logs/debug/`

---
**Categoria:** Debug e Troubleshooting  
**Data organizzazione:** 16 Novembre 2025