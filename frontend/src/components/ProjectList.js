import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, useLocation, Link, Outlet } from 'react-router-dom';
import { getProjects, createProject, getAllNotes } from '../services/api';
import { PlusIcon } from 'lucide-react';

const ProjectList = () => {
  const [projects, setProjects] = useState([]);
  const [notes, setNotes] = useState([]);
  const [newProject, setNewProject] = useState({ name: '', description: '' });
  const [loading, setLoading] = useState(true);
  const [showNewProjectForm, setShowNewProjectForm] = useState(false);
  const navigate = useNavigate();
  const { projectId } = useParams();
  const location = useLocation();
  const isNotesTab = location.pathname.startsWith('/notes');

  useEffect(() => {
    if (isNotesTab) {
      fetchNotes();
    } else {
      fetchProjects();
    }
  }, [isNotesTab]);

  const fetchProjects = async () => {
    try {
      const response = await getProjects();
      setProjects(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching projects:', error);
      setLoading(false);
    }
  };

  const fetchNotes = async () => {
    try {
      const response = await getAllNotes();
      const sortedNotes = response.data.sort((a, b) => 
        new Date(b.created_at) - new Date(a.created_at)
      );
      setNotes(sortedNotes);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching notes:', error);
      setLoading(false);
    }
  };

  const handleCreateProject = async (e) => {
    e.preventDefault();
    try {
      const response = await createProject(newProject);
      setNewProject({ name: '', description: '' });
      await fetchProjects();
      setShowNewProjectForm(false);
      navigate(`/projects/${response.data.id}`);
    } catch (error) {
      console.error('Error creating project:', error);
    }
  };

  const ProjectsTab = () => (
    <div className="space-y-4">
      <button 
        onClick={() => setShowNewProjectForm(true)}
        className="w-full flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
      >
        <PlusIcon className="w-4 h-4 mr-2" />
        New Project
      </button>
      <div className="border-t border-gray-200" />
      {projects.map((project) => (
        <button
          key={project.id}
          onClick={() => navigate(`/projects/${project.id}`)}
          className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
            projectId === project.id 
              ? 'bg-blue-50 text-blue-700 font-medium border border-blue-100' 
              : 'hover:bg-gray-50'
          }`}
        >
          <div className="font-medium text-gray-900 truncate">{project.name}</div>
        </button>
      ))}
    </div>
  );

  const NotesTab = () => (
    <div className="space-y-4">
      {notes.map((note) => (
        <button
          key={note.id}
          onClick={() => navigate(`/notes/${note.id}`)}
          className="w-full text-left bg-white rounded-lg shadow-sm border border-gray-200 p-3 hover:shadow-md transition-shadow hover:border-gray-300"
        >
          <div className="text-sm text-gray-900 truncate">
            {note.content}
          </div>
          <div className="mt-1 text-xs text-gray-500">
            {new Date(note.created_at).toLocaleString()}
          </div>
        </button>
      ))}
    </div>
  );

  return (
    <div className="h-full flex">
      {/* Sidebar */}
      <div className="w-80 border-r bg-gray-50/40 flex-shrink-0 flex flex-col">
        <div className="p-4 flex-1 flex flex-col min-h-0">
          {/* Tabs */}
          <div className="flex space-x-1 mb-4">
            <Link
              to="/projects"
              className={`flex-1 text-center px-4 py-2 text-sm font-medium rounded-md ${
                !isNotesTab
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Projects
            </Link>
            <Link
              to="/notes"
              className={`flex-1 text-center px-4 py-2 text-sm font-medium rounded-md ${
                isNotesTab
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Notes
            </Link>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="text-gray-500">Loading...</div>
              </div>
            ) : isNotesTab ? (
              <NotesTab />
            ) : (
              <ProjectsTab />
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto min-h-0">
        <Outlet />
      </div>

      {/* New Project Modal */}
      {showNewProjectForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Create New Project</h3>
              <button 
                onClick={() => setShowNewProjectForm(false)}
                className="text-gray-400 hover:text-gray-500"
              >
                ×
              </button>
            </div>
            <form onSubmit={handleCreateProject} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Name</label>
                <input
                  type="text"
                  value={newProject.name}
                  onChange={(e) => setNewProject({ ...newProject, name: e.target.value })}
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  value={newProject.description}
                  onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                  rows="3"
                  className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <button
                type="submit"
                className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                Create Project
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectList; 