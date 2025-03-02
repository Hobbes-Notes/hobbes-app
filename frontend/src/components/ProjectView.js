import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useOutletContext } from 'react-router-dom';
import { useApiService } from '../services/api';
import ReactMarkdown from 'react-markdown';
import { RefreshCw } from 'lucide-react';

const ProjectView = () => {
  const [project, setProject] = useState(null);
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [notesLoading, setNotesLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('summary'); // 'summary' or 'notes'
  const { projectId } = useParams();
  const { getProject, getNotes } = useApiService();
  const { onNoteCreated: parentNoteCreated } = useOutletContext() || {};

  const fetchProjectData = useCallback(async (silent = false) => {
    if (!projectId) return;
    
    try {
      if (!silent) setIsRefreshing(true);
      setError(null);
      const projectResponse = await getProject(projectId);
      setProject(projectResponse.data);
    } catch (err) {
      console.error('Error fetching project data:', err);
      setError('Failed to load project data');
    } finally {
      setLoading(false);
      if (!silent) setIsRefreshing(false);
    }
  }, [projectId, getProject]);

  const fetchNotes = useCallback(async (silent = false) => {
    if (!projectId) return;
    
    try {
      if (!silent) setNotesLoading(true);
      const notesResponse = await getNotes(projectId);
      setNotes(notesResponse.data);
    } catch (err) {
      console.error('Error fetching notes:', err);
    } finally {
      if (!silent) setNotesLoading(false);
    }
  }, [projectId, getNotes]);

  const refreshData = useCallback(async (silent = false) => {
    await Promise.all([
      fetchProjectData(silent),
      fetchNotes(silent)
    ]);
  }, [fetchProjectData, fetchNotes]);

  // Handle new note creation
  const handleNoteCreated = useCallback(async (newNote) => {
    if (!newNote) return;

    // Check if the note belongs to this project
    if (newNote.linked_projects?.includes(projectId)) {
      // First update the notes list optimistically
      setNotes(prevNotes => {
        // Check if note already exists to prevent duplicates
        const exists = prevNotes.some(note => note.id === newNote.id);
        if (exists) return prevNotes;
        return [newNote, ...prevNotes];
      });

      // Refresh both project and notes data silently
      await refreshData(true);
    }

    // Call parent note created handler
    if (parentNoteCreated) {
      parentNoteCreated(newNote);
    }
  }, [projectId, refreshData, parentNoteCreated]);

  // Initial data fetch
  useEffect(() => {
    if (projectId) {
      refreshData();
    }
  }, [projectId, refreshData]);

  // Set up note creation listener
  useEffect(() => {
    // Add the handler to the global note input
    if (window.globalNoteHandlers) {
      window.globalNoteHandlers.push(handleNoteCreated);
    } else {
      window.globalNoteHandlers = [handleNoteCreated];
    }

    // Cleanup
    return () => {
      if (window.globalNoteHandlers) {
        window.globalNoteHandlers = window.globalNoteHandlers.filter(
          handler => handler !== handleNoteCreated
        );
      }
    };
  }, [handleNoteCreated]);

  // Handle tab change
  const handleTabChange = useCallback((tab) => {
    setActiveTab(tab);
    if (tab === 'notes') {
      fetchNotes();
    }
  }, [fetchNotes]);

  if (loading && !project) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-red-600 bg-red-100 rounded-lg">
        {error}
      </div>
    );
  }

  if (!project) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        Project not found
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
          {project.description && (
            <p className="mt-2 text-gray-600">{project.description}</p>
          )}
        </div>
        <button
          onClick={() => refreshData()}
          disabled={isRefreshing || notesLoading}
          className={`p-2 rounded-full hover:bg-gray-100 transition-colors ${
            (isRefreshing || notesLoading) ? 'opacity-50 cursor-not-allowed' : ''
          }`}
          title="Refresh data"
        >
          <RefreshCw className={`w-5 h-5 text-gray-500 ${(isRefreshing || notesLoading) ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => handleTabChange('summary')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'summary'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Summary
            </button>
            <button
              onClick={() => handleTabChange('notes')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'notes'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Notes ({notes.length})
            </button>
          </nav>
        </div>

        <div className="mt-6">
          {activeTab === 'summary' ? (
            <div className="prose max-w-none">
              {project.summary ? (
                <ReactMarkdown>{project.summary}</ReactMarkdown>
              ) : (
                <p className="text-gray-500 italic">
                  No summary available yet. Add some notes to generate a summary.
                </p>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {notesLoading ? (
                <div className="flex justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
                </div>
              ) : (
                <>
                  {notes.map((note) => (
                    <div
                      key={note.id}
                      className="bg-white rounded-lg shadow-sm border border-gray-200 p-4"
                    >
                      <p className="text-gray-900 whitespace-pre-wrap">{note.content}</p>
                      <p className="mt-2 text-sm text-gray-500">
                        {new Date(note.created_at).toLocaleString()}
                      </p>
                    </div>
                  ))}
                  {notes.length === 0 && (
                    <p className="text-gray-500 text-center py-8">
                      No notes yet. Start adding notes to this project.
                    </p>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProjectView; 