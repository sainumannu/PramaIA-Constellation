import React, { useState } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Box,
  Text,
  Flex,
  Divider,
  List,
  ListItem,
  Tag,
  Spinner,
  Alert,
  AlertIcon,
  Code
} from "@chakra-ui/react";
import { determineNodeCategory } from '../utils/nodeCategories';
import { NODE_CATEGORIES, PDK_PLUGINS_URL, PDK_EVENT_SOURCES_URL, PDK_BACKEND_PLUGINS_URL, PDK_BACKEND_EVENT_SOURCES_URL } from '../config/appConfig';
import PDKConfigDebugger from './PDKConfigDebugger';

/**
 * Componente Modal per visualizzare i dettagli di un nodo
 */
const NodeDetailsModal = ({ open, node, plugin, onClose }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [pluginDetails, setPluginDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  if (!node) {
    return null;
  }
  
  // Determina la categoria del nodo
  const nodeCategory = determineNodeCategory(node, plugin);
  const categoryInfo = NODE_CATEGORIES.find(c => c.value === nodeCategory) || { label: nodeCategory, description: '' };
  
  // Determina se è un event source
  const isEventSource = plugin?.type === 'event-source' || 
                        plugin?.eventTypes?.length > 0 || 
                        node.type === 'event-source';
  
  // Formatta i tag come componenti Tag
  const renderTags = (tags = []) => {
    if (!tags || tags.length === 0) {
      return <Text fontSize="sm" color="gray.500">Nessun tag disponibile</Text>;
    }
    
    return (
      <Flex wrap="wrap" gap="1">
        {tags.map(tag => (
          <Tag 
            key={tag} 
            size="sm" 
            variant="outline" 
            colorScheme="blue" 
            m="1"
          >
            {tag}
          </Tag>
        ))}
      </Flex>
    );
  };
  
  // Carica i dettagli del plugin manualmente quando si seleziona la scheda
  const loadPluginDetails = async () => {
    if (!plugin || !plugin.id) return;
    
    setLoading(true);
    setError(null);
    
    try {
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
          const res = await fetch(url);
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
      } else {
        setError('Non è stato possibile caricare i dettagli del plugin da nessuno degli URL provati.');
      }
    } catch (err) {
      console.error('Errore nel caricamento dei dettagli del plugin:', err);
      setError(`Errore: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  // Gestisce il cambio di tab
  const handleTabChange = (index) => {
    setActiveTab(index);
    
    // Carica i dettagli del plugin quando si seleziona la scheda Plugin (index 3)
    if (index === 3 && plugin && !pluginDetails && !loading) {
      loadPluginDetails();
    }
  };
  
  return (
    <Modal isOpen={open} onClose={onClose} size="xl">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>
          {node.name}
        </ModalHeader>
        <ModalCloseButton />
        
        <ModalBody>
          <Tabs 
            isFitted 
            variant="enclosed" 
            colorScheme="blue" 
            index={activeTab} 
            onChange={handleTabChange}
            mb="4"
          >
            <TabList>
              <Tab>Informazioni</Tab>
              <Tab>Categoria</Tab>
              {node.schema && <Tab>Schema</Tab>}
              {plugin && <Tab>Plugin</Tab>}
              <Tab>Debug</Tab>
            </TabList>
            
            <TabPanels>
              {/* Pannello Informazioni */}
              <TabPanel>
                <Text fontWeight="semibold" mb="3">Dettagli del nodo</Text>
                
                <List spacing={2}>
                  <ListItem>
                    <Text fontSize="xs" color="gray.500">ID</Text>
                    <Text>{node.id}</Text>
                  </ListItem>
                  
                  <ListItem>
                    <Text fontSize="xs" color="gray.500">Descrizione</Text>
                    <Text>{node.description || 'Nessuna descrizione disponibile'}</Text>
                  </ListItem>
                  
                  <ListItem>
                    <Text fontSize="xs" color="gray.500">Tipo</Text>
                    <Text>{plugin ? (isEventSource ? 'Event Source PDK' : 'Nodo PDK') : 'Nodo Core'}</Text>
                  </ListItem>
                  
                  {plugin && (
                    <ListItem>
                      <Text fontSize="xs" color="gray.500">Plugin</Text>
                      <Text>{plugin.name}</Text>
                    </ListItem>
                  )}
                  
                  <ListItem>
                    <Text fontSize="xs" color="gray.500">Versione</Text>
                    <Text>{node.version || (plugin ? plugin.version : '1.0.0')}</Text>
                  </ListItem>
                </List>
                
                <Divider my={3} />
                
                <Text fontSize="xs" color="gray.500" mb={2}>Tag</Text>
                {renderTags(node.tags)}
              </TabPanel>
              
              {/* Pannello Categoria */}
              <TabPanel>
                <Text fontWeight="semibold" mb="3">Categoria del nodo</Text>
                
                <Box p={4} bg="gray.50" borderRadius="md" mb={4} borderWidth="1px">
                  <Text fontWeight="bold" fontSize="lg" mb={2}>
                    {categoryInfo.label}
                  </Text>
                  
                  <Text color="gray.600" mb={3}>
                    {categoryInfo.description}
                  </Text>
                  
                  <Divider my={2} />
                  
                  <Text fontSize="xs" color="gray.500">
                    Valore interno: <Code>{nodeCategory}</Code>
                  </Text>
                </Box>
                
                <Text fontWeight="semibold" fontSize="sm" mb={2}>
                  Come viene determinata la categoria
                </Text>
                
                <List spacing={2}>
                  {node.category && (
                    <ListItem>
                      <Text fontWeight="medium">Categoria esplicita</Text>
                      <Text fontSize="sm">Il nodo specifica esplicitamente la categoria "{node.category}"</Text>
                    </ListItem>
                  )}
                  
                  {!node.category && node.tags && node.tags.length > 0 && (
                    <ListItem>
                      <Text fontWeight="medium">Inferita dai tag</Text>
                      <Text fontSize="sm">La categoria è stata inferita dai tag del nodo: {node.tags.join(', ')}</Text>
                    </ListItem>
                  )}
                  
                  {!node.category && plugin && plugin.category && (
                    <ListItem>
                      <Text fontWeight="medium">Categoria del plugin</Text>
                      <Text fontSize="sm">Ereditata dalla categoria del plugin: "{plugin.category}"</Text>
                    </ListItem>
                  )}
                  
                  {!node.category && (!node.tags || node.tags.length === 0) && (!plugin || !plugin.category) && (
                    <ListItem>
                      <Text fontWeight="medium">Categoria predefinita</Text>
                      <Text fontSize="sm">Viene utilizzata la categoria predefinita "utility"</Text>
                    </ListItem>
                  )}
                </List>
              </TabPanel>
              
              {/* Pannello Schema */}
              {node.schema && (
                <TabPanel>
                  <Text fontWeight="semibold" mb="3">Schema del nodo</Text>
                  
                  <Box
                    p={3}
                    bg="gray.50"
                    borderRadius="md"
                    borderWidth="1px"
                    overflowX="auto"
                  >
                    <pre style={{ maxHeight: '300px', overflow: 'auto' }}>
                      {JSON.stringify(node.schema, null, 2)}
                    </pre>
                  </Box>
                </TabPanel>
              )}
              
              {/* Pannello Plugin */}
              {plugin && (
                <TabPanel>
                  <Text fontWeight="semibold" mb="3">Informazioni sul Plugin</Text>
                  
                  {loading ? (
                    <Flex justify="center" p={5}>
                      <Spinner />
                    </Flex>
                  ) : error ? (
                    <Alert status="error" mb={4}>
                      <AlertIcon />
                      {error}
                      <Button
                        ml={2}
                        size="sm"
                        onClick={loadPluginDetails}
                        mt={2}
                      >
                        Riprova
                      </Button>
                    </Alert>
                  ) : pluginDetails ? (
                    <Box>
                      <Text fontSize="xl" fontWeight="bold" mb={2}>
                        {pluginDetails.name}
                      </Text>
                      
                      <Text mb={4}>
                        {pluginDetails.description}
                      </Text>
                      
                      <Text fontWeight="medium">
                        Versione: {pluginDetails.version}
                      </Text>
                      
                      <Divider my={4} />
                      
                      {/* Visualizza altre informazioni specifiche in base al tipo di plugin */}
                      {isEventSource ? (
                        <Box mt={4}>
                          <Text fontSize="lg" fontWeight="semibold">Tipi di Eventi</Text>
                          {pluginDetails.eventTypes && pluginDetails.eventTypes.length > 0 ? (
                            <List spacing={2} mt={2}>
                              {pluginDetails.eventTypes.map(eventType => (
                                <ListItem key={eventType.id}>
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
                              {pluginDetails.nodes.map(node => (
                                <ListItem key={node.id}>
                                  <Text fontWeight="medium">
                                    {node.name}
                                  </Text>
                                  <Text fontSize="sm">
                                    {node.description}
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
                        onClick={loadPluginDetails}
                      >
                        Carica Dettagli Plugin
                      </Button>
                    </Box>
                  )}
                </TabPanel>
              )}
              
              {/* Pannello Debug */}
              <TabPanel>
                <Text fontWeight="semibold" mb="3">Debug Configurazione PDK</Text>
                <PDKConfigDebugger />
              </TabPanel>
            </TabPanels>
          </Tabs>
        </ModalBody>
        
        <ModalFooter>
          <Button onClick={onClose}>
            Chiudi
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default NodeDetailsModal;
