import React from 'react';
import {
  Box,
  Text
} from "@chakra-ui/react";
import PDKConfigDebugger from './PDKConfigDebugger';

/**
 * Componente per visualizzare le informazioni di debug
 */
const NodeDebugTab = () => {
  return (
    <>
      <Text fontWeight="semibold" mb="3">Debug Configurazione PDK</Text>
      <PDKConfigDebugger />
    </>
  );
};

export default NodeDebugTab;
