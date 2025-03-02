import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useApiService } from '../services/api';

const NotesPage = () => {
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { projectId } = useParams();
  const { getNotes } = useApiService();

  useEffect(() => {
    const fetchNotes = async () => {
      try {
        setLoading(true);
        const response = await getNotes(projectId);
        setNotes(response.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching notes:', err);
        setError('Failed to load notes');
      } finally {
        setLoading(false);
      }
    };

    if (projectId) {
      fetchNotes();
    }
  }, [projectId, getNotes]);

  if (loading) {
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

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Project Notes</h1>
      <div className="space-y-4">
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
      </div>
    </div>
  );
};

export default NotesPage; 