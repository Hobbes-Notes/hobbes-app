import React from 'react';
import { useNavigate } from 'react-router-dom';

const ActionItemsList = ({ actionItems = [], projects = [], selectedProject = null }) => {
  const navigate = useNavigate();

  // Filter action items based on selected project
  const filteredActionItems = selectedProject 
    ? actionItems.filter(item => item.projects && item.projects.includes(selectedProject))
    : actionItems;

  // Get project name by ID
  const getProjectName = (projectId) => {
    const project = projects.find(p => p.id === projectId);
    return project ? project.name : projectId;
  };

  const handleNoteClick = (noteId) => {
    navigate(`/notes/${noteId}`);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Action Items</h1>
        {selectedProject && (
          <p className="text-sm text-gray-600 mt-1">
            Filtered by: {getProjectName(selectedProject)}
          </p>
        )}
      </div>
      
      <div className="space-y-4">
        {filteredActionItems.map((item) => (
          <div
            key={item.id}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => navigate(`/action-items/${item.id}`)}
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
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/projects/${projectId}`);
                    }}
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
                    onClick={(e) => {
                      e.stopPropagation();
                      handleNoteClick(item.source_note_id);
                    }}
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

export default ActionItemsList; 