import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, Outlet } from 'react-router-dom';
import { getProjects, createProject } from '../services/api';
import { PlusIcon } from 'lucide-react';

const ProjectList = () => {
  const [projects, setProjects] = useState([]);
  const [newProject, setNewProject] = useState({ name: '', description: '' });
  const [loading, setLoading] = useState(true);
  const [showNewProjectForm, setShowNewProjectForm] = useState(false);
  const navigate = useNavigate();
  const { projectId } = useParams();

  useEffect(() => {
    fetchProjects();
  }, []);

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

  const handleCreateProject = async (e) => {
    e.preventDefault();
    try {
      await createProject(newProject);
      setNewProject({ name: '', description: '' });
      fetchProjects();
      setShowNewProjectForm(false);
    } catch (error) {
      console.error('Error creating project:', error);
    }
  };

  const ProjectSidebar = () => (
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
          className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
            projectId === project.id 
              ? 'bg-gray-100 font-medium' 
              : 'hover:bg-gray-50'
          }`}
        >
          <div className="font-medium text-gray-900">{project.name}</div>
          {project.description && (
            <div className="text-sm text-gray-500 truncate mt-1">
              {project.description}
            </div>
          )}
        </button>
      ))}
    </div>
  );

  return (
    <div className="h-screen flex">
      {/* Sidebar */}
      <div className="w-80 border-r bg-gray-50/40">
        <div className="p-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Projects</h2>
          <div className="h-[calc(100vh-8rem)] overflow-y-auto">
            <ProjectSidebar />
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        <div className="h-full p-8">
          {showNewProjectForm ? (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
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
          ) : projectId ? (
            <Outlet />
          ) : (
            <div className="max-w-md mx-auto text-center mt-20">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Welcome to Project Notes</h2>
              <p className="text-gray-600">
                Select a project from the sidebar or create a new one to get started.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProjectList; 