import React, { useState, useEffect } from 'react';
import axios from 'axios';
import config from '../config';

function DocumentManager() {
  const [files, setFiles] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [totalFilesInfo, setTotalFilesInfo] = useState(null); // Per le info totali dell'admin

  const fetchDocuments = async () => {
    try {
      const res = await axios.get(`${config.BACKEND_URL}/documents/`);
      setFiles(res.data.files || []);
      // Se la risposta contiene total_files, l'utente è probabilmente un admin
      if (res.data.total_files !== undefined) {
        setTotalFilesInfo({
          total_files: res.data.total_files,
          total_size_human: res.data.total_size_human
        });
      } else {
        setTotalFilesInfo(null); // Resetta se non è admin o non ci sono info totali
      }
    } catch (err) {
      console.error('Errore nel recupero documenti:', err);
    }
  };
 
  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleUpload = async () => {
    if (!selectedFiles.length) return;

    setLoading(true);
    setMessage('📤 Caricamento in corso, attendi...');

    const formData = new FormData();
    for (const file of selectedFiles) {
      formData.append('files', file);
    }

    try {
      const res = await axios.post(
        `${config.BACKEND_URL}/documents/`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 30000 }
      );
      setMessage(res.data.message);
      setSelectedFiles([]);
      setTimeout(() => {
        fetchDocuments();
        setLoading(false);
        setTimeout(() => setMessage(''), 3000);
      }, 1000);
    } catch (err) {
      console.error('❌ Errore upload:', err);
      setMessage('Errore durante il caricamento. Riprova tra qualche secondo.');
      setLoading(false);
    }
  };

  const handleDelete = async (filename) => {
    setLoading(true);
    setMessage(`Eliminazione di "${filename}" in corso...`);
    try {
      await axios.delete(`${config.BACKEND_URL}/documents/${encodeURIComponent(filename)}`);
      setTimeout(() => {
        fetchDocuments();
        setMessage(`File "${filename}" eliminato.`);
        setTimeout(() => setMessage(''), 3000);
        setLoading(false);
      }, 1500);
    } catch (err) {
      console.error('❌ Errore nella cancellazione:', err);
      setMessage('Errore durante l\'eliminazione.');
      setLoading(false);
      setTimeout(() => setMessage(''), 3000);
    }
  };

  const handleDownload = async (filename) => {
    try {
      const response = await axios.get(
        `${config.BACKEND_URL}/documents/download/${encodeURIComponent(filename)}`,
        {
          responseType: 'blob',
        }
      );
  
      // Crea un URL blob per il file e simula un click per il download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename); // Imposta il nome del file per il download
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url); // Pulisci l'URL blob
    } catch (error) {
      console.error("Errore durante il download del file:", error);
      setMessage("Impossibile scaricare il file. " + (error.response?.data?.detail || error.message));
      setTimeout(() => setMessage(''), 3000);
    }
  };

  return (
    <div className="p-6 bg-gray-100 h-screen flex flex-col">
      <h2 className="text-xl font-bold mb-4 text-blue-700">Gestione Documenti</h2>

      <div className="mb-4">
        <label className="block mb-1">Carica nuovi PDF</label>
        <input
          type="file"
          multiple
          accept="application/pdf"
          onChange={(e) => setSelectedFiles(Array.from(e.target.files))}
          disabled={loading}
        />
        <button
          className="mt-2 bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-50"
          onClick={handleUpload}
          disabled={loading || selectedFiles.length === 0}
        >
          Carica
        </button>
        {message && <p className="text-sm text-gray-700 mt-2">{message}</p>}
      </div>

      <div className="flex-1 overflow-y-auto">
        <h3 className="font-semibold mb-2">Documenti caricati:</h3>
        {totalFilesInfo && (
          <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-md text-sm">
            <p><strong>Riepilogo Amministratore:</strong></p>
            <p>Numero Totale File: {totalFilesInfo.total_files}</p>
            <p>Dimensione Totale Occupata: {totalFilesInfo.total_size_human}</p>
          </div>
        )}
        {files.length === 0 ? (
          <p className="text-sm text-gray-600">Nessun documento caricato.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white shadow-md rounded-lg">
              <thead className="bg-gray-200">
                <tr>
                  <th className="text-left py-2 px-3">Nome File</th>
                  <th className="text-left py-2 px-3">Proprietario</th>
                  <th className="text-left py-2 px-3">Data Caricamento</th>
                  <th className="text-left py-2 px-3">Dimensione</th>
                  <th className="text-left py-2 px-3">Azioni</th>
                </tr>
              </thead>
              <tbody>
                {files.map((file) => (
                  <tr key={file.filename} className="border-b hover:bg-gray-50">
                    <td className="py-2 px-3 font-mono text-sm">{file.filename}</td>
                    <td className="py-2 px-3 text-xs">{file.owner}</td>
                    <td className="py-2 px-3 text-xs">{new Date(file.timestamp).toLocaleString()}</td>
                    <td className="py-2 px-3 text-xs">{file.size_human || 'N/D'}</td>
                    <td className="py-2 px-3">
                      <button onClick={() => handleDownload(file.filename)} className="text-blue-600 hover:text-blue-800 text-xs mr-2 underline disabled:opacity-50" disabled={loading}>Download</button>
                      <button onClick={() => handleDelete(file.filename)} className="bg-red-600 text-white px-2 py-1 rounded text-xs disabled:opacity-50" disabled={loading}>Elimina</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
                  </div>
        )}
      </div>
    </div>
  );
}

export default DocumentManager;
