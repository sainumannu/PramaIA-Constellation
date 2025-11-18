import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Info, 
  Eye,
  EyeOff,
  AlertCircle
} from 'lucide-react';
import workflowService from '../services/workflowService';

const ValidationPanel = ({ workflow, onValidationChange, isVisible = true }) => {
  const [validationResult, setValidationResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [autoValidate, setAutoValidate] = useState(true);

  // Effettua validazione automatica quando il workflow cambia
  useEffect(() => {
    if (autoValidate && workflow?.nodes?.length > 0) {
      validateWorkflow();
    }
  }, [workflow, autoValidate]);

  // Notifica il parent component dei cambiamenti
  useEffect(() => {
    if (onValidationChange) {
      onValidationChange(validationResult);
    }
  }, [validationResult, onValidationChange]);

  const validateWorkflow = async () => {
    if (!workflow || !workflow.nodes || workflow.nodes.length === 0) {
      setValidationResult(null);
      return;
    }

    // Temporaneamente disabilitato - endpoint non implementato
    console.log('[ValidationPanel] Validation temporarily disabled');
    setValidationResult({
      isValid: true,
      issues: [],
      warnings: [],
      message: 'Validazione temporaneamente disabilitata'
    });
    return;

    setIsLoading(true);
    try {
      const result = await workflowService.validateWorkflow({
        name: workflow.name || 'Untitled Workflow',
        description: workflow.description || '',
        nodes: workflow.nodes,
        connections: workflow.connections || []
      });
      setValidationResult(result);
    } catch (error) {
      console.error('Errore validazione:', error);
      setValidationResult({
        is_valid: false,
        summary: 'Errore durante la validazione',
        errors: [{
          type: 'validation_error',
          message: error.message,
          severity: 'error'
        }],
        warnings: []
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      case 'info':
        return <Info className="w-4 h-4 text-blue-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'error':
        return 'border-red-200 bg-red-50';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50';
      case 'info':
        return 'border-blue-200 bg-blue-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  if (!isVisible) {
    return null;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="font-medium text-gray-900">Validazione Workflow</h3>
          {isLoading && (
            <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full" />
          )}
        </div>
        
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1 text-sm">
            <input
              type="checkbox"
              checked={autoValidate}
              onChange={(e) => setAutoValidate(e.target.checked)}
              className="rounded border-gray-300"
            />
            Auto
          </label>
          
          <button
            onClick={validateWorkflow}
            disabled={isLoading}
            className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            Valida
          </button>
          
          {validationResult && (
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="p-1 text-gray-500 hover:text-gray-700"
            >
              {showDetails ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          )}
        </div>
      </div>

      {/* Status */}
      <div className="px-4 py-3">
        {!validationResult ? (
          <div className="text-gray-500 text-sm">
            Aggiungi nodi al workflow per iniziare la validazione
          </div>
        ) : (
          <div className="space-y-3">
            {/* Summary */}
            <div className="flex items-center gap-2">
              {validationResult.is_valid ? (
                <CheckCircle className="w-5 h-5 text-green-500" />
              ) : (
                <XCircle className="w-5 h-5 text-red-500" />
              )}
              
              <span className={`font-medium ${
                validationResult.is_valid ? 'text-green-700' : 'text-red-700'
              }`}>
                {validationResult.summary}
              </span>
            </div>

            {/* Quick stats */}
            {(validationResult.errors?.length > 0 || validationResult.warnings?.length > 0) && (
              <div className="flex gap-4 text-sm">
                {validationResult.errors?.length > 0 && (
                  <span className="text-red-600">
                    {validationResult.errors.length} errori
                  </span>
                )}
                {validationResult.warnings?.length > 0 && (
                  <span className="text-yellow-600">
                    {validationResult.warnings.length} avvertimenti
                  </span>
                )}
              </div>
            )}

            {/* Detailed results */}
            {showDetails && (validationResult.errors?.length > 0 || validationResult.warnings?.length > 0) && (
              <div className="space-y-2 border-t pt-3">
                {/* Errors */}
                {validationResult.errors?.map((error, index) => (
                  <div
                    key={`error-${index}`}
                    className={`p-3 border rounded-md ${getSeverityColor(error.severity)}`}
                  >
                    <div className="flex items-start gap-2">
                      {getSeverityIcon(error.severity)}
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900">
                          {error.message}
                        </div>
                        {error.node_name && (
                          <div className="text-xs text-gray-600 mt-1">
                            Nodo: {error.node_name}
                          </div>
                        )}
                        {error.type && (
                          <div className="text-xs text-gray-500 mt-1">
                            Tipo: {error.type}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}

                {/* Warnings */}
                {validationResult.warnings?.map((warning, index) => (
                  <div
                    key={`warning-${index}`}
                    className={`p-3 border rounded-md ${getSeverityColor(warning.severity)}`}
                  >
                    <div className="flex items-start gap-2">
                      {getSeverityIcon(warning.severity)}
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium text-gray-900">
                          {warning.message}
                        </div>
                        {warning.node_name && (
                          <div className="text-xs text-gray-600 mt-1">
                            Nodo: {warning.node_name}
                          </div>
                        )}
                        {warning.type && (
                          <div className="text-xs text-gray-500 mt-1">
                            Tipo: {warning.type}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ValidationPanel;
