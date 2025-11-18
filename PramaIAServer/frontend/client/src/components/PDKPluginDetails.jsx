import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  CircularProgress, 
  Alert, 
  Typography, 
  Box 
} from '@mui/material';
import { 
  PDK_PLUGINS_URL, 
  PDK_EVENT_SOURCES_URL,
  PDK_BACKEND_PLUGINS_URL,
  PDK_BACKEND_EVENT_SOURCES_URL
} from '../config/appConfig';

/**
 * Custom hook per caricare i dati di un plugin PDK
 * @param {string} pluginId - ID del plugin
 * @param {boolean} isEventSource - Se il plugin è un event source
 * @returns {Object} - Stato di caricamento, errore e dati del plugin
 */
export const usePDKPluginDetails = (pluginId, isEventSource = false) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pluginData, setPluginData] = useState(null);
  
  useEffect(() => {
    const fetchPluginDetails = async () => {
      if (!pluginId) {
        setLoading(false);
        return;
      }
      
      setLoading(true);
      setError(null);
      
      
      try {
        // Determina gli URL da provare in base al tipo di plugin
        const urls = isEventSource 
          ? [`${PDK_EVENT_SOURCES_URL}/${pluginId}`, `${PDK_BACKEND_EVENT_SOURCES_URL}/${pluginId}`]
          : [`${PDK_PLUGINS_URL}/${pluginId}`, `${PDK_BACKEND_PLUGINS_URL}/${pluginId}`];
        
        let success = false;
        
        for (const url of urls) {
          try {
            console.log(`Fetching plugin details from: ${url}`);
            const response = await axios.get(url);
            
            if (response.status === 200) {
              setPluginData(response.data);
              success = true;
              console.log(`Successo nel caricamento da: ${url}`);
              break;
            }
          } catch (innerErr) {
            console.log(`Errore nel tentativo di caricamento da ${url}:`, innerErr);
            // Continua con il prossimo URL
          }
        }
        
        if (!success) {
          setError('Impossibile caricare i dettagli del plugin da nessun endpoint disponibile.');
        }
      } catch (err) {
        console.error('Errore nel caricamento dei dettagli del plugin:', err);
        
        // Gestione degli errori migliorata
        if (err.response) {
          // Errore di risposta dal server
          setError(`Errore ${err.response.status}: ${err.response.data.message || err.response.statusText}`);
        } else if (err.request) {
          // Nessuna risposta ricevuta
          setError('Nessuna risposta dal server. Verificare che il server PDK sia in esecuzione.');
        } else {
          // Errore nella configurazione della richiesta
          setError(`Errore nella richiesta: ${err.message}`);
        }
      } finally {
        setLoading(false);
      }
    };
    
    fetchPluginDetails();
  }, [pluginId, isEventSource]);
  
  return { loading, error, pluginData };
};

/**
 * Componente per visualizzare i dettagli di un plugin PDK
 */
const PDKPluginDetails = ({ pluginId, isEventSource = false }) => {
  const { loading, error, pluginData } = usePDKPluginDetails(pluginId, isEventSource);
  
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }
  
  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
        <Typography variant="body2" sx={{ mt: 1 }}>
          Suggerimenti:
          <ul>
            <li>Verificare che il server PDK sia in esecuzione sulla porta corretta</li>
            <li>Controllare che l'ID del plugin sia corretto</li>
            <li>Verificare le impostazioni CORS nel server PDK</li>
          </ul>
        </Typography>
      </Alert>
    );
  }
  
  if (!pluginData) {
    return (
      <Alert severity="info">
        Nessun dato disponibile per questo plugin.
      </Alert>
    );
  }
  
  // Render dei dettagli del plugin
  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        {pluginData.name}
      </Typography>
      
      <Typography variant="body1" paragraph>
        {pluginData.description}
      </Typography>
      
      <Typography variant="subtitle2">
        Versione: {pluginData.version}
      </Typography>
      
      {/* Visualizza altre informazioni specifiche in base al tipo di plugin */}
      {isEventSource ? (
        <Box sx={{ mt: 2 }}>
          <Typography variant="h6">Tipi di Eventi</Typography>
          {pluginData.eventTypes && pluginData.eventTypes.length > 0 ? (
            <ul>
              {pluginData.eventTypes.map(eventType => (
                <li key={eventType.id}>
                  <Typography>
                    <strong>{eventType.name}</strong>: {eventType.description}
                  </Typography>
                </li>
              ))}
            </ul>
          ) : (
            <Typography>Nessun tipo di evento definito.</Typography>
          )}
        </Box>
      ) : (
        <Box sx={{ mt: 2 }}>
          <Typography variant="h6">Nodi</Typography>
          {pluginData.nodes && pluginData.nodes.length > 0 ? (
            <ul>
              {pluginData.nodes.map(node => (
                <li key={node.id}>
                  <Typography>
                    <strong>{node.name}</strong>: {node.description}
                  </Typography>
                </li>
              ))}
            </ul>
          ) : (
            <Typography>Nessun nodo definito.</Typography>
          )}
        </Box>
      )}
    </Box>
  );
};

export default PDKPluginDetails;
