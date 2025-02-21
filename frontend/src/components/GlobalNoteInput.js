import React, { useState, useEffect } from 'react';
import { createNote } from '../services/api';
import { useAuth } from '../hooks/useAuth';
import { useParams } from 'react-router-dom';

const GlobalNoteInput = ({ projects, onNoteCreated }) => {
  const [content, setContent] = useState('');
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState(null);
  const [isCreating, setIsCreating] = useState(false);
  const { user } = useAuth();
  const { projectId } = useParams();

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
      setContent('');
      setError(null);
      
      // Get project names for notification
      const linkedProjects = response.data.linked_projects
        .map(projectId => projects.find(p => p.id === projectId))
        .filter(Boolean)
        .map(p => p.name);
      
      setNotification({
        message: linkedProjects.length > 0
          ? `Note created and linked to: ${linkedProjects.join(', ')}`
          : 'Note created successfully',
        type: 'success'
      });

      // Always trigger the refresh callback if provided
      if (onNoteCreated) {
        onNoteCreated();
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
    <div className="relative">
      {/* Notification Toast */}
      {notification && (
        <div className="fixed bottom-32 right-8 z-50 animate-fade-in">
          <div className={`rounded-lg px-6 py-4 shadow-xl ${
            notification.type === 'success' 
              ? 'bg-green-50 border border-green-100' 
              : 'bg-blue-50 border border-blue-100'
          }`}>
            <div className="flex items-center">
              {notification.type === 'success' && (
                <svg className="h-5 w-5 text-green-400 mr-3" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              )}
              <p className={`text-sm font-medium ${
                notification.type === 'success' ? 'text-green-800' : 'text-blue-800'
              }`}>
                {notification.message}
              </p>
              <button
                onClick={() => setNotification(null)}
                className="ml-4 text-gray-400 hover:text-gray-600"
              >
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Note Input Form */}
      <form onSubmit={handleCreateNote} className="p-4 flex items-end space-x-4">
        <div className="flex-1">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Write a note... (Press Enter to save)"
            className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none h-24"
            disabled={isCreating}
          />
          {error && <p className="text-sm text-red-500 mt-2">{error}</p>}
        </div>
        <button
          type="submit"
          disabled={!content.trim() || isCreating}
          className={`px-6 py-3 rounded-lg text-white font-medium h-12 flex items-center justify-center min-w-[120px] ${
            content.trim() && !isCreating
              ? 'bg-blue-500 hover:bg-blue-600'
              : 'bg-gray-300 cursor-not-allowed'
          }`}
        >
          {isCreating ? (
            <>
              <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white mr-2"></div>
              Creating...
            </>
          ) : (
            'Create Note'
          )}
        </button>
      </form>
    </div>
  );
};

export default GlobalNoteInput; 