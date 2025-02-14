import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getNote, getProjects } from '../services/api';

const NoteDetail = () => {
  const { noteId } = useParams();
  const navigate = useNavigate();
  const [note, setNote] = useState(null);
  const [linkedProjects, setLinkedProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchNoteAndProjects = async () => {
      if (!noteId) return;
      
      try {
        setLoading(true);
        setError(null);

        // Fetch note details
        const noteResponse = await getNote(noteId);
        if (!noteResponse?.data) {
          throw new Error('Note not found');
        }
        setNote(noteResponse.data);

        // Fetch project details for linked projects
        if (noteResponse.data.linked_projects?.length > 0) {
          const projectsResponse = await getProjects();
          if (projectsResponse?.data) {
            const linked = projectsResponse.data.filter(project => 
              noteResponse.data.linked_projects.includes(project.id)
            );
            setLinkedProjects(linked);
          }
        }
      } catch (err) {
        console.error('Error fetching note details:', err);
        setError(err.message || 'Failed to load note details');
      } finally {
        setLoading(false);
      }
    };

    fetchNoteAndProjects();
  }, [noteId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-red-500">{error}</div>
      </div>
    );
  }

  if (!note) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-500">Note not found</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        {/* Note Content */}
        <div className="prose max-w-none mb-4">
          <p className="text-gray-900 whitespace-pre-wrap">{note.content}</p>
        </div>

        {/* Metadata */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <div>
              Created: {new Date(note.created_at).toLocaleString()}
            </div>
          </div>

          {/* Linked Projects */}
          {linkedProjects.length > 0 && (
            <div className="mt-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Linked Projects</h3>
              <div className="flex flex-wrap gap-2">
                {linkedProjects.map(project => (
                  <button
                    key={project.id}
                    onClick={() => navigate(`/projects/${project.id}`)}
                    className="inline-flex items-center px-2.5 py-1.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 transition-colors"
                  >
                    {project.name}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NoteDetail; 