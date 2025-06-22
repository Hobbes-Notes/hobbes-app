import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { AuthProvider } from './hooks/useAuth';
import { ProtectedRoute } from './components/ProtectedRoute';
import TopBar from './components/TopBar';
import BottomNavigation from './components/BottomNavigation';
import LoginPage from './components/LoginPage';
import ProfilePage from './components/ProfilePage';
import ProjectsPage from './components/ProjectsPage';
import ProjectsTreePage from './components/ProjectsTreePage';
import NotesPage from './components/NotesPage';
import NotesView from './components/NotesView';
import ProjectView from './components/ProjectView';
import ActionItemsPage from './components/ActionItemsPage';
import AIConfigPage from './components/AIConfigPage';
import AIFilesPage from './components/AIFilesPage';

// Create a layout component for protected routes
const ProtectedLayout = ({ children }) => (
  <div className="min-h-screen bg-gray-100">
    <TopBar />
    <div className="pt-0 pb-20">
      {children}
    </div>
    <BottomNavigation />
  </div>
);

function App() {
  const clientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;

  if (!clientId) {
    console.error('REACT_APP_GOOGLE_CLIENT_ID is not set');
    return <div>Error: Google Client ID not configured</div>;
  }

  return (
    <GoogleOAuthProvider clientId={clientId}>
      <Router>
        <AuthProvider>
          <div className="min-h-screen bg-gray-100">
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <ProtectedLayout>
                      <ProjectsPage />
                    </ProtectedLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/projects"
                element={
                  <ProtectedRoute>
                    <ProtectedLayout>
                      <ProjectsPage />
                    </ProtectedLayout>
                  </ProtectedRoute>
                }
              >
                <Route path=":projectId" element={<ProjectView />} />
              </Route>
              <Route
                path="/notes"
                element={
                  <ProtectedRoute>
                    <ProtectedLayout>
                      <ProjectsPage />
                    </ProtectedLayout>
                  </ProtectedRoute>
                }
              >
                <Route path=":noteId" element={<NotesView />} />
              </Route>
              <Route
                path="/action-items"
                element={
                  <ProtectedRoute>
                    <ProtectedLayout>
                      <ProjectsPage />
                    </ProtectedLayout>
                  </ProtectedRoute>
                }
              >
                <Route index element={<ActionItemsPage />} />
                <Route path=":actionItemId" element={<ActionItemsPage />} />
              </Route>
              <Route
                path="/projects/:projectId/notes"
                element={
                  <ProtectedRoute>
                    <ProtectedLayout>
                      <NotesPage />
                    </ProtectedLayout>
                  </ProtectedRoute>
                }
              />
              <Route
                path="/profile"
                element={
                  <ProtectedRoute>
                    <ProtectedLayout>
                      <ProfilePage />
                    </ProtectedLayout>
                  </ProtectedRoute>
                }
              />
              <Route path="/projects-tree" element={
                <ProtectedRoute>
                  <ProtectedLayout>
                    <ProjectsTreePage />
                  </ProtectedLayout>
                </ProtectedRoute>
              } />
              <Route path="/ai-config" element={
                <ProtectedLayout>
                  <AIConfigPage />
                </ProtectedLayout>
              } />
              <Route path="/ai-files" element={
                <ProtectedLayout>
                  <AIFilesPage />
                </ProtectedLayout>
              } />
            </Routes>
          </div>
        </AuthProvider>
      </Router>
    </GoogleOAuthProvider>
  );
}

export default App; 