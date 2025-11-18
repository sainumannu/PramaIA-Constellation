import React from 'react';
import WorkflowManagement from '../components/WorkflowManagement.jsx';

const WorkflowManagementPage = () => {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4 text-blue-700">Gestione Workflow</h1>
      <WorkflowManagement />
    </div>
  );
};

export default WorkflowManagementPage;
