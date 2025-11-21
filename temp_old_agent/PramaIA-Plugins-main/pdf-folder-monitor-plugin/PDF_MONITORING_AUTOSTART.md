# PDF Folder Monitoring - Guida all'uso

## Introduzione

Il plugin PDF Folder Monitor consente di monitorare automaticamente le cartelle del filesystem per rilevare nuovi file PDF. Quando viene rilevato un nuovo file PDF, il plugin lo invia automaticamente al backend di PramaIA per l'elaborazione e l'indicizzazione semantica.

## Caratteristiche principali

- Monitoraggio di cartelle multiple in parallelo
- Rilevamento automatico di nuovi file PDF
- Invio automatico dei file al backend
- **Autostart di cartelle selezionate all'avvio del plugin**
- Configurazione persistente delle cartelle monitorate
- Dashboard di controllo integrata in PramaIA

## Funzionalità di Autostart

La funzionalità di autostart consente di avviare automaticamente il monitoraggio di cartelle selezionate all'avvio del plugin, senza la necessità di un'attivazione manuale da parte dell'utente.

### Come funziona

1. All'avvio del plugin, viene caricata la configurazione dal file `monitor_config.json`
2. Dopo un breve ritardo (5 secondi per assicurare l'inizializzazione corretta), il sistema avvia automaticamente il monitoraggio delle cartelle contrassegnate con autostart
3. Le cartelle non contrassegnate con autostart devono essere avviate manualmente dall'interfaccia di PramaIA

### Configurazione

È possibile configurare l'autostart attraverso:

1. **Interfaccia web PramaIA**: Nella dashboard di monitoraggio PDF, ogni cartella ha un interruttore "Autostart" che può essere attivato o disattivato.
2. **Configurazione manuale**: Modificando il file `monitor_config.json` nella directory del plugin.

Esempio di configurazione:

```json
{
  "folders": [
    "C:/Cartella1",
    "C:/Cartella2",
    "C:/Cartella3"
  ],
  "autostart_folders": [
    "C:/Cartella1",
    "C:/Cartella3"
  ]
}
```

In questo esempio, le cartelle "Cartella1" e "Cartella3" verranno monitorate automaticamente all'avvio del plugin.

## API e integrazione

Il plugin espone le seguenti API per la gestione dell'autostart:

- `GET /monitor/status` - Restituisce lo stato attuale, inclusa la lista delle cartelle con autostart abilitato
- `POST /monitor/autostart` - Imposta o rimuove l'autostart per una cartella
- `POST /monitor/start` - Avvia il monitoraggio di cartelle specifiche
- `POST /monitor/stop` - Ferma tutto il monitoraggio attivo

### Esempio di utilizzo API

```javascript
// Abilitare l'autostart per una cartella
fetch('http://localhost:8001/monitor/autostart', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    folder_path: "C:/Cartella1", 
    autostart: true 
  })
});

// Disabilitare l'autostart
fetch('http://localhost:8001/monitor/autostart', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    folder_path: "C:/Cartella1", 
    autostart: false 
  })
});
```

## Risoluzione problemi

Se le cartelle con autostart non vengono avviate automaticamente:

1. Verificare che il file `monitor_config.json` sia correttamente formattato
2. Controllare che le cartelle esistano e siano accessibili
3. Verificare i log all'avvio del plugin per messaggi di errore
4. Riavviare il plugin per forzare il caricamento della configurazione
