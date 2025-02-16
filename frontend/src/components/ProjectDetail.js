import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { getProject, getNotes } from '../services/api';

const ProjectDetail = () => {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('summary'); // 'summary' or 'notes'

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
      setError(error);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  // Initial data fetch
  useEffect(() => {
    fetchProjectData();
  }, [fetchProjectData]);

  // Set up polling for updates
  useEffect(() => {
    if (!projectId) return;

    const pollInterval = setInterval(() => {
      fetchProjectData();
    }, 5000); // Poll every 5 seconds

    return () => clearInterval(pollInterval);
  }, [projectId, fetchProjectData]);

  const SummaryTab = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Project Summary</h3>
        {project?.summary ? (
          <div className="prose max-w-none">
            <p className="text-gray-600">{project.summary}</p>
          </div>
        ) : (
          <p className="text-gray-500 italic">No summary available yet. Add some notes to generate a summary.</p>
        )}
      </div>
    </div>
  );

  const NotesTab = () => (
    <div className="space-y-4">
      {notes.length === 0 ? (
        <div className="text-center text-gray-500 py-8">
          No notes linked to this project yet.
        </div>
      ) : (
        notes.map((note) => (
          <div
            key={note.id}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
          >
            <div className="prose max-w-none">
              <p className="text-gray-900 whitespace-pre-wrap">{note.content}</p>
            </div>
            <div className="mt-3 text-sm text-gray-500">
              {new Date(note.created_at).toLocaleString()}
            </div>
          </div>
        ))
      )}
    </div>
  );

  if (loading && !project) {
    return <div className="flex items-center justify-center h-full">Loading...</div>;
  }

  if (!projectId) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8">
        <h2 className="text-2xl font-semibold text-gray-700 mb-4">Welcome to Project Notes</h2>
        <p className="text-gray-600 max-w-md">
          Select a project from the list on the left or create a new project to get started.
        </p>
      </div>
    );
  }

  if (error) {
    return <div className="flex items-center justify-center h-full text-red-600">Error loading project</div>;
  }

  if (!project) {
    return null;
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
            Related Notes
          </button>
        </div>
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'summary' ? <SummaryTab /> : <NotesTab />}
      </div>
    </div>
  );
};

export default ProjectDetail; 