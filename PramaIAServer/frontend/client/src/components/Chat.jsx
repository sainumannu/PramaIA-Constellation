// Supponiamo che questo sia il tuo frontend/client/src/components/Chat.jsx

import React, { useState, useEffect, useRef } from 'react';
import { endpoints } from '../services/api';
import LLMProviderSelect from './LLMProviderSelect.jsx';
import LLMConfig from './LLMConfig.jsx';
import WorkflowSelector from './WorkflowSelector.jsx';

function Chat() {
  // Stato per i messaggi: prova a caricarli da localStorage o inizia con un array vuoto
  const [messages, setMessages] = useState(() => {
    const savedMessages = localStorage.getItem('chat_messages');
    return savedMessages ? JSON.parse(savedMessages) : [];
  });

  // Stato per l'input dell'utente
  const [input, setInput] = useState('');

  // Stato per l'ID della sessione: prova a caricarlo da localStorage
  const [sessionId, setSessionId] = useState(() => {
    return localStorage.getItem('chat_session_id') || null;
  });

  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null); // Per lo scroll automatico
  const [selectedModel, setSelectedModel] = useState(localStorage.getItem("defaultModel") || "gpt-4o");
  const [firstPrompt, setFirstPrompt] = useState('');
  const [showPromptEditor, setShowPromptEditor] = useState(false);
  const [showSessionInfo, setShowSessionInfo] = useState(false); // Nuovo stato per mostrare/nascondere info sessione
  const [selectedProvider, setSelectedProvider] = useState(localStorage.getItem('llmProvider') || 'openai');
  const [showConfig, setShowConfig] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null); // Nuovo stato workflow

  // Modelli cloud per provider cloud
  const CLOUD_MODEL_OPTIONS = [
    { value: "gpt-4o", label: "GPT-4o" },
    { value: "gpt-4", label: "GPT-4 Turbo" },
    { value: "gpt-3.5-turbo", label: "GPT-3.5 Turbo" },
    // Puoi aggiungere qui altri modelli Anthropic/Gemini se vuoi
  ];
  // Modelli locali per Ollama (dinamico)
  const [ollamaModels, setOllamaModels] = useState([]);
  const [ollamaLoading, setOllamaLoading] = useState(false);
  useEffect(() => {
    if (selectedProvider === 'ollama') {
      setOllamaLoading(true);
      endpoints.chat.ollamaModels()
        .then(res => {
          setOllamaModels(res.data.models || []);
        })
        .catch(() => setOllamaModels([]))
        .finally(() => setOllamaLoading(false));
    }
  }, [selectedProvider]);

  // Effetto per salvare i messaggi in localStorage ogni volta che cambiano
  useEffect(() => {
    localStorage.setItem('chat_messages', JSON.stringify(messages));
  }, [messages]);

  // Effetto per salvare sessionId in localStorage ogni volta che cambia
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem('chat_session_id', sessionId);
    } else {
      // Se sessionId diventa null (es. nuova sessione esplicita), rimuovilo
      localStorage.removeItem('chat_session_id');
    }
  }, [sessionId]);

  // Effetto per salvare il provider LLM selezionato in localStorage
  useEffect(() => {
    localStorage.setItem('llmProvider', selectedProvider);
  }, [selectedProvider]);

  // Effetto per scrollare alla fine quando arrivano nuovi messaggi
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);


  const handleSendMessage = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim()) return;

    const userMessage = { sender: 'user', text: input, timestamp: new Date().toISOString() };
    setMessages(prevMessages => [...prevMessages, userMessage]);

    const currentInput = input;
    setInput('');
    setIsLoading(true);

    try {
      const maxHistory = Number(localStorage.getItem('maxInteractions')) || 100;
      const params = {
        question: currentInput,
        model: selectedModel,
        max_history: maxHistory,
        provider: selectedProvider
      };

      if (sessionId) {
        params.session_id = sessionId;
      } else if (firstPrompt) {
        params.first_prompt = firstPrompt;
      }

      const response = await endpoints.chat.ask(params);
      
      const botMessage = {
        sender: 'bot',
        text: response.data.answer,
        source: response.data.source,
        timestamp: new Date().toISOString(),
        tokens: response.data.tokens
      };
      
      setMessages(prevMessages => [...prevMessages, botMessage]);

      if (response.data.session_id) {
        setSessionId(response.data.session_id);
      }

    } catch (error) {
      console.error('Errore invio messaggio:', error);
      const errorMessage = {
        sender: 'bot',
        text: 'Si è verificato un errore nella comunicazione con il server.',
        isError: true,
        timestamp: new Date().toISOString()
      };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFirstPromptChange = (e) => {
    setFirstPrompt(e.target.value);
  };

  // Funzione per iniziare una nuova chat (opzionale, ma utile)
  const handleNewChat = () => {
    setMessages([]);
    setSessionId(null); // Questo farà sì che localStorage.removeItem('chat_session_id') venga chiamato
    setInput('');
    setFirstPrompt('');
    // localStorage.removeItem('chat_messages'); // Già gestito da setMessages([]) e l'effetto
    // localStorage.removeItem('chat_session_id'); // Già gestito da setSessionId(null) e l'effetto
    console.log("Nuova chat iniziata, stato resettato.");
  };

  const handleModelChange = (e) => {
    setSelectedModel(e.target.value);
    localStorage.setItem("defaultModel", e.target.value);
  };

  // Funzione per svuotare la cronologia locale della chat
  const handleClearHistory = () => {
    setMessages([]);
    localStorage.removeItem('chat_messages');
  };

  return (
    <div className="flex flex-col h-full p-4 bg-gray-100">
      {/* Selezione provider e modello */}
      <div className="mb-6 flex gap-4 items-center">
        <LLMProviderSelect value={selectedProvider} onChange={setSelectedProvider} />
        {selectedProvider === 'ollama' && (
          <button className="ml-2 px-3 py-2 bg-gray-300 rounded" onClick={() => setShowConfig(v => !v)}>
            {showConfig ? 'Nascondi configurazione Ollama' : 'Configura Ollama'}
          </button>
        )}
        <div>
          <label className="mr-2 font-semibold">Modello:</label>
          {selectedProvider === 'ollama' ? (
            ollamaLoading ? <span>Caricamento modelli...</span> :
            <select value={selectedModel} onChange={handleModelChange} className="p-2 border rounded">
              <option value="">-- Seleziona modello --</option>
              {ollamaModels.map(m => <option key={m.name} value={m.name}>{m.name}</option>)}
            </select>
          ) : (
            <select value={selectedModel} onChange={handleModelChange} className="p-2 border rounded">
              {CLOUD_MODEL_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          )}
        </div>
      </div>
      {selectedProvider === 'ollama' && showConfig && <LLMConfig onSave={() => setShowConfig(false)} />}

      {!sessionId && (
        <div className="mb-2">
          <label className="mr-2 font-semibold">Prompt personalizzato:</label>
          <input
            type="text"
            value={firstPrompt}
            onChange={handleFirstPromptChange}
            placeholder="Prompt di sistema per questa chat (opzionale)"
            className="p-2 border rounded w-full"
          />
        </div>
      )}

      {/* Mostra il prompt personalizzato corrente se la sessione è attiva e il prompt è stato impostato */}
      {sessionId && firstPrompt && (
        <div className="mb-2 p-2 bg-yellow-100 border-l-4 border-yellow-400 text-yellow-800 rounded">
          <span className="font-semibold">Prompt di sistema attivo:</span> {firstPrompt}
        </div>
      )}

      {/* Pulsante per Nuova Chat, Svuota Cronologia, Modifica Prompt e Info Sessione */}
      <div className="mb-2 flex flex-row justify-between items-center w-full">
        <div className="flex flex-row gap-2">
          <button
            onClick={handleNewChat}
            className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded"
          >
            Nuova Chat
          </button>
          <button
            onClick={handleClearHistory}
            className="bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-4 rounded"
          >
            Svuota chat
          </button>
        </div>
        <div className="flex flex-row gap-2">
          {sessionId && (
            <>
              <button
                onClick={() => setShowPromptEditor((v) => !v)}
                className="bg-yellow-500 hover:bg-yellow-600 text-white font-bold py-2 px-4 rounded"
              >
                {showPromptEditor ? 'Nascondi prompt' : 'Modifica prompt'}
              </button>
              <button
                onClick={() => setShowSessionInfo((v) => !v)}
                className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded"
              >
                {showSessionInfo ? 'Nascondi info' : 'Info sessione'}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Box per modificare e salvare il prompt personalizzato a sessione attiva - ora subito sotto i pulsanti */}
      {sessionId && showPromptEditor && (
        <div className="mb-4 flex items-center gap-2 p-2 bg-yellow-50 border-l-4 border-yellow-400 rounded">
          <input
            type="text"
            value={firstPrompt}
            onChange={handleFirstPromptChange}
            placeholder="Prompt di sistema per questa chat"
            className="p-2 border rounded flex-grow"
            disabled={isLoading}
          />
          <button
            className="ml-2 px-2 py-1 bg-yellow-500 hover:bg-yellow-600 text-white text-xs rounded"
            onClick={async () => {
              if (!firstPrompt.trim()) return;
              try {
                await endpoints.chat.updatePrompt({
                  session_id: sessionId,
                  new_prompt: firstPrompt
                });
                alert('Prompt aggiornato nel DB!');
              } catch (err) {
                alert('Errore aggiornamento prompt');
              }
            }}
            type="button"
            disabled={isLoading || !firstPrompt.trim()}
            title="Aggiorna prompt nel DB"
          >
            Salva prompt
          </button>
        </div>
      )}

      {/* Mostra Session ID se richiesto */}
      {sessionId && showSessionInfo && (
        <div className="mb-2 flex items-center gap-2 p-2 bg-gray-200 border-l-4 border-blue-400 rounded">
          <span className="font-semibold">Session ID:</span>
          <span className="font-mono text-xs select-all" style={{wordBreak: 'break-all'}}>{sessionId}</span>
          <button
            className="ml-2 px-2 py-1 bg-blue-500 hover:bg-blue-600 text-white text-xs rounded"
            onClick={() => {
              navigator.clipboard.writeText(sessionId);
            }}
            title="Copia Session ID"
            type="button"
          >
            Copia
          </button>
        </div>
      )}

      {/* Workflow Selector - nuovo componente */}
      <WorkflowSelector 
        onWorkflowSelect={setSelectedWorkflow}
        currentWorkflow={selectedWorkflow}
      />

      <div className="flex-grow overflow-y-auto mb-4 p-3 bg-white rounded shadow">
        {messages.map((msg, index) => (
          <div key={index} className={`mb-3 p-3 rounded-lg max-w-xl ${
            msg.sender === 'user' ? 'bg-blue-500 text-white ml-auto' : 'bg-gray-200 text-gray-800 mr-auto'
          } ${msg.isError ? 'bg-red-200 text-red-800' : ''}`}>
            <p className="whitespace-pre-wrap">{msg.text}</p>
            {msg.sender === 'bot' && msg.tokens && (
              <p className="text-xs mt-1 opacity-75">Token usati: {msg.tokens}</p>
            )}
            {msg.sender === 'bot' && msg.source && (
              <p className="text-xs mt-1 opacity-75">Sorgente: {msg.source}</p>
            )}
             <p className="text-xs mt-1 opacity-60 text-right">{new Date(msg.timestamp).toLocaleTimeString()}</p>
          </div>
        ))}
        {isLoading && (
          <div className="mb-3 p-3 rounded-lg max-w-xl bg-gray-200 text-gray-800 mr-auto">
            <p><em>Il server sta pensando...</em></p>
          </div>
        )}
        <div ref={messagesEndRef} /> {/* Elemento per lo scroll automatico */}
      </div>

      <form onSubmit={handleSendMessage} className="flex items-center">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Scrivi il tuo messaggio..."
          className="flex-grow p-3 border rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        />
        <button
          type="submit"
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-r-md disabled:opacity-50"
          disabled={isLoading || !input.trim()}
        >
          Invia
        </button>
      </form>
    </div>
  );
}

export default Chat;
