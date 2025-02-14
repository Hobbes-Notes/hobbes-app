import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { getProject, getNotes } from '../services/api';

const ProjectDetail = () => {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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

  if (loading && !project) { // Only show loading on initial load
    return <div className="flex items-center justify-center h-full">Loading...</div>;
  }

  if (!projectId) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8">
        <h2 className="text-2xl font-semibold text-gray-700 mb-4">Welcome to Project Notes</h2>
        <p className="text-gray-600 max-w-md">
          Select a project from the list on the left or create a new project to get started.
        </p>
        <div className="mt-8">
          <svg className="w-32 h-32 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
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
    <div className="space-y-6 max-w-4xl mx-auto p-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
        {project.description && (
          <p className="text-gray-600 mt-2">{project.description}</p>
        )}
      </div>

      {project.summary && (
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <h3 className="font-medium text-gray-900 mb-2">Summary</h3>
          <p className="text-gray-600">{project.summary}</p>
        </div>
      )}

      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Related Notes</h2>
          {loading && <span className="text-sm text-gray-500">Refreshing...</span>}
        </div>
        <div className="space-y-4 h-[500px] overflow-y-auto pr-4">
          {notes.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              No notes linked to this project yet.
            </div>
          ) : (
            notes.map((note) => (
              <div
                key={note.id}
                className="bg-white rounded-lg border border-gray-200 p-4 space-y-2"
              >
                <p className="text-gray-700">{note.content}</p>
                <p className="text-sm text-gray-500">
                  {new Date(note.created_at).toLocaleString()}
                </p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default ProjectDetail; 