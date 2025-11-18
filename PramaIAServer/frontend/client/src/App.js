// c:\Users\fabmi\OneDrive\Desktop\PramaIA 2.0\frontend\client\src\App.js
import React, { useEffect, useState, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { ChakraProvider, extendTheme } from '@chakra-ui/react';
import LoginPage from './LoginPage';
import RegisterPage from './RegisterPage'; // Importa la pagina di registrazione
import AppContent from './AppContent';
import { endpoints } from './services/api';
import { decodeJwtPayload } from './utils/authUtils';

console.log('[DEBUG] App.js caricato');

// Tema personalizzato per Chakra UI con z-index values più alti per le modali
const customTheme = extendTheme({
  components: {
    Modal: {
      baseStyle: {
        dialog: {
          zIndex: 15000, // Molto alto per assicurarsi che le modali siano sopra tutto
        },
        overlay: {
          zIndex: 14999, // Appena sotto il dialog
        },
      },
    },
    Tooltip: {
      baseStyle: {
        zIndex: 13000, // Più basso delle modali ma alto per altri elementi
      },
    },
    Popover: {
      baseStyle: {
        content: {
          zIndex: 12000,
        },
      },
    },
    Menu: {
      baseStyle: {
        list: {
          zIndex: 11000,
        },
      },
    },
  },
  // Z-index tokens personalizzati
  zIndices: {
    hide: -1,
    auto: 'auto',
    base: 0,
    docked: 10,
    dropdown: 1000,
    sticky: 1100,
    banner: 1200,
    overlay: 1300,
    modal: 1400,
    popover: 1500,
    skipLink: 1600,
    toast: 1700,
    tooltip: 1800,
  },
});

// Hook per gestire lo stato di autenticazione e utente
const useAuth = () => {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [currentUser, setCurrentUser] = useState(null);
  const [loadingAuth, setLoadingAuth] = useState(true); // Inizia come true

  const fetchUserDetails = useCallback(async (authToken) => {
    console.log('[AUTH] fetchUserDetails chiamato con token:', authToken);
    if (!authToken) {
      setCurrentUser(null);
      setLoadingAuth(false);
      return;
    }
    try {
      const response = await endpoints.protected.me();
      const userData = response.data;
      const decodedPayload = decodeJwtPayload(authToken);
      setCurrentUser({ ...userData, role: decodedPayload?.role || 'user' });
      console.log('[AUTH] User details caricati:', userData);
    } catch (error) {
      console.error('[AUTH] Errore nel recupero dei dettagli utente:', error);
      localStorage.removeItem('token');
      localStorage.removeItem('userRole');
      setToken(null);
      setCurrentUser(null);
    } finally {
      setLoadingAuth(false);
    }
  }, []);

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    console.log('[AUTH] useEffect: token in localStorage:', storedToken);
    if (storedToken) {
      setToken(storedToken);
      fetchUserDetails(storedToken);
    } else {
      setLoadingAuth(false); // Nessun token, autenticazione non necessaria, smetti di caricare
    }
  }, [fetchUserDetails]);

  const updateUser = useCallback((newToken) => {
    console.log('[AUTH] updateUser chiamato con:', newToken);
    if (newToken) {
      localStorage.setItem('token', newToken);
      const decodedPayload = decodeJwtPayload(newToken);
      if (decodedPayload && decodedPayload.role) {
        localStorage.setItem('userRole', decodedPayload.role);
      }
      setToken(newToken);
      setLoadingAuth(true);
      const justSaved = localStorage.getItem('token');
      console.log('[AUTH] Token appena salvato in localStorage:', justSaved);
      fetchUserDetails(newToken);
      // RIMOSSO: redirect forzato con window.location.replace
    } else {
      // Logout
      localStorage.removeItem('token');
      localStorage.removeItem('userRole');
      setToken(null);
      setCurrentUser(null);
    }
  }, [fetchUserDetails]); // fetchUserDetails è già memoizzato

  const logout = useCallback(() => {
    updateUser(null); // Chiama updateUser con null per gestire il logout
  }, [updateUser]); // updateUser è ora memoizzato

  return { token, currentUser, loadingAuth, updateUser, logout };
};


// Componente per gestire il reindirizzamento iniziale e catturare il token dall'URL
function RootPathHandler({ updateUser }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [processed, setProcessed] = useState(false);

  useEffect(() => {
    if (processed) return;

    const params = new URLSearchParams(location.search);
    const urlToken = params.get('token');

    if (urlToken) {
      updateUser(urlToken);
      // Rimuovi il token dall'URL e reindirizza per pulire la barra degli indirizzi
      // e per assicurare che AppContent venga renderizzato con il token corretto
      navigate(location.pathname, { replace: true });
    }
    setProcessed(true);
  }, [location, navigate, updateUser, processed]);

  return null; // Questo componente non renderizza nulla
}

function AuthRedirect({ token }) {
  const navigate = useNavigate();
  useEffect(() => {
    if (token && window.location.pathname === '/login') {
      console.log('[DEBUG] Navigazione automatica a /app/chat dopo login');
      navigate('/app/chat', { replace: true });
    }
  }, [token, navigate]);
  return null;
}

function App() {
  console.log('[DEBUG] Funzione App eseguita');
  const auth = useAuth();

  if (auth.loadingAuth && !auth.token) {
    return (
      <ChakraProvider theme={customTheme}>
        <div className="flex justify-center items-center h-screen">
          <p>Caricamento...</p>
        </div>
      </ChakraProvider>
    );
  }

  return (
    <ChakraProvider theme={customTheme}>
      <Router>
        <AuthRedirect token={auth.token} />
        <RootPathHandler updateUser={auth.updateUser} />
        <Routes>
          <Route
            path="/login"
            element={
              auth.token ? (
                <Navigate to="/app/chat" replace />
              ) : (
                <LoginPage onLoginSuccess={auth.updateUser} />
              )
            }
          />
          <Route
            path="/register"
            element={
              auth.token ? (
                <Navigate to="/app/chat" replace />
              ) : (
                <RegisterPage />
              )
            }
          />
          <Route
            path="/app/*"
            element={auth.token ? <AppContent currentUserRole={auth.currentUser?.role} onLogout={auth.logout} /> : <Navigate to="/login" replace />}
          />
          {/* La rotta radice reindirizza in base allo stato del token */}
          <Route path="/" element={auth.token ? <Navigate to="/app/chat" replace /> : <Navigate to="/login" replace />} />
          <Route path="*" element={<Navigate to={auth.token ? "/app/chat" : "/login"} replace />} /> {/* Fallback per rotte non trovate */}
        </Routes>
      </Router>
    </ChakraProvider>
  );
}

export default App;
