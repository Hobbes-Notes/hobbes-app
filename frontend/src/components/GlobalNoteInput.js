import React, { useState, useEffect } from 'react';
import { useApiService } from '../services/api';
import { useAuth } from '../hooks/useAuth';

const GlobalNoteInput = ({ projects, onNoteCreated }) => {
  const [content, setContent] = useState('');
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState(null);
  const [isCreating, setIsCreating] = useState(false);
  const { user } = useAuth();
  const { createNote } = useApiService();

  useEffect(() => {
    let timer;
    if (notification) {
      timer = setTimeout(() => {
        setNotification(null);
      }, 3000);
    }
    return () => clearTimeout(timer);
  }, [notification]);

  const handleCreateNote = async (e) => {
    e.preventDefault();
    if (!content.trim() || isCreating) return;

    try {
      setIsCreating(true);
      const response = await createNote(content.trim(), user.id);
      const newNote = response.data;
      setContent('');
      setError(null);
      
      // Get project names for notification
      const linkedProjects = newNote.projects
        .map(project => project.name)
        .filter(Boolean);
      
      if (linkedProjects.length > 0) {
        setNotification({
          message: `Note linked to: ${linkedProjects.join(', ')}`,
          type: 'success'
        });
      } else {
        setNotification({
          message: 'Note created successfully',
          type: 'success'
        });
      }

      // Call any registered global handlers
      if (window.globalNoteHandlers) {
        window.globalNoteHandlers.forEach(handler => {
          try {
            handler(newNote);
          } catch (error) {
            console.error('Error in note handler:', error);
          }
        });
      }

      // Pass the new note data to parent components
      if (onNoteCreated) {
        onNoteCreated(newNote);
      }
    } catch (error) {
      console.error('Error creating note:', error);
      setError('Failed to create note. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleCreateNote(e);
    }
  };

  return (
    <div className="p-4">
      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">
          {error}
        </div>
      )}
      {notification && (
        <div className={`mb-4 p-3 rounded-lg ${
          notification.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
        }`}>
          {notification.message}
        </div>
      )}
      <form onSubmit={handleCreateNote} className="relative">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your note here... (Press Enter to save)"
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
          rows="3"
          disabled={isCreating}
        />
        <button
          type="submit"
          disabled={!content.trim() || isCreating}
          className={`absolute bottom-3 right-3 px-4 py-2 rounded-lg text-white ${
            !content.trim() || isCreating
              ? 'bg-gray-300 cursor-not-allowed'
              : 'bg-blue-500 hover:bg-blue-600'
          }`}
        >
          {isCreating ? 'Creating...' : 'Create Note'}
        </button>
      </form>
    </div>
  );
};

export default GlobalNoteInput; 