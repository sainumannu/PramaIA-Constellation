# API dei Trigger per i Workflow

## Panoramica

L'API dei trigger permette di creare associazioni tra eventi (come l'upload di un file PDF) e workflow specifici nel sistema PramaIA. Quando si verifica un evento che corrisponde a un trigger configurato, il workflow associato viene eseguito automaticamente.

## Autenticazione

Tutte le richieste API richiedono un token JWT valido nell'header `Authorization`:

```
Authorization: Bearer <token>
```

Per ottenere un token, utilizzare l'endpoint di autenticazione:

```
POST /auth/token/local
Content-Type: application/x-www-form-urlencoded

username=<username>&password=<password>
```

## Endpoint

### Ottieni tutti i trigger

```
GET /api/workflows/triggers/
```

Restituisce un array di tutti i trigger configurati nel sistema.

#### Risposta

```json
[
  {
    "id": "2cf4add5-5fa5-485f-a8b1-549557b14955",
    "name": "Trigger Aggiunta PDF",
    "event_type": "pdf_file_added",
    "source": "pdf-monitor-event-source",
    "workflow_id": "wf_bd11290f923b",
    "target_node_id": "pdf_input_validator",
    "conditions": {},
    "active": 1,
    "created_at": "2025-10-08T20:27:37Z",
    "updated_at": "2025-11-19T10:00:00Z"
  },
  {
    "id": "11f4a284-9ac3-4fe7-bbe3-ca90d0c22f7a",
    "name": "Trigger Eliminazione PDF",
    "event_type": "pdf_file_deleted",
    "source": "pdf-monitor-event-source",
    "workflow_id": "wf_b32ead12131c",
    "target_node_id": "pdf_input_validator",
    "conditions": {},
    "active": 1,
    "created_at": "2025-10-08T20:27:37Z",
    "updated_at": "2025-11-19T10:00:00Z"
  }
]
```

### Ottieni un trigger specifico

```
GET /api/workflows/triggers/{trigger_id}
```

Restituisce i dettagli di un trigger specifico.

#### Risposta

```json
{
  "id": "2cf4add5-5fa5-485f-a8b1-549557b14955",
  "name": "Trigger Aggiunta PDF",
  "event_type": "pdf_file_added",
  "source": "pdf-monitor-event-source",
  "workflow_id": "wf_bd11290f923b",
  "target_node_id": "pdf_input_validator",
  "conditions": {},
  "active": 1,
  "created_at": "2025-10-08T20:27:37Z",
  "updated_at": "2025-11-19T10:00:00Z"
}
```

### Crea un nuovo trigger

```
POST /api/workflows/triggers/
Content-Type: application/json
```

#### Corpo della richiesta

```json
{
  "name": "Trigger Aggiunta PDF",
  "event_type": "pdf_file_added",
  "source": "pdf-monitor-event-source",
  "workflow_id": "wf_bd11290f923b",
  "target_node_id": "pdf_input_validator",
  "conditions": {},
  "active": true
}
```

#### Risposta

```json
{
  "id": "2cf4add5-c7e5-42a2-9c1e-8b0a9f5d3e2c",
  "name": "Trigger Aggiunta PDF",
  "event_type": "pdf_file_added",
  "source": "pdf-monitor-event-source",
  "workflow_id": "wf_bd11290f923b",
  "target_node_id": "pdf_input_validator",
  "conditions": {},
  "active": 1,
  "created_at": "2025-11-19T10:27:37Z",
  "updated_at": "2025-11-19T10:30:00Z"
}
```

### Aggiorna un trigger esistente

```
PUT /api/workflows/triggers/{trigger_id}
Content-Type: application/json
```

#### Corpo della richiesta

```json
{
  "name": "Trigger Eliminazione PDF",
  "event_type": "pdf_file_deleted",
  "source": "pdf-monitor-event-source",
  "workflow_id": "wf_b32ead12131c",
  "target_node_id": "pdf_input_validator",
  "conditions": {},
  "active": 1
}
```

#### Risposta

```json
{
  "id": "2cf4add5-5fa5-485f-a8b1-549557b14955",
  "name": "Trigger Aggiunta PDF",
  "event_type": "pdf_file_added",
  "source": "pdf-monitor-event-source",
  "workflow_id": "wf_bd11290f923b",
  "target_node_id": "pdf_input_validator",
  "conditions": {},
  "active": 1,
  "created_at": "2025-10-08T20:27:37Z",
  "updated_at": "2025-11-19T10:00:00Z"
}
```

### Attiva/Disattiva un trigger

```
PATCH /api/workflows/triggers/{trigger_id}/toggle
Content-Type: application/json
```

#### Corpo della richiesta

```json
{
  "active": false
}
```

#### Risposta

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Upload PDF Aggiornato",
  "active": false,
  "updated_at": "2025-08-03T15:40:00Z"
}
```

### Elimina un trigger

```
DELETE /api/workflows/triggers/{trigger_id}
```

#### Risposta

```json
{
  "message": "Trigger eliminato con successo"
}
```

## Tipi di eventi supportati

| Tipo di evento | Descrizione |
|----------------|-------------|
| pdf_file_added | Quando un PDF viene rilevato come nuovo nel monitoraggio |
| pdf_file_deleted | Quando un PDF viene rimosso dal sistema |
| pdf_file_modified | Quando un PDF viene modificato o aggiornato |

## Sorgenti supportate

| Sorgente | Descrizione |
|----------|-------------|
| pdf-monitor-event-source | Sistema di monitoraggio PDF integrato |

## Condizioni

Le condizioni sono specificate come un oggetto JSON e permettono di filtrare ulteriormente gli eventi che attivano un workflow. I campi disponibili dipendono dal tipo di evento.

### Esempi di condizioni

**Per pdf_upload:**
```json
{
  "file_type": "pdf",
  "size_gt": 1024,
  "name_contains": "fattura"
}
```

**Per schedule:**
```json
{
  "cron": "0 9 * * 1-5",
  "timezone": "Europe/Rome"
}
```

## Codici di errore

| Codice | Descrizione |
|--------|-------------|
| 400 | Richiesta non valida |
| 401 | Non autorizzato (token mancante o non valido) |
| 403 | Accesso negato (permessi insufficienti) |
| 404 | Risorsa non trovata |
| 500 | Errore interno del server |
