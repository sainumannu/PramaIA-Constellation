import React from 'react';
import {
  AlertDialog,
  AlertDialogBody,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogContent,
  AlertDialogOverlay,
  Button,
} from '@chakra-ui/react';

const DeleteConfirmationModal = ({ isOpen, onClose, onConfirm, title, message }) => {
  const cancelRef = React.useRef();

  return (
    <AlertDialog
      isOpen={isOpen}
      leastDestructiveRef={cancelRef}
      onClose={onClose}
      blockScrollOnMount={true}
      motionPreset="slideInBottom"
      isCentered
      trapFocus={true}
      preserveScrollBarGap={true}
    >
      <AlertDialogOverlay bg="blackAlpha.600">
        <AlertDialogContent maxW="500px" mx="auto" bg="white" position="relative" zIndex="1">
          <AlertDialogHeader fontSize="lg" fontWeight="bold">
            {title || 'Conferma eliminazione'}
          </AlertDialogHeader>

          <AlertDialogBody>
            {message || 'Sei sicuro di voler eliminare questo elemento? Questa azione non può essere annullata.'}
          </AlertDialogBody>

          <AlertDialogFooter>
            <Button ref={cancelRef} onClick={onClose}>
              Annulla
            </Button>
            <Button colorScheme="red" onClick={onConfirm} ml={3}>
              Elimina
            </Button>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialogOverlay>
    </AlertDialog>
  );
};

export default DeleteConfirmationModal;
