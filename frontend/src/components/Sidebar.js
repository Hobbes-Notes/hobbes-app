import React, { useState } from 'react';
import { Link, useNavigate, useLocation, useParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useApiService } from '../services/api';
import { PlusIcon, TrashIcon } from 'lucide-react';

const Sidebar = ({ projects, onProjectCreated, onProjectDeleted }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { projectId: currentProjectId } = useParams();
  const { createProject, deleteProject } = useApiService();
  const [isCreating, setIsCreating] = useState(false);
  const [newProject, setNewProject] = useState({ name: '', description: '' });
  const [error, setError] = useState(null);
  const [showNewProjectForm, setShowNewProjectForm] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState(null);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleCreateProject = async (e) => {
    e.preventDefault();
    if (!newProject.name.trim() || isCreating) return;

    try {
      setIsCreating(true);
      setError(null);
      const response = await createProject({
        ...newProject,
        user_id: user.id
      });
      setNewProject({ name: '', description: '' });
      setShowNewProjectForm(false);
      if (onProjectCreated) {
        await onProjectCreated();
      }
      navigate(`/projects/${response.data.id}`);
    } catch (error) {
      console.error('Error creating project:', error);
      setError('Failed to create project. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteProject = async (projectId) => {
    try {
      await deleteProject(projectId);
      if (onProjectDeleted) {
        await onProjectDeleted();
      }
      setProjectToDelete(null);
      setError(null);
      navigate('/projects');
    } catch (error) {
      console.error('Error deleting project:', error);
      setError('Failed to delete project. Please try again.');
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Delete Confirmation Modal */}
      {projectToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Delete Project</h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete this project? This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-4">
              <button
                onClick={() => {
                  setProjectToDelete(null);
                  setError(null);
                }}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteProject(projectToDelete)}
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
            <button
              onClick={() => setShowNewProjectForm(true)}
              className="w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              New Project
            </button>
          </div>

          {error && (
            <div className="mt-2 p-3 text-sm text-red-700 bg-red-100 rounded-lg">
              {error}
            </div>
          )}

          {showNewProjectForm && (
            <form onSubmit={handleCreateProject} className="mt-3 space-y-3">
              <input
                type="text"
                value={newProject.name}
                onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                placeholder="Project name"
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
              <textarea
                value={newProject.description}
                onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                placeholder="Description (optional)"
                className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows="3"
              />
              <div className="flex space-x-2">
                <button
                  type="submit"
                  disabled={!newProject.name.trim() || isCreating}
                  className={`flex-1 px-3 py-2 text-sm font-medium text-white rounded-md ${
                    !newProject.name.trim() || isCreating
                      ? 'bg-gray-300 cursor-not-allowed'
                      : 'bg-blue-500 hover:bg-blue-600'
                  }`}
                >
                  {isCreating ? 'Creating...' : 'Create'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowNewProjectForm(false);
                    setNewProject({ name: '', description: '' });
                    setError(null);
                  }}
                  className="px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </form>
          )}

          {/* Projects List */}
          <div className="mt-3 space-y-0.5">
            {projects?.map((project) => (
              <div
                key={project.id}
                className={`group flex items-center justify-between px-4 py-2 rounded-lg transition-colors ${
                  currentProjectId === project.id
                    ? 'bg-blue-50 text-blue-700'
                    : 'hover:bg-gray-50'
                }`}
              >
                <button
                  onClick={() => navigate(`/projects/${project.id}`)}
                  className="flex-1 text-left truncate"
                >
                  <span className="font-medium">{project.name}</span>
                </button>
                <button
                  onClick={() => setProjectToDelete(project.id)}
                  className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-opacity"
                  title="Delete project"
                >
                  <TrashIcon className="w-4 h-4" />
                </button>
              </div>
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