import React, { useState } from 'react';
import NotebooksPage from '../components/NotebooksPage.jsx';
import RAGChat from '../components/RAGChat.jsx';

function NotebooksRoutePage() {
  const [openSessionId, setOpenSessionId] = useState(null);

  if (openSessionId) {
    // Mostra la chat notebook selezionata (puoi passare openSessionId come prop)
    return <RAGChat sessionId={openSessionId} onBack={() => setOpenSessionId(null)} />;
  }

  return <NotebooksPage onOpenNotebook={setOpenSessionId} />;
}

export default NotebooksRoutePage;
