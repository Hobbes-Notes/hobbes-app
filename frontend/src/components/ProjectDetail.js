import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { getProject, getNotes, createNote } from '../services/api';

const ProjectDetail = () => {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [notes, setNotes] = useState([]);
  const [newNote, setNewNote] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProjectAndNotes();
  }, [projectId]);

  const fetchProjectAndNotes = async () => {
    try {
      const [projectResponse, notesResponse] = await Promise.all([
        getProject(projectId),
        getNotes(projectId)
      ]);
      setProject(projectResponse.data);
      setNotes(notesResponse.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching project data:', error);
      setLoading(false);
    }
  };

  const handleCreateNote = async (e) => {
    e.preventDefault();
    try {
      await createNote(projectId, { content: newNote });
      setNewNote('');
      fetchProjectAndNotes();
    } catch (error) {
      console.error('Error creating note:', error);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-full">Loading...</div>;
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">{project.name}</h1>
        {project.description && (
          <p className="text-gray-600 mt-2">{project.description}</p>
        )}
      </div>

      {project.summary && (
        <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
          <h3 className="font-medium text-gray-900 mb-2">Summary</h3>
          <p className="text-gray-600">{project.summary}</p>
        </div>
      )}

      <div className="space-y-4">
        <form onSubmit={handleCreateNote}>
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">Add Note</label>
            <textarea
              value={newNote}
              onChange={(e) => setNewNote(e.target.value)}
              placeholder="Write your note here..."
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              rows="4"
            />
          </div>
          <button
            type="submit"
            className="mt-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Add Note
          </button>
        </form>
      </div>

      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Notes</h2>
        <div className="space-y-4 h-[500px] overflow-y-auto pr-4">
          {notes.map((note) => (
            <div
              key={note.id}
              className="bg-white rounded-lg border border-gray-200 p-4 space-y-2"
            >
              <p className="text-gray-700">{note.content}</p>
              <p className="text-sm text-gray-500">
                {new Date(note.created_at).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ProjectDetail; 