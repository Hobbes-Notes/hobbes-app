import { useCallback } from 'react';
import { useAuth } from '../hooks/useAuth';
import { createLogger } from '../utils/logging';

// Create a logger for the API service
const logger = createLogger('API Service');

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
  logger.logError(`${context} - Error`, formatErrorDetails(error));
};

const logRequest = (config) => {
  logger.log(`Request: ${config.method?.toUpperCase()} ${config.url}`, {
    correlationId: config.correlationId,
    timestamp: new Date().toISOString(),
    headers: config.headers,
    data: config.data,
    params: config.params
  });
};

const logResponse = (response) => {
  const duration = Date.now() - response.config.requestTime;
  logger.log(`Response: ${response.config.method?.toUpperCase()} ${response.config.url}`, {
    correlationId: response.config.correlationId,
    status: response.status,
    duration: `${duration}ms`,
    data: response.data
  });
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

// Create an unauthenticated API client for AI configuration endpoints
export const useUnauthenticatedApi = () => {
  const { getUnauthenticatedApi } = useAuth();
  const api = getUnauthenticatedApi();

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
  const unauthenticatedApi = useUnauthenticatedApi();

  return {
    // Projects
    getProjects: useCallback(async (user_id) => {
      if (!user_id) {
        throw new Error('User ID is required');
      }
      return api.get(`/projects?user_id=${user_id}`);
    }, [api]),

    createProject: useCallback(async (projectData) => {
      return api.post('/projects', projectData);
    }, [api]),

    getProject: useCallback(async (id) => {
      return api.get(`/projects/${id}`);
    }, [api]),

    updateProject: useCallback(async (id, data) => {
      return api.patch(`/projects/${id}`, data);
    }, [api]),

    deleteProject: useCallback(async (id) => {
      return api.delete(`/projects/${id}`);
    }, [api]),

    // Notes
    getNotes: useCallback(async (projectId, userId, page = 1, pageSize = 10, cursor = null) => {
      const params = new URLSearchParams();
      if (projectId) params.append('project_id', projectId);
      if (userId) params.append('user_id', userId);
      if (cursor) params.append('exclusive_start_key', JSON.stringify(cursor));
      params.append('page', page);
      params.append('page_size', pageSize);
      return api.get(`/notes?${params.toString()}`);
    }, [api]),

    getAllNotes: useCallback(async () => {
      return api.get('/notes');
    }, [api]),

    getNote: useCallback(async (id) => {
      return api.get(`/notes/${id}`);
    }, [api]),

    createNote: useCallback(async (content, user_id, project_id = null) => {
      const noteData = { content, user_id };
      if (project_id) {
        noteData.project_id = project_id;
      }
      return api.post('/notes', noteData);
    }, [api]),

    // AI Configurations (using unauthenticated API)
    getAllAIConfigurations: useCallback(async (useCase) => {
      return unauthenticatedApi.get(`/ai/configurations/${useCase}`);
    }, [unauthenticatedApi]),

    getActiveAIConfiguration: useCallback(async (useCase) => {
      return unauthenticatedApi.get(`/ai/configurations/${useCase}/active`);
    }, [unauthenticatedApi]),

    getAIConfiguration: useCallback(async (useCase, version) => {
      return unauthenticatedApi.get(`/ai/configurations/${useCase}/${version}`);
    }, [unauthenticatedApi]),

    createAIConfiguration: useCallback(async (configuration) => {
      return unauthenticatedApi.post('/ai/configurations', configuration);
    }, [unauthenticatedApi]),

    setActiveAIConfiguration: useCallback(async (useCase, version) => {
      return unauthenticatedApi.put(`/ai/configurations/${useCase}/${version}/activate`);
    }, [unauthenticatedApi]),

    deleteAIConfiguration: useCallback(async (useCase, version) => {
      return unauthenticatedApi.delete(`/ai/configurations/${useCase}/${version}`);
    }, [unauthenticatedApi]),

    getAIConfigurationParameters: useCallback(async (useCase) => {
      return unauthenticatedApi.get(`/ai/configurations/${useCase}/parameters`);
    }, [unauthenticatedApi])
  };
};