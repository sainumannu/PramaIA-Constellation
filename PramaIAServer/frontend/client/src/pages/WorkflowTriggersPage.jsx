import React, { useState, useEffect } from 'react';
import { useToast, Spinner, Box, Flex, Heading, Button, Table, Thead, Tbody, Tr, Th, Td, Badge, 
         IconButton, useDisclosure, Menu, MenuButton, MenuList, MenuItem, Text, 
         HStack, VStack, Alert, AlertIcon } from '@chakra-ui/react';
import { AddIcon, EditIcon, DeleteIcon, SettingsIcon, CheckIcon, CloseIcon } from '@chakra-ui/icons';
import { FaFilter } from 'react-icons/fa';
import apiClient from '../utils/apiClient';
import config from '../config';

import TriggerFormModal from '../components/workflow/TriggerFormModal';
import TriggerConditionsModal from '../components/workflow/TriggerConditionsModal';
import DeleteConfirmationModal from '../components/common/DeleteConfirmationModal';

const WorkflowTriggersPage = () => {
  const [triggers, setTriggers] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTrigger, setSelectedTrigger] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  
  const { isOpen: isFormOpen, onOpen: onFormOpen, onClose: onFormClose } = useDisclosure();
  const { isOpen: isConditionsOpen, onOpen: onConditionsOpen, onClose: onConditionsClose } = useDisclosure();
  const { isOpen: isDeleteOpen, onOpen: onDeleteOpen, onClose: onDeleteClose } = useDisclosure();
  
  const toast = useToast();

  // Carica i trigger e i workflow disponibili
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Carica i trigger
        const triggersResponse = await apiClient.get('/api/workflows/triggers/');
        setTriggers(triggersResponse.data);
        
        // Carica i workflow disponibili
        const workflowsResponse = await apiClient.get('/api/workflows/');
        setWorkflows(workflowsResponse.data);
      } catch (error) {
        console.error('Errore nel caricamento dei dati:', error);
        toast({
          title: 'Errore',
          description: 'Impossibile caricare i dati dei trigger e dei workflow.',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [refreshKey, toast]);

  // Gestisce l'apertura del form per un nuovo trigger
  const handleNewTrigger = () => {
    setSelectedTrigger(null);
    onFormOpen();
  };

  // Gestisce l'apertura del form per la modifica di un trigger esistente
  const handleEditTrigger = (trigger) => {
    setSelectedTrigger(trigger);
    onFormOpen();
  };

  // Gestisce l'apertura del form per le condizioni di un trigger
  const handleEditConditions = (trigger) => {
    setSelectedTrigger(trigger);
    onConditionsOpen();
  };

  // Gestisce l'apertura della conferma di eliminazione
  const handleDeleteClick = (trigger) => {
    setSelectedTrigger(trigger);
    onDeleteOpen();
  };

  // Gestisce l'attivazione/disattivazione di un trigger
  const handleToggleActive = async (triggerId, currentStatus) => {
    try {
      await apiClient.patch(`/api/workflows/triggers/${triggerId}/toggle`, {
        active: !currentStatus
      });
      
      // Aggiorna lo stato locale
      setTriggers(triggers.map(t => 
        t.id === triggerId ? { ...t, active: !currentStatus } : t
      ));
      
      toast({
        title: 'Trigger aggiornato',
        description: `Trigger ${!currentStatus ? 'attivato' : 'disattivato'} con successo.`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      console.error('Errore nell\'aggiornamento del trigger:', error);
      toast({
        title: 'Errore',
        description: 'Impossibile aggiornare lo stato del trigger.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  // Gestisce l'eliminazione effettiva di un trigger
  const handleDeleteConfirm = async () => {
    if (!selectedTrigger) return;
    
    try {
      await apiClient.delete(`/api/workflows/triggers/${selectedTrigger.id}`);
      
      // Aggiorna lo stato locale
      setTriggers(triggers.filter(t => t.id !== selectedTrigger.id));
      
      toast({
        title: 'Trigger eliminato',
        description: 'Il trigger è stato eliminato con successo.',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      
      onDeleteClose();
    } catch (error) {
      console.error('Errore nell\'eliminazione del trigger:', error);
      toast({
        title: 'Errore',
        description: 'Impossibile eliminare il trigger.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };

  // Gestisce la chiusura del form e il refresh dei dati
  const handleFormClose = (refreshNeeded = false) => {
    onFormClose();
    if (refreshNeeded) {
      setRefreshKey(prev => prev + 1);
    }
  };

  // Gestisce la chiusura del form delle condizioni e il refresh dei dati
  const handleConditionsClose = (refreshNeeded = false) => {
    onConditionsClose();
    if (refreshNeeded) {
      setRefreshKey(prev => prev + 1);
    }
  };

  // Ottiene il nome del workflow per un dato ID
  const getWorkflowName = (workflowId) => {
    const workflow = workflows.find(w => w.id === workflowId);
    return workflow ? workflow.name : workflowId;
  };

  // Ottiene il colore del badge in base al tipo di evento
  const getEventTypeColor = (eventType) => {
    const colorMap = {
      'pdf_upload': 'blue',
      'file_created': 'green',
      'schedule': 'purple',
      'api_call': 'orange',
      'document_processed': 'teal'
    };
    return colorMap[eventType] || 'gray';
  };

  // Rendering della pagina
  return (
    <Box p={4}>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading size="lg">Associazioni Eventi-Workflow</Heading>
        <Button leftIcon={<AddIcon />} colorScheme="blue" onClick={handleNewTrigger}>
          Nuovo Trigger
        </Button>
      </Flex>
      
      {loading ? (
        <Flex justify="center" align="center" h="200px">
          <Spinner size="xl" />
        </Flex>
      ) : triggers.length === 0 ? (
        <Alert status="info" borderRadius="md">
          <AlertIcon />
          <VStack align="start" spacing={2}>
            <Text>Nessun trigger configurato.</Text>
            <Text fontSize="sm">
              I trigger permettono di associare eventi (come l'upload di un PDF) a specifici workflow.
              Clicca su "Nuovo Trigger" per creare la tua prima associazione.
            </Text>
          </VStack>
        </Alert>
      ) : (
        <Box overflowX="auto">
          <Table variant="simple" borderWidth="1px" borderRadius="md">
            <Thead bg="gray.50">
              <Tr>
                <Th>Nome</Th>
                <Th>Tipo Evento</Th>
                <Th>Sorgente</Th>
                <Th>Workflow</Th>
                <Th>Condizioni</Th>
                <Th>Stato</Th>
                <Th>Azioni</Th>
              </Tr>
            </Thead>
            <Tbody>
              {triggers.map((trigger) => (
                <Tr key={trigger.id}>
                  <Td fontWeight="medium">{trigger.name}</Td>
                  <Td>
                    <Badge colorScheme={getEventTypeColor(trigger.event_type)}>
                      {trigger.event_type}
                    </Badge>
                  </Td>
                  <Td>{trigger.source}</Td>
                  <Td>{getWorkflowName(trigger.workflow_id)}</Td>
                  <Td>
                    <HStack>
                      {Object.keys(trigger.conditions || {}).length > 0 ? (
                        <>
                          <Badge colorScheme="purple">{Object.keys(trigger.conditions).length} filtri</Badge>
                          <IconButton
                            aria-label="Modifica condizioni"
                            icon={<FaFilter />}
                            size="sm"
                            variant="ghost"
                            onClick={() => handleEditConditions(trigger)}
                          />
                        </>
                      ) : (
                        <Text fontSize="sm" color="gray.500">Nessun filtro</Text>
                      )}
                    </HStack>
                  </Td>
                  <Td>
                    <Badge 
                      colorScheme={trigger.active ? 'green' : 'red'}
                      cursor="pointer"
                      onClick={() => handleToggleActive(trigger.id, trigger.active)}
                    >
                      {trigger.active ? 'Attivo' : 'Inattivo'}
                    </Badge>
                  </Td>
                  <Td>
                    <Menu>
                      <MenuButton
                        as={IconButton}
                        aria-label="Opzioni"
                        icon={<SettingsIcon />}
                        variant="outline"
                        size="sm"
                      />
                      <MenuList>
                        <MenuItem icon={<EditIcon />} onClick={() => handleEditTrigger(trigger)}>
                          Modifica
                        </MenuItem>
                        <MenuItem icon={<FaFilter />} onClick={() => handleEditConditions(trigger)}>
                          Condizioni
                        </MenuItem>
                        <MenuItem 
                          icon={trigger.active ? <CloseIcon /> : <CheckIcon />}
                          onClick={() => handleToggleActive(trigger.id, trigger.active)}
                        >
                          {trigger.active ? 'Disattiva' : 'Attiva'}
                        </MenuItem>
                        <MenuItem icon={<DeleteIcon />} onClick={() => handleDeleteClick(trigger)}>
                          Elimina
                        </MenuItem>
                      </MenuList>
                    </Menu>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      )}
      
      {/* Modal per la creazione/modifica dei trigger */}
      <TriggerFormModal
        isOpen={isFormOpen}
        onClose={handleFormClose}
        trigger={selectedTrigger}
        workflows={workflows}
      />
      
      {/* Modal per la modifica delle condizioni */}
      <TriggerConditionsModal
        isOpen={isConditionsOpen}
        onClose={handleConditionsClose}
        trigger={selectedTrigger}
      />
      
      {/* Modal di conferma eliminazione */}
      <DeleteConfirmationModal
        isOpen={isDeleteOpen}
        onClose={onDeleteClose}
        onConfirm={handleDeleteConfirm}
        title="Elimina Trigger"
        message={`Sei sicuro di voler eliminare il trigger "${selectedTrigger?.name}"? Questa azione non può essere annullata.`}
      />
    </Box>
  );
};

export default WorkflowTriggersPage;
