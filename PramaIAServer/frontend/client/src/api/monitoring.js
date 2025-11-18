import api from '../services/api';

// Ottieni la lista dei client document monitor registrati
export const fetchDocumentMonitorClients = async () => {
  const response = await api.get('/api/document-monitor/clients');
  // Per ogni client, aggiorna status/folders reali interrogando il plugin
  const plugins = response.data.plugins || [];
  
  // Aggiungiamo un timeout di 2.5 secondi per le richieste di stato 
  // (un po' più lungo per dare tempo ai servizi di rispondere all'avvio)
  const fetchOptions = {
    signal: AbortSignal.timeout(2500) // Timeout di 2.5 secondi per ogni richiesta
  };
  
  // Funzione helper per tentare di connettersi a un client con retry
  const tryConnectClient = async (client, retryCount = 0) => {
    try {
      const statusResp = await fetch(`${client.endpoint}/monitor/status`, fetchOptions);
      if (!statusResp.ok) throw new Error('status fetch failed');
      const status = await statusResp.json();
      console.log(`[API] Client ${client.name} connesso con successo, stato: ${status.is_running ? 'online' : 'paused'}`);
      return {
        ...client,
        status: status.is_running ? 'online' : 'paused',
        folders: status.monitoring_folders || [],
        autostart_folders: status.autostart_folders || [],
        canStart: !status.is_running,
        canPause: status.is_running,
        canStop: status.is_running,
      };
    } catch (e) {
      console.log(`[API] Client ${client.name} non raggiungibile${retryCount > 0 ? ` (tentativo ${retryCount})` : ''}: ${e.message}`);
      
      // Per i primi tentativi all'avvio, facciamo un retry immediato
      if (retryCount < 1) {
        console.log(`[API] Riprovo immediatamente per ${client.name}...`);
        // Breve attesa per dare tempo al servizio di inizializzarsi
        await new Promise(resolve => setTimeout(resolve, 500));
        return tryConnectClient(client, retryCount + 1);
      }
      
      return {
        ...client,
        status: 'offline',
        folders: [],
        autostart_folders: [],
        canStart: false,
        canPause: false,
        canStop: false,
      };
    }
  };
  
  // Esegui il tentativo di connessione per tutti i client in parallelo
  const enriched = await Promise.all(plugins.map(client => tryConnectClient(client)));
  return enriched;
};

// Azioni di controllo reali
export const startDocumentMonitorClient = async (client) => {
  // Avvia monitoraggio su tutte le cartelle già configurate
  return fetch(`${client.endpoint}/monitor/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ folder_paths: client.folders || [] })
  }).then(r => r.json());
};
export const pauseDocumentMonitorClient = async (client) => {
  // Non implementato: il plugin non ha PAUSE, solo STOP
  return stopDocumentMonitorClient(client);
};
export const stopDocumentMonitorClient = async (client) => {
  return fetch(`${client.endpoint}/monitor/stop`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  }).then(r => r.json());
};

export const addFolderToClient = async (client, folder) => {
  return fetch(`${client.endpoint}/monitor/configure`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ folder_path: folder })
  }).then(r => r.json());
};
export const removeFolderFromClient = async (client, folder) => {
  // Chiama l'endpoint reale del plugin
  return fetch(`${client.endpoint}/monitor/remove_folder`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ folder_path: folder })
  }).then(r => r.json());
};

export const toggleFolderAutostart = async (client, folder, enable) => {
  // Abilita o disabilita l'autostart per una cartella
  return fetch(`${client.endpoint}/monitor/autostart`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ folder_path: folder, autostart: enable })
  }).then(r => r.json());
};

export const fetchRecentEvents = async (client, limit = 50, includeHistory = false) => {
  // Recupera gli eventi recenti dal plugin
  try {
    const response = await fetch(`${client.endpoint}/monitor/events/recent?limit=${limit}&include_history=${includeHistory}`);
    const data = await response.json();
    const events = data.events || [];
    
    // Trova e correggi gli eventi completati che dovrebbero avere un document_id
    // cercando negli eventi precedenti dello stesso file
    const fileEventMap = {};
    
    // Prima passata per raggruppare gli eventi per nome file
    events.forEach(event => {
      if (!fileEventMap[event.file_name]) {
        fileEventMap[event.file_name] = [];
      }
      fileEventMap[event.file_name].push(event);
    });
    
    // Seconda passata per trovare document_id mancanti
    events.forEach(event => {
      // Gestione normale dei document_id mancanti
      if (!event.document_id && event.status === 'completed') {
        // Cerca un document_id in altri eventi dello stesso file
        const fileEvents = fileEventMap[event.file_name] || [];
        const eventsWithId = fileEvents.filter(e => e.document_id && e.id !== event.id);
        
        if (eventsWithId.length > 0) {
          // Ordina per più recenti e prendi il primo document_id
          eventsWithId.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
          event.document_id = eventsWithId[0].document_id;
          console.log(`Aggiunto document_id mancante a evento ${event.id} per file ${event.file_name}`);
        }
      }
      
      // Se c'è un documento duplicato, assicurati che abbia lo stato corretto
      if (event.status === 'duplicate' && !event.document_id) {
        // Cerca tra gli altri eventi se ce n'è uno con lo stesso document_id
        const fileEvents = fileEventMap[event.file_name] || [];
        const eventsWithId = fileEvents.filter(e => e.document_id && e.id !== event.id);
        
        if (eventsWithId.length > 0) {
          // Usa il document_id dell'evento più recente
          eventsWithId.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
          event.document_id = eventsWithId[0].document_id;
          console.log(`Evento duplicato ${event.id}: associato document_id ${event.document_id} dal file originale`);
        }
      }
    });
    
    return events;
  } catch (error) {
    console.error("Errore durante il recupero degli eventi recenti:", error);
    return [];
  }
};

export const deleteEvent = async (client, eventId) => {
  // Elimina un evento dal plugin
  return fetch(`${client.endpoint}/monitor/events/${eventId}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' }
  }).then(r => r.json());
};

  // Elimina tutti gli eventi recenti per un client
  export const clearAllEvents = async (client) => {
    return fetch(`${client.endpoint}/monitor/events/clear`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' }
    }).then(r => r.json());
  };
export const retryEvent = async (client, eventId) => {
  // Riprova l'elaborazione di un evento in errore
  return fetch(`${client.endpoint}/monitor/events/${eventId}/retry`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  }).then(r => r.json());
};
