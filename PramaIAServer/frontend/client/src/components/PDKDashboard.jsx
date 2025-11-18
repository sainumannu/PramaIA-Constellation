/**
 * PDK Management Dashboard - Main Component
 */

import React, { useState } from 'react';
import PDKPluginList from './PDKPluginList';
import PDKEventSourcesList from './PDKEventSourcesList';

const PDKDashboard = () => {
  const [activeTab, setActiveTab] = useState('plugins');

  const tabs = [
    { id: 'plugins', name: 'Plugin', icon: '🔌', component: PDKPluginList },
    { id: 'event-sources', name: 'Event Sources', icon: '⚡', component: PDKEventSourcesList }
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component || PDKPluginList;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">PramaIA PDK Dashboard</h1>
              <span className="text-sm text-gray-500">Plugin Development Kit Management</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 bg-green-400 rounded-full"></div>
              <span className="text-sm text-gray-600">PDK Server Active</span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-purple-500 text-purple-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="text-lg">{tab.icon}</span>
                <span>{tab.name}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ActiveComponent />
      </div>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-500">
              PramaIA PDK System • Tag Management • v1.0.0
            </div>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span>🏷️ Tag System Active</span>
              <span>🔧 Plugin API Ready</span>
              <span>⚡ Event Sources Ready</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default PDKDashboard;
