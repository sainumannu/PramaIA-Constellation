import React, { useEffect, useState, useCallback } from "react";
import axios from "axios";
import config from '../config';

function ChatHistory() {
  const [history, setHistory] = useState({});
  const [loading, setLoading] = useState(true); // Stato per il caricamento
  const [error, setError] = useState(''); // Stato per gli errori
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [selectedUser, setSelectedUser] = useState("");
  const [availableUsers, setAvailableUsers] = useState([]);
  const [role, setRole] = useState("");

  // Stati per la paginazione delle sessioni
  const [currentPage, setCurrentPage] = useState(1);
  const [sessionsPerPage] = useState(5); // Numero di sessioni per pagina
  // Stati per la selezione dei messaggi
  const [selectedMessages, setSelectedMessages] = useState({}); // Oggetto: { "sessionId_timestamp": true }
  const [sortByTokens, setSortByTokens] = useState(null); // null, 'asc', 'desc'
  const [sortByTime, setSortByTime] = useState(null); // null, 'asc', 'desc'

  useEffect(() => {
    fetchUserRole(); // Chiama per ottenere il ruolo e gli utenti disponibili se admin
    // fetchHistory sarà chiamato dopo fetchUserRole o al click del filtro
  }, []);


  const fetchUserRole = async () => {
    try {
      const res = await axios.get(`${config.BACKEND_URL}/protected/me`);
      setRole(res.data.role);
      if (res.data.role === "admin") {
        const usageSummaryRes = await axios.get(`${config.BACKEND_URL}/usage/all/`);
        const users = usageSummaryRes.data.map(item => item.user_id);
        setAvailableUsers([...new Set(users)]);
      }
    } catch (err) {
      console.error("Errore nel recupero del ruolo utente o degli utenti:", err);
      setError(err.response?.data?.detail || 'Impossibile determinare il ruolo utente o caricare la lista utenti.');
    }
  };

  const fetchHistory = useCallback(async () => {
    try {
      setLoading(true);
      setError('');
      const params = {};
      if (fromDate) params.from_date = fromDate;
      if (toDate) params.to_date = toDate;
      if (role === "admin" && selectedUser) {
        params.target_user = selectedUser;
      }
      const res = await axios.get(`${config.BACKEND_URL}/sessions/history`, { params });
      setHistory(res.data || {});
      setCurrentPage(1);
    } catch (err) {
      console.error("Errore caricamento cronologia:", err.response?.data || err.message);
      setError(err.response?.data?.detail || 'Impossibile caricare la cronologia.');
      setHistory({});
    } finally {
      setLoading(false);
    }
  }, [role, selectedUser, fromDate, toDate]);

  useEffect(() => {
    // Chiama fetchHistory solo dopo che il ruolo è stato determinato,
    // per caricare la cronologia iniziale (dell'utente corrente o tutti per admin se nessun filtro utente)
    // o se fetchHistory stesso cambia (a causa delle sue dipendenze come i filtri)
    if (role) {
        fetchHistory();
    }
  }, [role, fetchHistory]); // Ora include fetchHistory

  // Logica per la paginazione delle sessioni
  const sessionIds = Object.keys(history);
  const indexOfLastSession = currentPage * sessionsPerPage;
  const indexOfFirstSession = indexOfLastSession - sessionsPerPage;

  // Funzione per ordinare le sessioni
  const sortedSessionIds = [...sessionIds].sort((a, b) => {
    // Ordinamento per ora (timestamp primo messaggio della sessione)
    if (sortByTime) {
      const aTime = history[a]?.[0]?.timestamp ? new Date(history[a][0].timestamp).getTime() : 0;
      const bTime = history[b]?.[0]?.timestamp ? new Date(history[b][0].timestamp).getTime() : 0;
      if (sortByTime === 'asc') return aTime - bTime;
      if (sortByTime === 'desc') return bTime - aTime;
    }
    // Ordinamento per token
    const aTokens = history[a]?.reduce((sum, entry) => sum + (entry.tokens || 0), 0);
    const bTokens = history[b]?.reduce((sum, entry) => sum + (entry.tokens || 0), 0);
    if (sortByTokens === 'asc') return aTokens - bTokens;
    if (sortByTokens === 'desc') return bTokens - aTokens;
    return 0;
  });
  const currentSessionIds = sortedSessionIds.slice(indexOfFirstSession, indexOfLastSession);

  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  // Logica per la selezione dei messaggi
  const getMessageId = (sessionId, entryTimestamp) => `${sessionId}___${entryTimestamp}`;

  const handleSelectMessage = (sessionId, entryTimestamp) => {
    const messageId = getMessageId(sessionId, entryTimestamp);
    setSelectedMessages(prev => ({
      ...prev,
      [messageId]: !prev[messageId]
    }));
  };

  const handleSelectAllVisible = () => {
    const newSelectedMessages = { ...selectedMessages };
    let allCurrentlySelected = true;

    // Controlla se tutti i messaggi visibili sono già selezionati
    currentSessionIds.forEach(sid => {
      if (history[sid]) { // Assicurati che la sessione esista
        history[sid].forEach(entry => {
          const msgId = getMessageId(sid, entry.timestamp);
          if (!selectedMessages[msgId]) {
            allCurrentlySelected = false;
          }
        });
      }
    });

    // Se tutti sono già selezionati, deselezionali tutti. Altrimenti, seleziona tutti.
    currentSessionIds.forEach(sid => {
      if (history[sid]) {
        history[sid].forEach(entry => {
          const msgId = getMessageId(sid, entry.timestamp);
          newSelectedMessages[msgId] = !allCurrentlySelected;
        });
      }
    });
    setSelectedMessages(newSelectedMessages);
  };

  const handleDeleteSelectedMessages = async () => {
    const messagesToDelete = Object.keys(selectedMessages).filter(k => selectedMessages[k]);
    if (messagesToDelete.length === 0) {
      setError("Nessun messaggio selezionato per l'eliminazione.");
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await axios.delete(`${config.BACKEND_URL}/sessions/delete_entries`, {
        data: messagesToDelete,
      });
      console.log(response.data.message);
      setSelectedMessages({});
      fetchHistory();
    } catch (err) {
      console.error("Errore durante l'eliminazione dei messaggi:", err.response?.data || err.message);
      setError(err.response?.data?.detail || "Impossibile eliminare i messaggi selezionati.");
    } finally {
      setLoading(false);
    }
  };

  const renderSessions = () => {
    if (loading) {
      return <p className="text-center text-gray-500 py-4">Caricamento cronologia...</p>;
    }

    if (error && sessionIds.length === 0) { // Mostra errore solo se non ci sono dati da visualizzare
      return <p className="text-center text-red-500 py-4">{error}</p>;
    }

    if (currentSessionIds.length === 0 && sessionIds.length > 0 && !loading) { // Se ci sono sessioni totali ma nessuna per la pagina corrente
        return <p className="text-center text-gray-600 py-4">Nessuna sessione in questa pagina. Prova una pagina precedente.</p>;
    } else if (sessionIds.length === 0 && !loading) { // Nessuna sessione in assoluto
      return (
        <div className="bg-white p-6 rounded-lg shadow text-center">
          <p className="text-gray-600 text-lg">Nessuna sessione trovata per i filtri selezionati.</p>
          {role !== "admin" && <p className="text-sm text-gray-500 mt-2">Inizia una nuova chat per vedere la tua cronologia qui.</p>}
        </div>
      );
    }

    return currentSessionIds.map((sessionId) => {
      const entries = history[sessionId];
      if (!entries || entries.length === 0) return null; // Salta sessioni vuote se dovessero esistere

      const sessionUserId = entries[0]?.user_id;

      return (
      <div key={sessionId} className="border rounded p-4 mb-6 bg-white shadow-md hover:shadow-lg transition-shadow">
        <div className="flex justify-between items-center border-b pb-2 mb-3">
            <h4 className="font-semibold text-lg text-blue-600">
            Sessione: <span className="font-mono text-sm">{sessionId === 'unknown' ? 'Senza ID' : sessionId}</span>
            </h4>
            {role === "admin" && !selectedUser && sessionUserId && (
                <span className="text-xs text-gray-500">Utente: {sessionUserId}</span>
            )}
        </div>
        <div className="text-sm text-blue-700 mb-2">
          Totale token sessione: {entries.reduce((sum, entry) => sum + (entry.tokens || 0), 0)}
        </div>
        {entries.map((entry, index) => {
          const messageId = getMessageId(sessionId, entry.timestamp);
          return (
            <div key={messageId} className={`p-3 rounded-md mb-2 flex items-start ${selectedMessages[messageId] ? 'bg-blue-100 border border-blue-300' : (index % 2 === 0 ? 'bg-blue-50' : 'bg-gray-50')}`}>
              <input
                type="checkbox"
                className="mr-3 mt-1 h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                checked={!!selectedMessages[messageId]}
                onChange={() => handleSelectMessage(sessionId, entry.timestamp)}
              />
              <div className="flex-1">
                <div className="mb-1"><strong className="text-gray-700">🧑 Domanda:</strong> {entry.prompt}</div>
                <div><strong className="text-gray-700">🤖 Risposta:</strong> {entry.answer || <span className="italic text-gray-400">Nessuna risposta registrata</span>}</div>
                <div className="text-xs text-gray-500 mt-1">
                  {new Date(entry.timestamp).toLocaleString()} – Tokens: {entry.tokens || 0} – Sorgente: {entry.source || 'N/D'}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    )});
  };

  const numSelectedMessages = Object.values(selectedMessages).filter(Boolean).length;

  const PaginationControls = () => {
    const pageNumbers = [];
    for (let i = 1; i <= Math.ceil(sessionIds.length / sessionsPerPage); i++) {
      pageNumbers.push(i);
    }
    if (pageNumbers.length <= 1) return null;

    return (
      <nav className="mt-6 flex justify-center">
        <ul className="inline-flex items-center -space-x-px">
          {pageNumbers.map(number => (
            <li key={number}>
              <button
                onClick={() => paginate(number)}
                className={`py-2 px-3 leading-tight ${currentPage === number ? 'bg-blue-500 text-white hover:bg-blue-600' : 'bg-white text-blue-500 border border-gray-300 hover:bg-gray-100 hover:text-gray-700'}`}
              >{number}</button>
            </li>
          ))}
        </ul>
      </nav>
    );
  }


  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h2 className="text-2xl font-bold mb-6 text-blue-700">🕓 Cronologia Conversazioni</h2>
      {/* Pulsante svuota cronologia */}
      <div className="mb-4 flex flex-row gap-2 items-center">
        <button
          className="bg-red-500 hover:bg-red-600 text-white px-5 py-2 rounded-md shadow"
          onClick={() => {
            if (window.confirm('Sei sicuro di voler svuotare tutta la cronologia delle sessioni?')) {
              setHistory({});
              setSelectedMessages({});
            }
          }}
        >
          Svuota cronologia
        </button>
      </div>
      <div className="mb-6 p-4 bg-white rounded-lg shadow flex flex-wrap gap-4 items-center">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Dal:</label>
          <input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} className="form-input p-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Al:</label>
          <input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} className="form-input p-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" />
        </div>
        {role === "admin" && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Utente:</label>
            <select className="form-select ml-2 p-2 border rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500" value={selectedUser} onChange={(e) => setSelectedUser(e.target.value)}>
              <option value="">-- Tutti gli Utenti --</option>
              {availableUsers.map((user) => (
                <option key={user} value={user}>{user}</option>
              ))}
            </select>
          </div>
        )}
        <div className="self-end pt-4 md:pt-0">
          <button className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-md shadow-sm" onClick={fetchHistory}>Filtra</button>
        </div>
      </div>
      {sessionIds.length > 0 && !loading && (
        <div className="mb-4 flex justify-between items-center">
          <div>
            <button
              onClick={handleSelectAllVisible}
              className="bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-2 rounded-md text-sm"
            >
              { Object.values(selectedMessages).filter(Boolean).length === currentSessionIds.reduce((acc, sid) => acc + (history[sid]?.length || 0), 0) && currentSessionIds.length > 0 ? 'Deseleziona Tutti i Visibili' : 'Seleziona Tutti i Visibili'}
            </button>
          </div>
          {numSelectedMessages > 0 && (
            <button
              className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-md text-sm"
              onClick={handleDeleteSelectedMessages}
            >
              Elimina {numSelectedMessages} Messaggi Selezionati
            </button>
          )}
        </div>
      )}
      {error && !loading && Object.keys(history).length === 0 && (
         <p className="text-center text-red-500 py-4 bg-red-50 p-3 rounded-md shadow">{error}</p>
      )}
      <div className="space-y-4">
        {/* Opzioni di ordinamento */}
        <div className="mb-2 flex gap-2 items-center">
          <span className="font-semibold">Ordina per:</span>
          <button
            className={`px-3 py-1 rounded ${sortByTokens === 'asc' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            onClick={() => {
              setSortByTokens(sortByTokens === 'asc' ? 'desc' : 'asc');
              setSortByTime(null); // Disattiva ordinamento per ora se si clicca su token
            }}
          >
            Token {sortByTokens === 'asc' ? '▲' : '▼'}
          </button>
          <button
            className={`px-3 py-1 rounded ${sortByTime === 'asc' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            onClick={() => {
              setSortByTime(sortByTime === 'asc' ? 'desc' : 'asc');
              setSortByTokens(null); // Disattiva ordinamento per token se si clicca su ora
            }}
          >
            Ora {sortByTime === 'asc' ? '▲' : '▼'}
          </button>
        </div>
        {renderSessions()}
      </div>
      <PaginationControls />
    </div>
  );
}

export default ChatHistory;
