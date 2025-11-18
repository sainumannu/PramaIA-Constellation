import React from 'react';
import {
  Box,
  Text,
  List,
  ListItem,
  Divider
} from "@chakra-ui/react";
import { NodeTags } from './NodeTags';

/**
 * Componente per visualizzare le informazioni di base di un nodo
 */
const NodeInfoTab = ({ node, plugin, isEventSource }) => {
  return (
    <>
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
      <NodeTags tags={node.tags} />
    </>
  );
};

export default NodeInfoTab;
