import React from 'react';
import {
  Text,
  Flex,
  Tag
} from "@chakra-ui/react";

/**
 * Componente per la visualizzazione dei tag di un nodo
 */
const NodeTags = ({ tags = [] }) => {
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

export default NodeTags;
