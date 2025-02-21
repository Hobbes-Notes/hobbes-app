import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const LoginPage = () => {
  const navigate = useNavigate();
  const { login, user, error: authError } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Redirect if already logged in
  useEffect(() => {
    if (user) {
      navigate('/projects');
    }
  }, [user, navigate]);

  // Update error message from auth context
  useEffect(() => {
    if (authError) {
      setError(authError);
    }
  }, [authError]);

  const handleGoogleLogin = async () => {
    try {
      setLoading(true);
      setError(null);
      await login();
    } catch (error) {
      console.error('Login failed:', error);
      setError(error.message || 'Failed to sign in with Google. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-lg">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-gray-900">Welcome to Hobbes</h2>
          <p className="mt-2 text-sm text-gray-600">
            Sign in with your Google account to continue
          </p>
        </div>
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm">
            {error}
          </div>
        )}
        <div className="mt-8">
          <button
            onClick={handleGoogleLogin}
            disabled={loading}
            className={`w-full flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-base font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
              loading ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {loading ? (
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-white mr-2"></div>
                Signing in...
              </div>
            ) : (
              <>
                <svg
                  className="w-5 h-5 mr-2"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                >
                  {/* Google icon path */}
                  <path d="M12.545,12.151L12.545,12.151c0,1.054,0.855,1.909,1.909,1.909h3.536c-0.607,1.972-2.405,3.404-4.545,3.404c-2.627,0-4.545-2.127-4.545-4.545s2.127-4.545,4.545-4.545c1.127,0,2.163,0.399,2.972,1.063l2.595-2.595C17.363,4.953,14.927,4,12.545,4C7.018,4,4,7.018,4,12.545s3.018,8.545,8.545,8.545c4.545,0,8.545-3.018,8.545-8.545c0-0.582-0.063-1.145-0.181-1.691h-8.364V12.151z" />
                </svg>
                Sign in with Google
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default LoginPage; 