import React, { useState, useEffect } from 'react';
import { useParams, useOutletContext, useNavigate } from 'react-router-dom';
import { useApiService } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import ProjectTagManager from './ProjectTagManager';

const ActionItemsPage = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { actionItemId } = useParams();
  const { actionItems = [], projects = [], onActionItemsUpdate } = useOutletContext();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { getAllNotes } = useApiService();

  const handleNoteClick = (noteId) => {
    navigate(`/notes/${noteId}`);
  };

  // If specific action item is selected, show only that one
  const selectedActionItem = actionItemId ? 
    actionItems.find(item => item.id === actionItemId) : null;

  // Get project name by ID
  const getProjectName = (projectId) => {
    const project = projects.find(p => p.id === projectId);
    return project ? project.name : projectId;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="p-4 text-red-600 bg-red-100 rounded-lg">
          {error}
        </div>
      </div>
    );
  }

  // Show individual action item details
  if (selectedActionItem) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold text-gray-900">
              {selectedActionItem.task}
            </h1>
            <span className={`px-3 py-1 text-sm font-medium rounded-full ${
              selectedActionItem.status === 'completed' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              {selectedActionItem.status}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {selectedActionItem.doer && (
              <div>
                <h3 className="text-sm font-medium text-gray-500">Assigned to</h3>
                <p className="mt-1 text-gray-900">{selectedActionItem.doer}</p>
              </div>
            )}
            
            {selectedActionItem.deadline && (
              <div>
                <h3 className="text-sm font-medium text-gray-500">Deadline</h3>
                <p className="mt-1 text-gray-900">
                  {new Date(selectedActionItem.deadline).toLocaleDateString()}
                </p>
              </div>
            )}

            {selectedActionItem.theme && (
              <div>
                <h3 className="text-sm font-medium text-gray-500">Theme</h3>
                <p className="mt-1 text-gray-900">{selectedActionItem.theme}</p>
              </div>
            )}

            <div>
              <h3 className="text-sm font-medium text-gray-500">Type</h3>
              <p className="mt-1 text-gray-900 capitalize">{selectedActionItem.type}</p>
            </div>
          </div>

          {selectedActionItem.context && (
            <div className="mb-6">
              <h3 className="text-sm font-medium text-gray-500 mb-2">Context</h3>
              <p className="text-gray-900 whitespace-pre-wrap">{selectedActionItem.context}</p>
            </div>
          )}

          {selectedActionItem.projects && selectedActionItem.projects.length > 0 && (
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-500">Related Projects</h3>
                <ProjectTagManager
                  actionItem={selectedActionItem}
                  projects={projects}
                  onUpdate={(updatedProjects) => {
                    // Update the action item in the list
                    const updatedActionItem = {
                      ...selectedActionItem,
                      projects: updatedProjects
                    };
                    const updatedActionItems = actionItems.map(item =>
                      item.id === selectedActionItem.id ? updatedActionItem : item
                    );
                    // Update the context
                    if (typeof onActionItemsUpdate === 'function') {
                      onActionItemsUpdate(updatedActionItems);
                    }
                  }}
                />
              </div>
              <div className="flex flex-wrap gap-2">
                {selectedActionItem.projects.map((projectId) => (
                  <button
                    key={projectId}
                    onClick={() => navigate(`/projects/${projectId}`)}
                    className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded hover:bg-blue-200 transition-colors"
                  >
                    {getProjectName(projectId)}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="text-sm text-gray-500 border-t border-gray-200 pt-4">
            <p>Created: {new Date(selectedActionItem.created_at).toLocaleString()}</p>
            <p>Updated: {new Date(selectedActionItem.updated_at).toLocaleString()}</p>
            {selectedActionItem.source_note_id && (
              <p>Source Note: 
                <button
                  onClick={() => handleNoteClick(selectedActionItem.source_note_id)}
                  className="font-mono text-xs bg-blue-100 hover:bg-blue-200 text-blue-800 px-2 py-1 rounded ml-1 transition-colors cursor-pointer"
                  title="Click to view note"
                >
                  {selectedActionItem.source_note_id}
                </button>
              </p>
            )}
          </div>
        </div>
      </div>
    );
  }

  // If no specific action item is selected, show a message to use the home screen
  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="text-center py-12">
        <div className="text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">View All Action Items</h3>
          <p className="mt-1 text-sm text-gray-500">
            Go to the Home screen to view and filter all your action items.
          </p>
          <button
            onClick={() => navigate('/')}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
          >
            Go to Home
          </button>
        </div>
      </div>
    </div>
  );
};

export default ActionItemsPage; 