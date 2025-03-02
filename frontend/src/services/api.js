import { useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';

// Utility for generating correlation IDs
const generateCorrelationId = () => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

// Error handling utilities
const formatErrorDetails = (error) => {
  return {
    code: error.response?.status,
    data: error.response?.data,
    url: error.config?.url,
    method: error.config?.method,
    timestamp: new Date().toISOString(),
    correlationId: error.config?.correlationId,
    requestData: error.config?.data,
    stack: error.stack
  };
};

const logError = (context, error) => {
  if (process.env.NODE_ENV === 'development') {
    console.group(`🔴 API Error: ${context}`);
    console.error('Error Details:', formatErrorDetails(error));
    console.error('Stack:', error.stack);
    console.groupEnd();
  }
};

const logRequest = (config) => {
  if (process.env.NODE_ENV === 'development') {
    console.group(`🔵 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    console.log('Correlation ID:', config.correlationId);
    console.log('Timestamp:', new Date().toISOString());
    console.log('Headers:', config.headers);
    if (config.data) console.log('Data:', config.data);
    if (config.params) console.log('Params:', config.params);
    console.groupEnd();
  }
};

const logResponse = (response) => {
  if (process.env.NODE_ENV === 'development') {
    const duration = Date.now() - response.config.requestTime;
    console.group(`🟢 API Response: ${response.config.method?.toUpperCase()} ${response.config.url}`);
    console.log('Correlation ID:', response.config.correlationId);
    console.log('Status:', response.status);
    console.log('Duration:', `${duration}ms`);
    console.log('Data:', response.data);
    console.groupEnd();
  }
};

// API Hook for internal use
export const useApi = () => {
  const { getApi } = useAuth();
  const api = getApi();

  // Request interceptor with correlation ID and timing
  api.interceptors.request.use(
    (config) => {
      config.correlationId = generateCorrelationId();
      config.requestTime = Date.now();
      logRequest(config);
      return config;
    },
    (error) => {
      logError('Request Interceptor', error);
      return Promise.reject(error);
    }
  );

  // Response interceptor with timing and error handling
  api.interceptors.response.use(
    (response) => {
      logResponse(response);
      return response;
    },
    (error) => {
      logError('Response Interceptor', error);
      return Promise.reject(error);
    }
  );

  return api;
};

// Export individual API functions that use the hook internally
export const useApiService = () => {
  const api = useApi();

  return {
    // Projects
    getProjects: useCallback(async () => {
      return api.get('/projects');
    }, [api]),

    createProject: useCallback(async (projectData) => {
      return api.post('/projects', projectData);
    }, [api]),

    getProject: useCallback(async (id) => {
      return api.get(`/projects/${id}`);
    }, [api]),

    updateProject: useCallback(async (id, data) => {
      return api.put(`/projects/${id}`, data);
    }, [api]),

    deleteProject: useCallback(async (id) => {
      return api.delete(`/projects/${id}`);
    }, [api]),

    // Notes
    getNotes: useCallback(async (projectId) => {
      return api.get(`/notes${projectId ? `?project_id=${projectId}` : ''}`);
    }, [api]),

    getAllNotes: useCallback(async () => {
      return api.get('/notes');
    }, [api]),

    getNote: useCallback(async (id) => {
      return api.get(`/notes/${id}`);
    }, [api]),

    createNote: useCallback(async (content, user_id) => {
      return api.post('/notes', { content, user_id });
    }, [api])
  };
}; 