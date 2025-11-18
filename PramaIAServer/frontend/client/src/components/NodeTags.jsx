import React from 'react';
import {
  Flex,
  Tag,
  Text
} from "@chakra-ui/react";

/**
 * Componente per visualizzare i tag di un nodo
 */
export const NodeTags = ({ tags = [] }) => {
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
