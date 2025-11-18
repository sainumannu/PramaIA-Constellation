import React from 'react';
import { Navigate } from 'react-router-dom';

/**
 * AdminRoute è un componente che protegge le rotte,
 * rendendole accessibili solo agli utenti autenticati con ruolo 'admin'.
 * @param {object} props - Le props del componente.
 * @param {React.ReactNode} props.children - I componenti figli da renderizzare se l'utente è autorizzato.
 * @param {object} props.currentUser - L'oggetto utente corrente.
 * @param {string} props.currentUser.role - Il ruolo dell'utente corrente.
 * @param {boolean} props.loadingAuth - Flag che indica se l'autenticazione è in corso.
 */
function AdminRoute({ children, currentUser, loadingAuth }) {
  if (loadingAuth) {
    return <p>Verifica autenticazione in corso...</p>;
  }

  if (!currentUser || currentUser.role !== 'admin') {
    return <Navigate to="/app/chat" replace />; // O reindirizza a una pagina di login/non autorizzato
  }
  return children;
}

export default AdminRoute;
