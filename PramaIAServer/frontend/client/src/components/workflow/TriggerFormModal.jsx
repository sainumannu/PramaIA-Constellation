import React, { useState, useEffect } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Button,
  FormControl,
  FormLabel,
  Input,
  Select,
  Switch,
  FormHelperText,
  useToast,
  VStack,
  HStack,
  Text,
  Divider,
  Badge,
  Box,
  Spinner,
  Alert,
  AlertIcon
} from '@chakra-ui/react';
import apiClient from '../../utils/apiClient';
import config from '../../config';
import useEventSources from '../../hooks/useEventSources';
import InputNodeSelector from '../InputNodeSelector';

const TriggerFormModal = ({ isOpen, onClose, trigger, workflows }) => {
  const [formData, setFormData] = useState({
    name: '',
    event_type: '',
    source: '',
    workflow_id: '',
    target_node_id: '',
    active: true
  });
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const toast = useToast();
  
  // Usa il hook per le sorgenti dinamiche
  const { 
    eventSources, 
    eventTypes, 
    loading: sourcesLoading, 
    error: sourcesError,
    loadEventTypesForSource 
  } = useEventSources();
  
  // Filtra i tipi di eventi per la sorgente selezionata
  const [availableEventTypes, setAvailableEventTypes] = useState([]);
  
  // Effetto per inizializzare gli event types disponibili
  useEffect(() => {
    if (eventTypes && eventTypes.length > 0 && availableEventTypes.length === 0) {
      setAvailableEventTypes(eventTypes);
    }
  }, [eventTypes, availableEventTypes.length]);

  // Effetto per caricare i tipi di eventi quando cambia la sorgente
  useEffect(() => {
    const loadEventTypesForSelectedSource = async () => {
      if (formData.source) {
        try {
          const sourceEventTypes = await loadEventTypesForSource(formData.source);
          setAvailableEventTypes(sourceEventTypes);
          
          // Se il tipo di evento corrente non è disponibile per la nuova sorgente, resetta
          const currentEventTypeAvailable = sourceEventTypes.some(et => et.type === formData.event_type);
          if (!currentEventTypeAvailable && sourceEventTypes.length > 0) {
            setFormData(prev => ({ ...prev, event_type: sourceEventTypes[0].type }));
          }
        } catch (error) {
          console.error('Errore caricamento tipi eventi:', error);
          setAvailableEventTypes([]);
        }
      } else {
        // Se non c'è una sorgente selezionata, mostra tutti i tipi di eventi disponibili
        if (eventTypes && eventTypes.length > 0) {
          setAvailableEventTypes(eventTypes);
        }
      }
    };

    loadEventTypesForSelectedSource();
  }, [formData.source, loadEventTypesForSource, eventTypes]);

  // Inizializza il form quando il trigger cambia
  useEffect(() => {
    if (trigger) {
      setFormData({
        name: trigger.name,
        event_type: trigger.event_type,
        source: trigger.source,
        workflow_id: trigger.workflow_id,
        target_node_id: trigger.target_node_id || '',
        active: trigger.active
      });
    } else {
      // Reset form per un nuovo trigger con defaults dinamici
      const defaultSource = eventSources.length > 0 ? eventSources[0].id : '';
      const defaultWorkflow = workflows.length > 0 ? workflows[0].workflow_id : '';
      
      setFormData({
        name: '',
        event_type: '',
        source: defaultSource,
        workflow_id: defaultWorkflow,
        target_node_id: '',
        active: true
      });
    }
  }, [trigger, workflows, eventSources]);

  // Gestisce i cambiamenti nei campi del form
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    
    // Se sta cambiando il workflow, resetta anche il nodo target
    if (name === 'workflow_id') {
      setFormData({
        ...formData,
        [name]: value,
        target_node_id: '' // Reset del nodo target quando cambia workflow
      });
    } else {
      setFormData({
        ...formData,
        [name]: type === 'checkbox' ? checked : value
      });
    }
  };

  // Gestisce l'invio del form
  const handleSubmit = async () => {
    setIsSubmitting(true);
    
    try {
      if (trigger) {
        // Aggiorna un trigger esistente
        await apiClient.put(`/api/workflows/triggers/${trigger.id}`, formData);
        toast({
          title: 'Trigger aggiornato',
          description: 'Il trigger è stato aggiornato con successo.',
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
      } else {
        // Crea un nuovo trigger
        await apiClient.post('/api/workflows/triggers/', formData);
        toast({
          title: 'Trigger creato',
          description: 'Il nuovo trigger è stato creato con successo.',
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
      }
      
      onClose(true); // true indica che è necessario un refresh
    } catch (error) {
      toast({
        title: 'Errore',
        description: `Impossibile ${trigger ? 'aggiornare' : 'creare'} il trigger. ${error.response?.data?.detail || ''}`,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Trova le informazioni su un tipo di evento
  const getEventTypeInfo = (value) => {
    return availableEventTypes.find(et => et.type === value) || { label: value, description: '' };
  };

  // Trova le informazioni su una sorgente
  const getSourceInfo = (value) => {
    return eventSources.find(s => s.id === value) || { name: value, description: '' };
  };

  // Gestisce i cambiamenti nella sorgente
  const handleSourceChange = (e) => {
    const newSource = e.target.value;
    setFormData(prev => ({
      ...prev,
      source: newSource,
      event_type: '' // Reset event type quando cambia sorgente
    }));
  };

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={() => onClose(false)} 
      size="lg"
      blockScrollOnMount={true}
      closeOnOverlayClick={false}
      motionPreset="slideInBottom"
      isCentered
      trapFocus={true}
      preserveScrollBarGap={true}
    >
      <ModalOverlay bg="blackAlpha.600" />
      <ModalContent maxW="600px" mx="auto" bg="white" position="relative" zIndex="1">
        <ModalHeader>
          {trigger ? 'Modifica Trigger' : 'Nuovo Trigger'}
        </ModalHeader>
        <ModalCloseButton position="absolute" top="8px" right="8px" zIndex="2" />
        
        <ModalBody>
          {sourcesLoading ? (
            <VStack spacing={4} align="center" py={8}>
              <Spinner size="lg" />
              <Text>Caricamento sorgenti di eventi...</Text>
            </VStack>
          ) : sourcesError ? (
            <Alert status="warning" borderRadius="md" mb={4}>
              <AlertIcon />
              <VStack align="start" spacing={1}>
                <Text fontSize="sm" fontWeight="medium">
                  Avviso: {sourcesError}
                </Text>
                <Text fontSize="xs">
                  Utilizzando configurazione di fallback.
                </Text>
              </VStack>
            </Alert>
          ) : null}
          
          <VStack spacing={6} align="stretch" width="100%" position="relative">
            <FormControl isRequired>
              <FormLabel fontWeight="medium">Nome</FormLabel>
              <Input 
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="Nome descrittivo per il trigger"
                bg="white"
              />
              <FormHelperText>
                Un nome descrittivo che identifica chiaramente lo scopo del trigger.
              </FormHelperText>
            </FormControl>
            
            <FormControl isRequired>
              <FormLabel>Sorgente</FormLabel>
              <Select 
                name="source"
                value={formData.source}
                onChange={handleSourceChange}
                disabled={sourcesLoading}
              >
                <option value="">Seleziona sorgente...</option>
                {eventSources.map(source => (
                  <option key={source.id} value={source.id}>
                    {source.name}
                  </option>
                ))}
              </Select>
              <FormHelperText>
                {getSourceInfo(formData.source).description || 'Seleziona una sorgente di eventi'}
              </FormHelperText>
            </FormControl>
            
            <FormControl isRequired>
              <FormLabel>Tipo di Evento</FormLabel>
              <Select 
                name="event_type"
                value={formData.event_type}
                onChange={handleChange}
                disabled={!formData.source || availableEventTypes.length === 0}
              >
                <option value="">Seleziona tipo evento...</option>
                {availableEventTypes.map(type => (
                  <option key={type.type} value={type.type}>
                    {type.label}
                  </option>
                ))}
              </Select>
              <FormHelperText>
                {availableEventTypes.length === 0 && formData.source ? 
                  'Nessun tipo di evento disponibile per questa sorgente' :
                  getEventTypeInfo(formData.event_type).description || 'Seleziona prima una sorgente'
                }
              </FormHelperText>
            </FormControl>
            
            <FormControl isRequired>
              <FormLabel>Workflow</FormLabel>
              <Select 
                name="workflow_id"
                value={formData.workflow_id}
                onChange={handleChange}
              >
                <option value="">Seleziona workflow...</option>
                {workflows.map(workflow => (
                  <option key={workflow.workflow_id} value={workflow.workflow_id}>
                    {workflow.name}
                  </option>
                ))}
              </Select>
              <FormHelperText>
                Il workflow che verrà eseguito quando si verifica l'evento.
              </FormHelperText>
            </FormControl>

            {/* Selettore del nodo di input */}
            {formData.workflow_id ? (
              <FormControl>
                <FormLabel>Nodo di Input Target</FormLabel>
                <Box bg="gray.50" p={4} borderRadius="md" border="1px" borderColor="gray.200">
                  <InputNodeSelector
                    workflowId={formData.workflow_id}
                    selectedNodeId={formData.target_node_id}
                    onNodeSelect={(nodeId) => {
                      console.log('Node selected:', nodeId);
                      setFormData(prev => ({ ...prev, target_node_id: nodeId }));
                    }}
                    triggerEventType={formData.event_type}
                    disabled={isSubmitting}
                    className="w-full"
                  />
                </Box>
                <FormHelperText>
                  Seleziona il nodo di input specifico del workflow che riceverà i dati dell'evento. 
                  Se non specificato, verrà utilizzato il primo nodo di input disponibile.
                </FormHelperText>
              </FormControl>
            ) : null}
            
            <Divider />
            
            <FormControl display="flex" alignItems="center">
              <FormLabel htmlFor="active" mb={0}>
                Stato Attivo
              </FormLabel>
              <Switch 
                id="active"
                name="active"
                isChecked={formData.active}
                onChange={handleChange}
                colorScheme="green"
              />
            </FormControl>
            
            <Box width="100%">
              <Badge colorScheme={formData.active ? 'green' : 'red'} p={2} borderRadius="md">
                {formData.active ? 'Il trigger è attivo' : 'Il trigger è inattivo'}
              </Badge>
              <Text fontSize="sm" color="gray.500" mt={2}>
                {formData.active
                  ? 'Il workflow verrà eseguito quando si verifica l\'evento specificato.'
                  : 'Il workflow non verrà eseguito finché il trigger non viene attivato.'}
              </Text>
            </Box>
          </VStack>
        </ModalBody>
        
        <ModalFooter bg="gray.50" borderBottomRadius="md">
          <Button variant="outline" mr={3} onClick={() => onClose(false)}>
            Annulla
          </Button>
          <Button 
            colorScheme="blue" 
            onClick={handleSubmit}
            isLoading={isSubmitting}
            loadingText="Salvataggio..."
            isDisabled={!formData.name || !formData.workflow_id}
          >
            {trigger ? 'Aggiorna' : 'Crea'}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default TriggerFormModal;
