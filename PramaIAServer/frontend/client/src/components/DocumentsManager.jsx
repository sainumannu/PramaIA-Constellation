import React, { useEffect, useState } from 'react';
import axios from 'axios';
import config from '../config';

function DocumentsManager({ onBack }) {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [uploadFiles, setUploadFiles] = useState([]);
  const [isPublic, setIsPublic] = useState(false);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await axios.get(`${config.BACKEND_URL}/documents/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      console.log('Documents response:', res.data);
      setDocuments(res.data.files || []);
    } catch (error) {
      console.error('Errore nel caricamento documenti:', error);
      setMessage('Errore nel caricamento dei documenti');
      setTimeout(() => setMessage(''), 3000);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (uploadFiles.length === 0) {
      setMessage('Seleziona almeno un file');
      return;
    }

    setUploading(true);
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      
      // Aggiungi tutti i file
      for (let file of uploadFiles) {
        formData.append('files', file);
      }
      
      // Aggiungi il flag di visibilità
      formData.append('is_public', isPublic);

      const res = await axios.post(`${config.BACKEND_URL}/documents/upload-with-visibility/`, 
        formData, {
          headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      setMessage(`${uploadFiles.length} file(s) caricato/i con successo`);
      setUploadFiles([]);
      setShowUploadForm(false);
      setIsPublic(false);
      fetchDocuments(); // Ricarica la lista
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Errore nel caricamento:', error);
      const errorMsg = error.response?.data?.detail || 'Errore nel caricamento dei file';
      setMessage(errorMsg);
      setTimeout(() => setMessage(''), 3000);
    } finally {
      setUploading(false);
    }
  };

  const toggleVisibility = async (filename, currentVisibility) => {
    try {
      const token = localStorage.getItem('token');
      const newVisibility = !currentVisibility;
      
      const formData = new FormData();
      formData.append('is_public', newVisibility);

      await axios.patch(`${config.BACKEND_URL}/documents/${encodeURIComponent(filename)}/visibility`, 
        formData, {
          headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );

      setMessage(`Visibilità di "${filename}" aggiornata a ${newVisibility ? 'pubblico' : 'privato'}`);
      fetchDocuments(); // Ricarica la lista
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Errore nell\'aggiornamento visibilità:', error);
      const errorMsg = error.response?.data?.detail || 'Errore nell\'aggiornamento della visibilità';
      setMessage(errorMsg);
      setTimeout(() => setMessage(''), 3000);
    }
  };

  const deleteDocument = async (filename) => {
    // eslint-disable-next-line no-restricted-globals
    if (!confirm(`Sei sicuro di voler eliminare "${filename}"? Questa azione non può essere annullata.`)) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${config.BACKEND_URL}/documents/${encodeURIComponent(filename)}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      setMessage(`Documento "${filename}" eliminato con successo`);
      fetchDocuments(); // Ricarica la lista
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Errore nell\'eliminazione:', error);
      const errorMsg = error.response?.data?.detail || 'Errore nell\'eliminazione del documento';
      setMessage(errorMsg);
      setTimeout(() => setMessage(''), 3000);
    }
  };

  if (loading) {
    return (
      <div className="p-4 flex justify-center items-center min-h-screen">
        <div className="text-lg">Caricamento documenti...</div>
      </div>
    );
  }

  return (
    <div className="p-4 bg-gray-100 min-h-screen">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-blue-700">Gestione Documenti</h2>
          <div className="space-x-2">
            <button 
              onClick={() => setShowUploadForm(!showUploadForm)}
              className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md"
            >
              {showUploadForm ? 'Annulla' : '📤 Carica Documenti'}
            </button>
            {onBack && (
              <button 
                onClick={onBack}
                className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded-md"
              >
                ← Indietro
              </button>
            )}
          </div>
        </div>

        {/* Messaggio di stato */}
        {message && (
          <div className={`mb-4 p-3 rounded-md ${
            message.includes('Errore') ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
          }`}>
            {message}
          </div>
        )}

        {/* Form di upload */}
        {showUploadForm && (
          <div className="bg-white p-6 rounded-lg shadow-md mb-6">
            <h3 className="text-lg font-semibold mb-4">Carica Nuovi Documenti</h3>
            <form onSubmit={handleFileUpload}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Seleziona file PDF
                </label>
                <input
                  type="file"
                  multiple
                  accept=".pdf"
                  onChange={(e) => setUploadFiles([...e.target.files])}
                  className="w-full p-2 border border-gray-300 rounded-md"
                  required
                />
                {uploadFiles.length > 0 && (
                  <div className="mt-2 text-sm text-gray-600">
                    {uploadFiles.length} file(s) selezionato/i: {[...uploadFiles].map(f => f.name).join(', ')}
                  </div>
                )}
              </div>

              <div className="mb-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={isPublic}
                    onChange={(e) => setIsPublic(e.target.checked)}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium text-gray-700">
                    Rendi i documenti pubblici (visibili a tutti gli utenti)
                  </span>
                </label>
              </div>

              <div className="flex space-x-2">
                <button
                  type="submit"
                  disabled={uploading || uploadFiles.length === 0}
                  className="bg-green-500 hover:bg-green-600 disabled:bg-gray-400 text-white px-4 py-2 rounded-md"
                >
                  {uploading ? 'Caricamento...' : 'Carica'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowUploadForm(false);
                    setUploadFiles([]);
                    setIsPublic(false);
                  }}
                  className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded-md"
                >
                  Annulla
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Lista documenti */}
        <div className="bg-white rounded-lg shadow-md">
          <div className="p-4 border-b">
            <h3 className="text-lg font-semibold text-gray-800">
              I Tuoi Documenti ({documents.length})
            </h3>
            <p className="text-sm text-gray-600">
              Gestisci i tuoi documenti: visibilità, eliminazione e collegamento ai notebook
            </p>
          </div>

          {documents.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <div className="text-4xl mb-4">📄</div>
              <p className="text-lg mb-2">Nessun documento caricato</p>
              <p className="text-sm">Carica dei file PDF per iniziare ad usare il sistema RAG</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {documents.map((doc) => {
                const currentUser = localStorage.getItem('user_id'); // Assumendo che salvi l'user_id
                const isOwner = doc.owner === currentUser;
                
                return (
                  <div key={doc.filename} className="p-4 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <span className="text-lg font-medium text-gray-900">
                            📄 {doc.filename}
                          </span>
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            doc.is_public ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                          }`}>
                            {doc.is_public ? '🌐 Pubblico' : '🔒 Privato'}
                          </span>
                          {!isOwner && (
                            <span className="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-800">
                              👤 Proprietario: {doc.owner}
                            </span>
                          )}
                        </div>
                        <div className="text-sm text-gray-600 mt-1">
                          Dimensione: {doc.size_human || 'N/D'} | Caricato: {new Date(doc.timestamp).toLocaleDateString()}
                        </div>
                      </div>

                      {isOwner && (
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => toggleVisibility(doc.filename, doc.is_public)}
                            className={`px-3 py-1 rounded text-sm font-medium ${
                              doc.is_public 
                                ? 'bg-yellow-500 hover:bg-yellow-600 text-white' 
                                : 'bg-green-500 hover:bg-green-600 text-white'
                            }`}
                            title={doc.is_public ? 'Rendi privato' : 'Rendi pubblico'}
                          >
                            {doc.is_public ? '🔒 Rendi Privato' : '🌐 Rendi Pubblico'}
                          </button>
                          <button
                            onClick={() => deleteDocument(doc.filename)}
                            className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm font-medium"
                            title="Elimina documento"
                          >
                            🗑️ Elimina
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Statistiche */}
        {documents.length > 0 && (
          <div className="mt-6 bg-white rounded-lg shadow-md p-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">Statistiche</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {documents.filter(d => d.owner === localStorage.getItem('user_id')).length}
                </div>
                <div className="text-sm text-gray-600">Documenti Tuoi</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {documents.filter(d => d.is_public).length}
                </div>
                <div className="text-sm text-gray-600">Documenti Pubblici</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">
                  {documents.filter(d => !d.is_public).length}
                </div>
                <div className="text-sm text-gray-600">Documenti Privati</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default DocumentsManager;
