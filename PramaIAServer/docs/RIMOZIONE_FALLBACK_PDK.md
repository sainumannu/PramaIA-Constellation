# Rimozione dei Meccanismi di Fallback PDK

## Problema

Il sistema PDF Monitor utilizzava un meccanismo di fallback che, in caso di indisponibilità del PDK (Platform Development Kit), tentava di inserire direttamente i documenti nel vectorstore. Questo comportamento presentava diversi problemi:

1. **Elaborazione incompleta**: Il fallback inseriva i documenti senza la corretta elaborazione (suddivisione in chunk, estrazione strutturata, etc.)
2. **Feedback ingannevole**: Il sistema sembrava funzionare anche quando in realtà non lo stava facendo correttamente
3. **Diagnostica difficile**: Gli errori venivano mascherati rendendo difficile capire che il PDK non era disponibile
4. **Inconsistenza dei dati**: I documenti inseriti tramite fallback avevano una struttura diversa

## Soluzione Implementata

Abbiamo rimosso completamente i meccanismi di fallback dal sistema e implementato un approccio più robusto:

1. **Errori espliciti**: Quando il PDK non è disponibile, viene generato un errore HTTP 503 (Service Unavailable) chiaro e specifico
2. **Logging avanzato**: Gli errori vengono registrati in modo dettagliato nei log e nel database degli eventi
3. **Pulizia dei file temporanei**: I file caricati vengono rimossi in caso di errore per evitare accumulo di dati
4. **Tracciamento degli errori**: Gli errori vengono registrati nel sistema di monitoraggio degli eventi per visibilità

## Endpoint Modificati

Sono stati modificati i seguenti endpoint nel file `pdf_monitor_router.py`:

1. `/api/pdf-monitor/upload/` - Rimozione del fallback per l'upload dei PDF
2. `/api/pdf-monitor/query/` - Rimozione del fallback per le query semantiche

## Benefici

1. **Trasparenza**: Gli errori sono ora visibili e chiari, facilitando la diagnosi
2. **Consistenza dei dati**: Tutti i documenti nel vectorstore sono elaborati correttamente dal PDK
3. **Diagnostica semplificata**: È immediatamente evidente quando il PDK non è disponibile
4. **Visibilità completa**: Gli errori vengono registrati nel sistema di monitoraggio eventi

## Comportamento Atteso

Quando il PDK non è disponibile o il workflow specificato non è trovato:

1. L'API restituirà un errore HTTP 503
2. Nella UI comparirà un messaggio di errore chiaro
3. L'errore sarà visibile nei log del server
4. Un evento di errore sarà registrato nella tabella `pdf_monitor_events`

## Come Verificare il Funzionamento

1. Avviare il sistema senza avviare il PDK (o con un PDK mal configurato)
2. Tentare di caricare un documento o eseguire una query
3. Verificare che venga mostrato un errore esplicito
4. Controllare che l'evento di errore sia stato registrato nella tabella `pdf_monitor_events`
