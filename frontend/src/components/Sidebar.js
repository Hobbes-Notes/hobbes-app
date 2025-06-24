import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  FolderIcon,
  CheckSquareIcon,
  ChevronDownIcon, 
  ChevronRightIcon
} from 'lucide-react';

// Filter Tree Item Component - simplified version of ProjectTreeItem for filtering
const FilterTreeItem = ({ 
  project, 
  projects, 
  level = 1, 
  selectedFilterProject, 
  onFilterProjectChange 
}) => {
  const [isExpanded, setIsExpanded] = useState(true); // Default to expanded for filter tree

  // Find child projects
  const childProjects = projects.filter(p => p.parent_id === project.id);
  const hasChildren = childProjects.length > 0;

  // Calculate indentation based on level (minimal spacing for filter tree)
  const indentationStyle = {
    paddingLeft: `${level * 4}px`
  };

  return (
    <>
      <div
        className={`group flex items-center py-1 transition-colors cursor-pointer ${
          selectedFilterProject === project.id
            ? 'bg-blue-50 text-blue-700'
            : 'hover:bg-gray-50'
        }`}
        style={indentationStyle}
        onClick={() => onFilterProjectChange && onFilterProjectChange(project.id)}
      >
        <div className="flex items-center flex-1 min-w-0">
          {hasChildren ? (
            <button
              onClick={(e) => {
                e.stopPropagation();
                setIsExpanded(!isExpanded);
              }}
              className="p-1 text-gray-400 hover:text-gray-600"
            >
              {isExpanded ? (
                <ChevronDownIcon className="w-3 h-3" />
              ) : (
                <ChevronRightIcon className="w-3 h-3" />
              )}
            </button>
          ) : (
            <div className="w-5" /> /* Spacer for alignment */
          )}
          
          <div className="flex items-center space-x-2 flex-1 text-left truncate px-2">
            <FolderIcon className="w-3 h-3 text-gray-400" />
            <span className="text-sm">{project.name}</span>
          </div>
        </div>
      </div>

      {/* Render child projects if expanded */}
      {isExpanded && hasChildren && (
        <div>
          {childProjects.map(childProject => (
            <FilterTreeItem
              key={childProject.id}
              project={childProject}
              projects={projects}
              level={level + 1}
              selectedFilterProject={selectedFilterProject}
              onFilterProjectChange={onFilterProjectChange}
            />
          ))}
        </div>
      )}
    </>
  );
};

const Sidebar = ({ 
  projects = [], 
  onProjectCreated, 
  onProjectDeleted,
  selectedFilterProject = null,
  onFilterProjectChange
}) => {
  const navigate = useNavigate(); // Keep for potential navigation needs

  // No collapsible sections needed anymore - Projects section removed
  // All project management handlers removed - use Projects Tab for project management

  // Filter root projects (those without a parent)
  const rootProjects = projects.filter(p => !p.parent_id);

  return (
    <div className="h-full flex flex-col">
      {/* Project Form Modal removed - use Projects Tab for project management */}

      {/* Project Filter Section */}
      <div className="border-b border-gray-200 bg-gray-50">
        <div className="px-3 py-2">
          <div className="flex items-center space-x-2">
            <CheckSquareIcon className="w-4 h-4" />
            <span className="text-sm font-semibold text-gray-700 uppercase tracking-wider">Filter Action Items</span>
          </div>
        </div>
        
        <div className="px-3 pb-3">
          {/* Projects Tree for filtering */}
          <div className="space-y-0.5">
            {rootProjects.map((project) => (
              <FilterTreeItem
                key={project.id}
                project={project}
                projects={projects}
                selectedFilterProject={selectedFilterProject}
                onFilterProjectChange={onFilterProjectChange}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Collapsible Sections */}
      <div className="flex-1 overflow-y-auto">
        {/* Projects Section Removed - Use Projects Tab for project management */}
      </div>
    </div>
  );
};

export default Sidebar; 