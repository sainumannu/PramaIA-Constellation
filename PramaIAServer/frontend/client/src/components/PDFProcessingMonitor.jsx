import React from 'react';
import DocumentProcessingMonitor from './DocumentProcessingMonitor';

/**
 * Componente legacy per mantenere la retrocompatibilità.
 * Ora rimanda a DocumentProcessingMonitor per la funzionalità effettiva.
 * @deprecated Usare DocumentProcessingMonitor al posto di PDFProcessingMonitor
 */
const PDFProcessingMonitor = () => {
  console.warn(
    'PDFProcessingMonitor è deprecato. Utilizzare DocumentProcessingMonitor per una migliore compatibilità con tutti i tipi di documenti.'
  );
  
  return <DocumentProcessingMonitor />;
};

export default PDFProcessingMonitor;
