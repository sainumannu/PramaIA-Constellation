# Sistema di Gestione Eventi e Trigger

## Introduzione

Questo sistema implementa un framework generico per la gestione di eventi e trigger in PramaIA. Consente di configurare workflow che vengono eseguiti automaticamente in risposta a eventi specifici.

## Concetti principali

- **Evento**: Qualsiasi occorrenza nel sistema che può richiedere una risposta. Esempi: caricamento di un PDF, chiamata API, timer.
- **Trigger**: Una regola che associa un tipo di evento a un workflow specifico, con condizioni opzionali.
- **Workflow**: Una sequenza configurata di operazioni da eseguire quando un trigger viene attivato.

## Architettura

Il sistema si basa su un'architettura a eventi che separa:

1. **Produttori di eventi**: Componenti che generano eventi (PDF Monitor, API, Scheduler, ecc.)
2. **Gestori di eventi**: Il sistema centrale che riceve gli eventi e trova i trigger corrispondenti
3. **Workflow**: Le sequenze di operazioni da eseguire in risposta agli eventi

## Flusso di un evento

```
Produttore di Eventi → Endpoint /api/events/process → Valutazione Trigger → Esecuzione Workflow
```

## Componenti del sistema

### Router degli eventi (`event_trigger_system.py`)

Router principale che fornisce endpoint per:
- Processare eventi generici
- Retrocompatibilità con i client esistenti (es. endpoint PDF)
- Gestione amministrativa dei trigger

### Servizio Trigger (`trigger_service.py`)

Implementa la logica per:
- Recuperare trigger configurati dal database
- Valutare le condizioni dei trigger
- Elaborare gli eventi e attivare i workflow appropriati

## Configurazione di un Trigger

I trigger possono essere configurati con:

- **Tipo di evento**: Quale tipo di evento deve attivare il trigger
- **Sorgente**: Da quale componente deve provenire l'evento
- **Condizioni**: Regole opzionali per filtrare gli eventi (es. pattern del nome file)
- **Workflow Target**: Quale workflow eseguire quando il trigger è attivato

## Uso

### Inviare un evento

```python
# Esempio di invio evento via API
import requests

response = requests.post(
    "http://localhost:8000/api/events/process",
    json={
        "event_type": "file_upload",
        "data": {
            "filename": "documento.pdf",
            "content_type": "application/pdf",
            "size": 12345
        },
        "metadata": {
            "source": "pdf-monitor",
            "timestamp": "2025-08-15T12:34:56Z",
            "additional_data": {
                "folder": "documenti_in_arrivo"
            }
        }
    }
)
```

### Creare un trigger (via API futura)

```python
# Esempio di creazione trigger via API
import requests

response = requests.post(
    "http://localhost:8000/api/workflows/triggers",
    json={
        "name": "Elaborazione PDF in arrivo",
        "event_type": "file_upload",
        "source": "pdf-monitor",
        "workflow_id": "workflow-pdf-processing-123",
        "conditions": {
            "filename_pattern": ".*\\.pdf$",
            "metadata_contains": {
                "folder": "documenti_in_arrivo"
            }
        },
        "active": true
    }
)
```

## Note di sviluppo

Questo sistema è attualmente in fase di sviluppo. Implementazioni future includeranno:

- UI di amministrazione per configurare i trigger
- Supporto per trigger con condizioni avanzate
- Sistema di logging e monitoraggio degli eventi
- Supporto per eventi asincroni e code di eventi
