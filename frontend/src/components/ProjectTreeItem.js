import React, { useState } from 'react';
import { ChevronRight, ChevronDown, PlusIcon, PencilIcon, TrashIcon } from 'lucide-react';

const DeleteConfirmationDialog = ({ project, onConfirm, onCancel }) => (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div className="bg-white rounded-lg p-6 max-w-sm w-full mx-4 shadow-xl">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">Delete Project</h3>
      <p className="text-gray-600 mb-2">
        Are you sure you want to delete "{project.name}"?
      </p>
      {project.level < 5 && (
        <p className="text-red-600 text-sm mb-4">
          Warning: This will also delete all child projects under this project.
        </p>
      )}
      <div className="flex justify-end space-x-4">
        <button
          onClick={onCancel}
          className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={onConfirm}
          className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
        >
          Delete
        </button>
      </div>
    </div>
  </div>
);

const ProjectTreeItem = ({
  project,
  projects,
  level = 1,
  currentProjectId,
  onNavigate,
  onAddChild,
  onEdit,
  onDelete
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Find child projects
  const childProjects = projects.filter(p => p.parent_id === project.id);
  const hasChildren = childProjects.length > 0;

  // Calculate indentation based on level
  const indentationStyle = {
    paddingLeft: `${level * 16}px`
  };

  const handleDelete = () => {
    setShowDeleteConfirm(true);
  };

  const handleDeleteConfirm = () => {
    onDelete(project.id);
    setShowDeleteConfirm(false);
  };

  const handleDeleteCancel = () => {
    setShowDeleteConfirm(false);
  };

  return (
    <>
      {showDeleteConfirm && (
        <DeleteConfirmationDialog
          project={project}
          onConfirm={handleDeleteConfirm}
          onCancel={handleDeleteCancel}
        />
      )}
      
      <div
        className={`group flex items-center justify-between py-2 transition-colors ${
          currentProjectId === project.id
            ? 'bg-blue-50 text-blue-700'
            : 'hover:bg-gray-50'
        }`}
        style={indentationStyle}
      >
        <div className="flex items-center flex-1 min-w-0">
          {hasChildren ? (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1 text-gray-400 hover:text-gray-600"
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>
          ) : (
            <div className="w-6" /> /* Spacer for alignment */
          )}
          
          <button
            onClick={() => onNavigate(project.id)}
            className="flex-1 text-left truncate px-2"
          >
            <span className="font-medium">{project.name}</span>
          </button>
        </div>

        <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity pr-2">
          {/* Only show add child button if not at max level */}
          {(project.level || 1) < 5 && (
            <button
              onClick={() => onAddChild(project.id)}
              className="p-1 text-gray-400 hover:text-green-500 transition-colors"
              title="Add child project"
            >
              <PlusIcon className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={() => onEdit(project)}
            className="p-1 text-gray-400 hover:text-blue-500 transition-colors"
            title="Edit project"
          >
            <PencilIcon className="w-4 h-4" />
          </button>
          <button
            onClick={handleDelete}
            className="p-1 text-gray-400 hover:text-red-500 transition-colors"
            title="Delete project"
          >
            <TrashIcon className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Render child projects if expanded */}
      {isExpanded && hasChildren && (
        <div>
          {childProjects.map(childProject => (
            <ProjectTreeItem
              key={childProject.id}
              project={childProject}
              projects={projects}
              level={level + 1}
              currentProjectId={currentProjectId}
              onNavigate={onNavigate}
              onAddChild={onAddChild}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </>
  );
};

export default ProjectTreeItem; 