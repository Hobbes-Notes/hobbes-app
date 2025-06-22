import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApiService } from '../services/api';
import { useAuth } from '../hooks/useAuth';

const NotepadPage = () => {
  const [newNoteContent, setNewNoteContent] = useState('');
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [expandedNote, setExpandedNote] = useState(null);
  const [expandedActionItems, setExpandedActionItems] = useState(null);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  const [noteActionItems, setNoteActionItems] = useState({});
  const { user } = useAuth();
  const { getAllNotes, createNote, getActionItems } = useApiService();
  const navigate = useNavigate();

  // Load past notes and their associated action items on component mount
  useEffect(() => {
    const fetchNotesAndActionItems = async () => {
      if (!user?.id) return;
      
      try {
        setLoading(true);
        setError(null);
        
        // Fetch notes
        const notesResponse = await getAllNotes(user.id);
        const notesData = notesResponse.data.items || [];
        setNotes(notesData);
        
        // Fetch all action items
        const actionItemsResponse = await getActionItems();
        const actionItems = actionItemsResponse.data?.data || actionItemsResponse.data || [];
        
        // Group action items by source_note_id
        const actionItemsByNote = {};
        actionItems.forEach(item => {
          if (item.source_note_id) {
            if (!actionItemsByNote[item.source_note_id]) {
              actionItemsByNote[item.source_note_id] = [];
            }
            actionItemsByNote[item.source_note_id].push(item);
          }
        });
        
        setNoteActionItems(actionItemsByNote);
        
      } catch (err) {
        console.error('Error fetching notes and action items:', err);
        setError('Failed to load notes');
      } finally {
        setLoading(false);
      }
    };

    fetchNotesAndActionItems();
  }, [user?.id, getAllNotes, getActionItems]);

  const handleSubmitNote = async () => {
    if (!newNoteContent.trim() || !user?.id) return;

    try {
      setSubmitting(true);
      setError(null);
      
      await createNote(newNoteContent, user.id);
      
      // Clear the form
      setNewNoteContent('');
      
      // Refresh notes list
      const notesResponse = await getAllNotes(user.id);
      setNotes(notesResponse.data.items || []);
      
      // Refresh action items
      const actionItemsResponse = await getActionItems();
      const actionItems = actionItemsResponse.data?.data || actionItemsResponse.data || [];
      
      // Group action items by source_note_id
      const actionItemsByNote = {};
      actionItems.forEach(item => {
        if (item.source_note_id) {
          if (!actionItemsByNote[item.source_note_id]) {
            actionItemsByNote[item.source_note_id] = [];
          }
          actionItemsByNote[item.source_note_id].push(item);
        }
      });
      
      setNoteActionItems(actionItemsByNote);
      
      // Show success message
      setSuccessMessage('Note created successfully!');
      setTimeout(() => setSuccessMessage(''), 3000);
      
    } catch (err) {
      console.error('Error creating note:', err);
      setError('Failed to create note');
    } finally {
      setSubmitting(false);
    }
  };

  const toggleExpandNote = (noteId) => {
    setExpandedNote(expandedNote === noteId ? null : noteId);
  };

  const toggleExpandActionItems = (noteId) => {
    setExpandedActionItems(expandedActionItems === noteId ? null : noteId);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const truncateText = (text, maxWords = 20) => {
    const words = text.split(' ');
    if (words.length <= maxWords) return text;
    return words.slice(0, maxWords).join(' ') + '...';
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* New Note Section */}
      <div className="bg-white border-b border-gray-200 p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">New Note</h2>
        
        <div className="space-y-4">
          <textarea
            value={newNoteContent}
            onChange={(e) => setNewNoteContent(e.target.value)}
            placeholder="Write your note here..."
            className="w-full h-32 p-4 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            disabled={submitting}
          />
          
          <div className="flex justify-end">
            <button
              onClick={handleSubmitNote}
              disabled={!newNoteContent.trim() || submitting}
              className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                !newNoteContent.trim() || submitting
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}
            >
              {submitting ? 'Creating...' : 'Submit'}
            </button>
          </div>
          
          {submitting && (
            <div className="flex items-center justify-center py-4">
              <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-500 mr-3"></div>
              <span className="text-gray-600">Creating your note...</span>
            </div>
          )}
          
          {successMessage && (
            <div className="p-4 bg-green-100 border border-green-400 text-green-700 rounded-lg">
              {successMessage}
            </div>
          )}
        </div>
      </div>

      {/* Past Notes Section */}
      <div className="flex-1 overflow-y-auto p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Past Notes</h2>
        
        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
            {error}
          </div>
        )}
        
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500 mr-3"></div>
            <span className="text-gray-600">Loading notes...</span>
          </div>
        ) : notes.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            No notes yet. Create your first note above!
          </div>
        ) : (
          <div className="space-y-4">
                        {notes.map((note) => (
              <div
                key={note.id}
                className="bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow"
              >
                {/* Top Bar - Date */}
                <div className="bg-gray-50 px-4 py-2 rounded-t-lg border-b border-gray-200">
                  <span className="text-sm text-gray-600 font-medium">
                    {formatDate(note.created_at)}
                  </span>
                  {note.project_id && (
                    <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                      Project Note
                    </span>
                  )}
                </div>

                {/* Body - Note Content */}
                <div className="p-4">
                  <div className="mb-3">
                                         <p className="text-gray-900 leading-relaxed mb-2">
                       {expandedNote === note.id ? note.content : truncateText(note.content, 20)}
                     </p>
                     {note.content.split(' ').length > 20 && (
                      <button
                        onClick={() => toggleExpandNote(note.id)}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium transition-colors"
                      >
                        {expandedNote === note.id ? 'Show less' : 'Read more'}
                      </button>
                    )}
                  </div>
                </div>

                                 {/* Bottom - Action Items */}
                 <div className="px-4 pb-4">
                   <button
                     onClick={() => toggleExpandActionItems(note.id)}
                     className="flex items-center justify-between w-full text-left text-sm text-gray-600 hover:text-gray-800 transition-colors"
                   >
                     <span>
                       {noteActionItems[note.id]?.length || 0} Action Items Extracted
                     </span>
                     {noteActionItems[note.id] && noteActionItems[note.id].length > 0 && (
                       <svg
                         className={`w-4 h-4 transition-transform ${
                           expandedActionItems === note.id ? 'rotate-180' : ''
                         }`}
                         fill="none"
                         stroke="currentColor"
                         viewBox="0 0 24 24"
                       >
                         <path
                           strokeLinecap="round"
                           strokeLinejoin="round"
                           strokeWidth={2}
                           d="M19 9l-7 7-7-7"
                         />
                       </svg>
                     )}
                   </button>
                   
                   {/* Expandable Action Items */}
                   {expandedActionItems === note.id && noteActionItems[note.id] && noteActionItems[note.id].length > 0 && (
                     <div className="mt-3 flex flex-wrap gap-2">
                       {noteActionItems[note.id].map((actionItem) => (
                         <button
                           key={actionItem.id}
                           onClick={() => navigate(`/action-items/${actionItem.id}`)}
                           className={`px-2 py-1 text-xs rounded font-medium transition-colors ${
                             actionItem.status === 'completed'
                               ? 'bg-green-100 text-green-700 hover:bg-green-200'
                               : 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
                           }`}
                           title={`${actionItem.task} (${actionItem.status})`}
                         >
                           #{actionItem.id.slice(-4)}
                         </button>
                       ))}
                     </div>
                   )}
                 </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default NotepadPage; 