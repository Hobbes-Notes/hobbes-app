import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useEffect } from 'react';

export const ProtectedRoute = ({ children }) => {
  const { user, loading, error } = useAuth();
  const location = useLocation();

  // If there's an auth error, redirect to login
  useEffect(() => {
    if (error) {
      console.error('Auth error:', error);
    }
  }, [error]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!user) {
    // Redirect to login page but save the attempted url
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}; 