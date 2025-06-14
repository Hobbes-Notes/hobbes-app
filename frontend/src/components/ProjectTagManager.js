import React, { useState } from 'react';
import { useApiService } from '../services/api';

const ProjectTagManager = ({ actionItem, projects, onUpdate }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedProjects, setSelectedProjects] = useState(actionItem.projects || []);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { updateActionItem } = useApiService();

  const handleToggleProject = (projectId) => {
    setSelectedProjects(prev => {
      if (prev.includes(projectId)) {
        return prev.filter(id => id !== projectId);
      } else {
        return [...prev, projectId];
      }
    });
  };

  const handleSave = async () => {
    try {
      setIsSubmitting(true);
      await updateActionItem(actionItem.id, {
        ...actionItem,
        projects: selectedProjects
      });
      onUpdate(selectedProjects);
      setIsOpen(false);
    } catch (error) {
      console.error('Error updating project tags:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="text-sm text-blue-600 hover:text-blue-800 flex items-center space-x-1"
      >
        <span>{isOpen ? 'Close' : 'Manage Projects'}</span>
        <svg
          className={`w-4 h-4 transform transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute z-10 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 p-4">
          <h3 className="text-sm font-medium text-gray-900 mb-3">Select Projects</h3>
          
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {projects.map(project => (
              <label
                key={project.id}
                className="flex items-center space-x-2 text-sm text-gray-700 hover:bg-gray-50 p-2 rounded cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={selectedProjects.includes(project.id)}
                  onChange={() => handleToggleProject(project.id)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span>{project.name}</span>
              </label>
            ))}
          </div>

          <div className="mt-4 flex justify-end space-x-2">
            <button
              onClick={() => setIsOpen(false)}
              className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSubmitting}
              className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {isSubmitting ? 'Saving...' : 'Save'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectTagManager; 