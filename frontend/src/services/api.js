import axios from 'axios';

// Use environment variable for API URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8888';

// Debug API configuration
console.log('API Configuration:', {
  baseURL: API_URL,
  environment: process.env.NODE_ENV
});

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for authentication
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for handling auth errors
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', {
      url: response.config.url,
      status: response.status,
      data: response.data
    });
    return response;
  },
  async (error) => {
    console.error('API Error:', {
      url: error.config?.url,
      status: error.response?.status,
      data: error.response?.data
    });

    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Add request interceptor for debugging
api.interceptors.request.use(request => {
  console.log('API Request:', {
    method: request.method,
    url: request.url,
    baseURL: request.baseURL,
    headers: request.headers,
    params: request.params,
    data: request.data
  });
  const token = localStorage.getItem('token');
  if (token) {
    request.headers.Authorization = `Bearer ${token}`;
  }
  return request;
});

// Add response interceptor for debugging
api.interceptors.response.use(
  response => {
    console.log('API Response:', {
      status: response.status,
      statusText: response.statusText,
      data: response.data,
      headers: response.headers
    });
    return response;
  },
  error => {
    console.error('API Error:', {
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      config: error.config
    });
    return Promise.reject(error);
  }
);

// Project endpoints
export const getProjects = () => {
  return api.get('/projects');
};

export const createProject = (projectData) => {
  return api.post('/projects', projectData);
};

export const getProject = (id) => api.get(`/projects/${id}`);

export const updateProject = async (id, data) => {
  return await api.put(`/projects/${id}`, data);
};

export const deleteProject = async (id) => {
  return await api.delete(`/projects/${id}`);
};

// Note endpoints
export const getNotes = (projectId) => {
  return api.get(`/notes?project_id=${projectId}`);
};

export const getAllNotes = async () => {
  console.log('getAllNotes called');
  try {
    const response = await api.get('/notes');
    console.log('getAllNotes response:', response);
    return response;
  } catch (error) {
    console.error('getAllNotes error:', {
      message: error.message,
      response: error.response,
      request: error.request
    });
    throw error;
  }
};

export const getNote = (id) => api.get(`/notes/${id}`);

export const createNote = (content, user_id) => {
  return api.post('/notes', { content, user_id });
};

export const updateNote = async (projectId, noteId, data) => {
  return await api.put(`/projects/${projectId}/notes/${noteId}`, data);
};

export const deleteNote = async (projectId, noteId) => {
  return await api.delete(`/projects/${projectId}/notes/${noteId}`);
};

export const loginWithGoogle = async (token) => {
  console.log('Sending login request with token:', token);
  try {
    const response = await api.post('/auth/google', { token });
    console.log('Login response:', response.data);
    return response;
  } catch (error) {
    console.error('Login error:', error.response?.data || error.message);
    throw error;
  }
};

export const logoutUser = async () => {
  return await api.post('/auth/logout');
};

export const getUserActivity = async () => {
  try {
    console.log('Fetching user activities...');
    const token = localStorage.getItem('token');
    console.log('Auth token present:', !!token);
    
    const response = await api.get('/auth/activity');
    console.log('Activity API Response:', {
      status: response.status,
      headers: response.headers,
      data: response.data
    });

    // Return the activities array from the response data
    if (response.data?.status === 'success' && Array.isArray(response.data.data)) {
      return response.data.data;
    } else {
      console.warn('Invalid activity response format:', response.data);
      return [];
    }
  } catch (error) {
    console.error('Error fetching activities:', {
      message: error.message,
      status: error.response?.status,
      data: error.response?.data,
      headers: error.response?.headers
    });
    throw error;
  }
};

export default api; 