import React, { useState } from 'react';
import { Link, useNavigate, useLocation, useParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useApiService } from '../services/api';
import { PlusIcon, TrashIcon, PencilIcon } from 'lucide-react';
import ProjectFormModal from './ProjectFormModal';

const Sidebar = ({ projects, onProjectCreated, onProjectDeleted }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { projectId: currentProjectId } = useParams();
  const { createProject, updateProject, deleteProject } = useApiService();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [showProjectForm, setShowProjectForm] = useState(false);
  const [projectToDelete, setProjectToDelete] = useState(null);
  const [editingProject, setEditingProject] = useState(null);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleCreateProject = async (projectData) => {
    try {
      setIsSubmitting(true);
      setError(null);
      const response = await createProject({
        ...projectData,
        user_id: user.id
      });
      setShowProjectForm(false);
      if (onProjectCreated) {
        await onProjectCreated();
      }
      navigate(`/projects/${response.data.id}`);
    } catch (error) {
      console.error('Error creating project:', error);
      // Extract error message from the response if available
      const errorMessage = error.response?.data?.detail || 'Failed to create project. Please try again.';
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditProject = async (projectData) => {
    if (!editingProject) return;
    
    try {
      setIsSubmitting(true);
      setError(null);
      await updateProject(editingProject.id, {
        name: projectData.name,
        description: projectData.description,
        user_id: user.id
      });
      setEditingProject(null);
      if (onProjectCreated) {
        await onProjectCreated();
      }
    } catch (error) {
      console.error('Error updating project:', error);
      setError('Failed to update project. Please try again.');
    } finally {
      setIsSubmitting(false);
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

  const handleCloseForm = () => {
    setShowProjectForm(false);
    setEditingProject(null);
    setError(null);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Project Form Modal */}
      <ProjectFormModal
        isOpen={showProjectForm || editingProject !== null}
        onClose={handleCloseForm}
        onSubmit={editingProject ? handleEditProject : handleCreateProject}
        initialData={editingProject || { name: '', description: '' }}
        title={editingProject ? 'Edit Project' : 'New Project'}
        submitLabel={editingProject ? 'Save' : 'Create'}
        isSubmitting={isSubmitting}
        error={error}
        projects={projects}
        editingProjectId={editingProject?.id}
      />

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
          
          {/* New Project Button */}
          <div className="mt-2">
            <button
              onClick={() => setShowProjectForm(true)}
              className="w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              New Project
            </button>
          </div>

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
                <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setEditingProject(project);
                    }}
                    className="p-1 text-gray-400 hover:text-blue-500 transition-colors"
                    title="Edit project"
                  >
                    <PencilIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setProjectToDelete(project.id);
                    }}
                    className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                    title="Delete project"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
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