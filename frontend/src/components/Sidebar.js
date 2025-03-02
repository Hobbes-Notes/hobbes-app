import React, { useState } from 'react';
import { Link, useNavigate, useLocation, useParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useApiService } from '../services/api';
import { PlusIcon } from 'lucide-react';
import ProjectFormModal from './ProjectFormModal';
import ProjectTreeItem from './ProjectTreeItem';

const Sidebar = ({ projects, onProjectCreated, onProjectDeleted }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { projectId: currentProjectId } = useParams();
  const { createProject, updateProject, deleteProject } = useApiService();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [showProjectForm, setShowProjectForm] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [selectedParentId, setSelectedParentId] = useState(null);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const handleCreateProject = async (projectData) => {
    try {
      setIsSubmitting(true);
      setError(null);
      
      // Find parent project if we have a parent_id
      const parentProject = selectedParentId ? 
        projects.find(p => p.id === selectedParentId) : null;
      
      // Check nesting level before making the API call
      if (parentProject) {
        const parentLevel = parentProject.level || 1;
        if (parentLevel >= 3) {
          setError("Cannot create project: Maximum nesting level (3) exceeded");
          setIsSubmitting(false);
          return;
        }
      }
      
      const response = await createProject({
        ...projectData,
        user_id: user.id,
        parent_id: selectedParentId
      });
      
      setShowProjectForm(false);
      setSelectedParentId(null);
      if (onProjectCreated) {
        await onProjectCreated();
      }
      navigate(`/projects/${response.data.id}`);
    } catch (error) {
      console.error('Error creating project:', error);
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
      const errorMessage = error.response?.data?.detail || 'Failed to update project. Please try again.';
      setError(errorMessage);
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
      setError(null);
      navigate('/projects');
    } catch (error) {
      console.error('Error deleting project:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to delete project. Please try again.';
      setError(errorMessage);
    }
  };

  const handleCloseForm = () => {
    setShowProjectForm(false);
    setEditingProject(null);
    setSelectedParentId(null);
    setError(null);
  };

  const handleAddChild = (parentId) => {
    setSelectedParentId(parentId);
    setShowProjectForm(true);
  };

  // Get root level projects
  const rootProjects = projects.filter(p => !p.parent_id);

  return (
    <div className="h-full flex flex-col">
      {/* Project Form Modal */}
      <ProjectFormModal
        isOpen={showProjectForm || editingProject !== null}
        onClose={handleCloseForm}
        onSubmit={editingProject ? handleEditProject : handleCreateProject}
        initialData={editingProject || { name: '', description: '' }}
        title={editingProject ? 'Edit Project' : (selectedParentId ? 'New Child Project' : 'New Project')}
        submitLabel={editingProject ? 'Save' : 'Create'}
        isSubmitting={isSubmitting}
        error={error}
        projects={projects}
        editingProjectId={editingProject?.id}
      />

      {/* Projects Section */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-3">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">Projects</h2>
          
          {/* New Project Button */}
          <div className="mt-2">
            <button
              onClick={() => {
                setSelectedParentId(null);
                setShowProjectForm(true);
              }}
              className="w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              New Project
            </button>
          </div>

          {/* Projects Tree */}
          <div className="mt-3 space-y-0.5">
            {rootProjects.map((project) => (
              <ProjectTreeItem
                key={project.id}
                project={project}
                projects={projects}
                currentProjectId={currentProjectId}
                onNavigate={(id) => navigate(`/projects/${id}`)}
                onAddChild={handleAddChild}
                onEdit={setEditingProject}
                onDelete={handleDeleteProject}
              />
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