import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGoogleLogin } from '@react-oauth/google';
import axios from 'axios';

const AuthContext = createContext(null);
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8888';

// Constants
const ACCESS_TOKEN_EXPIRE_MINUTES = 15; // 15 minutes
const REFRESH_INTERVAL = (ACCESS_TOKEN_EXPIRE_MINUTES - 1) * 60 * 1000; // Refresh 1 minute before expiry

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  withCredentials: true // Important for cookies
});

// Create unauthenticated axios instance for AI configuration endpoints and OAuth
const unauthenticatedApi = axios.create({
  baseURL: API_URL,
  withCredentials: false // No credentials needed for AI endpoints and OAuth
});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [accessToken, setAccessToken] = useState(null);
  const navigate = useNavigate();

  const refreshAccessToken = useCallback(async (shouldRedirect = true) => {
    try {
      const response = await api.post('/auth/refresh');
      const newToken = response.data.access_token;
      setAccessToken(newToken);
      return newToken;
    } catch (error) {
      console.error('Token refresh failed:', error);
      // Clear user state and tokens
      setUser(null);
      setAccessToken(null);
      if (shouldRedirect) {
        setError('Session expired. Please login again.');
        navigate('/login');
      }
      throw error;
    }
  }, [navigate]);

  // Check for existing session
  useEffect(() => {
    let mounted = true;
    let retryCount = 0;
    const maxRetries = 3;
    
    const checkAuth = async () => {
      if (!mounted) return;
      
      try {
        setLoading(true);
        // First try to refresh the token
        const newToken = await refreshAccessToken(false);
        
        if (mounted && newToken) {
          // Then get user data with the new token
          const userResponse = await api.get('/auth/user', {
            headers: { Authorization: `Bearer ${newToken}` }
          });
          setUser(userResponse.data);
          setError(null);
        }
      } catch (error) {
        console.error('Session validation failed:', error);
        if (mounted) {
          if (error.response?.status === 401) {
            if (retryCount < maxRetries) {
              retryCount++;
              console.log(`Retrying auth check (${retryCount}/${maxRetries})...`);
              setTimeout(checkAuth, 1000); // Retry after 1 second
              return;
            }
            setError('Session expired. Please login again.');
            navigate('/login');
          }
          // Clear any stale state
          setUser(null);
          setAccessToken(null);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    checkAuth();

    return () => {
      mounted = false;
    };
  }, []); // Only run on mount

  // Set up axios interceptors
  useEffect(() => {
    let isRefreshing = false;
    let failedQueue = [];
    let refreshTimeout = null;

    const processQueue = (error, token = null) => {
      failedQueue.forEach(prom => {
        if (error) {
          prom.reject(error);
        } else {
          prom.resolve(token);
        }
      });
      failedQueue = [];
    };

    // Request interceptor
    const requestInterceptor = api.interceptors.request.use(
      (config) => {
        if (accessToken && !config.headers.Authorization) {
          config.headers.Authorization = `Bearer ${accessToken}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    const responseInterceptor = api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // Don't retry refresh token endpoint failures
        if (originalRequest.url === '/auth/refresh') {
          return Promise.reject(error);
        }

        if (error.response?.status === 401 && !originalRequest._retry) {
          if (isRefreshing) {
            try {
              const token = await new Promise((resolve, reject) => {
                failedQueue.push({ resolve, reject });
              });
              originalRequest.headers.Authorization = `Bearer ${token}`;
              return api(originalRequest);
            } catch (err) {
              return Promise.reject(err);
            }
          }

          originalRequest._retry = true;
          isRefreshing = true;

          try {
            const newToken = await refreshAccessToken(false);
            processQueue(null, newToken);
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return api(originalRequest);
          } catch (refreshError) {
            processQueue(refreshError, null);
            return Promise.reject(refreshError);
          } finally {
            isRefreshing = false;
          }
        }

        return Promise.reject(error);
      }
    );

    // Set up periodic token refresh if we have a token
    if (accessToken) {
      refreshTimeout = setTimeout(() => {
        refreshAccessToken(false).catch(console.error);
      }, REFRESH_INTERVAL);
    }

    // Cleanup
    return () => {
      api.interceptors.request.eject(requestInterceptor);
      api.interceptors.response.eject(responseInterceptor);
      if (refreshTimeout) {
        clearTimeout(refreshTimeout);
      }
    };
  }, [accessToken, refreshAccessToken]);

  const handleLoginSuccess = async (tokenResponse) => {
    try {
      console.log('Google login response:', tokenResponse);
      
      // Create a dedicated axios instance for OAuth with specific configuration
      const oauthApi = axios.create({
        baseURL: API_URL,
        withCredentials: true,
        timeout: 10000,
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      const result = await oauthApi.post('/auth/google', {
        token: tokenResponse.access_token
      });
      
      console.log('Backend login result:', result);
      setUser(result.data.user);
      setAccessToken(result.data.access_token);
      setError(null);
      navigate('/projects');
    } catch (error) {
      console.error('Login failed:', error);
      console.error('Error details:', {
        message: error.message,
        response: error.response?.data,
        status: error.response?.status,
        config: error.config
      });
      setError(error.response?.data?.detail || 'Failed to login. Please try again.');
      throw error;
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
      await api.post('/auth/logout');
      setUser(null);
      setAccessToken(null);
      setError(null);
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
      // Force logout even if the API call fails
      setUser(null);
      setAccessToken(null);
      navigate('/login');
    }
  };

  // Export the api instance for use in other components
  const getApi = useCallback(() => api, []);
  
  // Export the unauthenticated api instance for AI configuration endpoints
  const getUnauthenticatedApi = useCallback(() => unauthenticatedApi, []);

  return (
    <AuthContext.Provider value={{ user, loading, error, login, logout, getApi, getUnauthenticatedApi }}>
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