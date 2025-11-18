import React from 'react';
import { Text } from "@chakra-ui/react";
import PDKConfigDebugger from '../PDKConfigDebugger';

/**
 * Componente per il tab Debug del NodeDetailsModal
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
