import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Outlet, useParams } from 'react-router-dom';
import { useApiService } from '../services/api';
import Sidebar from './Sidebar';
import GlobalNoteInput from './GlobalNoteInput';
import { useAuth } from '../hooks/useAuth';

const MIN_SIDEBAR_WIDTH = 200;
const MAX_SIDEBAR_WIDTH = 600;
const DEFAULT_SIDEBAR_WIDTH = 256;

const ProjectsPage = () => {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    const savedWidth = localStorage.getItem('sidebarWidth');
    return savedWidth ? parseInt(savedWidth, 10) : DEFAULT_SIDEBAR_WIDTH;
  });
  const [isResizing, setIsResizing] = useState(false);
  const sidebarRef = useRef(null);
  const { user } = useAuth();
  const { projectId } = useParams();
  const { getProjects } = useApiService();

  // Handle mouse move during resize
  const handleMouseMove = useCallback((e) => {
    if (!isResizing) return;
    
    const newWidth = Math.min(Math.max(e.clientX, MIN_SIDEBAR_WIDTH), MAX_SIDEBAR_WIDTH);
    setSidebarWidth(newWidth);
  }, [isResizing]);

  // Handle mouse up to stop resizing
  const handleMouseUp = useCallback(() => {
    setIsResizing(false);
    document.body.style.cursor = 'default';
    // Save width to localStorage
    localStorage.setItem('sidebarWidth', sidebarWidth.toString());
  }, [sidebarWidth]);

  // Add and remove event listeners for resize
  useEffect(() => {
    if (isResizing) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'ew-resize';
    }

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'default';
    };
  }, [isResizing, handleMouseMove, handleMouseUp]);

  // Save sidebar width when it changes
  useEffect(() => {
    localStorage.setItem('sidebarWidth', sidebarWidth.toString());
  }, [sidebarWidth]);

  const fetchProjects = useCallback(async () => {
    if (!user) return;

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
    <div className={`flex h-screen bg-gray-100 relative ${isResizing ? 'resizing' : ''}`}>
      <div 
        ref={sidebarRef}
        className="flex-shrink-0 bg-white border-r border-gray-200 relative"
        style={{ width: `${sidebarWidth}px` }}
      >
        <Sidebar 
          projects={projects} 
          onProjectCreated={handleProjectUpdated}
          onProjectDeleted={handleProjectUpdated}
        />
        {/* Resize handle */}
        <div
          className="resize-handle absolute top-0 right-0 w-1 h-full cursor-ew-resize"
          onMouseDown={() => setIsResizing(true)}
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
      <div 
        className="fixed bottom-0 right-0 bg-white border-t border-gray-200 shadow-lg"
        style={{ width: `calc(100% - ${sidebarWidth}px)` }}
      >
        <GlobalNoteInput 
          projects={projects} 
          onNoteCreated={handleNoteCreated}
        />
      </div>
    </div>
  );
};

export default ProjectsPage; 