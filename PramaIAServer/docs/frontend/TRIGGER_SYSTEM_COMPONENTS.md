# Frontend Components - Advanced Trigger System

## 🎨 Component Architecture

### Component Hierarchy
```
TriggerFormModal (Container)
├── InputNodeSelector (Smart Component)
│   ├── NodeCard (Presentation)
│   ├── ValidationIndicator (Presentation)
│   └── DebugPanel (Development)
├── EventSourceSelector (Existing)
├── EventTypeSelector (Enhanced)
└── TriggerConfigForm (Existing)
```

## 📦 Components Documentation

### InputNodeSelector

**Percorso:** `src/components/InputNodeSelector.jsx`

#### Props Interface
```typescript
interface InputNodeSelectorProps {
  workflowId: string;              // ID del workflow target
  selectedNodeId?: string;         // Nodo attualmente selezionato
  onNodeSelect: (nodeId: string) => void;  // Callback selezione nodo
  eventType?: string;              // Tipo evento per validazione
  showDebugInfo?: boolean;         // Mostra informazioni debug
  disabled?: boolean;              // Disabilita selezione
}
```

#### Usage Example
```jsx
import InputNodeSelector from './components/InputNodeSelector';

function TriggerForm() {
  const [selectedNode, setSelectedNode] = useState(null);
  
  return (
    <InputNodeSelector
      workflowId="workflow_123"
      selectedNodeId={selectedNode}
      onNodeSelect={setSelectedNode}
      eventType="any_change"
      showDebugInfo={process.env.NODE_ENV === 'development'}
    />
  );
}
```

#### Internal State
```javascript
const [availableNodes, setAvailableNodes] = useState([]);
const [loading, setLoading] = useState(false);
const [error, setError] = useState(null);
const [validationResults, setValidationResults] = useState({});
```

#### Key Methods
```javascript
// Carica nodi disponibili per il workflow
const loadAvailableNodes = async (workflowId) => {
  try {
    const response = await workflowService.getWorkflowInputNodes(workflowId);
    setAvailableNodes(response.input_nodes || []);
  } catch (error) {
    console.error('Error loading nodes:', error);
    setError('Impossibile caricare i nodi disponibili');
  }
};

// Valida compatibilità nodo con evento
const validateNodeCompatibility = (node, eventType) => {
  if (!eventType || !node.compatibility) return 'unknown';
  return node.compatibility[eventType] || 'incompatible';
};

// Gestisce selezione nodo
const handleNodeSelection = (nodeId) => {
  const isValid = validateNodeCompatibility(
    availableNodes.find(n => n.node_id === nodeId),
    eventType
  ) === 'compatible';
  
  if (isValid) {
    onNodeSelect(nodeId);
  } else {
    // Mostra warning ma permette selezione
    console.warn('Selected node may not be compatible with event type');
    onNodeSelect(nodeId);
  }
};
```

#### Component Structure
```jsx
return (
  <div className="input-node-selector">
    {/* Header */}
    <div className="selector-header">
      <h3>Seleziona Nodo di Input</h3>
      {loading && <Spinner />}
    </div>
    
    {/* Error Display */}
    {error && (
      <Alert status="error">
        <AlertIcon />
        {error}
      </Alert>
    )}
    
    {/* Nodes Grid */}
    <div className="nodes-grid">
      {availableNodes.map(node => (
        <NodeCard
          key={node.node_id}
          node={node}
          selected={selectedNodeId === node.node_id}
          compatibility={validateNodeCompatibility(node, eventType)}
          onClick={() => handleNodeSelection(node.node_id)}
        />
      ))}
    </div>
    
    {/* Debug Panel */}
    {showDebugInfo && (
      <DebugPanel
        availableNodes={availableNodes}
        selectedNodeId={selectedNodeId}
        eventType={eventType}
        validationResults={validationResults}
      />
    )}
  </div>
);
```

### NodeCard (Sub-component)

#### Props Interface
```typescript
interface NodeCardProps {
  node: InputNode;
  selected: boolean;
  compatibility: 'compatible' | 'incompatible' | 'unknown';
  onClick: () => void;
}
```

#### Component Structure
```jsx
const NodeCard = ({ node, selected, compatibility, onClick }) => {
  const getCompatibilityColor = (status) => {
    switch (status) {
      case 'compatible': return 'green';
      case 'incompatible': return 'red';
      default: return 'gray';
    }
  };

  return (
    <div 
      className={`node-card ${selected ? 'selected' : ''}`}
      onClick={onClick}
    >
      <div className="node-header">
        <h4>{node.node_name}</h4>
        <Badge colorScheme={getCompatibilityColor(compatibility)}>
          {compatibility}
        </Badge>
      </div>
      
      <p className="node-description">
        {node.description}
      </p>
      
      <div className="node-meta">
        <span className="node-type">{node.node_type}</span>
        <span className="plugin-id">{node.plugin_id}</span>
      </div>
      
      {/* Input Schema Preview */}
      <div className="inputs-preview">
        <strong>Inputs richiesti:</strong>
        <ul>
          {node.inputs?.filter(input => input.required).map(input => (
            <li key={input.name}>
              {input.name} ({input.type})
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
```

### Enhanced TriggerFormModal

**Percorso:** `src/components/workflow/TriggerFormModal.jsx`

#### Enhanced State Management
```javascript
const [formData, setFormData] = useState({
  name: '',
  description: '',
  workflow_id: '',
  source: '',
  event_type: '',
  target_node_id: '',  // NEW: Target node selection
  config: {},
  is_active: true
});

const [availableEventTypes, setAvailableEventTypes] = useState([]);
const [nodeValidation, setNodeValidation] = useState(null);  // NEW
const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);
```

#### Validation Logic
```javascript
// Real-time validation dei dati form
const validateForm = useCallback(() => {
  const errors = {};
  
  if (!formData.name?.trim()) {
    errors.name = 'Nome trigger richiesto';
  }
  
  if (!formData.workflow_id) {
    errors.workflow_id = 'Workflow richiesto';
  }
  
  if (!formData.source) {
    errors.source = 'Event source richiesto';
  }
  
  if (!formData.event_type) {
    errors.event_type = 'Tipo evento richiesto';
  }
  
  // NEW: Validazione nodo target
  if (formData.workflow_id && !formData.target_node_id) {
    errors.target_node_id = 'Nodo target richiesto per workflow complessi';
  }
  
  setFormErrors(errors);
  return Object.keys(errors).length === 0;
}, [formData]);

// Validazione compatibilità nodo-evento
const validateNodeCompatibility = async () => {
  if (!formData.target_node_id || !formData.event_type) return;
  
  try {
    const result = await workflowService.validateTriggerCompatibility({
      target_node_id: formData.target_node_id,
      event_type: formData.event_type,
      source: formData.source
    });
    
    setNodeValidation(result);
  } catch (error) {
    console.error('Validation error:', error);
    setNodeValidation({ isValid: false, error: error.message });
  }
};
```

#### Enhanced Form Structure
```jsx
return (
  <Modal isOpen={isOpen} onClose={onClose} size="xl">
    <ModalOverlay />
    <ModalContent>
      <ModalHeader>
        {editingTrigger ? 'Modifica Trigger' : 'Nuovo Trigger'}
      </ModalHeader>
      
      <ModalBody>
        <VStack spacing={4}>
          {/* Basic Fields */}
          <FormControl isRequired isInvalid={formErrors.name}>
            <FormLabel>Nome Trigger</FormLabel>
            <Input
              value={formData.name}
              onChange={(e) => updateFormData('name', e.target.value)}
              placeholder="Nome descrittivo del trigger"
            />
            {formErrors.name && <FormErrorMessage>{formErrors.name}</FormErrorMessage>}
          </FormControl>

          {/* Workflow Selection */}
          <FormControl isRequired isInvalid={formErrors.workflow_id}>
            <FormLabel>Workflow Target</FormLabel>
            <Select
              value={formData.workflow_id}
              onChange={(e) => {
                updateFormData('workflow_id', e.target.value);
                // Reset target node when workflow changes
                updateFormData('target_node_id', '');
              }}
            >
              <option value="">Seleziona workflow...</option>
              {workflows.map(workflow => (
                <option key={workflow.id} value={workflow.id}>
                  {workflow.name}
                </option>
              ))}
            </Select>
          </FormControl>

          {/* Event Source Selection */}
          <FormControl isRequired isInvalid={formErrors.source}>
            <FormLabel>Event Source</FormLabel>
            <Select
              value={formData.source}
              onChange={(e) => handleSourceChange(e.target.value)}
            >
              <option value="">Seleziona event source...</option>
              {eventSources.map(source => (
                <option key={source.id} value={source.id}>
                  {source.name}
                </option>
              ))}
            </Select>
          </FormControl>

          {/* Event Type Selection */}
          <FormControl isRequired isInvalid={formErrors.event_type}>
            <FormLabel>Tipo Evento</FormLabel>
            <Select
              value={formData.event_type}
              onChange={(e) => updateFormData('event_type', e.target.value)}
              disabled={!formData.source}
            >
              <option value="">Seleziona tipo evento...</option>
              {availableEventTypes.map(eventType => (
                <option key={eventType.type} value={eventType.type}>
                  {eventType.label}
                </option>
              ))}
            </Select>
          </FormControl>

          {/* NEW: Input Node Selection */}
          {formData.workflow_id && (
            <FormControl isRequired isInvalid={formErrors.target_node_id}>
              <FormLabel>Nodo di Input Target</FormLabel>
              <InputNodeSelector
                workflowId={formData.workflow_id}
                selectedNodeId={formData.target_node_id}
                onNodeSelect={(nodeId) => updateFormData('target_node_id', nodeId)}
                eventType={formData.event_type}
                showDebugInfo={process.env.NODE_ENV === 'development'}
              />
              {formErrors.target_node_id && (
                <FormErrorMessage>{formErrors.target_node_id}</FormErrorMessage>
              )}
            </FormControl>
          )}

          {/* Validation Results */}
          {nodeValidation && (
            <Alert 
              status={nodeValidation.isValid ? 'success' : 'warning'}
              borderRadius="md"
            >
              <AlertIcon />
              <Box>
                <AlertTitle>
                  {nodeValidation.isValid ? 'Configurazione Valida' : 'Attenzione'}
                </AlertTitle>
                <AlertDescription>
                  {nodeValidation.message || nodeValidation.error}
                </AlertDescription>
              </Box>
            </Alert>
          )}

          {/* Advanced Configuration */}
          <Accordion allowToggle>
            <AccordionItem>
              <AccordionButton>
                <Box flex="1" textAlign="left">
                  Configurazione Avanzata
                </Box>
                <AccordionIcon />
              </AccordionButton>
              <AccordionPanel pb={4}>
                <TriggerConfigForm
                  config={formData.config}
                  onChange={(config) => updateFormData('config', config)}
                  eventSource={formData.source}
                />
              </AccordionPanel>
            </AccordionItem>
          </Accordion>
        </VStack>
      </ModalBody>

      <ModalFooter>
        <Button variant="ghost" mr={3} onClick={onClose}>
          Annulla
        </Button>
        <Button
          colorScheme="blue"
          onClick={handleSubmit}
          isLoading={isSubmitting}
          disabled={!validateForm()}
        >
          {editingTrigger ? 'Aggiorna' : 'Crea'} Trigger
        </Button>
      </ModalFooter>
    </ModalContent>
  </Modal>
);
```

## 🔧 Hooks Enhancement

### Enhanced useEventSources

#### Added Cache Busting
```javascript
const loadEventTypesForSource = useCallback(async (sourceId) => {
  try {
    // Cache busting per evitare stale data
    const timestamp = new Date().getTime();
    const response = await axios.get(
      `http://localhost:3001/api/event-sources/${sourceId}/events?t=${timestamp}`
    );
    
    console.log(`[useEventSources] Events for ${sourceId}:`, response.data);
    
    const eventTypesData = response.data.eventTypes || response.data || [];
    const convertedEventTypes = eventTypesData.map(eventType => ({
      type: eventType.id || eventType.type,
      label: eventType.name || eventType.label,
      description: eventType.description,
      sourceId: eventType.sourceId || sourceId,
      sourceName: eventType.sourceName
    }));
    
    console.log(`[useEventSources] Converted events for ${sourceId}:`, convertedEventTypes);
    return convertedEventTypes;
  } catch (err) {
    console.error(`Errore nel caricamento eventi per ${sourceId}:`, err);
    return [];
  }
}, []);
```

#### Enhanced Error Handling
```javascript
const [eventSources, setEventSources] = useState([]);
const [eventTypes, setEventTypes] = useState([]);
const [sourcesLoading, setSourcesLoading] = useState(true);
const [sourcesError, setSourcesError] = useState(null);
const [retryCount, setRetryCount] = useState(0);

// Retry logic for failed API calls
const retryFailedRequest = useCallback(async (operation, maxRetries = 3) => {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      if (attempt === maxRetries) {
        throw error;
      }
      console.warn(`Attempt ${attempt} failed, retrying...`, error);
      await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
    }
  }
}, []);
```

## 🎯 State Management

### Form State Pattern
```javascript
// Centralized form state management
const useFormState = (initialState) => {
  const [formData, setFormData] = useState(initialState);
  const [formErrors, setFormErrors] = useState({});
  const [touched, setTouched] = useState({});

  const updateFormData = useCallback((field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when field is updated
    if (formErrors[field]) {
      setFormErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  }, [formErrors]);

  const markFieldTouched = useCallback((field) => {
    setTouched(prev => ({ ...prev, [field]: true }));
  }, []);

  const resetForm = useCallback(() => {
    setFormData(initialState);
    setFormErrors({});
    setTouched({});
  }, [initialState]);

  return {
    formData,
    formErrors,
    touched,
    updateFormData,
    markFieldTouched,
    resetForm,
    setFormErrors
  };
};
```

### Validation State Pattern
```javascript
// Real-time validation state
const useValidationState = () => {
  const [validationResults, setValidationResults] = useState({});
  const [validating, setValidating] = useState(false);

  const validateField = useCallback(async (field, value, validator) => {
    setValidating(true);
    try {
      const result = await validator(value);
      setValidationResults(prev => ({
        ...prev,
        [field]: result
      }));
    } catch (error) {
      setValidationResults(prev => ({
        ...prev,
        [field]: { isValid: false, error: error.message }
      }));
    } finally {
      setValidating(false);
    }
  }, []);

  return {
    validationResults,
    validating,
    validateField
  };
};
```

## 🎨 Styling & Theming

### CSS Classes
```scss
// InputNodeSelector styles
.input-node-selector {
  .selector-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .nodes-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
  }
}

// NodeCard styles
.node-card {
  border: 2px solid var(--chakra-colors-gray-200);
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: var(--chakra-colors-blue-300);
    box-shadow: var(--chakra-shadows-md);
  }

  &.selected {
    border-color: var(--chakra-colors-blue-500);
    background-color: var(--chakra-colors-blue-50);
  }

  .node-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 0.5rem;
  }

  .node-description {
    color: var(--chakra-colors-gray-600);
    font-size: 0.875rem;
    margin-bottom: 0.75rem;
  }

  .node-meta {
    display: flex;
    gap: 0.5rem;
    font-size: 0.75rem;
    color: var(--chakra-colors-gray-500);
  }

  .inputs-preview {
    margin-top: 0.75rem;
    font-size: 0.75rem;
    
    ul {
      margin: 0.25rem 0 0 1rem;
      list-style-type: disc;
    }
  }
}

// Compatibility indicators
.compatibility-badge {
  &.compatible {
    background-color: var(--chakra-colors-green-100);
    color: var(--chakra-colors-green-800);
  }

  &.incompatible {
    background-color: var(--chakra-colors-red-100);
    color: var(--chakra-colors-red-800);
  }

  &.unknown {
    background-color: var(--chakra-colors-gray-100);
    color: var(--chakra-colors-gray-800);
  }
}
```

### Responsive Design
```scss
// Mobile responsiveness
@media (max-width: 768px) {
  .nodes-grid {
    grid-template-columns: 1fr;
  }

  .node-card {
    padding: 0.75rem;
  }

  .trigger-form-modal {
    .modal-content {
      margin: 1rem;
      max-height: calc(100vh - 2rem);
    }
  }
}
```

## 🧪 Testing Components

### Component Test Examples
```javascript
// InputNodeSelector.test.jsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChakraProvider } from '@chakra-ui/react';
import InputNodeSelector from '../InputNodeSelector';

const renderComponent = (props = {}) => {
  const defaultProps = {
    workflowId: 'test-workflow',
    selectedNodeId: null,
    onNodeSelect: jest.fn(),
    ...props
  };

  return render(
    <ChakraProvider>
      <InputNodeSelector {...defaultProps} />
    </ChakraProvider>
  );
};

describe('InputNodeSelector', () => {
  test('loads and displays available nodes', async () => {
    const mockNodes = [
      {
        node_id: 'node1',
        node_name: 'Test Node 1',
        description: 'Test description',
        node_type: 'test-type',
        inputs: [{ name: 'input1', type: 'string', required: true }]
      }
    ];

    // Mock API call
    jest.spyOn(workflowService, 'getWorkflowInputNodes')
      .mockResolvedValue({ input_nodes: mockNodes });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Test Node 1')).toBeInTheDocument();
    });
  });

  test('handles node selection', async () => {
    const onNodeSelect = jest.fn();
    const mockNodes = [
      { node_id: 'node1', node_name: 'Test Node 1' }
    ];

    jest.spyOn(workflowService, 'getWorkflowInputNodes')
      .mockResolvedValue({ input_nodes: mockNodes });

    renderComponent({ onNodeSelect });

    await waitFor(() => {
      expect(screen.getByText('Test Node 1')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Test Node 1'));
    expect(onNodeSelect).toHaveBeenCalledWith('node1');
  });

  test('displays compatibility status', async () => {
    const mockNodes = [
      {
        node_id: 'node1',
        node_name: 'Compatible Node',
        compatibility: { 'test_event': 'compatible' }
      }
    ];

    jest.spyOn(workflowService, 'getWorkflowInputNodes')
      .mockResolvedValue({ input_nodes: mockNodes });

    renderComponent({ eventType: 'test_event' });

    await waitFor(() => {
      expect(screen.getByText('compatible')).toBeInTheDocument();
    });
  });
});
```

---

**Versione:** 1.0.0
**Framework:** React 18 + Chakra UI
**Ultima modifica:** 2025-08-05
