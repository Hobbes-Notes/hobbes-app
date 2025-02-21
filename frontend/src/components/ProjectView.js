import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { getProject, getNotes } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import ReactMarkdown from 'react-markdown';

const ProjectView = () => {
  const [project, setProject] = useState(null);
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('summary'); // 'summary' or 'notes'
  const { projectId } = useParams();
  const { user } = useAuth();

  const fetchProjectData = useCallback(async () => {
    if (!projectId) return;
    
    try {
      setLoading(true);
      setError(null);
      const [projectResponse, notesResponse] = await Promise.all([
        getProject(projectId),
        getNotes(projectId)
      ]);
      setProject(projectResponse.data);
      setNotes(notesResponse.data);
    } catch (error) {
      console.error('Error fetching project data:', error);
      setError('Failed to load project data');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  // Initial data fetch
  useEffect(() => {
    if (projectId) {
      fetchProjectData();
    }
  }, [projectId, fetchProjectData]);

  // Set up polling for updates
  useEffect(() => {
    if (!projectId) return;

    const pollInterval = setInterval(() => {
      fetchProjectData();
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(pollInterval);
  }, [projectId, fetchProjectData]);

  if (loading && !project) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
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
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
        {project.description && (
          <p className="text-gray-600 mt-2">{project.description}</p>
        )}
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <div className="flex space-x-8">
          <button
            onClick={() => setActiveTab('summary')}
            className={`py-4 px-1 relative ${
              activeTab === 'summary'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Summary
          </button>
          <button
            onClick={() => setActiveTab('notes')}
            className={`py-4 px-1 relative ${
              activeTab === 'notes'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            Notes
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'summary' ? (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Project Summary</h3>
              {project.summary ? (
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown>{project.summary}</ReactMarkdown>
                </div>
              ) : (
                <p className="text-gray-500 italic">No summary available yet. Add some notes to generate a summary.</p>
              )}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {notes.map((note) => (
              <div key={note.id} className="bg-white rounded-lg shadow-sm p-6">
                <p className="text-gray-800 whitespace-pre-wrap">{note.content}</p>
                <div className="mt-2 text-sm text-gray-500">
                  {new Date(note.created_at).toLocaleString()}
                </div>
              </div>
            ))}
            {notes.length === 0 && (
              <p className="text-center text-gray-500 py-8">
                No notes yet. Start writing below!
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectView; 