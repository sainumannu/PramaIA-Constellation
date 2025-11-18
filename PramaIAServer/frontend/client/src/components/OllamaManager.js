import React, { useState, useEffect } from 'react';
import { endpoints } from '../services/api';
import { 
  Server, 
  Download, 
  CheckCircle, 
  XCircle, 
  RefreshCw, 
  Play,
  Info,
  AlertTriangle
} from 'lucide-react';

const OllamaManager = () => {
  const [status, setStatus] = useState(null);
  const [models, setModels] = useState([]);
  const [recommendedModels, setRecommendedModels] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [pullingModel, setPullingModel] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [showTestModal, setShowTestModal] = useState(false);

  useEffect(() => {
    checkStatus();
    loadRecommendedModels();
  }, []);

  const checkStatus = async () => {
    try {
      const response = await endpoints.ollama.status();
      setStatus(response.data);
      
      if (response.data.is_running) {
        loadModels();
      }
    } catch (error) {
      console.error('Error checking Ollama status:', error);
      setStatus({ is_running: false, status: 'error' });
    }
  };

  const loadModels = async () => {
    try {
      const response = await endpoints.ollama.models();
      setModels(response.data);
    } catch (error) {
      console.error('Error loading models:', error);
    }
  };

  const loadRecommendedModels = async () => {
    try {
      const response = await endpoints.ollama.recommendedModels();
      setRecommendedModels(response.data);
    } catch (error) {
      console.error('Error loading recommended models:', error);
    }
  };

  const pullModel = async (modelName) => {
    setPullingModel(modelName);
    try {
      const response = await endpoints.ollama.pullModel(modelName);
      
      console.log('Model pull result:', response.data);
      
      // Ricarica la lista dei modelli
      await loadModels();
      await loadRecommendedModels();
    } catch (error) {
      console.error('Error pulling model:', error);
    } finally {
      setPullingModel(null);
    }
  };

  const testGeneration = async (modelName) => {
    setIsLoading(true);
    try {
      const response = await endpoints.ollama.test({
        prompt: "Explain what you are in one sentence.",
        model: modelName,
        temperature: 0.7,
        max_tokens: 50
      });
      
      setTestResult(response.data);
      setShowTestModal(true);
    } catch (error) {
      console.error('Error testing model:', error);
      setTestResult({ status: 'error', message: error.message });
      setShowTestModal(true);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusIcon = () => {
    if (!status) return <RefreshCw className="w-5 h-5 animate-spin text-gray-500" />;
    
    if (status.is_running) {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    } else {
      return <XCircle className="w-5 h-5 text-red-500" />;
    }
  };

  const getStatusText = () => {
    if (!status) return 'Checking...';
    
    if (status.is_running) {
      return `Running (${status.total_models} models)`;
    } else {
      return 'Not running';
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      'Programming': 'bg-blue-100 text-blue-800',
      'Conversation': 'bg-green-100 text-green-800', 
      'Compact': 'bg-purple-100 text-purple-800',
      'Instruction': 'bg-orange-100 text-orange-800',
      'General': 'bg-gray-100 text-gray-800'
    };
    return colors[category] || colors.General;
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Server className="w-6 h-6 text-gray-700" />
              <div>
                <h1 className="text-xl font-semibold text-gray-900">Ollama Manager</h1>
                <p className="text-sm text-gray-600">Gestisci modelli LLM locali</p>
              </div>
            </div>
            
            <button
              onClick={checkStatus}
              className="flex items-center gap-2 px-3 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Aggiorna
            </button>
          </div>
        </div>

        {/* Status Section */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center gap-4">
            {getStatusIcon()}
            <div>
              <div className="font-medium text-gray-900">
                Status: {getStatusText()}
              </div>
              {status?.base_url && (
                <div className="text-sm text-gray-600">
                  URL: {status.base_url}
                </div>
              )}
            </div>
          </div>

          {!status?.is_running && (
            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
              <div className="flex items-start gap-2">
                <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5" />
                <div>
                  <div className="font-medium text-yellow-800">Ollama non è in esecuzione</div>
                  <div className="text-sm text-yellow-700 mt-1">
                    Per utilizzare modelli locali:
                    <br />• Installa Ollama: <code className="bg-yellow-100 px-1 rounded">curl -fsSL https://ollama.ai/install.sh | sh</code>
                    <br />• Avvia il servizio: <code className="bg-yellow-100 px-1 rounded">ollama serve</code>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Models Section */}
        {status?.is_running && (
          <>
            {/* Installed Models */}
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Modelli Installati ({models.length})
              </h2>
              
              {models.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Server className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                  <p>Nessun modello installato</p>
                  <p className="text-sm">Installa alcuni modelli dalla sezione raccomandati</p>
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {models.map((model, index) => (
                    <div key={index} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <div className="font-medium text-gray-900">{model.name}</div>
                          {model.description && (
                            <div className="text-sm text-gray-600 mt-1">{model.description}</div>
                          )}
                        </div>
                        {model.recommended && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            Raccomandato
                          </span>
                        )}
                      </div>
                      
                      <div className="flex gap-2 mt-3">
                        <button
                          onClick={() => testGeneration(model.name)}
                          disabled={isLoading}
                          className="flex items-center gap-1 px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
                        >
                          <Play className="w-3 h-3" />
                          Test
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Recommended Models */}
            <div className="p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Modelli Raccomandati
              </h2>
              
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {recommendedModels.map((model, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <div className="font-medium text-gray-900">{model.name}</div>
                        <div className="text-sm text-gray-600 mt-1">{model.description}</div>
                      </div>
                      
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(model.category)}`}>
                        {model.category}
                      </span>
                    </div>
                    
                    <div className="flex items-center justify-between mt-3">
                      <div className="flex items-center gap-2">
                        {model.installed ? (
                          <span className="flex items-center gap-1 text-sm text-green-600">
                            <CheckCircle className="w-4 h-4" />
                            Installato
                          </span>
                        ) : (
                          <span className="text-sm text-gray-500">Non installato</span>
                        )}
                      </div>
                      
                      {!model.installed && (
                        <button
                          onClick={() => pullModel(model.name)}
                          disabled={pullingModel === model.name}
                          className="flex items-center gap-1 px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                        >
                          {pullingModel === model.name ? (
                            <>
                              <RefreshCw className="w-3 h-3 animate-spin" />
                              Scaricando...
                            </>
                          ) : (
                            <>
                              <Download className="w-3 h-3" />
                              Installa
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Test Modal */}
      {showTestModal && testResult && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowTestModal(false)}></div>
            
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <div className="sm:flex sm:items-start">
                  <div className="w-full">
                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                      Test Generazione
                    </h3>
                    
                    {testResult.status === 'success' ? (
                      <div className="space-y-3">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Modello:</label>
                          <div className="text-sm text-gray-900">{testResult.model}</div>
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Prompt:</label>
                          <div className="text-sm text-gray-600 bg-gray-50 p-2 rounded">{testResult.prompt}</div>
                        </div>
                        
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Risposta:</label>
                          <div className="text-sm text-gray-900 bg-blue-50 p-3 rounded border">{testResult.response}</div>
                        </div>
                      </div>
                    ) : (
                      <div className="text-red-600">
                        Errore durante il test: {testResult.message}
                      </div>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button
                  type="button"
                  onClick={() => setShowTestModal(false)}
                  className="w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:w-auto sm:text-sm"
                >
                  Chiudi
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OllamaManager;
