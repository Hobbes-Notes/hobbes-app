import React, { useState, useEffect, useCallback } from 'react';
import { Outlet, useParams } from 'react-router-dom';
import { useApiService } from '../services/api';
import Sidebar from './Sidebar';
import GlobalNoteInput from './GlobalNoteInput';
import { useAuth } from '../hooks/useAuth';

const ProjectsPage = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { user } = useAuth();
  const { projectId } = useParams();
  const { getProjects } = useApiService();

  const fetchProjects = useCallback(async () => {
    if (!user) return; // Don't fetch if there's no user

    try {
      setLoading(true);
      setError(null);
      const response = await getProjects(user.id);
      setProjects(response.data);
    } catch (error) {
      console.error('Error fetching projects:', error);
      setError('Failed to load projects. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [getProjects, user]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handleProjectUpdated = useCallback(async () => {
    await fetchProjects();
  }, [fetchProjects]);

  const handleNoteCreated = useCallback((newNote) => {
    // Update projects list if the note is linked to any projects
    if (newNote.linked_projects?.length > 0) {
      fetchProjects();
    }
  }, [fetchProjects]);

  if (error) {
    return (
      <div className="p-4 text-red-600 bg-red-100 rounded-lg">
        {error}
      </div>
    );
  }

  if (loading && projects.length === 0) {
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
        <Outlet context={{ onNoteCreated: handleNoteCreated }} />
      </main>
      <div className="fixed bottom-0 right-0 w-[calc(100%-16rem)] bg-white border-t border-gray-200 shadow-lg">
        <GlobalNoteInput 
          projects={projects} 
          onNoteCreated={handleNoteCreated}
        />
      </div>
    </div>
  );
};

export default ProjectsPage; 