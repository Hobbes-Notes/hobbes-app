import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useApiService } from '../services/api';
import { useAuth } from '../hooks/useAuth';

const NotesView = () => {
  const { noteId } = useParams();
  const { user } = useAuth();
  const { getAllNotes } = useApiService();
  const [note, setNote] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchNote = async () => {
      if (!user || !noteId) return;

      try {
        setLoading(true);
        setError(null);
        
        // Get all notes and find the specific one
        const response = await getAllNotes(user.id);
        if (response.data && response.data.items) {
          const foundNote = response.data.items.find(n => n.id === noteId);
          if (foundNote) {
            setNote(foundNote);
          } else {
            setError('Note not found');
          }
        }
      } catch (err) {
        console.error('Error fetching note:', err);
        setError('Failed to load note');
      } finally {
        setLoading(false);
      }
    };

    fetchNote();
  }, [noteId, user, getAllNotes]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="p-4 text-red-600 bg-red-100 rounded-lg">
          {error}
        </div>
      </div>
    );
  }

  if (!note) {
    return (
      <div className="p-6">
        <div className="text-center text-gray-500">
          <p>No note selected</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Note</h1>
          <div className="text-sm text-gray-500">
            Created: {new Date(note.created_at).toLocaleDateString()} at {new Date(note.created_at).toLocaleTimeString()}
          </div>
        </div>

        <div className="prose max-w-none">
          <div className="whitespace-pre-wrap text-gray-900 leading-relaxed">
            {note.content}
          </div>
        </div>

        {note.projects && note.projects.length > 0 && (
          <div className="mt-6 pt-4 border-t border-gray-200">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Related Projects</h3>
            <div className="flex flex-wrap gap-2">
              {note.projects.map((project, index) => (
                <span
                  key={index}
                  className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded"
                >
                  {project.name}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default NotesView; 