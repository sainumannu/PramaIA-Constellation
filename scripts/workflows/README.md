# Scripts Workflow Management

**Script per gestione, creazione e manutenzione workflow**

## 📋 Script Disponibili

### Gestione Workflow

#### `create_delete_update_workflows.py`
**Funzione:** CRUD completo workflow
- Creazione nuovi workflow
- Update workflow esistenti  
- Eliminazione sicura workflow

#### `list_workflows_triggers.py`
**Funzione:** Lista workflow e trigger
- Overview completa sistema
- Mapping workflow-trigger
- Status workflow attivi

#### `list_workflow_nodes.py`
**Funzione:** Lista nodi workflow
- Inventario nodi disponibili
- Mapping nodi-processori
- Validazione configurazioni

### Inserimento Dati

#### `insert_crud_workflows.py`
**Funzione:** Insert workflow CRUD
- Template workflow per operazioni CRUD
- Workflow database standard
- Configurazioni predefinite

#### `insert_pdf_semantic_workflow.py`
**Funzione:** Insert workflow PDF semantico
- Workflow elaborazione PDF
- Estrazione semantica
- Integrazione vector store

### Update e Manutenzione

#### `update_workflow_processors.py`
**Funzione:** Update processori workflow
- Aggiornamento processori esistenti
- Migrazione a nuovi processori
- Batch update configurazioni

#### `update_workflow_triggers.py`
**Funzione:** Update trigger workflow
- Modifica trigger esistenti
- Riconfigurazione eventi
- Batch update trigger

### File SQL

#### `create_delete_update_workflows.sql`
- **Funzione:** Script SQL gestione workflow
- Template SQL per operazioni comuni
- Procedure stored workflow

## 🚀 Utilizzo

```bash
# Gestione workflow
python scripts/workflows/create_delete_update_workflows.py

# Lista completa sistema
python scripts/workflows/list_workflows_triggers.py

# Inserimento workflow predefiniti
python scripts/workflows/insert_crud_workflows.py
python scripts/workflows/insert_pdf_semantic_workflow.py

# Manutenzione
python scripts/workflows/update_workflow_processors.py
python scripts/workflows/update_workflow_triggers.py
```

## 📋 Workflow Templates

### CRUD Standard
```python
# Workflow per operazioni database standard
python scripts/workflows/insert_crud_workflows.py --type=standard
```

### PDF Semantico
```python
# Workflow elaborazione documenti PDF
python scripts/workflows/insert_pdf_semantic_workflow.py --mode=full
```

### Custom Workflow
```python
# Creazione workflow personalizzato
python scripts/workflows/create_delete_update_workflows.py --create --config=custom.json
```

## ⚡ Best Practices

- **Test prima:** Validare workflow in ambiente test
- **Backup workflow:** Esportare configurazioni esistenti
- **Incremental:** Modifiche graduali, non massive
- **Monitoring:** Verificare performance post-modifica

---
**Categoria:** Workflow Management  
**Target:** Amministratori sistema  
**Data organizzazione:** 16 Novembre 2025