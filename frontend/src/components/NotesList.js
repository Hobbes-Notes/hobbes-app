import React, { useState, useEffect } from 'react';
import { getAllNotes } from '../services/api';

const NotesList = () => {
  console.log('NotesList component rendering');
  const [notes, setNotes] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Test API connection immediately
  useEffect(() => {
    const testAPI = async () => {
      try {
        const response = await fetch(`${process.env.REACT_APP_API_URL}/`);
        const data = await response.json();
        console.log('API Test Response:', data);
      } catch (err) {
        console.error('API Test Error:', err);
      }
    };
    testAPI();
  }, []);

  useEffect(() => {
    console.log('useEffect triggered');
    let mounted = true;

    const fetchNotes = async () => {
      console.log('fetchNotes started, isLoading:', isLoading);
      try {
        console.log('API URL:', process.env.REACT_APP_API_URL);
        const response = await getAllNotes();
        console.log('API Response received:', response);
        
        if (!mounted) {
          console.log('Component unmounted, skipping state updates');
          return;
        }

        if (!response || !response.data) {
          console.error('Invalid response:', response);
          throw new Error('Invalid response format');
        }

        // Sort notes by created_at in descending order (newest first)
        const sortedNotes = response.data.sort((a, b) => 
          new Date(b.created_at) - new Date(a.created_at)
        );
        
        console.log('Setting sorted notes:', sortedNotes);
        setNotes(sortedNotes);
        console.log('Setting isLoading to false');
        setIsLoading(false);
      } catch (err) {
        console.error('Error in fetchNotes:', err);
        if (mounted) {
          setError(err.message || 'Failed to load notes. Please try again later.');
          setIsLoading(false);
        }
      }
    };

    fetchNotes();

    return () => {
      console.log('Cleanup: marking component as unmounted');
      mounted = false;
    };
  }, []);

  console.log('Current render state:', { isLoading, error, notesCount: notes.length });

  if (isLoading) {
    console.log('Rendering loading state');
    return (
      <div className="flex items-center justify-center min-h-[200px]">
        <div className="text-gray-500">Loading notes...</div>
      </div>
    );
  }

  if (error) {
    console.log('Rendering error state:', error);
    return (
      <div className="text-red-600 p-4 text-center">
        <p className="font-semibold">Error loading notes</p>
        <p className="text-sm mt-2">{error}</p>
      </div>
    );
  }

  if (notes.length === 0) {
    console.log('Rendering empty state');
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
        <div className="bg-white rounded-lg shadow-sm p-8 max-w-md w-full text-center">
          <div className="mb-6">
            <svg 
              className="w-24 h-24 mx-auto text-gray-300" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth="1.5" 
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" 
              />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            No Notes Yet
          </h3>
          <p className="text-gray-600 mb-6">
            Get started by adding your first note using the form below. Your notes will be automatically organized and linked to relevant projects.
          </p>
          <div className="flex items-center justify-center text-sm text-gray-500">
            <svg 
              className="w-5 h-5 mr-2" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth="2" 
                d="M19 13l-7 7-7-7m14-8l-7 7-7-7" 
              />
            </svg>
            <span>Scroll down to add a note</span>
          </div>
        </div>
      </div>
    );
  }

  console.log('Rendering notes list:', notes);
  return (
    <div className="space-y-4 max-w-4xl mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">All Notes</h2>
      </div>
      <div className="space-y-4">
        {notes.map((note) => (
          <div
            key={note.id}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow"
          >
            <div className="prose max-w-none">
              <p className="text-gray-900 whitespace-pre-wrap">{note.content}</p>
            </div>
            <div className="mt-3 flex items-center justify-between text-sm text-gray-500">
              <div>
                {new Date(note.created_at).toLocaleString()}
              </div>
              {note.linked_projects && note.linked_projects.length > 0 && (
                <div className="flex gap-2">
                  {note.linked_projects.map((projectId) => (
                    <span
                      key={projectId}
                      className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      Linked to project
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default NotesList; 