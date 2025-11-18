import React, { useState, useEffect, useRef } from 'react';
import { PLUGIN_DOCUMENT_MONITOR_BASE_URL } from '../config/appConfig';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  FileText, 
  Clock, 
  CheckCircle, 
  XCircle, 
  RefreshCw, 
  Upload,
  Database,
  Activity,
  Loader2
} from 'lucide-react';

const DocumentProcessingMonitor = () => {
  const [events, setEvents] = useState([]);
  const [summary, setSummary] = useState({
    total: 0,
    pending: 0,
    processing: 0,
    completed: 0,
    error: 0
  });
  const [isPolling, setIsPolling] = useState(true);
  const intervalRef = useRef(null);

  // Polling per aggiornamenti in tempo reale
  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const response = await fetch(`${PLUGIN_DOCUMENT_MONITOR_BASE_URL}/monitor/events/recent?limit=50`);
        if (response.ok) {
          const data = await response.json();
          const eventsList = data.events || [];
          
          setEvents(eventsList);
          
          // Calcola summary
          const summary = eventsList.reduce((acc, event) => {
            acc.total++;
            acc[event.status] = (acc[event.status] || 0) + 1;
            return acc;
          }, { total: 0, pending: 0, processing: 0, completed: 0, error: 0 });
          
          setSummary(summary);
        }
      } catch (error) {
        console.error('Errore fetching eventi:', error);
      }
    };

    if (isPolling) {
      fetchEvents(); // Fetch iniziale
      intervalRef.current = setInterval(fetchEvents, 2000); // Poll ogni 2 secondi
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isPolling]);

  const togglePolling = () => {
    setIsPolling(!isPolling);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'bg-gray-500';
      case 'processing': return 'bg-blue-500';
      case 'completed': return 'bg-green-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-400';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending': return <Clock className="h-4 w-4" />;
      case 'processing': return <Loader2 className="h-4 w-4 animate-spin" />;
      case 'completed': return <CheckCircle className="h-4 w-4" />;
      case 'error': return <XCircle className="h-4 w-4" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  const getProgressPercentage = () => {
    if (summary.total === 0) return 0;
    return Math.round((summary.completed / summary.total) * 100);
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString('it-IT');
  };

  const recentProcessingEvents = events.filter(e => e.status === 'processing');
  const recentCompletedEvents = events.filter(e => e.status === 'completed').slice(0, 10);
  const recentErrorEvents = events.filter(e => e.status === 'error').slice(0, 10);

  return (
    <div className="space-y-6">
      {/* Header con controlli */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Monitor Vettorizzazione Documenti</h2>
          <p className="text-gray-600">Monitoraggio in tempo reale del processing automatico</p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant={isPolling ? "destructive" : "default"}
            onClick={togglePolling}
            size="sm"
          >
            {isPolling ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Live
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4 mr-2" />
                Stopped
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <FileText className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-sm text-gray-600">Totali</p>
                <p className="text-2xl font-bold">{summary.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-gray-500" />
              <div>
                <p className="text-sm text-gray-600">In Coda</p>
                <p className="text-2xl font-bold">{summary.pending}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
              <div>
                <p className="text-sm text-gray-600">Processing</p>
                <p className="text-2xl font-bold">{summary.processing}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-sm text-gray-600">Completati</p>
                <p className="text-2xl font-bold">{summary.completed}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <XCircle className="h-5 w-5 text-red-500" />
              <div>
                <p className="text-sm text-gray-600">Errori</p>
                <p className="text-2xl font-bold">{summary.error}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Progress Bar */}
      {summary.total > 0 && (
        <Card>
          <CardContent className="p-6">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Progresso Vettorizzazione</span>
                <span>{getProgressPercentage()}%</span>
              </div>
              <Progress value={getProgressPercentage()} className="h-3" />
              <div className="flex justify-between text-xs text-gray-500">
                <span>{summary.completed} completati</span>
                <span>{summary.total} totali</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs per dettagli */}
      <Tabs defaultValue="processing" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="processing">
            In Elaborazione ({recentProcessingEvents.length})
          </TabsTrigger>
          <TabsTrigger value="completed">
            Completati ({recentCompletedEvents.length})
          </TabsTrigger>
          <TabsTrigger value="errors">
            Errori ({recentErrorEvents.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="processing" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
                Documenti in Elaborazione
              </CardTitle>
            </CardHeader>
            <CardContent>
              {recentProcessingEvents.length === 0 ? (
                <p className="text-center text-gray-500 py-8">
                  Nessun documento in elaborazione
                </p>
              ) : (
                <div className="space-y-3">
                  {recentProcessingEvents.map((event) => (
                    <div key={event.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className="animate-pulse">
                          <Database className="h-5 w-5 text-blue-500" />
                        </div>
                        <div>
                          <p className="font-medium">{event.file_name}</p>
                          <p className="text-sm text-gray-500">{event.folder}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge className={getStatusColor(event.status)}>
                          {event.status}
                        </Badge>
                        <p className="text-xs text-gray-500 mt-1">
                          {formatTimestamp(event.timestamp)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="completed" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                Documenti Vettorizzati
              </CardTitle>
            </CardHeader>
            <CardContent>
              {recentCompletedEvents.length === 0 ? (
                <p className="text-center text-gray-500 py-8">
                  Nessun documento completato di recente
                </p>
              ) : (
                <div className="space-y-3">
                  {recentCompletedEvents.map((event) => (
                    <div key={event.id} className="flex items-center justify-between p-3 border rounded-lg bg-green-50">
                      <div className="flex items-center space-x-3">
                        <CheckCircle className="h-5 w-5 text-green-500" />
                        <div>
                          <p className="font-medium">{event.file_name}</p>
                          <p className="text-sm text-gray-500">{event.folder}</p>
                          {event.document_id && (
                            <p className="text-xs text-blue-600">ID: {event.document_id}</p>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge className="bg-green-500 text-white">
                          Completato
                        </Badge>
                        <p className="text-xs text-gray-500 mt-1">
                          {formatTimestamp(event.timestamp)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="errors" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <XCircle className="h-5 w-5 text-red-500" />
                Errori di Elaborazione
              </CardTitle>
            </CardHeader>
            <CardContent>
              {recentErrorEvents.length === 0 ? (
                <p className="text-center text-gray-500 py-8">
                  Nessun errore recente 🎉
                </p>
              ) : (
                <div className="space-y-3">
                  {recentErrorEvents.map((event) => (
                    <div key={event.id} className="flex items-center justify-between p-3 border rounded-lg bg-red-50">
                      <div className="flex items-center space-x-3">
                        <XCircle className="h-5 w-5 text-red-500" />
                        <div>
                          <p className="font-medium">{event.file_name}</p>
                          <p className="text-sm text-gray-500">{event.folder}</p>
                          {event.error_message && (
                            <p className="text-xs text-red-600 mt-1">
                              {event.error_message}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge className="bg-red-500 text-white">
                          Errore
                        </Badge>
                        <p className="text-xs text-gray-500 mt-1">
                          {formatTimestamp(event.timestamp)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DocumentProcessingMonitor;
