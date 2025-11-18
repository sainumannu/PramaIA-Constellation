import React from 'react';
import {
  Box,
  Text,
  Flex,
  Divider,
  List,
  ListItem,
  Alert,
  AlertIcon,
  Button,
  Spinner
} from "@chakra-ui/react";

/**
 * Componente per visualizzare i dettagli di un plugin
 */
const NodePluginTab = ({ 
  plugin, 
  pluginDetails, 
  loading, 
  error, 
  isEventSource, 
  loadPluginDetails 
}) => {
  return (
    <>
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
    </>
  );
};

export default NodePluginTab;
