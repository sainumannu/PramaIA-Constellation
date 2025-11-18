import React, { useState } from 'react';
import { PDK_SERVER_BASE_URL, API_BASE_URL } from '../config/appConfig';
import { 
  Box, 
  Button, 
  Text, 
  Heading,
  Alert, 
  AlertIcon, 
  AlertTitle,
  Spinner,
  Stack,
  Code,
  Divider
} from '@chakra-ui/react';

/**
 * Componente per il debugging delle configurazioni PDK
 * Questo componente aiuta a identificare e risolvere problemi di configurazione con il server PDK
 */
const PDKConfigDebugger = () => {
  const [debugInfo, setDebugInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Funzione per testare la connessione al server PDK
  const testPDKConnection = async () => {
    setLoading(true);
    setError(null);
    setDebugInfo(null);
    
    try {
      // Ottieni le configurazioni da window per vedere esattamente cosa viene usato a runtime
      const configs = {
        BACKEND_BASE_URL: window.BACKEND_BASE_URL || 'Non disponibile',
        PDK_SERVER_BASE_URL: window.PDK_SERVER_BASE_URL || 'Non disponibile',
        PDK_API_BASE_URL: window.PDK_API_BASE_URL || 'Non disponibile',
        PDK_PLUGINS_URL: window.PDK_PLUGINS_URL || 'Non disponibile',
        PDK_EVENT_SOURCES_URL: window.PDK_EVENT_SOURCES_URL || 'Non disponibile',
        // Configura gli URL alternativi che potrebbero essere usati
        ALTERNATE_PDK_URL_1: window.location.origin + '/api/pdk/plugins',
        ALTERNATE_PDK_URL_2: `${PDK_SERVER_BASE_URL}/api/plugins`,
        ALTERNATE_PDK_URL_3: `${PDK_SERVER_BASE_URL}/api/event-sources`,
      };
      
      // Prova a caricare dati da diversi possibili endpoint
      const testResults = await Promise.allSettled([
        fetch(configs.PDK_PLUGINS_URL || `${PDK_SERVER_BASE_URL}/api/plugins`).then(r => ({ url: configs.PDK_PLUGINS_URL, status: r.status, ok: r.ok })),
        fetch(configs.PDK_EVENT_SOURCES_URL || `${PDK_SERVER_BASE_URL}/api/event-sources`).then(r => ({ url: configs.PDK_EVENT_SOURCES_URL, status: r.status, ok: r.ok })),
        fetch(configs.ALTERNATE_PDK_URL_1).then(r => ({ url: configs.ALTERNATE_PDK_URL_1, status: r.status, ok: r.ok })),
        fetch(configs.ALTERNATE_PDK_URL_2).then(r => ({ url: configs.ALTERNATE_PDK_URL_2, status: r.status, ok: r.ok })),
        fetch(configs.ALTERNATE_PDK_URL_3).then(r => ({ url: configs.ALTERNATE_PDK_URL_3, status: r.status, ok: r.ok }))
      ]);
      
      // Estrai i risultati
      const results = testResults.map((result, index) => {
        if (result.status === 'fulfilled') {
          return result.value;
        } else {
          return { 
            url: ['PDK_PLUGINS_URL', 'PDK_EVENT_SOURCES_URL', 'ALTERNATE_PDK_URL_1', 'ALTERNATE_PDK_URL_2', 'ALTERNATE_PDK_URL_3'][index],
            error: result.reason.message,
            status: 'error'
          };
        }
      });
      
      // Trova gli URL che funzionano
      const workingUrls = results.filter(r => r.ok);
      
      setDebugInfo({
        configs,
        testResults: results,
        workingUrls,
        recommendation: workingUrls.length > 0 
          ? `Si consiglia di usare: ${workingUrls[0].url}`
          : 'Nessun URL funzionante trovato. Verificare che il server PDK sia in esecuzione e che CORS sia configurato correttamente.'
      });
    } catch (err) {
      setError(`Errore durante il test: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Box p={5} borderWidth="1px" borderRadius="lg" bg="white" shadow="md" mb={3}>
      <Heading as="h5" size="md" mb={3}>Diagnostica Configurazione PDK</Heading>
      
      <Text mb={4}>
        Questo strumento aiuta a identificare problemi con la configurazione del server PDK.
        Cliccando sul pulsante "Esegui Diagnostica" verranno testati diversi possibili URL per identificare quello corretto.
      </Text>
      
      <Button 
        colorScheme="blue" 
        onClick={testPDKConnection}
        isDisabled={loading}
        mb={4}
      >
        {loading ? <Spinner size="sm" mr={2} /> : null}
        {loading ? 'Test in corso...' : 'Esegui Diagnostica'}
      </Button>
      
      {error && (
        <Alert status="error" mb={4} borderRadius="md">
          <AlertIcon />
          <Box>
            <AlertTitle>Errore</AlertTitle>
            <Text>{error}</Text>
          </Box>
        </Alert>
      )}
      
      {debugInfo && (
        <Box mt={4}>
          <Alert 
            status={debugInfo.workingUrls.length > 0 ? "success" : "warning"}
            mb={4}
            borderRadius="md"
          >
            <AlertIcon />
            <Box>
              <AlertTitle>
                {debugInfo.workingUrls.length > 0 ? "URL funzionanti trovati" : "Nessun URL funzionante"}
              </AlertTitle>
              <Text>{debugInfo.recommendation}</Text>
            </Box>
          </Alert>
          
          <Stack spacing={4}>
            <Box>
              <Heading as="h6" size="sm" mb={2}>Configurazioni attuali:</Heading>
              <Box 
                p={3} 
                borderWidth="1px" 
                borderRadius="md"
                bg="gray.50"
                mb={3}
                overflowX="auto"
              >
                <Code display="block" whiteSpace="pre">
                  {JSON.stringify(debugInfo.configs, null, 2)}
                </Code>
              </Box>
            </Box>
            
            <Divider />
            
            <Box>
              <Heading as="h6" size="sm" mb={2}>Risultati dei test:</Heading>
              <Box 
                p={3} 
                borderWidth="1px" 
                borderRadius="md"
                bg="gray.50"
                overflowX="auto"
              >
                <Code display="block" whiteSpace="pre">
                  {JSON.stringify(debugInfo.testResults, null, 2)}
                </Code>
              </Box>
            </Box>
          </Stack>
        </Box>
      )}
    </Box>
  );
};

export default PDKConfigDebugger;
