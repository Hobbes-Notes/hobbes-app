import React, { useState, useEffect } from 'react';
import { Outlet, useParams } from 'react-router-dom';
import { getProjects } from '../services/api';
import Sidebar from './Sidebar';
import GlobalNoteInput from './GlobalNoteInput';
import { useAuth } from '../hooks/useAuth';

const ProjectsPage = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const { projectId } = useParams();

  const fetchProjects = async () => {
    try {
      const response = await getProjects();
      // Filter projects for the current user
      const userProjects = response.data.filter(
        (project) => project.user_id === user.id
      );
      setProjects(userProjects);
    } catch (error) {
      console.error('Error fetching projects:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user) {
      fetchProjects();
    }
  }, [user]);

  const handleProjectUpdated = async () => {
    // Refresh the projects list
    await fetchProjects();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-100 relative">
      <div className="w-64 bg-white border-r border-gray-200 flex-shrink-0">
        <Sidebar 
          projects={projects} 
          onProjectCreated={handleProjectUpdated}
          onProjectDeleted={handleProjectUpdated}
        />
      </div>
      <main className="flex-1 overflow-y-auto pb-32">
        {!projectId && (
          <div className="flex items-center justify-center h-full text-gray-500">
            Select a project or create a new one
          </div>
        )}
        <Outlet />
      </main>
      <div className="fixed bottom-0 right-0 w-[calc(100%-16rem)] bg-white border-t border-gray-200 shadow-lg">
        <GlobalNoteInput 
          projects={projects} 
          onNoteCreated={handleProjectUpdated}
        />
      </div>
    </div>
  );
};

export default ProjectsPage; 