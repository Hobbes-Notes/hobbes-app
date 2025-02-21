import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { createProject, deleteProject } from '../services/api';

const Sidebar = ({ projects, onProjectCreated, onProjectDeleted }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isCreating, setIsCreating] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [error, setError] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;
    
    try {
      setIsCreating(true);
      setError(null);
      const response = await createProject({
        name: newProjectName.trim(),
        user_id: user.id
      });
      setNewProjectName('');
      if (onProjectCreated) {
        onProjectCreated();
      }
    } catch (error) {
      console.error('Error creating project:', error);
      setError('Failed to create project. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteClick = (e, project) => {
    e.preventDefault();
    e.stopPropagation();
    setDeleteConfirm(project);
  };

  const handleDeleteConfirm = async () => {
    if (!deleteConfirm) return;
    
    try {
      await deleteProject(deleteConfirm.id);
      
      // Navigate away if we're on the deleted project's page
      if (location.pathname.includes(deleteConfirm.id)) {
        navigate('/projects');
      }
      
      // Call the onProjectDeleted callback to refresh the projects list
      if (onProjectDeleted) {
        onProjectDeleted();
      }
      
      setDeleteConfirm(null);
    } catch (error) {
      console.error('Error deleting project:', error);
      setError('Failed to delete project. Please try again.');
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Delete Project</h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete "{deleteConfirm.name}"? This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-4">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteConfirm}
                className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Projects Section */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-3">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Projects</h2>
          
          {/* New Project Form */}
          <div className="mt-2">
            <input
              type="text"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              placeholder="New project name"
              className="w-full px-2 py-1.5 text-sm border rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              onKeyPress={(e) => e.key === 'Enter' && handleCreateProject()}
            />
            {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
          </div>

          {/* Projects List */}
          <div className="mt-3 space-y-0.5">
            {projects?.map((project) => (
              <Link
                key={project.id}
                to={`/projects/${project.id}`}
                className={`group flex items-center justify-between px-2 py-1.5 rounded text-sm ${
                  location.pathname.includes(project.id)
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <span className="truncate flex-1">{project.name}</span>
                {project.name !== 'Miscellaneous' && (
                  <button
                    onClick={(e) => handleDeleteClick(e, project)}
                    className="opacity-0 group-hover:opacity-100 p-0.5 rounded-full hover:bg-red-100 transition-opacity ml-2"
                  >
                    <svg
                      className="w-3.5 h-3.5 text-gray-400 hover:text-red-500 transition-colors"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                  </button>
                )}
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* User Controls Section */}
      <div className="border-t border-gray-200 p-3">
        {user && (
          <div className="flex items-center space-x-2 mb-2">
            {user.picture_url && (
              <img
                src={user.picture_url}
                alt={user.name}
                className="w-6 h-6 rounded-full"
              />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {user.name}
              </p>
              <p className="text-xs text-gray-500 truncate">{user.email}</p>
            </div>
          </div>
        )}
        <div className="space-y-0.5">
          <Link
            to="/profile"
            className={`block w-full text-left px-2 py-1.5 text-sm rounded ${
              location.pathname === '/profile'
                ? 'bg-blue-50 text-blue-700'
                : 'text-gray-600 hover:bg-gray-50'
            }`}
          >
            Profile
          </Link>
          <button
            onClick={handleLogout}
            className="w-full text-left px-2 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
};

export default Sidebar; 