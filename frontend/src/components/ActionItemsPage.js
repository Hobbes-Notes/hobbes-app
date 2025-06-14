import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useOutletContext, useNavigate } from 'react-router-dom';
import { useApiService } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import ProjectTagManager from './ProjectTagManager';

const ActionItemsPage = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);
  const [filteredActionItems, setFilteredActionItems] = useState([]);

  const { actionItemId } = useParams();
  const { actionItems = [], projects = [] } = useOutletContext();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { getAllNotes } = useApiService();

  // Filter action items when selected project changes
  useEffect(() => {
    if (selectedProject) {
      setFilteredActionItems(actionItems.filter(item => 
        item.projects && item.projects.includes(selectedProject)
      ));
    } else {
      setFilteredActionItems(actionItems);
    }
  }, [selectedProject, actionItems]);

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

  // Show all action items
  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Action Items</h1>
        
        {/* Project Filter */}
        <div className="flex items-center space-x-2">
          <label htmlFor="project-filter" className="text-sm text-gray-600">Filter by Project:</label>
          <select
            id="project-filter"
            value={selectedProject || ''}
            onChange={(e) => setSelectedProject(e.target.value || null)}
            className="rounded-md border-gray-300 text-sm focus:border-blue-500 focus:ring-blue-500"
          >
            <option value="">All Projects</option>
            {projects.map(project => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </div>
      </div>
      
      <div className="space-y-4">
        {filteredActionItems.map((item) => (
          <div
            key={item.id}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-lg font-medium text-gray-900">
                {item.task}
              </h3>
              <span className={`px-2 py-1 text-xs font-medium rounded ${
                item.status === 'completed' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {item.status}
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600 mb-3">
              {item.doer && (
                <div>
                  <span className="font-medium">Doer:</span> {item.doer}
                </div>
              )}
              {item.deadline && (
                <div>
                  <span className="font-medium">Deadline:</span> {new Date(item.deadline).toLocaleDateString()}
                </div>
              )}
              {item.theme && (
                <div>
                  <span className="font-medium">Theme:</span> {item.theme}
                </div>
              )}
            </div>

            {item.context && (
              <p className="text-gray-700 mb-3 line-clamp-2">
                {item.context}
              </p>
            )}

            {item.projects && item.projects.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-3">
                {item.projects.map(projectId => (
                  <button
                    key={projectId}
                    onClick={() => navigate(`/projects/${projectId}`)}
                    className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded hover:bg-blue-200 transition-colors"
                  >
                    {getProjectName(projectId)}
                  </button>
                ))}
              </div>
            )}

            <div className="text-xs text-gray-500">
              Created: {new Date(item.created_at).toLocaleDateString()}
              {item.source_note_id && (
                <span className="ml-2">• Source Note: 
                  <button
                    onClick={() => handleNoteClick(item.source_note_id)}
                    className="font-mono text-xs bg-blue-100 hover:bg-blue-200 text-blue-800 px-1 py-0.5 rounded transition-colors cursor-pointer"
                    title="Click to view note"
                  >
                    {item.source_note_id}
                  </button>
                </span>
              )}
            </div>
          </div>
        ))}

        {filteredActionItems.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-500">
              <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No action items</h3>
              <p className="mt-1 text-sm text-gray-500">
                {selectedProject ? 'No action items found for this project.' : 'Get started by creating your first action item.'}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ActionItemsPage; 