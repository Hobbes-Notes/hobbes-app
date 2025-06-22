import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const BottomNavigation = () => {
  const [activeTab, setActiveTab] = useState('home');
  const navigate = useNavigate();
  const location = useLocation();

  // Update active tab based on current route
  useEffect(() => {
    if (location.pathname === '/projects-tree') {
      setActiveTab('projects');
    } else if (location.pathname === '/' || location.pathname.startsWith('/projects')) {
      setActiveTab('home');
    }
  }, [location.pathname]);

  const handleTabClick = (tab) => {
    if (tab === 'home') {
      setActiveTab(tab);
      navigate('/');
    } else if (tab === 'projects') {
      setActiveTab(tab);
      navigate('/projects-tree');
    }
    // Notepad is not clickable for now
  };

  const tabs = [
    {
      id: 'home',
      label: 'Home',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      ),
      enabled: true
    },
    {
      id: 'notepad',
      label: 'Notepad',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
      ),
      enabled: false
    },
    {
      id: 'projects',
      label: 'Projects',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      ),
      enabled: true
    }
  ];

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg z-50">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-around items-center py-2">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => handleTabClick(tab.id)}
              disabled={!tab.enabled}
              className={`flex flex-col items-center justify-center py-2 px-4 min-w-0 flex-1 transition-colors duration-200 ${
                activeTab === tab.id && tab.enabled
                  ? 'text-blue-600 bg-blue-50 rounded-lg'
                  : tab.enabled
                  ? 'text-gray-600 hover:text-blue-600 hover:bg-gray-50 rounded-lg'
                  : 'text-gray-300 cursor-not-allowed'
              }`}
            >
              <div className="mb-1">
                {tab.icon}
              </div>
              <span className="text-xs font-medium truncate">
                {tab.label}
              </span>
              {!tab.enabled && (
                <span className="text-xs text-gray-400 mt-1">
                  Coming Soon
                </span>
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default BottomNavigation; 