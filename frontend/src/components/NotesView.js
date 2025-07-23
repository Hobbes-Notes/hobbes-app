import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useApiService } from '../services/api';
import { useAuth } from '../hooks/useAuth';

const NotesView = () => {
  const { noteId } = useParams();
  const { user, accessToken } = useAuth();
  const { getAllNotes, getActionItems } = useApiService();
  const navigate = useNavigate();
  const [note, setNote] = useState(null);
  const [actionItems, setActionItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const handleActionItemClick = (actionItemId) => {
    navigate(`/action-items/${actionItemId}`);
  };

  useEffect(() => {
    const fetchNote = async () => {
      if (!user || !noteId || !accessToken) return;

      try {
        setLoading(true);
        setError(null);
        
        // Get all notes and find the specific one
        const response = await getAllNotes(user.id);
        if (response.data && response.data.items) {
          const foundNote = response.data.items.find(n => n.id === noteId);
          if (foundNote) {
            setNote(foundNote);
            
            // Get action items linked to this note
            try {
              console.log('Fetching action items for note:', noteId);
              const actionItemsResponse = await getActionItems();
              console.log('Action items response:', actionItemsResponse);
              
              // Backend returns APIResponse with data field containing the actual action items
              const actionItemsData = actionItemsResponse.data?.data || actionItemsResponse.data;
              if (actionItemsData) {
                console.log('All action items:', actionItemsData);
                const linkedActionItems = actionItemsData
                  .filter(item => item.source_note_id === noteId)
                  .sort((a, b) => new Date(b.created_at) - new Date(a.created_at)); // Sort by created timestamp, newest first
                console.log('Linked action items for note', noteId, ':', linkedActionItems);
                setActionItems(linkedActionItems);
              } else {
                console.log('No action items data in response');
              }
            } catch (actionError) {
              console.error('Error fetching action items:', actionError);
              // Don't fail the whole component if action items fail
            }
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
  }, [noteId, user, accessToken, getAllNotes]);

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
            <div>Created: {new Date(note.created_at).toLocaleDateString()} at {new Date(note.created_at).toLocaleTimeString()}</div>
            <div>Note ID: <span className="font-mono text-xs bg-gray-100 px-1 py-0.5 rounded">{note.id}</span></div>
          </div>
        </div>

        <div className="prose max-w-none">
          <div className="whitespace-pre-wrap text-gray-900 leading-relaxed">
            {note.content}
          </div>
        </div>

        {actionItems.length > 0 && (
          <div className="mt-6 pt-4 border-t border-gray-200">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Generated Action Items ({actionItems.length})</h3>
            <div className="flex flex-wrap gap-2">
              {actionItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => handleActionItemClick(item.id)}
                  className={`px-2 py-1 text-xs font-mono rounded border transition-colors cursor-pointer hover:opacity-80 ${
                    item.status === 'completed' 
                      ? 'bg-green-50 text-green-700 border-green-200 hover:bg-green-100' 
                      : 'bg-yellow-50 text-yellow-700 border-yellow-200 hover:bg-yellow-100'
                  }`}
                  title={`${item.task} (${item.status}) - Click to view details`}
                >
                  {item.id}
                </button>
              ))}
            </div>
          </div>
        )}

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