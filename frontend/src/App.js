import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import ProjectList from './components/ProjectList';
import ProjectDetail from './components/ProjectDetail';
import AddNoteForm from './components/AddNoteForm';

const Layout = () => {
    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            <div className="flex-1 relative">
                <div className="absolute inset-0 pb-[200px] overflow-y-auto">
                    <Outlet />
                </div>
            </div>
            <AddNoteForm />
        </div>
    );
};

function App() {
    return (
        <Router>
            <Routes>
                <Route element={<Layout />}>
                    <Route path="/" element={<Navigate to="/projects" replace />} />
                    <Route path="/*" element={<ProjectList />}>
                        <Route path="projects/:projectId" element={<ProjectDetail />} />
                        <Route path="projects" element={<div className="flex items-center justify-center h-full text-gray-500">Select a project or create a new one</div>} />
                    </Route>
                </Route>
            </Routes>
        </Router>
    );
}

export default App; 