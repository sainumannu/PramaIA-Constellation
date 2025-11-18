import React, { useState, useEffect } from 'react';
import axios from 'axios';
import config from '../config';

const PdfEventsSettings = () => {
  const [settings, setSettings] = useState({
    PDF_EVENTS_MAX_AGE_HOURS: 24,
    PDF_EVENTS_MAX_COUNT: 1000,
    PDF_EVENTS_AUTO_CLEANUP: true
  });
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [totalEvents, setTotalEvents] = useState(0);
  const [oldestEvent, setOldestEvent] = useState('');
  const [newestEvent, setNewestEvent] = useState('');

  // Carica le impostazioni all'avvio
  useEffect(() => {
    fetchSettings();
    fetchEventStats();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${config.BACKEND_URL}/api/settings/config`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      // Filtra solo le impostazioni relative agli eventi PDF
      const pdfSettings = {};
      Object.entries(response.data).forEach(([key, setting]) => {
        if (key.startsWith('PDF_EVENTS_')) {
          pdfSettings[key] = setting.value;
        }
      });
      
      setSettings(prev => ({
        ...prev,
        ...pdfSettings
      }));
      
    } catch (err) {
      console.error('Errore nel recupero delle impostazioni:', err);
      setError('Errore nel caricamento delle impostazioni');
    } finally {
      setLoading(false);
    }
  };

  const fetchEventStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${config.BACKEND_URL}/api/pdf-events/details`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.data) {
        setTotalEvents(response.data.total_events || 0);
        setOldestEvent(response.data.oldest_event || '');
        setNewestEvent(response.data.newest_event || '');
      }
    } catch (err) {
      console.error('Errore nel recupero delle statistiche degli eventi:', err);
      // Non mostriamo un errore all'utente in questo caso
    }
  };

  const handleInputChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleSaveSetting = async (key) => {
    setLoading(true);
    setMessage('');
    setError('');
    
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${config.BACKEND_URL}/api/settings/config/${key}`,
        {
          key: key,
          value: settings[key]
        },
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      
      setMessage(`Impostazione "${key}" aggiornata con successo!`);
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      console.error('Errore nel salvataggio dell\'impostazione:', err);
      setError(err.response?.data?.detail || `Errore nell'aggiornamento di ${key}`);
      setTimeout(() => setError(''), 5000);
    } finally {
      setLoading(false);
    }
  };

  const handleCleanup = async () => {
    // Utilizziamo window.confirm invece di confirm per evitare l'errore ESLint
    if (!window.confirm("Sei sicuro di voler eliminare gli eventi PDF più vecchi? Questa operazione non può essere annullata.")) {
      return;
    }
    
    setLoading(true);
    setMessage('');
    setError('');
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${config.BACKEND_URL}/api/pdf-events/cleanup`,
        {
          max_age_hours: settings.PDF_EVENTS_MAX_AGE_HOURS,
          max_events: settings.PDF_EVENTS_MAX_COUNT
        },
        {
          headers: { 'Authorization': `Bearer ${token}` }
        }
      );
      
      setMessage(`Pulizia completata: ${response.data.deleted} eventi eliminati`);
      fetchEventStats(); // Aggiorna le statistiche
      setTimeout(() => setMessage(''), 5000);
    } catch (err) {
      console.error('Errore durante la pulizia degli eventi:', err);
      setError(err.response?.data?.detail || 'Errore durante la pulizia degli eventi');
      setTimeout(() => setError(''), 5000);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-xl font-semibold mb-4">📋 Gestione Eventi PDF</h3>
      
      {error && (
        <div className="mb-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {message && (
        <div className="mb-4 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
          {message}
        </div>
      )}

      <div className="mb-6 p-4 bg-blue-50 rounded-lg">
        <h4 className="font-medium text-blue-800 mb-2">Statistiche Eventi PDF</h4>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-2 bg-white rounded shadow-sm">
            <div className="text-2xl font-bold text-blue-600">{totalEvents}</div>
            <div className="text-sm text-gray-600">Eventi Totali</div>
          </div>
          <div className="text-center p-2 bg-white rounded shadow-sm">
            <div className="text-sm font-medium text-blue-600">
              {oldestEvent ? new Date(oldestEvent).toLocaleString() : 'N/D'}
            </div>
            <div className="text-sm text-gray-600">Evento più vecchio</div>
          </div>
          <div className="text-center p-2 bg-white rounded shadow-sm">
            <div className="text-sm font-medium text-blue-600">
              {newestEvent ? new Date(newestEvent).toLocaleString() : 'N/D'}
            </div>
            <div className="text-sm text-gray-600">Evento più recente</div>
          </div>
        </div>
        <div className="mt-3 flex justify-end">
          <button
            onClick={fetchEventStats}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            🔄 Aggiorna statistiche
          </button>
        </div>
      </div>

      <div className="space-y-6">
        {/* Età massima eventi */}
        <div className="border-b pb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Età massima eventi (ore)
          </label>
          <div className="flex items-center space-x-3">
            <input
              type="number"
              value={settings.PDF_EVENTS_MAX_AGE_HOURS}
              onChange={(e) => handleInputChange('PDF_EVENTS_MAX_AGE_HOURS', parseInt(e.target.value))}
              min="1"
              max="720" // 30 giorni
              className="border border-gray-300 rounded px-3 py-2 w-24"
            />
            <button
              onClick={() => handleSaveSetting('PDF_EVENTS_MAX_AGE_HOURS')}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
              disabled={loading}
            >
              Salva
            </button>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Gli eventi più vecchi di questo numero di ore verranno eliminati durante la pulizia.
          </p>
        </div>

        {/* Numero massimo eventi */}
        <div className="border-b pb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Numero massimo eventi
          </label>
          <div className="flex items-center space-x-3">
            <input
              type="number"
              value={settings.PDF_EVENTS_MAX_COUNT}
              onChange={(e) => handleInputChange('PDF_EVENTS_MAX_COUNT', parseInt(e.target.value))}
              min="100"
              max="10000"
              className="border border-gray-300 rounded px-3 py-2 w-24"
            />
            <button
              onClick={() => handleSaveSetting('PDF_EVENTS_MAX_COUNT')}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
              disabled={loading}
            >
              Salva
            </button>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Se il numero di eventi supera questo limite, i più vecchi verranno eliminati.
          </p>
        </div>

        {/* Pulizia automatica */}
        <div className="border-b pb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Pulizia automatica
          </label>
          <div className="flex items-center space-x-3">
            <select
              value={settings.PDF_EVENTS_AUTO_CLEANUP.toString()}
              onChange={(e) => handleInputChange('PDF_EVENTS_AUTO_CLEANUP', e.target.value === 'true')}
              className="border border-gray-300 rounded px-3 py-2"
            >
              <option value="true">Abilitata</option>
              <option value="false">Disabilitata</option>
            </select>
            <button
              onClick={() => handleSaveSetting('PDF_EVENTS_AUTO_CLEANUP')}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
              disabled={loading}
            >
              Salva
            </button>
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Quando abilitata, la pulizia degli eventi viene eseguita automaticamente.
          </p>
        </div>

        {/* Pulizia manuale */}
        <div className="pt-4">
          <h4 className="font-medium text-gray-700 mb-3">Pulizia Manuale</h4>
          <button
            onClick={handleCleanup}
            className="bg-red-500 hover:bg-red-600 text-white px-6 py-3 rounded-md"
            disabled={loading}
          >
            🗑️ Pulisci Eventi Vecchi
          </button>
          <p className="text-sm text-gray-500 mt-2">
            Elimina gli eventi più vecchi di {settings.PDF_EVENTS_MAX_AGE_HOURS} ore, mantenendo al massimo {settings.PDF_EVENTS_MAX_COUNT} eventi.
          </p>
        </div>
      </div>
    </div>
  );
};

export default PdfEventsSettings;
