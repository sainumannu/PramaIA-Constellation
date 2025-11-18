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
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Upload PDF",
    "event_type": "pdf_upload",
    "source": "pdf-monitor",
    "workflow_id": "workflow123",
    "conditions": {
      "file_type": "pdf",
      "size_gt": 1024
    },
    "active": true,
    "created_at": "2025-08-01T12:00:00Z",
    "updated_at": "2025-08-01T12:00:00Z"
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
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Upload PDF",
  "event_type": "pdf_upload",
  "source": "pdf-monitor",
  "workflow_id": "workflow123",
  "conditions": {
    "file_type": "pdf",
    "size_gt": 1024
  },
  "active": true,
  "created_at": "2025-08-01T12:00:00Z",
  "updated_at": "2025-08-01T12:00:00Z"
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
  "name": "Upload PDF",
  "event_type": "pdf_upload",
  "source": "pdf-monitor",
  "workflow_id": "workflow123",
  "conditions": {
    "file_type": "pdf",
    "size_gt": 1024
  },
  "active": true
}
```

#### Risposta

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Upload PDF",
  "event_type": "pdf_upload",
  "source": "pdf-monitor",
  "workflow_id": "workflow123",
  "conditions": {
    "file_type": "pdf",
    "size_gt": 1024
  },
  "active": true,
  "created_at": "2025-08-03T15:30:00Z",
  "updated_at": "2025-08-03T15:30:00Z"
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
  "name": "Upload PDF Aggiornato",
  "event_type": "pdf_upload",
  "source": "pdf-monitor",
  "workflow_id": "workflow456",
  "conditions": {
    "file_type": "pdf",
    "size_gt": 2048
  },
  "active": true
}
```

#### Risposta

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Upload PDF Aggiornato",
  "event_type": "pdf_upload",
  "source": "pdf-monitor",
  "workflow_id": "workflow456",
  "conditions": {
    "file_type": "pdf",
    "size_gt": 2048
  },
  "active": true,
  "created_at": "2025-08-01T12:00:00Z",
  "updated_at": "2025-08-03T15:35:00Z"
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
| pdf_upload | Quando un PDF viene caricato nel sistema |
| file_created | Quando un file viene creato nel sistema |
| schedule | Trigger basato su una pianificazione temporale |
| api_call | Quando viene effettuata una specifica chiamata API |
| document_processed | Quando un documento è stato elaborato |

## Sorgenti supportate

| Sorgente | Descrizione |
|----------|-------------|
| pdf-monitor | Plugin di monitoraggio PDF |
| scheduler | Sistema di pianificazione |
| api | Endpoint API esterni |
| ui | Azioni dell'interfaccia utente |
| system | Eventi di sistema interni |

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
