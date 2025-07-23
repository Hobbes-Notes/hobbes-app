import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGoogleLogin } from '@react-oauth/google';
import axios from 'axios';

const AuthContext = createContext(null);
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8888';

// Constants
const ACCESS_TOKEN_EXPIRE_MINUTES = 15; // 15 minutes
const REFRESH_INTERVAL = (ACCESS_TOKEN_EXPIRE_MINUTES - 1) * 60 * 1000; // Refresh 1 minute before expiry

// Utility for generating correlation IDs for request tracing
const generateCorrelationId = () => {
  return `auth_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

// Enhanced logging utility for authentication
const authLogger = {
  log: (message, data = {}, correlationId = null) => {
    const timestamp = new Date().toISOString();
    const logData = {
      timestamp,
      message,
      correlationId,
      ...data
    };
    console.log(`🔐 AUTH [${timestamp}]:`, message, logData);
  },
  error: (message, error, data = {}, correlationId = null) => {
    const timestamp = new Date().toISOString();
    const logData = {
      timestamp,
      message,
      correlationId,
      error: error?.message || error,
      stack: error?.stack,
      response: error?.response?.data,
      status: error?.response?.status,
      ...data
    };
    console.error(`❌ AUTH ERROR [${timestamp}]:`, message, logData);
  },
  timing: (operation, duration, correlationId = null) => {
    console.log(`⏱️  AUTH TIMING [${new Date().toISOString()}]:`, operation, `${duration}ms`, { correlationId });
  }
};

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
  const [backendStatus, setBackendStatus] = useState('unknown'); // unknown, checking, ready, failed
  const navigate = useNavigate();

  // Backend health check with detailed logging
  const checkBackendHealth = useCallback(async (correlationId = null) => {
    const startTime = Date.now();
    authLogger.log('🏥 Starting backend health check', { url: `${API_URL}/health` }, correlationId);
    
    try {
      setBackendStatus('checking');
      
      const response = await fetch(`${API_URL}/health`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-Correlation-ID': correlationId || generateCorrelationId()
        }
      });
      
      const duration = Date.now() - startTime;
      authLogger.timing('Backend health check', duration, correlationId);
      
      if (response.ok) {
        const data = await response.json();
        authLogger.log('✅ Backend health check successful', { 
          status: response.status, 
          data,
          duration: `${duration}ms`
        }, correlationId);
        setBackendStatus('ready');
        return true;
      } else {
        authLogger.error('❌ Backend health check failed', null, { 
          status: response.status,
          statusText: response.statusText,
          duration: `${duration}ms`
        }, correlationId);
        setBackendStatus('failed');
        return false;
      }
    } catch (error) {
      const duration = Date.now() - startTime;
      authLogger.error('❌ Backend health check error', error, { 
        duration: `${duration}ms`
      }, correlationId);
      setBackendStatus('failed');
      return false;
    }
  }, []);

  const refreshAccessToken = useCallback(async (shouldRedirect = true) => {
    const correlationId = generateCorrelationId();
    const startTime = Date.now();
    
    authLogger.log('🔄 Starting token refresh', { shouldRedirect }, correlationId);
    
    try {
      const response = await api.post('/auth/refresh', {}, {
        headers: { 'X-Correlation-ID': correlationId }
      });
      
      const duration = Date.now() - startTime;
      authLogger.timing('Token refresh', duration, correlationId);
      
      const newToken = response.data.access_token;
      setAccessToken(newToken);
      
      authLogger.log('✅ Token refresh successful', { 
        tokenLength: newToken?.length,
        duration: `${duration}ms`
      }, correlationId);
      
      return newToken;
    } catch (error) {
      const duration = Date.now() - startTime;
      authLogger.error('❌ Token refresh failed', error, { 
        duration: `${duration}ms`
      }, correlationId);
      
      // Clear user state and tokens
      setUser(null);
      setAccessToken(null);
      
      // Only set error and redirect if explicitly requested and not on login page
      if (shouldRedirect && window.location.pathname !== '/login') {
        setError('Session expired. Please login again.');
        navigate('/login');
      }
      throw error;
    }
  }, [navigate]);

  // Check for existing session
  useEffect(() => {
    let mounted = true;
    const correlationId = generateCorrelationId();
    
    const checkAuth = async () => {
      if (!mounted) return;
      
      authLogger.log('🔍 Starting session validation on mount', {}, correlationId);
      
      try {
        setLoading(true);
        setError(null);
        
        // First try to refresh the token - but handle the case where there's no session gracefully
        const newToken = await refreshAccessToken(false);
        
        if (mounted && newToken) {
          const userStartTime = Date.now();
          // Then get user data with the new token
          const userResponse = await api.get('/auth/user', {
            headers: { 
              Authorization: `Bearer ${newToken}`,
              'X-Correlation-ID': correlationId
            }
          });
          
          const userDuration = Date.now() - userStartTime;
          authLogger.timing('Get user data', userDuration, correlationId);
          
          setUser(userResponse.data);
          authLogger.log('✅ Session validation successful', { 
            userId: userResponse.data?.id,
            userEmail: userResponse.data?.email
          }, correlationId);
        }
      } catch (error) {
        authLogger.log('ℹ️  No existing session found (normal for new visitors)', { 
          error: error.message 
        }, correlationId);
        
        if (mounted) {
          // If there's no valid session, just clear state and don't show error message
          // This is normal for a fresh visit to the site
          setUser(null);
          setAccessToken(null);
          // Only show error and navigate if we're not already on the login page
          if (window.location.pathname !== '/login') {
            setError(null); // Don't show session expired error on first load
          }
        }
      } finally {
        if (mounted) {
          setLoading(false);
          authLogger.log('🏁 Session validation completed', {}, correlationId);
        }
      }
    };

    checkAuth();

    return () => {
      mounted = false;
    };
  }, [refreshAccessToken]);

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
    const correlationId = generateCorrelationId();
    const overallStartTime = Date.now();
    
    authLogger.log('🚀 Starting login success handler', {
      hasAccessToken: !!tokenResponse.access_token,
      hasIdToken: !!tokenResponse.id_token,
      accessTokenLength: tokenResponse.access_token?.length,
      idTokenLength: tokenResponse.id_token?.length
    }, correlationId);
    
    try {
      // Create a dedicated axios instance for OAuth with specific configuration
      const oauthApi = axios.create({
        baseURL: API_URL,
        withCredentials: true,
        timeout: 30000, // Increased to 30 seconds for cold starts
        headers: {
          'Content-Type': 'application/json',
          'X-Correlation-ID': correlationId
        }
      });
      
      const payload = {
        token: tokenResponse.access_token,
        id_token: tokenResponse.id_token
      };
      
      authLogger.log('📤 Sending tokens to backend', {
        url: `${API_URL}/auth/google`,
        payloadKeys: Object.keys(payload),
        backendStatus
      }, correlationId);
      
      const backendStartTime = Date.now();
      const result = await oauthApi.post('/auth/google', payload);
      const backendDuration = Date.now() - backendStartTime;
      
      authLogger.timing('Backend OAuth processing', backendDuration, correlationId);
      
      const overallDuration = Date.now() - overallStartTime;
      
      authLogger.log('✅ Login successful', {
        userId: result.data.user?.id,
        userEmail: result.data.user?.email,
        hasAccessToken: !!result.data.access_token,
        backendDuration: `${backendDuration}ms`,
        overallDuration: `${overallDuration}ms`
      }, correlationId);
      
      setUser(result.data.user);
      setAccessToken(result.data.access_token);
      setError(null);
      navigate('/');
    } catch (error) {
      const overallDuration = Date.now() - overallStartTime;
      
      authLogger.error('❌ Login failed', error, {
        overallDuration: `${overallDuration}ms`,
        backendStatus,
        url: error.config?.url,
        method: error.config?.method
      }, correlationId);
      
      setError(error.response?.data?.detail || 'Failed to login. Please try again.');
      throw error;
    }
  };

  const login = useGoogleLogin({
    onSuccess: handleLoginSuccess,
    onError: (error) => {
      const correlationId = generateCorrelationId();
      authLogger.error('❌ Google OAuth failed', error, {}, correlationId);
      setError('Google authentication failed. Please try again.');
    },
    flow: 'implicit'
  });

  // Enhanced login function with backend pre-warming (Option 2)
  const initiateLogin = useCallback(async () => {
    const correlationId = generateCorrelationId();
    const totalStartTime = Date.now();
    
    authLogger.log('🎯 OPTION 2: Starting enhanced login with backend pre-warming', {
      currentBackendStatus: backendStatus
    }, correlationId);
    
    try {
      setError(null);
      
      // Step 1: Pre-warm backend if needed
      if (backendStatus !== 'ready') {
        authLogger.log('🔥 Pre-warming backend before OAuth', {}, correlationId);
        
        const healthResult = await checkBackendHealth(correlationId);
        
        if (!healthResult) {
          authLogger.error('❌ Backend pre-warm failed, proceeding anyway', null, {}, correlationId);
          // Don't fail here - still attempt login in case it was a transient issue
        } else {
          authLogger.log('✅ Backend pre-warm successful', {}, correlationId);
        }
      } else {
        authLogger.log('✅ Backend already ready, skipping pre-warm', {}, correlationId);
      }
      
      // Step 2: Initiate Google OAuth
      const oauthStartTime = Date.now();
      authLogger.log('🔑 Starting Google OAuth flow', {}, correlationId);
      
      // Store correlation ID for the OAuth flow
      window.authCorrelationId = correlationId;
      
      await login();
      
      const oauthDuration = Date.now() - oauthStartTime;
      const totalDuration = Date.now() - totalStartTime;
      
      authLogger.timing('Google OAuth flow', oauthDuration, correlationId);
      authLogger.timing('Total enhanced login flow', totalDuration, correlationId);
      
    } catch (error) {
      const totalDuration = Date.now() - totalStartTime;
      authLogger.error('❌ Enhanced login flow failed', error, {
        totalDuration: `${totalDuration}ms`,
        step: backendStatus === 'ready' ? 'oauth' : 'pre_warm'
      }, correlationId);
      
      setError(error.message || 'Login failed. Please try again.');
      throw error;
    }
  }, [login, checkBackendHealth, backendStatus]);

  const logout = async () => {
    const correlationId = generateCorrelationId();
    authLogger.log('👋 Starting logout', {}, correlationId);
    
    try {
      await api.post('/auth/logout', {}, {
        headers: { 'X-Correlation-ID': correlationId }
      });
      
      setUser(null);
      setAccessToken(null);
      setError(null);
      setBackendStatus('unknown');
      
      authLogger.log('✅ Logout successful', {}, correlationId);
      navigate('/login');
    } catch (error) {
      authLogger.error('❌ Logout failed, forcing local logout', error, {}, correlationId);
      
      // Force logout even if the API call fails
      setUser(null);
      setAccessToken(null);
      setBackendStatus('unknown');
      navigate('/login');
    }
  };

  // Export the api instance for use in other components
  const getApi = useCallback(() => api, []);
  
  // Export the unauthenticated api instance for AI configuration endpoints
  const getUnauthenticatedApi = useCallback(() => unauthenticatedApi, []);

  return (
    <AuthContext.Provider value={{ 
      user, 
      loading, 
      error, 
      accessToken, 
      backendStatus,
      login: initiateLogin, // Use enhanced login instead of direct Google login
      logout, 
      getApi, 
      getUnauthenticatedApi,
      checkBackendHealth
    }}>
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