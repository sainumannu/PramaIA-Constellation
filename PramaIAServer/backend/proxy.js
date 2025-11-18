// proxy.js - Middleware per il proxy delle richieste PDK
const { createProxyMiddleware } = require('http-proxy-middleware');

// Funzione per configurare il proxy PDK
function setupPDKProxy(app) {
  // Proxy per le richieste PDK - inoltra le richieste al server PDK
  app.use('/api/pdk', createProxyMiddleware({
  target: process.env.PDK_SERVER_BASE_URL || process.env.REACT_APP_PDK_SERVER_BASE_URL || 'http://localhost:3001',
    pathRewrite: {
      '^/api/pdk/plugins': '/api/plugins',
      '^/api/pdk/event-sources': '/api/event-sources',
      '^/api/pdk/tags': '/api/tags'
    },
    changeOrigin: true,
    logLevel: 'debug',
    onError: (err, req, res) => {
      console.error('Proxy error:', err);
      res.status(500).json({
        error: 'Proxy Error',
        message: 'Impossibile connettersi al server PDK',
        details: err.message
      });
    }
  }));
  
  console.log(`PDK Proxy configurato - inoltro richieste a ${process.env.PDK_SERVER_BASE_URL || process.env.REACT_APP_PDK_SERVER_BASE_URL || 'http://localhost:3001'}`);
}

module.exports = setupPDKProxy;
