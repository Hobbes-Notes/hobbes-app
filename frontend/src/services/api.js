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
  return getApi();
};

// Create an unauthenticated API client for AI configuration endpoints
export const useUnauthenticatedApi = () => {
  const { getUnauthenticatedApi } = useAuth();
  return getUnauthenticatedApi();
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

    getAllNotes: useCallback(async (userId) => {
      const params = new URLSearchParams();
      if (userId) params.append('user_id', userId);
      return api.get(`/notes?${params.toString()}`);
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

    // Action Items
    getActionItems: useCallback(async () => {
      return api.get('/action-items');
    }, [api]),

    getActionItemsByProject: useCallback(async (projectId) => {
      if (!projectId) {
        throw new Error('Project ID is required');
      }
      return api.get(`/action-items/project/${projectId}`);
    }, [api]),

    createActionItem: useCallback(async (actionItemData) => {
      return api.post('/action-items', actionItemData);
    }, [api]),

    updateActionItem: useCallback(async (id, updateData) => {
      return api.put(`/action-items/${id}`, updateData);
    }, [api]),

    deleteActionItem: useCallback(async (id) => {
      return api.delete(`/action-items/${id}`);
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
    }, [unauthenticatedApi]),

    getAIConfigurationResponseFormat: useCallback(async (useCase) => {
      return unauthenticatedApi.get(`/ai/configurations/${useCase}/response_format`);
    }, [unauthenticatedApi]),

    // AI Use Cases
    getAIUseCases: useCallback(async () => {
      return unauthenticatedApi.get('/ai/use-cases');
    }, [unauthenticatedApi]),

    // AI Files
    getAIFiles: useCallback(async () => {
      return api.get('/ai/files');
    }, [api]),

    uploadAIFile: useCallback(async (formData) => {
      return api.post('/ai/files', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
    }, [api]),

    getAIFile: useCallback(async (fileId) => {
      return api.get(`/ai/files/${fileId}`);
    }, [api]),

    interruptAIFile: useCallback(async (fileId) => {
      return api.post(`/ai/files/${fileId}/interrupt`);
    }, [api])
  };
};