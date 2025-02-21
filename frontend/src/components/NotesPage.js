import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getNotes } from '../services/api';
import { useAuth } from '../hooks/useAuth';

const NotesPage = () => {
  const { projectId } = useParams();
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    const fetchNotes = async () => {
      try {
        const response = await getNotes(projectId);
        // Filter notes for the current user
        const userNotes = response.data.filter(
          (note) => note.user_id === user.id
        );
        setNotes(userNotes);
      } catch (error) {
        console.error('Error fetching notes:', error);
      } finally {
        setLoading(false);
      }
    };

    if (projectId && user) {
      fetchNotes();
    }
  }, [projectId, user]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-4">Notes</h2>
      <div className="space-y-4">
        {notes.map((note) => (
          <div
            key={note.id}
            className="bg-white rounded-lg shadow p-4"
          >
            <p className="text-gray-800 whitespace-pre-wrap">{note.content}</p>
            <p className="text-sm text-gray-500 mt-2">
              {new Date(note.created_at).toLocaleString()}
            </p>
          </div>
        ))}
        {notes.length === 0 && (
          <p className="text-gray-500 text-center py-8">
            No notes found for this project
          </p>
        )}
      </div>
    </div>
  );
};

export default NotesPage; 