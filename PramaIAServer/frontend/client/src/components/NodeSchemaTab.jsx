import React from 'react';
import {
  Box,
  Text
} from "@chakra-ui/react";

/**
 * Componente per visualizzare lo schema JSON di un nodo
 */
const NodeSchemaTab = ({ schema }) => {
  return (
    <>
      <Text fontWeight="semibold" mb="3">Schema del nodo</Text>
      
      <Box
        p={3}
        bg="gray.50"
        borderRadius="md"
        borderWidth="1px"
        overflowX="auto"
      >
        <pre style={{ maxHeight: '300px', overflow: 'auto' }}>
          {JSON.stringify(schema, null, 2)}
        </pre>
      </Box>
    </>
  );
};

export default NodeSchemaTab;
