import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useApiService } from '../services/api';
import ProjectFormModal from './ProjectFormModal';

const ProjectCard = ({ project, projects, onAddChild, onEdit, onDelete, level = 0, isMyLifeProject = false }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  
  // Find children of this project
  const children = projects.filter(p => p.parent_id === project.id);
  
  return (
    <div className="mb-4 relative">
      {/* Tree Lines */}
      {level > 0 && (
        <div className="absolute left-0 top-0 bottom-0 flex items-start pt-6">
          {/* Vertical line to parent */}
          <div 
            className="border-l-2 border-dotted border-gray-300 h-full"
            style={{ marginLeft: `${(level - 1) * 20 + 10}px` }}
          />
          {/* Horizontal line to card */}
          <div 
            className="border-t-2 border-dotted border-gray-300 w-4 mt-0"
          />
        </div>
      )}
      
      {/* Project Card */}
      <div 
        className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 relative z-10"
        style={{ marginLeft: `${level * 20}px` }}
      >
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <div className="flex items-center mb-2">
              <h3 className="text-lg font-semibold text-gray-900">{project.name}</h3>
              {children.length > 0 && (
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="ml-2 p-1 text-gray-400 hover:text-gray-600"
                >
                  <svg 
                    className={`w-4 h-4 transform transition-transform ${isExpanded ? 'rotate-90' : ''}`}
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              )}
            </div>
            {project.description && (
              <p className="text-gray-600 text-sm mb-3">{project.description}</p>
            )}
            <div className="flex items-center text-xs text-gray-500">
              <span>Created: {new Date(project.created_at).toLocaleDateString()}</span>
              {children.length > 0 && (
                <span className="ml-4">{children.length} subproject{children.length !== 1 ? 's' : ''}</span>
              )}
            </div>
          </div>
          
          {/* Actions */}
          <div className="flex space-x-2 ml-4">
            {/* Only show Add Child button if level < 2 (to limit to 3 levels: 0, 1, 2) */}
            {level < 2 && (
              <button
                onClick={() => onAddChild(project.id)}
                className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                title="Add child project"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </button>
            )}
            {/* Don't allow editing "My Life" project */}
            {!isMyLifeProject && (
              <button
                onClick={() => onEdit(project)}
                className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-md transition-colors"
                title="Edit project"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
            )}
            {/* Don't allow deleting "My Life" project */}
            {!isMyLifeProject && (
              <button
                onClick={() => onDelete(project.id)}
                className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                title="Delete project"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>
      
      {/* Children */}
      {isExpanded && children.length > 0 && (
        <div className="mt-2">
                     {children.map(child => (
             <ProjectCard
               key={child.id}
               project={child}
               projects={projects}
               onAddChild={onAddChild}
               onEdit={onEdit}
               onDelete={onDelete}
               level={level + 1}
               isMyLifeProject={child.name === 'My Life'}
             />
           ))}
        </div>
      )}
    </div>
  );
};

const ProjectsTreePage = () => {
  const { user } = useAuth();
  const { getProjects, createProject, updateProject, deleteProject } = useApiService();
  
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Form states
  const [showProjectForm, setShowProjectForm] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [selectedParentId, setSelectedParentId] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);

  // Fetch projects
  const fetchProjects = async () => {
    if (!user) return;
    
    try {
      setLoading(true);
      const response = await getProjects(user.id);
      setProjects(response.data || []);
    } catch (err) {
      console.error('Error fetching projects:', err);
      setError('Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [user]);

  // Handle project creation
  const handleCreateProject = async (projectData) => {
    try {
      setIsSubmitting(true);
      setFormError(null);
      
      // Find parent project if we have a parent_id
      const parentProject = selectedParentId ? 
        projects.find(p => p.id === selectedParentId) : null;
      
      // Check nesting level before making the API call (limit to 3 levels: 0, 1, 2)
      if (parentProject) {
        // Calculate parent's level by traversing up the tree
        let currentProject = parentProject;
        let level = 0;
        while (currentProject && level < 10) { // safety check to prevent infinite loops
          level++;
          currentProject = projects.find(p => p.id === currentProject.parent_id);
        }
        
        if (level >= 2) {
          setFormError("Cannot create project: Maximum nesting level (3 levels) exceeded");
          setIsSubmitting(false);
          return;
        }
      }
      
      await createProject({
        ...projectData,
        user_id: user.id,
        parent_id: selectedParentId
      });
      
      setShowProjectForm(false);
      setSelectedParentId(null);
      await fetchProjects(); // Refresh the list
    } catch (error) {
      console.error('Error creating project:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to create project. Please try again.';
      setFormError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle project editing
  const handleEditProject = async (projectData) => {
    if (!editingProject) return;
    
    try {
      setIsSubmitting(true);
      setFormError(null);
      await updateProject(editingProject.id, {
        name: projectData.name,
        description: projectData.description,
        user_id: user.id
      });
      setEditingProject(null);
      await fetchProjects(); // Refresh the list
    } catch (error) {
      console.error('Error updating project:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to update project. Please try again.';
      setFormError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle project deletion
  const handleDeleteProject = async (projectId) => {
    if (!window.confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
      return;
    }
    
    try {
      await deleteProject(projectId);
      await fetchProjects(); // Refresh the list
      setError(null);
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
    setFormError(null);
  };

  const handleAddChild = (parentId) => {
    setSelectedParentId(parentId);
    setShowProjectForm(true);
  };

  const handleAddRootProject = () => {
    // For new root projects, set "My Life" as parent if it exists
    const myLifeProject = projects.find(p => p.name === 'My Life' && !p.parent_id);
    setSelectedParentId(myLifeProject ? myLifeProject.id : null);
    setShowProjectForm(true);
  };

  // Get root projects (those without parents)
  const rootProjects = projects.filter(p => !p.parent_id);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
            <p className="text-gray-600 mt-1">Manage your projects in a tree-like structure</p>
          </div>
          <button
            onClick={handleAddRootProject}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md flex items-center space-x-2 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            <span>New Project</span>
          </button>
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="mb-4 p-4 text-red-600 bg-red-100 rounded-lg">
          {error}
        </div>
      )}

      {/* Projects Tree */}
      <div className="space-y-4">
        {rootProjects.length > 0 ? (
          rootProjects.map(project => (
            <ProjectCard
              key={project.id}
              project={project}
              projects={projects}
              onAddChild={handleAddChild}
              onEdit={setEditingProject}
              onDelete={handleDeleteProject}
              level={0}
              isMyLifeProject={project.name === 'My Life'}
            />
          ))
        ) : (
          <div className="text-center py-12">
            <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No projects yet</h3>
            <p className="text-gray-500 mb-4">Get started by creating your first project.</p>
            <button
              onClick={handleAddRootProject}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md inline-flex items-center space-x-2 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              <span>Create Project</span>
            </button>
          </div>
        )}
      </div>

      {/* Project Form Modal */}
      <ProjectFormModal
        isOpen={showProjectForm || editingProject !== null}
        onClose={handleCloseForm}
        onSubmit={editingProject ? handleEditProject : handleCreateProject}
        initialData={editingProject || { name: '', description: '' }}
        title={editingProject ? 'Edit Project' : (selectedParentId ? 'New Child Project' : 'New Project')}
        submitLabel={editingProject ? 'Save' : 'Create'}
        isSubmitting={isSubmitting}
        error={formError}
        projects={projects}
        editingProjectId={editingProject?.id}
        parentProject={selectedParentId ? projects.find(p => p.id === selectedParentId) : null}
      />
    </div>
  );
};

export default ProjectsTreePage; 