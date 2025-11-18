import React, { useState, useEffect, useCallback } from 'react';
import { endpoints } from './services/api';
import LayoutWithSidebar from './layout/LayoutWithSidebar.js';
import { useNavigate, useLocation, Routes, Route, Navigate } from 'react-router-dom';

// Importa i componenti di pagina originali
import ChatPage from './pages/ChatPage.js'; // Ora importa il ChatPage completo
import DocumentPage from './pages/DocumentPage.js';
import HistoryPage from './pages/HistoryPage.js';
import DashboardPage from './pages/DashboardPage.js';
import UserManagementPage from './pages/UserManagementPage.js'; // Importa il nuovo componente
import NotebooksRoutePage from './pages/NotebooksRoutePage.js';
import WorkflowPage from './pages/WorkflowPage.js'; // Importa la pagina workflow
import WorkflowListPage from './pages/WorkflowListPage.js'; // Importa la pagina lista workflow
import WorkflowManagementPage from './pages/WorkflowManagementPage.js';
import WorkflowTriggersPage from './pages/WorkflowTriggersPage.jsx'; // Importa la pagina dei trigger workflow
import TriggerTestPage from './pages/TriggerTestPage.jsx'; // Importa la pagina di test trigger
import DocumentManagementPage from './pages/DocumentManagementPage.js'; // Importa la pagina gestione documenti

// Log per debug del tipo di ChatPage
console.log("AppContent: Importing ChatPage. Type:", typeof ChatPage); // Rimosso Value per brevità
console.log("AppContent: Importing DocumentPage. Type:", typeof DocumentPage);
console.log("AppContent: Importing HistoryPage. Type:", typeof HistoryPage);
console.log("AppContent: Importing UserManagementPage. Type:", typeof UserManagementPage);
console.log("AppContent: Importing DashboardPage. Type:", typeof DashboardPage);

function AppContent({ currentUserRole, currentUser, onLogout }) {
  
  const [indexedFile, setIndexedFile] = useState(null);
  // Rimosso lo stato locale per currentUserRole, ora viene passato come prop
  // const [currentUserRole, setCurrentUserRole] = useState(localStorage.getItem('user_role') || '');

  const navigate = useNavigate();
  // eslint-disable-next-line no-unused-vars
  const location = useLocation(); // location è usata solo per il debug log, può essere rimossa se non serve altrove

  // Spostato fetchStatus prima di useEffect e avvolto in useCallback
  const fetchStatus = useCallback(async () => {
    try {
      const res = await endpoints.documents.status();
      if (res.data.status === 'ok') {
        setIndexedFile(res.data.filename);
      } else {
        setIndexedFile(null);
      }
    } catch (error) {
      setIndexedFile(null);
      if (error.response?.status === 401) {
        // Se il token non è valido o è scaduto, la chiamata fallisce con 401.
        // Invece di reindirizzare manualmente, usiamo la funzione onLogout
        // passata da App.js per gestire centralmente il logout.
        console.error("Errore di autenticazione (401) in fetchStatus:", error.response.data || error.message);
        onLogout();
      } else {
        console.error("Errore in fetchStatus:", error);
      }
    }
  }, [onLogout]); // La dipendenza ora è onLogout


  useEffect(() => {
    // La logica di autenticazione e reindirizzamento è ora centralizzata in App.js.
    // AppContent viene renderizzato solo se l'utente è autenticato.
    // Questo useEffect ora si occupa solo di impostare l'header per le chiamate API
    // e di caricare lo stato iniziale (es. fetchStatus).

    const token = localStorage.getItem("token"); // <-- CHIAVE CORRETTA
    if (!token) {
      // Questo caso non dovrebbe accadere grazie al controllo in App.js, ma è una sicurezza aggiuntiva.
      console.error("AppContent renderizzato senza token, reindirizzamento forzato.");
      onLogout(); // Usa la funzione di logout per pulire lo stato
      return;
    }

    fetchStatus();
  }, [fetchStatus, currentUserRole, onLogout]); // Aggiornate le dipendenze

  const handleNavigation = (newView) => {
    navigate(`/app/${newView}`);
  };

  // Rimosso handleLogout, ora viene passato come prop da App.js
  // const handleLogout = () => { ... };

  return (
    <LayoutWithSidebar
      onNavigate={handleNavigation}
      currentUserRole={currentUserRole}
      currentUser={currentUser}
      onLogout={onLogout}
    >
      <Routes>
        <Route path="chat" element={<ChatPage indexedFile={indexedFile} />} />
        <Route path="notebooks" element={<NotebooksRoutePage />} />
        <Route path="workflows" element={<WorkflowListPage />} />
        <Route path="workflows/:id" element={<WorkflowPage />} />
        <Route path="workflows/new" element={<WorkflowPage />} />
        <Route path="documenti" element={<DocumentPage />} />
        <Route path="document-management" element={<DocumentManagementPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="dashboard" element={<DashboardPage />} />
        {currentUserRole === 'admin' && <Route path="admin/users" element={<UserManagementPage />} />}
        {currentUserRole === 'admin' && <Route path="admin/workflows" element={<WorkflowManagementPage />} />}
        {currentUserRole === 'admin' && <Route path="admin/triggers" element={<WorkflowTriggersPage />} />}
        <Route path="test/trigger-nodes" element={<TriggerTestPage />} />
        <Route index element={<Navigate to="chat" replace />} />
        <Route path="*" element={<Navigate to="chat" replace />} />
      </Routes>
    </LayoutWithSidebar>
  );
}

export default AppContent;
