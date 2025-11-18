import React, { useState, useEffect } from 'react';
import axios from 'axios';
import config from '../config';
import NotebookSourcesManager from './NotebookSourcesManager';

function RAGChat({ sessionId: initialSessionId, onBack }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [showSourcesManager, setShowSourcesManager] = useState(false);
  const [sessionId, setSessionId] = useState(initialSessionId);
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    // Se non c'è sessionId, crea una nuova sessione
    if (!initialSessionId) {
      setIsCreating(true);
      
      const createSession = async () => {
        try {
          console.log('Creating new session...');
          const token = localStorage.getItem('token');
          const res = await axios.post(`${config.BACKEND_URL}/chat/ask/`, {
            question: 'init',
            model: 'gpt-4',
            mode: 'rag',
            documents: [],
            system_prompt: 'Benvenuto nel nuovo notebook!',
            title: 'Nuovo Notebook'
          }, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          console.log('Session created:', res.data);
          
          if (res.data.session_id) {
            // Verifica che la sessione sia pronta
            const checkStatus = async () => {
              try {
                const token = localStorage.getItem('token');
                const statusRes = await axios.get(
                  `${config.BACKEND_URL}/sessions/${res.data.session_id}/status`,
                  { headers: { 'Authorization': `Bearer ${token}` } }
                );
                return statusRes.data.status === 'ready';
              } catch (error) {
                console.error('Error checking session status:', error);
                return false;
              }
            };

            // Riprova fino a 5 volte con intervallo crescente
            for (let i = 0; i < 5; i++) {
              const isReady = await checkStatus();
              if (isReady) {
                setSessionId(res.data.session_id);
                break;
              }
              if (i < 4) { // non aspettare dopo l'ultimo tentativo
                await new Promise(resolve => setTimeout(resolve, 100 * Math.pow(2, i))); // 100ms, 200ms, 400ms, 800ms, 1600ms
              }
            }
          }
        } catch (error) {
          console.error('Errore creazione sessione:', error);
        } finally {
          setIsCreating(false);
        }
      };
      createSession();
    } else {
      setSessionId(initialSessionId);
    }
  }, [initialSessionId]);

  useEffect(() => {
    // Carica solo le fonti collegate a questa sessione
    fetchLinkedSources();
  }, [sessionId]);

  const fetchLinkedSources = async () => {
    if (sessionId) {
      console.log('Fetching sources for session:', sessionId);
      const token = localStorage.getItem('token');
      try {
        const res = await axios.get(`${config.BACKEND_URL}/sessions/${sessionId}/sources`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        console.log('Sources response:', res.data);
        setSelectedDocs(res.data || []);
      } catch (error) {
        console.error('Error fetching sources:', error.response?.status, error.response?.data);
        console.error('Full error:', error);
        setSelectedDocs([]);
      }
    } else {
      console.log('No sessionId available yet');
    }
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    setIsLoading(true);
    setMessages(msgs => [...msgs, { sender: 'user', text: input }]);
    try {
      const token = localStorage.getItem('token');
      const res = await axios.post(`${config.BACKEND_URL}/chat/ask/`, {
        question: input,
        model: 'gpt-4o', // o altro modello RAG
        mode: 'rag',
        documents: selectedDocs, // opzionale: backend deve supportare
        session_id: sessionId
      }, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setMessages(msgs => [...msgs, { sender: 'bot', text: res.data.answer, source: res.data.source }]);
    } catch {
      setMessages(msgs => [...msgs, { sender: 'bot', text: 'Errore nella richiesta.', isError: true }]);
    } finally {
      setIsLoading(false);
      setInput('');
    }
  };

  const handleSourcesManagerClose = () => {
    setShowSourcesManager(false);
    fetchLinkedSources(); // Ricarica le fonti dopo la chiusura del modale
  };

  if (isCreating) {
    return (
      <div className="p-4 flex flex-col items-center justify-center min-h-screen">
        <div className="mb-4">Creazione nuovo notebook in corso...</div>
        <button onClick={onBack} className="bg-gray-200 hover:bg-gray-300 px-4 py-2 rounded">
          Annulla
        </button>
      </div>
    );
  }

  return (
    <div className="p-4 bg-gray-100 min-h-screen">
      <h2 className="text-xl font-bold mb-4 text-blue-700">Chat con Fonti Interne</h2>
      <div className="mb-4 bg-white p-4 rounded shadow flex items-center justify-between">
        <div>
          <h3 className="font-semibold mb-2">Fonti collegate</h3>
          <div className="flex flex-wrap gap-2 mb-2">
            {selectedDocs.length ? selectedDocs.map(doc => (
              <span key={typeof doc === 'object' ? doc.filename : doc} className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                {typeof doc === 'object' ? doc.filename : doc}
              </span>
            )) : <span className="text-gray-400">Nessuna fonte selezionata</span>}
          </div>
        </div>
        <div className="flex gap-2">
          <button 
            className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded" 
            onClick={() => setShowSourcesManager(true)}
          >
            📂 Gestisci fonti
          </button>
          <button 
            className="bg-green-500 hover:bg-green-600 text-white px-3 py-2 rounded" 
            onClick={() => {
              setInput('');
              alert('Notebook salvato automaticamente!');
            }}
            title="Il notebook viene salvato automaticamente ad ogni interazione"
          >
            💾 Salvato
          </button>
        </div>
      </div>
      <div className="bg-white p-4 rounded shadow mb-4 min-h-[300px]">
        {messages.map((msg, i) => (
          <div key={i} className={`mb-2 p-2 rounded ${msg.sender === 'user' ? 'bg-blue-100 text-right' : msg.isError ? 'bg-red-100 text-red-700' : 'bg-gray-100'}`}>
            <span>{msg.text}</span>
            {msg.source && <span className="ml-2 text-xs text-gray-500">[{msg.source}]</span>}
          </div>
        ))}
        {isLoading && <div className="text-gray-500">Sto pensando...</div>}
      </div>
      <form onSubmit={handleSend} className="flex gap-2">
        <input type="text" value={input} onChange={e => setInput(e.target.value)} className="flex-grow p-2 border rounded" placeholder="Scrivi la tua domanda..." disabled={isLoading} />
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded" disabled={isLoading || !input.trim()}>Invia</button>
      </form>
      {onBack && <button className="mt-6 bg-gray-300 px-4 py-2 rounded" onClick={onBack}>Torna ai Notebooks</button>}
      
      {/* Modal per gestione fonti */}
      {showSourcesManager && (
        <NotebookSourcesManager 
          sessionId={sessionId} 
          isOpen={showSourcesManager}
          onClose={handleSourcesManagerClose} 
        />
      )}
    </div>
  );
}

export default RAGChat;
