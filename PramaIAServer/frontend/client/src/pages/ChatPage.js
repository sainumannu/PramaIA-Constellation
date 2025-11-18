import React from 'react';
import Chat from '../components/Chat.jsx'; // Importa il nuovo componente Chat

function ChatPage({ indexedFile }) { // Assicurati che il nome della funzione sia ChatPage
  return (
    // ChatPage ora renderizza semplicemente il componente Chat,
    // passando la prop indexedFile se necessario.
    // Tutta la logica della chat (stato, invio messaggi, localStorage)
    // dovrebbe essere gestita all'interno di Chat.jsx
    <Chat indexedFile={indexedFile} />
  );
}

export default ChatPage; // Assicurati che sia esportato correttamente
