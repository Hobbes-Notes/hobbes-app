import React, { useState } from 'react';
import { createNote } from '../services/api';

const AddNoteForm = () => {
  const [content, setContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!content.trim()) return;

    try {
      setIsSubmitting(true);
      setError(null);
      setSuccessMessage('');

      console.log('Submitting note:', { content });
      await createNote({ content });

      setContent('');
      setSuccessMessage('Note added successfully!');
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setSuccessMessage('');
      }, 3000);
    } catch (err) {
      console.error('Error creating note:', err);
      setError(err.response?.data?.detail || 'Failed to create note. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg">
      <form onSubmit={handleSubmit} className="max-w-4xl mx-auto p-4">
        <div className="relative">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            disabled={isSubmitting}
            placeholder="Add a new note..."
            className="w-full p-3 pr-24 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none h-20"
          />
          <button
            type="submit"
            disabled={isSubmitting || !content.trim()}
            className={`absolute right-2 bottom-2 px-4 py-2 rounded-md ${
              isSubmitting || !content.trim()
                ? 'bg-gray-300 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            } text-white font-medium transition-colors`}
          >
            {isSubmitting ? 'Adding...' : 'Add Note'}
          </button>
        </div>
        
        {error && (
          <div className="mt-2 text-red-600 text-sm">
            {error}
          </div>
        )}
        
        {successMessage && (
          <div className="mt-2 text-green-600 text-sm">
            {successMessage}
          </div>
        )}
      </form>
    </div>
  );
};

export default AddNoteForm; 