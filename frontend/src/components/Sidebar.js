import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useLocation, useParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useApiService } from '../services/api';
import { 
  PlusIcon, 
  ChevronDownIcon, 
  ChevronRightIcon,
  FolderIcon,
  StickyNoteIcon,
  CheckSquareIcon
} from 'lucide-react';
import ProjectFormModal from './ProjectFormModal';
import ProjectTreeItem from './ProjectTreeItem';

const Sidebar = ({ 
  projects = [], 
  actionItems = [],
  onProjectCreated, 
  onProjectDeleted 
}) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { projectId: currentProjectId } = useParams();
  const { 
    createProject, 
    updateProject, 
    deleteProject,
    getAllNotes
  } = useApiService();

    // State for collapsible sections
  const [sectionsExpanded, setSectionsExpanded] = useState({
    projects: true,
    notes: false
    // actionItems always visible, no collapse needed
  });

  // State for data
  const [notes, setNotes] = useState([]);
  const [allNotes, setAllNotes] = useState([]);
  const [loading, setLoading] = useState({
    notes: false
  });

  // State for project form
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [showProjectForm, setShowProjectForm] = useState(false);
  const [editingProject, setEditingProject] = useState(null);
  const [selectedParentId, setSelectedParentId] = useState(null);

  // Fetch all notes to get total count and first 10 for display
  const fetchNotes = useCallback(async () => {
    if (!user || loading.notes) return;

    try {
      setLoading(prev => ({ ...prev, notes: true }));
      console.log('🔍 Sidebar: Fetching notes for user:', user.id);
      const response = await getAllNotes(user.id);
      console.log('📝 Sidebar: Notes response:', response.data);
      
      if (response.data && response.data.items) {
        console.log('✅ Sidebar: Setting notes - Total:', response.data.items.length, 'Showing:', Math.min(10, response.data.items.length));
        setAllNotes(response.data.items); // Store all notes for count
        setNotes(response.data.items.slice(0, 10)); // Show first 10 for display
      }
    } catch (error) {
      console.error('❌ Sidebar: Error fetching notes:', error);
    } finally {
      setLoading(prev => ({ ...prev, notes: false }));
    }
  }, [getAllNotes, user, loading.notes]);

  // Toggle section expansion (only for notes and projects)
  const toggleSection = (section) => {
    setSectionsExpanded(prev => {
      const newState = { ...prev, [section]: !prev[section] };
      
      // Fetch data when expanding section
      if (newState[section]) {
        if (section === 'notes' && notes.length === 0) {
          fetchNotes();
        }
      }
      
      return newState;
    });
  };

  // Load notes on component mount to show count in sidebar
  useEffect(() => {
    if (allNotes.length === 0) {
      fetchNotes();
    }
  }, [allNotes.length, fetchNotes]);

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

  // Helper function to render section header with collapse toggle (for Projects and Notes only)
  const renderSectionHeader = (section, title, icon, count = null) => (
    <button
      onClick={() => toggleSection(section)}
      className="w-full flex items-center justify-between px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 rounded"
    >
      <div className="flex items-center space-x-2">
        {icon}
        <span className="uppercase tracking-wider">{title}</span>
        {count !== null && (
          <span className="text-xs text-gray-500">({count})</span>
        )}
      </div>
      {sectionsExpanded[section] ? (
        <ChevronDownIcon className="w-4 h-4" />
      ) : (
        <ChevronRightIcon className="w-4 h-4" />
      )}
    </button>
  );

  // Filter root projects (those without a parent)
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

      {/* Collapsible Sections */}
      <div className="flex-1 overflow-y-auto">
        {/* Action Items Section - Click to view all in right panel */}
        <div className="border-b border-gray-200">
          <button
            onClick={() => navigate('/action-items')}
            className={`w-full flex items-center justify-between px-3 py-2 text-sm font-semibold hover:bg-gray-50 rounded ${
              location.pathname.startsWith('/action-items') 
                ? 'bg-blue-50 text-blue-700' 
                : 'text-gray-700'
            }`}
          >
            <div className="flex items-center space-x-2">
              <CheckSquareIcon className="w-4 h-4" />
              <span className="uppercase tracking-wider">Action Items</span>
              {actionItems.length > 0 && (
                <span className="text-xs text-gray-500">({actionItems.length})</span>
              )}
            </div>
          </button>
        </div>

        {/* Projects Section */}
        <div className="border-b border-gray-200">
          {renderSectionHeader(
            'projects', 
            'Projects', 
            <FolderIcon className="w-4 h-4" />, 
            rootProjects.length
          )}
          
          {sectionsExpanded.projects && (
            <div className="px-3 pb-3">
              {/* New Project Button */}
              <div className="mb-3">
                <button
                  onClick={() => {
                    setSelectedParentId(null);
                    setShowProjectForm(true);
                  }}
                  className="w-full flex items-center justify-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  <PlusIcon className="w-4 h-4 mr-2" />
                  New Project
                </button>
              </div>

              {/* Projects Tree */}
              <div className="space-y-0.5">
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
                {rootProjects.length === 0 && (
                  <p className="text-sm text-gray-500 py-4 text-center">
                    No projects yet
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Notes Section */}
        <div className="border-b border-gray-200">
          {renderSectionHeader(
            'notes', 
            'Notes', 
            <StickyNoteIcon className="w-4 h-4" />, 
            allNotes.length
          )}
          
          {sectionsExpanded.notes && (
            <div className="px-3 pb-3">
              {loading.notes ? (
                <div className="flex justify-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-500"></div>
                </div>
              ) : (
                <div className="space-y-1">
                  {notes.map((note) => (
                    <button
                      key={note.id}
                      onClick={() => navigate(`/notes/${note.id}`)}
                      className="w-full text-left px-2 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded truncate"
                    >
                      <div className="truncate">
                        {note.content.substring(0, 50)}
                        {note.content.length > 50 ? '...' : ''}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {new Date(note.created_at).toLocaleDateString()}
                      </div>
                    </button>
                  ))}
                  {notes.length === 0 && !loading.notes && (
                    <p className="text-sm text-gray-500 py-4 text-center">
                      No notes yet
                    </p>
                  )}
                  {allNotes.length > 10 && (
                    <button
                      onClick={() => setNotes(allNotes)}
                      className="w-full mt-2 px-3 py-2 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded transition-colors"
                    >
                      Show All {allNotes.length} Notes
                    </button>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>


    </div>
  );
};

export default Sidebar; 