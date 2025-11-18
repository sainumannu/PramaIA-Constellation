import React, { useEffect, useState } from 'react';
import axios from 'axios';
import config from '../config';

function NotebookSourcesManager({ sessionId, isOpen, onClose, isAdmin = false }) {
  const [linkedDocs, setLinkedDocs] = useState([]);
  const [availableDocs, setAvailableDocs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [uploadFiles, setUploadFiles] = useState([]);
  const [isPublic, setIsPublic] = useState(false);
  const [uploading, setUploading] = useState(false);
 
  useEffect(() => {
    if (isOpen && sessionId) {
      fetchData();
    }
  }, [isOpen, sessionId]);

  const fetchData = async () => {
    setLoading(true);
    setMessage('');
    try {
      const token = localStorage.getItem('token');
      
      // Fetch documenti disponibili
      const docsRes = await axios.get(`${config.BACKEND_URL}/documents/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setAvailableDocs(docsRes.data.files || []);

      // Fetch documenti collegati al notebook
      const linkedRes = await axios.get(`${config.BACKEND_URL}/sessions/${sessionId}/sources`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setLinkedDocs(linkedRes.data || []);
      
    } catch (error) {
      console.error('Errore nel caricamento dati:', error);
      if (error.response?.status === 404) {
        setMessage('Questo notebook non è più disponibile o non hai accesso.');
      } else {
        setMessage('Errore nel caricamento dei dati');
      }
    } finally {
      setLoading(false);
    }
  };

  const linkDocument = async (filename) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${config.BACKEND_URL}/sessions/${sessionId}/sources`, 
        { filename },
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      
      setMessage(`Documento "${filename}" collegato con successo`);
      fetchData(); // Ricarica i dati
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Errore nel collegare il documento:', error);
      const errorMsg = error.response?.data?.detail || 'Errore nel collegare il documento';
      setMessage(errorMsg);
      setTimeout(() => setMessage(''), 3000);
    }
  };

  const unlinkDocument = async (filename) => {
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${config.BACKEND_URL}/sessions/${sessionId}/sources/${encodeURIComponent(filename)}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      setMessage(`Documento "${filename}" scollegato con successo`);
      fetchData(); // Ricarica i dati
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Errore nello scollegare il documento:', error);
      const errorMsg = error.response?.data?.detail || 'Errore nello scollegare il documento';
      setMessage(errorMsg);
      setTimeout(() => setMessage(''), 3000);
    }
  };

  const isDocumentLinked = (filename) => {
    return linkedDocs.some(doc => doc.filename === filename);
  };

  const handleUploadFiles = async () => {
    if (uploadFiles.length === 0) {
      setMessage('Seleziona almeno un file');
      setTimeout(() => setMessage(''), 3000);
      return;
    }

    setUploading(true);
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      
      uploadFiles.forEach(file => {
        formData.append('files', file);
      });
      formData.append('is_public', isPublic);

      const res = await axios.post(`${config.BACKEND_URL}/documents/upload-with-visibility/`, formData, {
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      // Collega automaticamente i file caricati al notebook corrente
      const uploadedFiles = res.data.uploaded_files || [];
      for (const fileInfo of uploadedFiles) {
        try {
          await linkDocument(fileInfo.filename);
        } catch (linkError) {
          console.error(`Errore nel collegare ${fileInfo.filename}:`, linkError);
        }
      }

      setMessage(`${uploadFiles.length} file(s) caricato/i e collegato/i con successo`);
      setUploadFiles([]);
      setShowUploadForm(false);
      setIsPublic(false);
      
      // Ricarica i dati per vedere i nuovi file
      fetchData();
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Errore nell\'upload:', error);
      const errorMsg = error.response?.data?.detail || 'Errore nell\'upload dei file';
      setMessage(errorMsg);
      setTimeout(() => setMessage(''), 3000);
    } finally {
      setUploading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-4xl w-full max-h-[80vh] overflow-y-auto mx-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-bold text-blue-700">
            Gestione Fonti per Notebook
          </h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        {message && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md text-sm">
            {message}
          </div>
        )}

        {loading ? (
          <div className="text-center py-8">Caricamento...</div>
        ) : (
          <div className="space-y-6">
            {/* Documenti collegati */}
            <div>
              <h4 className="text-lg font-semibold mb-3 text-green-700">
                Documenti Collegati ({linkedDocs.length})
              </h4>
              {linkedDocs.length === 0 ? (
                <p className="text-gray-500 italic">Nessun documento collegato a questo notebook</p>
              ) : (
                <div className="space-y-2">
                  {linkedDocs.map((doc) => (
                    <div key={doc.filename} className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-md">
                      <div className="flex-1">
                        <span className="font-medium">{doc.filename}</span>
                        <div className="text-xs text-gray-600">
                          Collegato il: {new Date(doc.linked_at).toLocaleString()}
                        </div>
                      </div>
                      <button
                        onClick={() => unlinkDocument(doc.filename)}
                        className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded-md text-sm"
                      >
                        Scollega
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Documenti disponibili */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-lg font-semibold text-blue-700">
                  Documenti Disponibili ({availableDocs.length})
                </h4>
                <button
                  onClick={() => setShowUploadForm(!showUploadForm)}
                  className="bg-green-500 hover:bg-green-600 text-white px-3 py-1 rounded-md text-sm"
                >
                  📤 Carica Nuovo File
                </button>
              </div>
              {availableDocs.length === 0 ? (
                <p className="text-gray-500 italic">Nessun documento disponibile. Carica dei PDF nella sezione Documenti.</p>
              ) : (
                <div className="space-y-2">
                  {availableDocs.map((doc) => {
                    const isLinked = isDocumentLinked(doc.filename);
                    return (
                      <div key={doc.filename} className={`flex items-center justify-between p-3 border rounded-md ${
                        isLinked ? 'bg-gray-100 border-gray-300' : 'bg-white border-gray-200'
                      }`}>
                        <div className="flex-1">
                          <span className={`font-medium ${isLinked ? 'text-gray-500' : 'text-gray-900'}`}>
                            {doc.filename}
                          </span>
                          <div className="text-xs text-gray-600">
                            Proprietario: {doc.owner} | Dimensione: {doc.size_human || 'N/D'}
                            {doc.is_public !== undefined && (
                              <span className={`ml-2 px-2 py-1 rounded text-xs font-medium ${
                                doc.is_public ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                              }`}>
                                {doc.is_public ? '🌐 Pubblico' : '🔒 Privato'}
                              </span>
                            )}
                          </div>
                        </div>
                        {isLinked ? (
                          <span className="text-green-600 text-sm font-medium">
                            ✓ Già collegato
                          </span>
                        ) : (
                          <button
                            onClick={() => linkDocument(doc.filename)}
                            className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded-md text-sm"
                          >
                            Collega
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Upload Form */}
            {showUploadForm && (
              <div className="bg-gray-50 p-4 rounded-md border mb-4">
                <h5 className="font-medium mb-3">Carica Nuovi Documenti</h5>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Seleziona file PDF:
                    </label>
                    <input
                      type="file"
                      multiple
                      accept=".pdf"
                      onChange={(e) => setUploadFiles(Array.from(e.target.files))}
                      className="w-full p-2 border border-gray-300 rounded-md text-sm"
                    />
                    {uploadFiles.length > 0 && (
                      <div className="mt-1 text-xs text-gray-600">
                        File selezionati: {uploadFiles.map(f => f.name).join(', ')}
                      </div>
                    )}
                  </div>
                  
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="uploadIsPublic"
                      checked={isPublic}
                      onChange={(e) => setIsPublic(e.target.checked)}
                      className="mr-2"
                    />
                    <label htmlFor="uploadIsPublic" className="text-sm text-gray-700">
                      Rendi pubblici (visibili a tutti gli utenti)
                    </label>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={handleUploadFiles}
                      disabled={uploading || uploadFiles.length === 0}
                      className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-3 py-1 rounded-md text-sm"
                    >
                      {uploading ? 'Caricamento...' : 'Carica e Collega'}
                    </button>
                    <button
                      onClick={() => {
                        setShowUploadForm(false);
                        setUploadFiles([]);
                        setIsPublic(false);
                      }}
                      className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-3 py-1 rounded-md text-sm"
                    >
                      Annulla
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-md"
          >
            Chiudi
          </button>
        </div>
      </div>
    </div>
  );
}

export default NotebookSourcesManager;
