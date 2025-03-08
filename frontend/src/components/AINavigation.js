import React from 'react';
import { Link, useLocation } from 'react-router-dom';

/**
 * Navigation component for AI-related pages
 * Provides links to switch between AI Configuration and AI Files pages
 */
const AINavigation = () => {
  const location = useLocation();
  
  return (
    <div className="bg-white shadow-sm mb-6">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex space-x-8">
              <Link
                to="/ai-config"
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                  location.pathname === '/ai-config'
                    ? 'border-blue-500 text-gray-900'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                }`}
              >
                AI Configuration
              </Link>
              <Link
                to="/ai-files"
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                  location.pathname === '/ai-files'
                    ? 'border-blue-500 text-gray-900'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                }`}
              >
                AI Files
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AINavigation; 