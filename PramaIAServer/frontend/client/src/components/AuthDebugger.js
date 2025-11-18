import React, { useState } from 'react';
import { endpoints } from '../services/api';
import { decodeJwtPayload } from '../utils/authUtils';

const AuthDebugger = () => {
  const [debugInfo, setDebugInfo] = useState(null);
  const [loading, setLoading] = useState(false);

  const testAuth = async () => {
    setLoading(true);
    const token = localStorage.getItem('token');
    
    const info = {
      tokenExists: !!token,
      tokenLength: token?.length || 0,
      decodedPayload: null,
      protectedEndpointTest: null,
      adminEndpointTest: null,
      error: null
    };

    try {
      if (token) {
        info.decodedPayload = decodeJwtPayload(token);
        
        // Test /protected/me
        try {
          const protectedResponse = await endpoints.protected.me();
          info.protectedEndpointTest = {
            success: true,
            data: protectedResponse.data
          };
        } catch (e) {
          info.protectedEndpointTest = {
            success: false,
            error: e.message
          };
        }

        // Test admin endpoint
        try {
          const adminResponse = await endpoints.admin.listUsers();
          info.adminEndpointTest = {
            success: true,
            count: adminResponse.data?.length || 0
          };
        } catch (e) {
          info.adminEndpointTest = {
            success: false,
            error: e.message
          };
        }
      }
    } catch (e) {
      info.error = e.message;
    }

    setDebugInfo(info);
    setLoading(false);
  };

  return (
    <div className="bg-gray-100 p-4 rounded-lg m-4">
      <h3 className="text-lg font-bold mb-4">🔍 Auth Debugger</h3>
      
      <button 
        onClick={testAuth}
        disabled={loading}
        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:opacity-50"
      >
        {loading ? 'Testing...' : 'Test Authentication'}
      </button>

      {debugInfo && (
        <div className="mt-4 space-y-2">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <strong>Token Present:</strong> {debugInfo.tokenExists ? '✅' : '❌'}
            </div>
            <div>
              <strong>Token Length:</strong> {debugInfo.tokenLength}
            </div>
          </div>

          {debugInfo.decodedPayload && (
            <div>
              <strong>Decoded Payload:</strong>
              <pre className="bg-gray-200 p-2 text-xs rounded mt-1">
                {JSON.stringify(debugInfo.decodedPayload, null, 2)}
              </pre>
            </div>
          )}

          <div>
            <strong>Protected Endpoint (/protected/me):</strong>
            {debugInfo.protectedEndpointTest?.success ? (
              <span className="text-green-600"> ✅ Success</span>
            ) : (
              <span className="text-red-600"> ❌ {debugInfo.protectedEndpointTest?.error}</span>
            )}
          </div>

          <div>
            <strong>Admin Endpoint (/admin/users):</strong>
            {debugInfo.adminEndpointTest?.success ? (
              <span className="text-green-600"> ✅ Success ({debugInfo.adminEndpointTest.count} users)</span>
            ) : (
              <span className="text-red-600"> ❌ {debugInfo.adminEndpointTest?.error}</span>
            )}
          </div>

          {debugInfo.error && (
            <div className="text-red-600">
              <strong>General Error:</strong> {debugInfo.error}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AuthDebugger;
