import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for debugging
api.interceptors.request.use(request => {
  console.log('Starting Request:', request);
  return request;
});

// Add response interceptor for debugging
api.interceptors.response.use(
  response => {
    console.log('Response:', response);
    return response;
  },
  error => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const getProjects = () => api.get('/projects');
export const createProject = (project) => api.post('/projects', project);
export const getProject = (id) => api.get(`/projects/${id}`);
export const getNotes = (projectId) => api.get(`/projects/${projectId}/notes`);
export const createNote = (projectId, note) => api.post(`/projects/${projectId}/notes`, note);

export default api; 