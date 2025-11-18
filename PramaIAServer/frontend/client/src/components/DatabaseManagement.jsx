import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { AlertTriangle, Database, Trash2, Download, RefreshCw, CheckCircle, XCircle } from 'lucide-react';

const DatabaseManagement = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [resetLoading, setResetLoading] = useState({});

  const fetchStatus = async () => {
    try {
      // Chiamata per riallineare le statistiche del vectorstore
      let recalcOk = true;
      try {
        const recalc = await fetch('/api/vectorstore/recalculate-stats', { method: 'POST' });
        if (!recalc.ok) recalcOk = false;
      } catch (err) {
        recalcOk = false;
        console.warn('Impossibile ricalcolare le statistiche:', err);
      }
      // Aggiorna comunque lo stato
      const response = await fetch('/api/database-management/status');
      const data = await response.json();
      setStatus(data);
      if (!recalcOk) {
        alert('Attenzione: impossibile ricalcolare le statistiche del vectorstore. I dati potrebbero essere non aggiornati.');
      }
    } catch (error) {
      console.error('Errore nel recuperare lo stato dei database:', error);
      setStatus({ error: 'Impossibile recuperare lo stato del database.' });
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleReset = async (type) => {
    if (!window.confirm(`Sei sicuro di voler resettare ${type}? Questa operazione non può essere annullata.`)) {
      return;
    }

    setResetLoading(prev => ({ ...prev, [type]: true }));
    
    try {
      const response = await fetch(`/api/database-management/reset/${type}`, {
        method: 'POST'
      });
      
      const result = await response.json();
      
      if (result.success) {
        alert(`Reset di ${type} completato con successo!`);
        await fetchStatus(); // Aggiorna lo stato
      } else {
        alert(`Errore durante il reset di ${type}: ${result.message}`);
      }
    } catch (error) {
      console.error(`Errore durante reset ${type}:`, error);
    } finally {
      setResetLoading(prev => ({ ...prev, [type]: false }));
    }
  };

  const handleBackup = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/database-management/backup/create', {
        method: 'POST'
      });
      
      const result = await response.json();
      
      if (result.success) {
        alert(`Backup creato con successo in: ${result.details.backup_path}`);
      } else {
        alert(`Errore durante la creazione del backup: ${result.message}`);
      }
    } catch (error) {
      console.error('Errore durante creazione backup:', error);
      alert('Errore durante la creazione del backup');
    } finally {
      setLoading(false);
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const StatusIcon = ({ success }) => {
    return success ? (
      <CheckCircle className="h-4 w-4 text-green-500" />
    ) : (
      <XCircle className="h-4 w-4 text-red-500" />
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Gestione Database</h2>
          <p className="text-gray-600">Monitora e gestisci i database del sistema</p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={fetchStatus} 
            variant="outline"
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Aggiorna
          </Button>
          <Button 
            onClick={handleBackup}
            disabled={loading}
          >
            <Download className="h-4 w-4 mr-2" />
            Crea Backup
          </Button>
        </div>
      </div>

      {status && (
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Panoramica</TabsTrigger>
            <TabsTrigger value="vectorstore">Vector Store</TabsTrigger>
            <TabsTrigger value="events">Eventi Documenti</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Database Principale */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Database Principale</CardTitle>
                  <StatusIcon success={!status.main_database?.error} />
                </CardHeader>
                <CardContent>
                  {status.main_database?.error ? (
                    <p className="text-sm text-red-500">{status.main_database.error}</p>
                  ) : (
                    <div className="space-y-2">
                      <p className="text-2xl font-bold">
                        {Object.keys(status.main_database?.tables || {}).length} tabelle
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatBytes(status.main_database?.size_bytes || 0)}
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Vector Store */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Vector Store</CardTitle>
                  <StatusIcon success={status.vectorstore?.status === 'ok'} />
                </CardHeader>
                <CardContent>
                  {status.vectorstore?.error ? (
                    <p className="text-sm text-red-500">{status.vectorstore.error}</p>
                  ) : (
                    <div className="space-y-2">
                      <p className="text-2xl font-bold">
                        {status.vectorstore?.collections?.document_documents?.document_count || 0}
                      </p>
                      <p className="text-xs text-gray-500">documenti vettorizzati</p>
                      <Badge variant={status.vectorstore?.status === 'ok' ? 'default' : 'secondary'}>
                        {status.vectorstore?.status}
                      </Badge>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Eventi Document Monitor */}
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Eventi Document Monitor</CardTitle>
                  <StatusIcon success={!status.document_monitor_events?.error} />
                </CardHeader>
                <CardContent>
                  {/* Retrocompatibilità per pdf_monitor_events */}
                  {(status.document_monitor_events?.error && status.pdf_monitor_events?.error) ? (
                    <p className="text-sm text-red-500">{status.document_monitor_events?.error || status.pdf_monitor_events?.error}</p>
                  ) : (
                    <div className="space-y-2">
                      <p className="text-2xl font-bold">
                        {status.document_monitor_events?.total_events || status.pdf_monitor_events?.total_events || 0}
                      </p>
                      <p className="text-xs text-gray-500">eventi totali</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="vectorstore" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Vector Store ChromaDB</CardTitle>
                <p className="text-sm text-gray-600">
                  Gestisci i documenti vettorizzati per la ricerca semantica
                </p>
              </CardHeader>
              <CardContent className="space-y-4">
                {status.vectorstore && (
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-medium">Stato</p>
                      <Badge variant={status.vectorstore.status === 'ok' ? 'default' : 'secondary'}>
                        {status.vectorstore.status}
                      </Badge>
                    </div>
                    <div>
                      <p className="text-sm font-medium">Documenti</p>
                      <p className="text-lg font-bold">{status.vectorstore?.collections?.document_documents?.document_count || status.vectorstore?.collections?.pdf_documents?.document_count || 0}</p>
                    </div>
                  </div>
                )}
                <Button 
                  onClick={() => handleReset('vectorstore')}
                  variant="destructive"
                  disabled={resetLoading.vectorstore}
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  {resetLoading.vectorstore ? 'Resettando...' : 'Reset Vector Store'}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="events" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Eventi Document Monitor</CardTitle>
                <p className="text-sm text-gray-600">
                  Gestisci gli eventi e contatori del sistema di monitoraggio documenti
                </p>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Supporto per la compatibilità con i vecchi campi pdf_monitor_events */}
                {(status.document_monitor_events || status.pdf_monitor_events) && !(status.document_monitor_events?.error && status.pdf_monitor_events?.error) && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm font-medium">Eventi Totali</p>
                        <p className="text-lg font-bold">{status.document_monitor_events?.total_events || status.pdf_monitor_events?.total_events || 0}</p>
                      </div>
                    </div>
                    
                    {/* Supporto per la compatibilità con entrambi gli schemi */}
                    {(status.document_monitor_events?.by_status || status.pdf_monitor_events?.by_status) && (
                      <div>
                        <p className="text-sm font-medium mb-2">Per Stato</p>
                        <div className="grid grid-cols-2 gap-2">
                          {Object.entries(status.document_monitor_events?.by_status || status.pdf_monitor_events?.by_status || {}).map(([status_name, count]) => (
                            <div key={status_name} className="flex justify-between">
                              <Badge variant="outline">{status_name}</Badge>
                              <span className="font-bold">{count}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
                
                <div className="flex flex-col gap-2">
                  <Button 
                    onClick={() => handleReset('document-monitor-events')}
                    variant="destructive"
                    disabled={resetLoading['document-monitor-events']}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    {resetLoading['document-monitor-events'] ? 'Resettando...' : 'Reset Eventi Document Monitor'}
                  </Button>
                  
                  {/* Mostra anche il pulsante vecchio per retrocompatibilità */}
                  <Button 
                    onClick={() => handleReset('pdf-monitor-events')}
                    variant="outline"
                    size="sm"
                    disabled={resetLoading['pdf-monitor-events']}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    {resetLoading['pdf-monitor-events'] ? 'Resettando...' : 'Reset Eventi PDF Monitor (Legacy)'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="reset" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <AlertTriangle className="h-5 w-5 mr-2 text-yellow-500" />
                  Reset Sistema
                </CardTitle>
                <p className="text-sm text-gray-600">
                  Operazioni di reset per ripristinare il sistema. Attenzione: queste operazioni non possono essere annullate.
                </p>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4">
                  <div className="p-4 border rounded-lg">
                    <h3 className="font-semibold mb-2">Reset Completo</h3>
                    <p className="text-sm text-gray-600 mb-3">
                      Resetta vector store, eventi Document Monitor e contatori. Equivale a ripartire da zero.
                    </p>
                    <Button 
                      onClick={() => handleReset('all')}
                      variant="destructive"
                      disabled={resetLoading.all}
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      {resetLoading.all ? 'Resettando tutto...' : 'Reset Completo Sistema'}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
};

export default DatabaseManagement;
