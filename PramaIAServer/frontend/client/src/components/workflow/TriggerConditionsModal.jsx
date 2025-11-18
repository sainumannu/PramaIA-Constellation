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
  FormHelperText,
  useToast,
  VStack,
  HStack,
  Box,
  Text,
  IconButton,
  Divider,
  Select,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Badge,
  Collapse,
  useDisclosure,
  Alert,
  AlertIcon,
} from '@chakra-ui/react';
import { AddIcon, DeleteIcon, InfoIcon } from '@chakra-ui/icons';
import apiClient from '../../utils/apiClient';
import config from '../../config';

const CONDITION_TYPES = [
  { 
    id: 'filename_pattern', 
    label: 'Pattern Nome File', 
    type: 'string',
    description: 'Espressione regolare per filtrare i nomi dei file',
    placeholder: 'es. .*\\.pdf$ per tutti i file PDF'
  },
  { 
    id: 'max_size_kb', 
    label: 'Dimensione Massima (KB)', 
    type: 'number',
    description: 'Dimensione massima del file in kilobytes',
    min: 0
  },
  { 
    id: 'min_size_kb', 
    label: 'Dimensione Minima (KB)', 
    type: 'number',
    description: 'Dimensione minima del file in kilobytes',
    min: 0
  },
  { 
    id: 'content_type', 
    label: 'Tipo di Contenuto', 
    type: 'string',
    description: 'MIME type del contenuto (es. application/pdf)',
    placeholder: 'es. application/pdf, image/jpeg'
  }
];

const TriggerConditionsModal = ({ isOpen, onClose, trigger }) => {
  const [conditions, setConditions] = useState({});
  const [conditionType, setConditionType] = useState('');
  const [conditionValue, setConditionValue] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const toast = useToast();
  
  const { isOpen: isHelpOpen, onToggle: onHelpToggle } = useDisclosure();
  
  // Inizializza le condizioni quando il trigger cambia
  useEffect(() => {
    if (trigger) {
      setConditions(trigger.conditions || {});
    } else {
      setConditions({});
    }
  }, [trigger]);
  
  // Gestisce l'aggiunta di una nuova condizione
  const handleAddCondition = () => {
    if (!conditionType) {
      toast({
        title: "Tipo mancante",
        description: "Seleziona un tipo di condizione",
        status: "warning",
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    const conditionInfo = CONDITION_TYPES.find(c => c.id === conditionType);
    
    // Validazione in base al tipo
    if (conditionInfo.type === 'number') {
      const numValue = Number(conditionValue);
      if (isNaN(numValue)) {
        toast({
          title: "Valore non valido",
          description: "Inserisci un valore numerico valido",
          status: "warning",
          duration: 3000,
          isClosable: true,
        });
        return;
      }
      
      if (conditionInfo.min !== undefined && numValue < conditionInfo.min) {
        toast({
          title: "Valore troppo basso",
          description: `Il valore minimo è ${conditionInfo.min}`,
          status: "warning",
          duration: 3000,
          isClosable: true,
        });
        return;
      }
      
      setConditions({
        ...conditions,
        [conditionType]: numValue
      });
    } else {
      // Per stringhe e altri tipi
      if (!conditionValue.trim()) {
        toast({
          title: "Valore mancante",
          description: "Inserisci un valore per la condizione",
          status: "warning",
          duration: 3000,
          isClosable: true,
        });
        return;
      }
      
      setConditions({
        ...conditions,
        [conditionType]: conditionValue
      });
    }
    
    // Reset dei campi
    setConditionType('');
    setConditionValue('');
  };
  
  // Gestisce la rimozione di una condizione
  const handleRemoveCondition = (key) => {
    const newConditions = { ...conditions };
    delete newConditions[key];
    setConditions(newConditions);
  };
  
  // Salva le modifiche alle condizioni
  const handleSave = async () => {
    if (!trigger) return;
    
    setIsSubmitting(true);
    
    try {
      await apiClient.put(`/api/workflows/triggers/${trigger.id}`, {
        conditions
      });
      
      toast({
        title: "Condizioni salvate",
        description: "Le condizioni sono state aggiornate con successo",
        status: "success",
        duration: 3000,
        isClosable: true,
      });
      
      onClose(true); // Indica che è necessario un refresh
    } catch (error) {
      console.error("Errore nel salvataggio delle condizioni:", error);
      toast({
        title: "Errore",
        description: "Impossibile salvare le condizioni",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Ottiene l'etichetta per un tipo di condizione
  const getConditionLabel = (key) => {
    const condition = CONDITION_TYPES.find(c => c.id === key);
    return condition ? condition.label : key;
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
          Condizioni per "{trigger?.name}"
        </ModalHeader>
        <ModalCloseButton position="absolute" top="8px" right="8px" zIndex="2" />
        
        <ModalBody>
          <VStack spacing={4} align="stretch">
            <HStack justify="space-between">
              <Text fontSize="sm">
                Le condizioni permettono di filtrare ulteriormente gli eventi che attiveranno questo trigger.
              </Text>
              <IconButton
                icon={<InfoIcon />}
                aria-label="Aiuto"
                size="sm"
                variant="ghost"
                onClick={onHelpToggle}
                _hover={{ bg: 'gray.100' }}
                position="relative"
                zIndex="1"
              />
            </HStack>
            
            <Collapse in={isHelpOpen} animateOpacity>
              <Alert status="info" borderRadius="md">
                <AlertIcon />
                <Box>
                  <Text fontWeight="medium" mb={1}>Come funzionano le condizioni</Text>
                  <Text fontSize="sm">
                    Quando si verifica un evento del tipo specificato, il sistema controllerà se tutte le condizioni
                    qui definite sono soddisfatte prima di eseguire il workflow. Se anche solo una condizione non
                    è soddisfatta, il workflow non verrà eseguito.
                  </Text>
                </Box>
              </Alert>
            </Collapse>
            
            <Divider />
            
            {/* Lista delle condizioni esistenti */}
            <VStack align="stretch" spacing={2}>
              <Text fontWeight="medium">Condizioni attive</Text>
              
              {Object.keys(conditions).length === 0 ? (
                <Text fontSize="sm" color="gray.500">
                  Nessuna condizione definita. Il trigger si attiverà per qualsiasi evento del tipo specificato.
                </Text>
              ) : (
                Object.entries(conditions).map(([key, value]) => (
                  <HStack key={key} p={2} borderWidth="1px" borderRadius="md" justify="space-between">
                    <VStack align="start" spacing={0}>
                      <Text fontWeight="medium">{getConditionLabel(key)}</Text>
                      <Text fontSize="sm" color="gray.600">{value}</Text>
                    </VStack>
                    <IconButton
                      icon={<DeleteIcon />}
                      aria-label="Rimuovi condizione"
                      size="sm"
                      colorScheme="red"
                      variant="ghost"
                      onClick={() => handleRemoveCondition(key)}
                    />
                  </HStack>
                ))
              )}
            </VStack>
            
            <Divider />
            
            {/* Form per aggiungere nuove condizioni */}
            <Box>
              <Text fontWeight="medium" mb={2}>Aggiungi condizione</Text>
              
              <HStack spacing={4} align="end">
                <FormControl flex="1">
                  <FormLabel fontSize="sm">Tipo</FormLabel>
                  <Select
                    value={conditionType}
                    onChange={(e) => setConditionType(e.target.value)}
                    placeholder="Seleziona tipo..."
                  >
                    {CONDITION_TYPES.map(type => (
                      <option key={type.id} value={type.id}>{type.label}</option>
                    ))}
                  </Select>
                </FormControl>
                
                {conditionType && (
                  <FormControl flex="1">
                    <FormLabel fontSize="sm">Valore</FormLabel>
                    {CONDITION_TYPES.find(c => c.id === conditionType)?.type === 'number' ? (
                      <NumberInput
                        value={conditionValue}
                        onChange={(valueString) => setConditionValue(valueString)}
                        min={CONDITION_TYPES.find(c => c.id === conditionType)?.min || 0}
                      >
                        <NumberInputField />
                        <NumberInputStepper>
                          <NumberIncrementStepper />
                          <NumberDecrementStepper />
                        </NumberInputStepper>
                      </NumberInput>
                    ) : (
                      <Input
                        value={conditionValue}
                        onChange={(e) => setConditionValue(e.target.value)}
                        placeholder={CONDITION_TYPES.find(c => c.id === conditionType)?.placeholder}
                      />
                    )}
                  </FormControl>
                )}
                
                <IconButton
                  icon={<AddIcon />}
                  aria-label="Aggiungi condizione"
                  colorScheme="blue"
                  isDisabled={!conditionType}
                  onClick={handleAddCondition}
                />
              </HStack>
              
              {conditionType && (
                <FormHelperText>
                  {CONDITION_TYPES.find(c => c.id === conditionType)?.description}
                </FormHelperText>
              )}
            </Box>
          </VStack>
        </ModalBody>
        
        <ModalFooter bg="gray.50" borderBottomRadius="md">
          <Button variant="outline" mr={3} onClick={() => onClose(false)}>
            Annulla
          </Button>
          <Button 
            colorScheme="blue" 
            onClick={handleSave}
            isLoading={isSubmitting}
            loadingText="Salvataggio..."
          >
            Salva condizioni
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default TriggerConditionsModal;
