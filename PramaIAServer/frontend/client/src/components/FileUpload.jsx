import React, { useState } from 'react';
import axios from 'axios';
import config from '../config';

function FileUpload({ onUploadComplete }) {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    setSelectedFiles(Array.from(e.target.files));
    setError('');
  };

  const handleUpload = async () => {
    if (!selectedFiles.length) {
      setError('Seleziona almeno un file da caricare');
      return;
    }

    setUploading(true);
    setError('');

    const formData = new FormData();
    selectedFiles.forEach(file => {
      formData.append('files', file);
    });

    try {
      await axios.post(`${config.BACKEND_URL}/documents/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setSelectedFiles([]);
      if (onUploadComplete) {
        onUploadComplete();
      }
    } catch (err) {
      setError('Errore durante il caricamento dei file');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="mb-4 p-4 border-2 border-dashed border-gray-300 rounded-lg">
      <input
        type="file"
        multiple
        accept=".pdf,.txt,.doc,.docx"
        onChange={handleFileChange}
        className="mb-2"
      />
      {selectedFiles.length > 0 && (
        <div className="mb-2 text-sm text-gray-600">
          {selectedFiles.length} file selezionati
        </div>
      )}
      {error && <div className="text-red-500 text-sm mb-2">{error}</div>}
      <button
        onClick={handleUpload}
        disabled={uploading || !selectedFiles.length}
        className={`px-4 py-2 rounded ${
          uploading || !selectedFiles.length
            ? 'bg-gray-300 cursor-not-allowed'
            : 'bg-blue-500 hover:bg-blue-600 text-white'
        }`}
      >
        {uploading ? 'Caricamento...' : 'Carica file'}
      </button>
    </div>
  );
}

export default FileUpload;
