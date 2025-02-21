import { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGoogleLogin } from '@react-oauth/google';
import { loginWithGoogle, logoutUser } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  // Check for existing session
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const response = await loginWithGoogle(token);
          setUser(response.data);
        } catch (error) {
          console.error('Session validation failed:', error);
          localStorage.removeItem('token');
          setError('Session expired. Please login again.');
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const handleLoginSuccess = async (tokenResponse) => {
    try {
      console.log('Google login response:', tokenResponse);
      const result = await loginWithGoogle(tokenResponse.access_token);
      console.log('Backend login result:', result);
      setUser(result.data);
      localStorage.setItem('token', tokenResponse.access_token);
      setError(null);
      navigate('/projects');
    } catch (error) {
      console.error('Login failed:', error);
      localStorage.removeItem('token');
      setError(error.response?.data?.detail || 'Failed to login. Please try again.');
      throw error; // Propagate error to the component
    }
  };

  const login = useGoogleLogin({
    onSuccess: handleLoginSuccess,
    onError: (error) => {
      console.error('Google Login Failed:', error);
      setError('Google authentication failed. Please try again.');
    },
    flow: 'implicit'
  });

  const logout = async () => {
    try {
      await logoutUser();
      setUser(null);
      setError(null);
      localStorage.removeItem('token');
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
      // Force logout even if the API call fails
      setUser(null);
      localStorage.removeItem('token');
      navigate('/login');
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, error, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 