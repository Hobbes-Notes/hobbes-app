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
  headers: {
    'Content-Type': 'application/json',
  },
});

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
export const getProjects = () => api.get('/projects');
export const createProject = (project) => api.post('/projects', project);
export const getProject = (id) => api.get(`/projects/${id}`);

// Note endpoints
export const getNotes = (projectId) => api.get('/notes', { params: { project_id: projectId } });
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
export const createNote = (note) => api.post('/notes', note);

export default api; 