import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ProjectList from './components/ProjectList';
import ProjectDetail from './components/ProjectDetail';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<ProjectList />}>
          <Route path="/projects/:projectId" element={<ProjectDetail />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App; 