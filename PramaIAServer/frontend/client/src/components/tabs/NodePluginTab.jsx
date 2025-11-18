import React, { useEffect, useState } from 'react';
import {
  Text,
  Box,
  Flex,
  Divider,
  List,
  ListItem,
  Spinner,
  Alert,
  AlertIcon,
  Button,
  Badge,
  Code,
  useToast
} from "@chakra-ui/react";
import { PDK_PLUGINS_URL, PDK_EVENT_SOURCES_URL, PDK_BACKEND_PLUGINS_URL, PDK_BACKEND_EVENT_SOURCES_URL } from '../../config/appConfig';

// Cache globale per i dettagli dei plugin (persiste tra le sessioni)
const PLUGIN_CACHE_KEY = 'pramaIA_plugin_cache';

/**
 * Componente per il tab Plugin del NodeDetailsModal
 */
const NodePluginTab = ({ 
  plugin, 
  isEventSource, 
  pluginDetails, 
  setPluginDetails,
  loading, 
  setLoading, 
  error, 
  setError,
  activeTab
}) => {
  const [cacheStatus, setCacheStatus] = useState('');
  const [usedCache, setUsedCache] = useState(false);
  const toast = useToast();
  
  // Salva dati nella cache
  const saveToCache = (pluginId, data) => {
    try {
      const cache = JSON.parse(localStorage.getItem(PLUGIN_CACHE_KEY) || '{}');
      cache[pluginId] = {
        data,
        timestamp: Date.now()
      };
      localStorage.setItem(PLUGIN_CACHE_KEY, JSON.stringify(cache));
      console.log(`Plugin ${pluginId} salvato in cache`);
    } catch (err) {
      console.error('Errore nel salvataggio nella cache:', err);
    }
  };
  
  // Recupera dati dalla cache
  const getFromCache = (pluginId) => {
    try {
      const cache = JSON.parse(localStorage.getItem(PLUGIN_CACHE_KEY) || '{}');
      const entry = cache[pluginId];
      
      if (!entry) return null;
      
      // Calcola l'età della cache in minuti
      const ageInMinutes = (Date.now() - entry.timestamp) / (1000 * 60);
      setCacheStatus(`Dati in cache da ${Math.round(ageInMinutes)} minuti`);
      
      // Invalida la cache dopo 30 minuti
      if (ageInMinutes > 30) {
        console.log(`Cache per ${pluginId} scaduta (${Math.round(ageInMinutes)} minuti)`);
        return null;
      }
      
      console.log(`Usando dati in cache per ${pluginId} (${Math.round(ageInMinutes)} minuti)`);
      return entry.data;
    } catch (err) {
      console.error('Errore nel recupero dalla cache:', err);
      return null;
    }
  };
  
  // Crea un fallback basato sui dati disponibili del plugin
  const createFallbackDetails = () => {
    if (!plugin) return null;
    
    return {
      id: plugin.id,
      name: plugin.name || 'Plugin sconosciuto',
      description: plugin.description || 'Nessuna descrizione disponibile',
      version: plugin.version || '0.0.0',
      isFallback: true,
      nodes: plugin.nodes || [],
      eventTypes: plugin.eventTypes || []
    };
  };
  
  // Carica i dettagli del plugin manualmente quando si seleziona la scheda
  const loadPluginDetails = async (forceRefresh = false) => {
    if (!plugin || !plugin.id) return;
    
    setLoading(true);
    setError(null);
    setUsedCache(false);
    
    try {
      // Verifica se ci sono dati in cache (a meno che non sia forzato il refresh)
      if (!forceRefresh) {
        const cachedData = getFromCache(plugin.id);
        if (cachedData) {
          console.log('Usando dati dalla cache:', cachedData);
          setPluginDetails(cachedData);
          setUsedCache(true);
          setLoading(false);
          return;
        }
      }
      
      // Prova diverse possibili URL fino a trovarne una che funziona
      const possibleUrls = [
        `${PDK_PLUGINS_URL}/${plugin.id}`,
        `${PDK_EVENT_SOURCES_URL}/${plugin.id}`,
        `${PDK_BACKEND_PLUGINS_URL}/${plugin.id}`,
        `${PDK_BACKEND_EVENT_SOURCES_URL}/${plugin.id}`
      ];
      
      let response = null;
      let successUrl = null;
      
      for (const url of possibleUrls) {
        try {
          console.log(`Tentativo di caricamento da: ${url}`);
          const res = await fetch(url, { 
            headers: { 'Cache-Control': 'no-cache' },
            timeout: 2000  // Timeout di 2 secondi per ogni richiesta
          });
          if (res.ok) {
            response = await res.json();
            successUrl = url;
            break;
          }
        } catch (err) {
          console.log(`Errore caricamento da ${url}:`, err);
          // Continua con il prossimo URL
        }
      }
      
      if (response) {
        console.log(`Dati caricati con successo da: ${successUrl}`, response);
        setPluginDetails(response);
        saveToCache(plugin.id, response);
      } else {
        const fallbackDetails = createFallbackDetails();
        if (fallbackDetails) {
          console.log('Usando dettagli di fallback:', fallbackDetails);
          setPluginDetails(fallbackDetails);
          setError('Non è stato possibile caricare i dettagli completi del plugin. Vengono mostrate informazioni limitate.');
          toast({
            title: "Informazioni limitate",
            description: "Impossibile connettersi al server PDK. Vengono mostrate informazioni limitate.",
            status: "warning",
            duration: 5000,
            isClosable: true,
          });
        } else {
          setError('Non è stato possibile caricare i dettagli del plugin da nessuno degli URL provati.');
        }
      }
    } catch (err) {
      console.error('Errore nel caricamento dei dettagli del plugin:', err);
      setError(`Errore: ${err.message}`);
      
      // Utilizza il fallback anche in caso di errore
      const fallbackDetails = createFallbackDetails();
      if (fallbackDetails) {
        setPluginDetails(fallbackDetails);
      }
    } finally {
      setLoading(false);
    }
  };
  
  // Carica i dettagli del plugin quando il tab diventa attivo
  useEffect(() => {
    if (activeTab === 3 && plugin && !pluginDetails && !loading) {
      loadPluginDetails();
    }
  }, [activeTab, plugin, pluginDetails, loading]);

  return (
    <>
      <Text fontWeight="semibold" mb="3">Informazioni sul Plugin</Text>
      
      {loading ? (
        <Flex justify="center" p={5}>
          <Spinner />
        </Flex>
      ) : error ? (
        <Box>
          <Alert status="warning" mb={4}>
            <AlertIcon />
            {error}
            <Button
              ml={2}
              size="sm"
              onClick={() => loadPluginDetails(true)}
              mt={2}
            >
              Riprova
            </Button>
          </Alert>
          
          {/* Mostra comunque i dettagli di base se disponibili */}
          {pluginDetails && (
            <Box mt={4}>
              <Text fontSize="xl" fontWeight="bold" mb={2}>
                {pluginDetails.name} 
                {pluginDetails.isFallback && (
                  <Badge ml={2} colorScheme="yellow">Informazioni limitate</Badge>
                )}
              </Text>
              
              <Text mb={4}>
                {pluginDetails.description}
              </Text>
              
              <Text fontWeight="medium">
                Versione: {pluginDetails.version}
              </Text>
              
              <Text fontSize="xs" color="gray.500" mt={2}>
                ID: <Code>{plugin.id}</Code>
              </Text>
            </Box>
          )}
        </Box>
      ) : pluginDetails ? (
        <Box>
          <Flex justifyContent="space-between" alignItems="center" mb={2}>
            <Text fontSize="xl" fontWeight="bold">
              {pluginDetails.name}
              {pluginDetails.isFallback && (
                <Badge ml={2} colorScheme="yellow">Informazioni limitate</Badge>
              )}
            </Text>
            
            {usedCache && (
              <Flex alignItems="center">
                <Badge colorScheme="blue" variant="outline" fontSize="xs">
                  {cacheStatus}
                </Badge>
                <Button 
                  size="xs" 
                  ml={2} 
                  onClick={() => loadPluginDetails(true)}
                  variant="ghost"
                >
                  Aggiorna
                </Button>
              </Flex>
            )}
          </Flex>
          
          <Text mb={4}>
            {pluginDetails.description}
          </Text>
          
          <Text fontWeight="medium">
            Versione: {pluginDetails.version}
          </Text>
          
          <Text fontSize="xs" color="gray.500" mt={2}>
            ID: <Code>{plugin.id}</Code>
          </Text>
          
          <Divider my={4} />
          
          {/* Visualizza altre informazioni specifiche in base al tipo di plugin */}
          {isEventSource ? (
            <Box mt={4}>
              <Text fontSize="lg" fontWeight="semibold">Tipi di Eventi</Text>
              {pluginDetails.eventTypes && pluginDetails.eventTypes.length > 0 ? (
                <List spacing={2} mt={2}>
                  {pluginDetails.eventTypes.map(eventType => (
                    <ListItem key={eventType.id || eventType.name || Math.random()}>
                      <Text fontWeight="medium">
                        {eventType.name}
                      </Text>
                      <Text fontSize="sm">
                        {eventType.description}
                      </Text>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Text>Nessun tipo di evento definito.</Text>
              )}
            </Box>
          ) : (
            <Box mt={4}>
              <Text fontSize="lg" fontWeight="semibold">Nodi</Text>
              {pluginDetails.nodes && pluginDetails.nodes.length > 0 ? (
                <List spacing={2} mt={2}>
                  {pluginDetails.nodes.map(nodeItem => (
                    <ListItem key={nodeItem.id || nodeItem.name || Math.random()}>
                      <Text fontWeight="medium">
                        {nodeItem.name}
                      </Text>
                      <Text fontSize="sm">
                        {nodeItem.description}
                      </Text>
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Text>Nessun nodo definito.</Text>
              )}
            </Box>
          )}
        </Box>
      ) : (
        <Box textAlign="center" p={5}>
          <Text mb={3}>Nessun dato disponibile per questo plugin.</Text>
          <Button
            colorScheme="blue"
            onClick={() => loadPluginDetails(true)}
          >
            Carica Dettagli Plugin
          </Button>
        </Box>
      )}
    </>
  );
};

export default NodePluginTab;
