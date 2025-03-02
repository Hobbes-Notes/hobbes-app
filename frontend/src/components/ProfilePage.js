import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useApiService } from '../services/api';
import { useNavigate } from 'react-router-dom';

const NoteIcon = () => (
  <svg
    className="w-5 h-5 text-purple-500"
    fill="none"
    stroke="currentColor"
    viewBox="0 0 24 24"
    strokeWidth={2}
  >
    <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
  </svg>
);

const ProfilePage = () => {
  const { user } = useAuth();
  const { getProjects, getNotes } = useApiService();
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [notes, setNotes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [paginationCursors, setPaginationCursors] = useState([null]);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [pageSize] = useState(10);

  useEffect(() => {
    const fetchData = async () => {
      if (!user) {
        navigate('/login');
        return;
      }

      try {
        setLoading(true);
        const [projectsResponse, notesResponse] = await Promise.all([
          getProjects(user.id),
          getNotes(null, user.id, currentPage, pageSize, paginationCursors[currentPage - 1])
        ]);

        setProjects(projectsResponse.data);
        setNotes(notesResponse.data.items);
        setHasMore(notesResponse.data.has_more);
        
        // Store the LastEvaluatedKey for pagination
        const lastEvaluatedKey = notesResponse.data.LastEvaluatedKey;
        if (lastEvaluatedKey) {
          setPaginationCursors(prev => {
            const newCursors = [...prev];
            newCursors[currentPage] = lastEvaluatedKey;
            return newCursors;
          });
        }
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Failed to load profile data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user, navigate, getProjects, getNotes, currentPage, pageSize]);

  const handleNextPage = () => {
    if (hasMore) {
      setCurrentPage(prev => prev + 1);
    }
  };

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(prev => prev - 1);
    }
  };

  const handleBack = () => {
    navigate(-1);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 text-red-600 bg-red-100 rounded-lg">
        {error}
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <button
          onClick={handleBack}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <svg
            className="w-5 h-5 mr-1"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Back
        </button>
      </div>

      <div className="bg-white shadow-lg rounded-lg overflow-hidden">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">My Profile</h1>
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-2">User Information</h2>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-gray-600"><span className="font-medium">Email:</span> {user?.email}</p>
              <p className="text-gray-600"><span className="font-medium">Name:</span> {user?.name}</p>
            </div>
          </div>

          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">My Notes</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Content
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Projects
                    </th>
                    <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created At
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {notes.map((note, index) => (
                    <tr key={index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <NoteIcon />
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">
                          {note.content.length > 100 
                            ? `${note.content.substring(0, 100)}...` 
                            : note.content}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-2">
                          {note.projects.map(project => (
                            <span
                              key={project.id}
                              className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                            >
                              {project.name}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(note.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                  {notes.length === 0 && (
                    <tr>
                      <td colSpan="4" className="px-6 py-4 text-center text-gray-500">
                        No notes created yet
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Updated Pagination Controls */}
            <div className="mt-4 flex justify-between items-center">
              <button
                onClick={handlePrevPage}
                disabled={currentPage === 1}
                className={`px-4 py-2 rounded-md ${
                  currentPage === 1
                    ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-500 text-white hover:bg-blue-600'
                }`}
              >
                Previous
              </button>
              <span className="text-gray-600">Page {currentPage}</span>
              <button
                onClick={handleNextPage}
                disabled={!hasMore}
                className={`px-4 py-2 rounded-md ${
                  !hasMore
                    ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-500 text-white hover:bg-blue-600'
                }`}
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProfilePage; 