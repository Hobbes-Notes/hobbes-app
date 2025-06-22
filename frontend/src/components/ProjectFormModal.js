import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';

const ProjectFormModal = ({ 
  isOpen, 
  onClose, 
  onSubmit, 
  initialData = { name: '', description: '' },
  title = 'New Project',
  submitLabel = 'Create',
  isSubmitting = false,
  error = null,
  projects = [],
  editingProjectId = null,
  parentProject = null
}) => {
  const [formData, setFormData] = useState(initialData);
  const [validationErrors, setValidationErrors] = useState({});

  // Reset form when modal opens with new data
  useEffect(() => {
    if (isOpen) {
      setFormData(initialData);
      setValidationErrors({});
    }
  }, [isOpen, initialData]);

  const validateForm = () => {
    const errors = {};
    
    // Validate name
    if (!formData.name || formData.name.trim().length < 3) {
      errors.name = `Project name must be at least 3 characters long (current length: ${formData.name ? formData.name.trim().length : 0})`;
    } else {
      // Check for duplicate project names (case insensitive)
      const normalizedName = formData.name.trim().toLowerCase();
      const projectExists = projects.some(project => 
        project.id !== editingProjectId &&
        project.name.toLowerCase() === normalizedName
      );
      
      if (projectExists) {
        errors.name = `A project with the name '${formData.name.trim()}' already exists`;
      }
    }
    
    // Validate description if provided
    if (formData.description && formData.description.trim().length < 5) {
      errors.description = `Project description must be at least 5 characters long (current length: ${formData.description.trim().length})`;
    }
    
    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  if (!isOpen) return null;

  // Combine all errors into an array
  const allErrors = [
    ...(error ? [error] : []),
    ...Object.values(validationErrors)
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          {allErrors.length > 0 && (
            <div className="space-y-2">
              {allErrors.map((err, index) => (
                <div key={index} className="p-3 text-sm text-red-700 bg-red-100 rounded-lg">
                  {err}
                </div>
              ))}
            </div>
          )}
          
          {/* Show parent project information */}
          {parentProject && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="text-sm text-blue-800">
                <span className="font-medium">Parent Project:</span> {parentProject.name}
                {parentProject.description && (
                  <div className="text-xs text-blue-600 mt-1">{parentProject.description}</div>
                )}
              </div>
            </div>
          )}
          
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Project Name
            </label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={(e) => {
                setFormData({ ...formData, name: e.target.value });
                if (validationErrors.name) {
                  setValidationErrors({ ...validationErrors, name: null });
                }
              }}
              className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                validationErrors.name ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Enter project name"
              required
              minLength={3}
            />
          </div>
          
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description (optional)
            </label>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) => {
                setFormData({ ...formData, description: e.target.value });
                if (validationErrors.description) {
                  setValidationErrors({ ...validationErrors, description: null });
                }
              }}
              className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none ${
                validationErrors.description ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Enter project description"
              rows="3"
            />
          </div>
          
          <div className="flex justify-end mt-6">
            <button
              type="button"
              onClick={onClose}
              className="mr-3 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className={`px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md transition-colors
                ${isSubmitting ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-700'}`}
            >
              {isSubmitting ? 'Saving...' : submitLabel}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProjectFormModal; 