import PDKNode from './PDKNode';
// PDF Semantic Nodes - RIMOSSO: ora gestiti dinamicamente dal PDK
// import { 
//   PDFInputNode, 
//   PDFTextExtractorNode, 
//   TextChunkerNode, 
//   TextEmbedderNode, 
//   ChromaVectorStoreNode, 
//   QueryInputNode, 
//   ChromaRetrieverNode, 
//   LLMProcessorNode, 
//   PDFResultsFormatterNode 
// } from './PDFSemanticNodes';

// Modalità debug per i log verbosi
const DEBUG_MODE = false;

// Helper per log condizionali
const debugLog = (...args) => {
  if (DEBUG_MODE) console.log(...args);
};

// Proxy per catturare nodi PDK dinamicamente
const pdkNodeProxy = new Proxy({}, {
  get: function(target, prop) {
    // Se il tipo inizia con 'pdk_', restituisci il componente PDK generico
    if (typeof prop === 'string' && prop.startsWith('pdk_')) {
      return PDKNode;
    }
    return target[prop];
  }
});

// Mappa dei tipi di nodi ai loro componenti
export const nodeTypes = new Proxy({}, {
  get: function(target, prop) {
    debugLog('[NodeTypes] Requesting node type:', prop);
    
    // Se il tipo inizia con 'pdk_', restituisci il componente PDK generico
    if (typeof prop === 'string' && prop.startsWith('pdk_')) {
      debugLog('[NodeTypes] ✅ Using PDK Node for type:', prop);
      return PDKNode;
    }
    
    debugLog('[NodeTypes] Nessun componente legacy disponibile per', prop);
    return undefined;
  }
});

// Definizioni di nodi di fallback per quando il server PDK non risponde
// Questi nodi appariranno solo se il server PDK non è disponibile
export const nodeDefinitions = [
  {
    type: 'pdk_core-input-plugin_user_input',
    label: 'Input Utente',
    category: 'Input',
    description: 'Input testuale dall\'utente',
    icon: '👤',
    configSchema: {
      type: 'object',
      properties: {
        prompt: {
          type: 'string',
          title: 'Prompt',
          description: 'Testo da mostrare all\'utente'
        }
      }
    },
    defaultConfig: {
      prompt: 'Inserisci il tuo testo qui:'
    }
  },
  {
    type: 'pdk_core-llm-plugin_openai',
    label: 'OpenAI',
    category: 'LLM',
    description: 'Modello linguistico OpenAI',
    icon: '🚀',
    configSchema: {
      type: 'object',
      properties: {
        model: {
          type: 'string',
          title: 'Modello',
          enum: ['gpt-3.5-turbo', 'gpt-4', 'gpt-4o'],
          default: 'gpt-3.5-turbo'
        }
      }
    },
    defaultConfig: {
      model: 'gpt-3.5-turbo'
    }
  },
  {
    type: 'pdk_core-output-plugin_text_output',
    label: 'Output Testo',
    category: 'Output',
    description: 'Visualizza testo come output',
    icon: '📝',
    configSchema: {
      type: 'object',
      properties: {
        format: {
          type: 'string',
          title: 'Formato',
          enum: ['plain', 'markdown', 'html'],
          default: 'markdown'
        }
      }
    },
    defaultConfig: {
      format: 'markdown'
    }
  }
];

export default nodeTypes;
